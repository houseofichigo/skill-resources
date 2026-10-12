// The render gate for components.html and the patterns. Called by
// components.py and patterns.py with one JSON argument (see uikit.render_gate).
//
// At each width it fails on what reading the source cannot show:
//   overflow   the document scrolls sideways
//   shadow     a computed box-shadow while effects.policy.shadow is none
//   font       a text element whose first computed family is not a loaded face
//   contrast   visible text under the a11y floors (background composited up
//              to the first opaque ancestor; disabled controls are exempt, as
//              WCAG 1.4.3 exempts inactive components)
//   target     an interactive element whose hit area is under a11y.target_min_px
//              in either dimension. The hit area is the element, its <label>s,
//              and an absolutely positioned ::after that extends it (.c-hit, the
//              documented dense-row exception). Inline links in running text are
//              exempt (WCAG 2.5.8 inline exception).
//   ink        a [data-surface=ink] whose background is not opaque (a var cycle)
// and saves out/shots/<name>-<width>.png for the book.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');

(async () => {
  const spec = JSON.parse(process.argv[2]);
  let b;
  const exe = process.env.CHROMIUM_PATH;
  try { b = await chromium.launch(exe ? { executablePath: exe } : {}); }
  catch (e) {
    try { b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' }); }
    catch (_) {
      console.error('cannot launch Chromium — set CHROMIUM_PATH or `npx playwright install chromium`');
      process.exit(1);
    }
  }
  const shots = path.join(spec.root, 'out', 'shots');
  fs.mkdirSync(shots, { recursive: true });
  const fails = [];
  let checked = 0, texts = 0, targets = 0;
  for (const f of spec.files) {
    for (const w of spec.widths) {
      const p = await b.newPage({ viewport: { width: w, height: 900 } });
      p.on('pageerror', e => fails.push(`${f.shot}@${w}: script error ${e.message}`));
      await p.goto('file://' + f.path, { waitUntil: 'load' });
      await p.evaluate(async (fams) => {
        await document.fonts.ready;
        const ws = new Set();
        document.querySelectorAll('body *').forEach(e => {
          const cs = getComputedStyle(e);
          ws.add(cs.fontWeight + '|' + cs.fontStyle);
        });
        for (const fam of fams) for (const x of ws) {
          const [wt, st] = x.split('|');
          try { await document.fonts.load(`${st} ${wt} 16px "${fam}"`); } catch (_) {}
        }
        await document.fonts.ready;
      }, spec.families);
      // play every authored moment once, then come back to the top
      const authored = await p.evaluate(() => {
        let n = 0;
        document.querySelectorAll('[data-authored]').forEach(a => {
          if (a.getClientRects().length) { a.scrollIntoView({ block: 'center' }); n++; }
        });
        return n;
      });
      if (authored) await p.waitForTimeout(1400);
      await p.evaluate(() => window.scrollTo(0, 0));
      await p.waitForTimeout(150);

      const r = await p.evaluate((spec) => {
        const out = { overflow: null, shadows: [], fonts: [], contrast: [], targets: [], ink: [], nText: 0, nTarget: 0 };
        const de = document.documentElement;
        const desc = e => {
          let s = e.tagName.toLowerCase();
          if (e.id) s += '#' + e.id;
          if (e.classList.length) s += '.' + [...e.classList].slice(0, 2).join('.');
          const t = (e.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 28);
          return t ? `${s} "${t}"` : s;
        };
        if (de.scrollWidth > de.clientWidth) {
          const wide = [...document.querySelectorAll('body *')].filter(e => {
            const r = e.getBoundingClientRect();
            return r.right > de.clientWidth + 1 && r.width > 0;
          }).slice(-4).map(desc);
          out.overflow = `${de.scrollWidth}>${de.clientWidth} ${wide.join(' | ')}`;
        }
        const all = [...document.querySelectorAll('body *')];
        // loaded faces
        const loaded = new Set();
        document.fonts.forEach(ff => { if (ff.status === 'loaded') loaded.add(ff.family.replace(/["']/g, '')); });
        const parse = s => {
          let m = s.match(/rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?\)/);
          if (m) return [+m[1], +m[2], +m[3], m[4] === undefined ? 1 : +m[4]];
          m = s.match(/color\(srgb ([\d.e-]+) ([\d.e-]+) ([\d.e-]+)(?: \/ ([\d.e-]+))?\)/);
          if (m) return [m[1] * 255, m[2] * 255, m[3] * 255, m[4] === undefined ? 1 : +m[4]];
          return null;
        };
        const over = (top, bot) => { // top over opaque bot
          const a = top[3];
          return [top[0] * a + bot[0] * (1 - a), top[1] * a + bot[1] * (1 - a), top[2] * a + bot[2] * (1 - a), 1];
        };
        const lum = c => {
          const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
          return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]);
        };
        const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
        const bgOf = e => {
          const layers = [];
          for (let n = e; n && n.nodeType === 1; n = n.parentElement) {
            const c = parse(getComputedStyle(n).backgroundColor);
            if (c && c[3] > 0) { layers.push(c); if (c[3] >= 1) break; }
          }
          let base = [255, 255, 255, 1];
          for (let i = layers.length - 1; i >= 0; i--) base = layers[i][3] >= 1 ? layers[i] : over(layers[i], base);
          return base;
        };
        const hidden = e => {
          for (let n = e; n && n.nodeType === 1; n = n.parentElement) {
            const cs = getComputedStyle(n);
            if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) return true;
          }
          return false;
        };
        const exempt = e => e.closest(':disabled, [aria-disabled="true"], [data-contrast="exempt"], [inert], label:has(:disabled)');
        for (const e of all) {
          const cs = getComputedStyle(e);
          if (cs.boxShadow && cs.boxShadow !== 'none') out.shadows.push(desc(e));
          if (e.matches('[data-surface="ink"]')) {
            const c = parse(cs.backgroundColor);
            if (!c || c[3] < 1) out.ink.push(`${desc(e)} bg=${cs.backgroundColor}`);
          }
          const own = [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
          if (!own) continue;
          const rect = e.getBoundingClientRect();
          if (rect.width < 1 || rect.height < 1 || hidden(e)) continue;
          if (e.closest('svg') && e.tagName.toLowerCase() !== 'text' && e.tagName.toLowerCase() !== 'tspan') continue;
          out.nText++;
          const fam = cs.fontFamily.split(',')[0].trim().replace(/["']/g, '');
          if (!loaded.has(fam)) out.fonts.push(`${desc(e)} → ${fam}`);
          if (exempt(e)) continue;
          const isSvg = e instanceof SVGElement;
          let fg = parse(isSvg ? cs.fill : cs.color);
          if (!fg) continue;
          const bg = bgOf(e);
          if (fg[3] < 1) fg = over(fg, bg);
          const size = parseFloat(cs.fontSize), wt = parseInt(cs.fontWeight, 10);
          const large = size >= 24 || (size >= 18.66 && wt >= 700);
          const need = large ? spec.large : spec.body;
          const cr = ratio(fg, bg);
          if (cr + 1e-6 < need) out.contrast.push(`${desc(e)} ${cr.toFixed(2)}<${need}`);
        }
        const SEL = 'a[href], button, input:not([type=hidden]), select, textarea, summary, [role=button], [role=tab], [role=menuitem], [role=option], [role=switch], [role=checkbox], [tabindex]:not([tabindex="-1"])';
        for (const e of document.querySelectorAll(SEL)) {
          if (e.closest('[inert], [aria-hidden="true"], [data-gate="skip"]')) continue;
          if (hidden(e)) continue;
          const r = e.getBoundingClientRect();
          if (r.width * r.height <= 1) continue;          // visually hidden (skip link at rest)
          out.nTarget++;
          let x0 = r.left, y0 = r.top, x1 = r.right, y1 = r.bottom;
          const grow = q => { x0 = Math.min(x0, q.left); y0 = Math.min(y0, q.top); x1 = Math.max(x1, q.right); y1 = Math.max(y1, q.bottom); };
          const ext = n => {   // an absolutely positioned ::after that extends the hit area
            const q = n.getBoundingClientRect(), af = getComputedStyle(n, '::after');
            grow(q);
            if (af.content !== 'none' && af.position === 'absolute') {
              const t = parseFloat(af.top), bt = parseFloat(af.bottom), l = parseFloat(af.left), rt = parseFloat(af.right);
              if (![t, bt, l, rt].some(isNaN)) grow({ left: q.left + l, top: q.top + t, right: q.right - rt, bottom: q.bottom - bt });
            }
          };
          ext(e);
          if (e.labels) for (const l of e.labels) ext(l);
          const W = x1 - x0, H = y1 - y0;
          if (W + 0.5 >= spec.target && H + 0.5 >= spec.target) continue;
          // inline link inside running text
          if (e.tagName === 'A' && getComputedStyle(e).display === 'inline') {
            const par = e.parentElement;
            const pt = (par.textContent || '').trim().length, et = (e.textContent || '').trim().length;
            if (pt > et + 1) continue;
          }
          out.targets.push(`${desc(e)} ${Math.round(W)}×${Math.round(H)}`);
        }
        return out;
      }, spec);
      checked++; texts += r.nText; targets += r.nTarget;
      const tag = `${f.shot}@${w}`;
      if (r.overflow) fails.push(`${tag}: horizontal overflow ${r.overflow}`);
      if (r.shadows.length && spec.shadow === 'none') fails.push(`${tag}: box-shadow on ${r.shadows.slice(0, 5).join(', ')}`);
      if (r.fonts.length) fails.push(`${tag}: fallback font on ${[...new Set(r.fonts)].slice(0, 5).join(', ')} (${r.fonts.length})`);
      if (r.contrast.length) fails.push(`${tag}: contrast ${r.contrast.slice(0, 6).join(' · ')} (${r.contrast.length})`);
      if (r.targets.length) fails.push(`${tag}: target under ${spec.target}px ${r.targets.slice(0, process.env.GATE_VERBOSE ? 200 : 6).join(' · ')} (${r.targets.length})`);
      if (r.ink.length) fails.push(`${tag}: ink surface not opaque ${r.ink.slice(0, 3).join(', ')}`);
      // the book's screenshot: the viewport grows to the document, so sticky
      // chrome lands where a reader expects it and nothing is re-rastered
      const H = await p.evaluate(() => Math.ceil(document.documentElement.scrollHeight));
      const shot = path.join(shots, `${f.shot}-${w}.png`);
      if (H <= 16000) {
        await p.setViewportSize({ width: w, height: H });
        await p.waitForTimeout(100);
        await p.screenshot({ path: shot });
      } else {
        await p.screenshot({ path: shot, fullPage: true });   // a long fixture: no sticky chrome to place
      }
      await p.close();
    }
    // the drawer, at phone width: the menu button opens it, focus moves in and
    // stays in under Tab, Esc closes it and focus returns to the button
    if (f.menu) {
      const p = await b.newPage({ viewport: { width: 375, height: 800 } });
      p.on('pageerror', e => fails.push(`${f.shot}@375 menu: script error ${e.message}`));
      await p.goto('file://' + f.path, { waitUntil: 'load' });
      await p.evaluate(() => document.fonts.ready);
      const tag = `${f.shot}@375 menu`;
      const btn = await p.$('[aria-controls="mnav"]');
      if (!btn || !(await btn.isVisible())) fails.push(`${tag}: no visible menu button`);
      else {
        await btn.click();
        await p.waitForTimeout(80);
        const st = await p.evaluate(() => {
          const l = document.getElementById('mnav'), d = l && l.querySelector('[role="dialog"]');
          const cta = d && [...d.querySelectorAll('a.c-button')].find(a => a.offsetParent !== null);
          return { open: !!l && !l.hidden && getComputedStyle(l).display !== 'none', inside: !!d && d.contains(document.activeElement),
                   expanded: document.querySelector('[aria-controls="mnav"]').getAttribute('aria-expanded'), cta: !!cta };
        });
        if (!st.open) fails.push(`${tag}: the drawer did not open`);
        if (!st.inside) fails.push(`${tag}: focus did not move into the drawer`);
        if (st.expanded !== 'true') fails.push(`${tag}: aria-expanded not true when open`);
        if (!st.cta) fails.push(`${tag}: the header CTA is not reachable in the drawer`);
        for (let i = 0; i < 25; i++) await p.keyboard.press(i % 7 === 6 ? 'Shift+Tab' : 'Tab');
        const trapped = await p.evaluate(() => document.querySelector('#mnav [role="dialog"]').contains(document.activeElement));
        if (!trapped) fails.push(`${tag}: focus escaped the drawer under Tab`);
        if (/-home$/.test(f.shot)) await p.screenshot({ path: path.join(shots, `${f.shot}-375-menu.png`) });
        await p.keyboard.press('Escape');
        await p.waitForTimeout(50);
        const back = await p.evaluate(() => ({ closed: document.getElementById('mnav').hidden,
          focus: document.activeElement === document.querySelector('[aria-controls="mnav"]') }));
        if (!back.closed) fails.push(`${tag}: Esc did not close the drawer`);
        if (!back.focus) fails.push(`${tag}: focus did not return to the menu button`);
      }
      await p.close();
    }
    // form states (?state=…): each renders as itself; sending keeps the button's width
    for (const s of (f.states || [])) {
      for (const w of [375, 1280]) {
        const p = await b.newPage({ viewport: { width: w, height: 900 } });
        p.on('pageerror', e => fails.push(`${f.shot}@${w} ${s}: script error ${e.message}`));
        await p.goto('file://' + f.path, { waitUntil: 'load' });
        await p.evaluate(() => document.fonts.ready);
        const rest = await p.evaluate(() => [...document.querySelectorAll('.c-formstate [type="submit"]')].map(x => x.getBoundingClientRect().width));
        await p.goto('file://' + f.path + '?state=' + s, { waitUntil: 'load' });
        await p.evaluate(() => document.fonts.ready);
        await p.waitForTimeout(60);
        const r = await p.evaluate((s) => [...document.querySelectorAll('.c-formstate')].map(wr => {
          const sh = wr.querySelector(`[data-show="${s}"]`), b = wr.querySelector('[type="submit"]');
          return { state: wr.getAttribute('data-state'), shown: sh ? getComputedStyle(sh).display !== 'none' : null,
                   busy: b ? b.getAttribute('aria-busy') : null, width: b ? b.getBoundingClientRect().width : 0,
                   invalid: wr.querySelectorAll('[aria-invalid="true"]').length };
        }), s);
        const tag = `${f.shot}@${w} ${s}`;
        r.forEach((x, i) => {
          if (x.state !== s) fails.push(`${tag}: data-state is ${x.state}`);
          if (s !== 'sending' && x.shown === false) fails.push(`${tag}: the ${s} message is not shown`);
          if (s === 'error' && !x.invalid) fails.push(`${tag}: no field marked invalid`);
          if (s === 'sending' && x.busy !== 'true') fails.push(`${tag}: submit not aria-busy`);
          if (s === 'sending' && rest[i] && Math.abs(x.width - rest[i]) > 0.5) fails.push(`${tag}: submit width ${x.width.toFixed(1)} ≠ ${rest[i].toFixed(1)} at rest`);
        });
        const H = await p.evaluate(() => Math.ceil(document.documentElement.scrollHeight));
        await p.setViewportSize({ width: w, height: Math.min(H, 16000) });
        await p.screenshot({ path: path.join(shots, `${f.shot}-${w}-${s}.png`) });
        await p.close();
      }
    }
  }
  await b.close();
  console.log(`render gate · ${checked} renders · ${texts} text nodes · ${targets} targets measured`);
  if (fails.length) {
    console.log('RENDER GATE FAILED:\n  ' + fails.join('\n  '));
    process.exit(1);
  }
  console.log('render ok — no overflow, no shadow, no fallback face, contrast and targets at the floors, ink opaque');
})();
