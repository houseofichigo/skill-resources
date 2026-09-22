// Render the book and refuse to finish if anything is silently wrong.
//
// Every failure below is one nobody sees by reading the source:
//   a clipped page   — .page is overflow:hidden, so it just vanishes
//   a fallback font  — the page looks fine to whoever made it
//   a fake italic    — the browser slants a roman and ships it
//   a shadow         — prohibited, but easy to reintroduce
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');

(async () => {
  const cfg = JSON.parse(fs.readFileSync('out/tokens.json', 'utf8'));
  const book = `out/${cfg.slug}-brand-book-${cfg.version}.html`;
  if (!fs.existsSync(book)) { console.error(`no ${book}`); process.exit(1); }

  // Launch, or say plainly what is missing. Without this the failure is a
  // 40-line Playwright stack trace, and the honest reading of it — "the
  // browser binary was never downloaded" — is on line 31.
  let b;
  try {
    b = await chromium.launch();
  } catch (e) {
    const exe = process.env.CHROMIUM_PATH
      || '/opt/pw-browsers/chromium';                 // some CI images ship one
    try {
      b = await chromium.launch({ executablePath: exe });
      console.error(`note: using ${exe}`);
    } catch (_) {
      console.error(
        'cannot launch Chromium, so the book cannot be rendered or measured.\n'
        + '  npx playwright install chromium\n'
        + 'If a Chromium is already on this machine, point at it:\n'
        + '  CHROMIUM_PATH=/path/to/chromium node build/verify.js\n'
        + 'This step is not optional — it is what catches a clipped page and '
        + 'a fallback font.');
      process.exit(1);
    }
  }
  const p = await b.newPage({ viewport: { width: 1400, height: 1000 } });
  await p.goto('file://' + path.resolve(book), { waitUntil: 'load' });
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(900);

  const fams = ['display', 'text', 'mono'].map(k => cfg.type[k].family);
  const arabic = (cfg.locales || []).includes('ar')
    ? cfg.type.arabic.family : null;

  const r = await p.evaluate(({ fams, arabic }) => {
    const over = [];
    document.querySelectorAll('section').forEach((s, i) => {
      const o = s.scrollHeight - s.clientHeight;
      if (o > 0) over.push(`p${i}:+${o}px`);
    });
    const d = document.createElement('span');
    d.style.cssText = 'position:absolute;visibility:hidden;font-size:100px;white-space:nowrap';
    d.textContent = 'Handgloves'; document.body.appendChild(d);
    const w = {};
    for (const f of fams) { d.style.fontFamily = `'${f}'`; w[f] = Math.round(d.getBoundingClientRect().width); }
    let ar = null;
    if (arabic) {
      d.textContent = 'الكفاءة';
      d.style.fontFamily = `'${arabic}'`; const a = Math.round(d.getBoundingClientRect().width);
      d.style.fontFamily = 'serif'; const f = Math.round(d.getBoundingClientRect().width);
      ar = { loaded: a, fallback: f };
    }
    d.remove();
    const shadows = [...document.querySelectorAll('*')]
      .filter(e => getComputedStyle(e).boxShadow !== 'none').length;
    const fakeItalic = [...document.querySelectorAll('*')].filter(e => {
      const cs = getComputedStyle(e);
      return cs.fontStyle === 'italic' && cs.fontFamily.includes(fams[0]);
    }).length;
    return { pages: document.querySelectorAll('section').length, over, w, ar, shadows, fakeItalic };
  }, { fams, arabic });

  const fails = [];
  if (r.over.length) fails.push(`CLIPPED PAGES: ${r.over.join(' ')}`);
  if (new Set(Object.values(r.w)).size !== fams.length)
    fails.push(`fonts not distinct — a fallback is in use: ${JSON.stringify(r.w)}`);
  if (r.ar && r.ar.loaded === r.ar.fallback)
    fails.push(`${arabic} not loaded — Arabic falls back`);
  if (r.shadows) fails.push(`${r.shadows} element(s) with box-shadow — prohibited`);
  if (r.fakeItalic && cfg.type.display.has_italic === false)
    fails.push(`${r.fakeItalic} synthesised italic(s) on ${fams[0]}, which has none`);

  console.log(`${r.pages} pages · fonts ${JSON.stringify(r.w)}`
    + (r.ar ? ` · arabic ${r.ar.loaded}/${r.ar.fallback}` : '')
    + ` · shadows ${r.shadows}`);
  await b.close();
  if (fails.length) { console.error('\nVERIFY FAILED:\n  ' + fails.join('\n  ')); process.exit(1); }
  console.log('verify ok — nothing clipped, no fallback font, no shadow, no fake italic');
})();
