#!/usr/bin/env python3
"""Choose a typeface on measurement, not on a specimen page.

    python3 build/measure_fonts.py Manrope Outfit "Plus Jakarta Sans"
    python3 build/measure_fonts.py --arabic Cairo "IBM Plex Sans Arabic"

Reports, for each candidate against your configured display face:

  line box   the height one line occupies. THIS is what breaks a density
             scale — a face 50% taller than yours turns every 28px row
             into 42px the moment you switch to it.
  width      set width relative to your face. A wider face needs more
             column, and a headline that fitted one line will not.
  italic     whether a real one exists, read from the font files rather
             than from the browser. Many geometric sans faces ship none,
             and asking for one gets you a slanted roman.
"""
import json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "brand.config.json").read_text(encoding="utf-8"))
VEND = ROOT / ".fonts"


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def install(names, arabic):
    VEND.mkdir(exist_ok=True)
    if not (VEND / "package.json").exists():
        (VEND / "package.json").write_text(
            '{"name":"brand-fonts","private":true,"version":"0.0.0"}\n')
    pkgs = []
    for n in names:
        s = slug(n)
        pkgs += [f"@fontsource-variable/{s}", f"@fontsource/{s}"]
    ok = []
    for p in pkgs:
        r = subprocess.run(["npm", "i", "--silent", p], cwd=VEND,
                           capture_output=True, text=True)
        if r.returncode == 0:
            ok.append(p)
    return ok


def files_for(name):
    s = slug(name)
    out = []
    for scope in ("@fontsource-variable", "@fontsource"):
        d = VEND / "node_modules" / scope / s / "files"
        if d.exists():
            out += sorted(d.glob("*.woff2"))
    return out


JS = r"""
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const spec = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const faces = spec.faces.map(f =>
    `@font-face{font-family:'${f.name}';font-style:${f.style};` +
    `font-weight:${f.weight};src:url(file://${f.path}) format('woff2')}`
  ).join('\n');

  // Write a real file and navigate to it. A page created with
  // setContent has an about:blank base URL, and Chromium refuses to load
  // file:// subresources into it — every face would silently fall back
  // and all candidates would measure identically.
  const tmp = spec.html;
  fs.writeFileSync(tmp, `<!DOCTYPE html><meta charset="utf-8">` +
    `<style>${faces}</style><body></body>`);
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('file://' + tmp, { waitUntil: 'load' });

  // A @font-face is only fetched when something on the page uses it.
  // Measuring before this point silently measures the fallback.
  await p.evaluate(({ names, probes }) => {
    const h = document.createElement('div');
    h.style.cssText = 'position:absolute;top:-9999px;font-size:100px';
    for (const n of names) {
      const probe = probes[n];
      for (const st of ['normal', 'italic']) {
        const s = document.createElement('span');
        s.style.cssText = `font-family:'${n}';font-style:${st}`;
        s.textContent = probe;
        h.appendChild(s);
      }
    }
    document.body.appendChild(h);
  }, spec);
  // A canvas has its own font set: document.fonts.ready is not enough,
  // the family must be explicitly loaded or ctx.font falls back.
  await p.evaluate(async ({ names }) => {
    for (const n of names) {
      await document.fonts.load(`400 100px '${n}'`);
      await document.fonts.load(`italic 400 100px '${n}'`);
    }
    await document.fonts.ready;
  }, spec);
  await p.waitForTimeout(800);

  const out = await p.evaluate(({ names, probes }) => {
    const host = document.createElement('div');
    host.style.cssText = 'position:absolute;top:-9999px;font-size:100px;' +
      'white-space:nowrap;line-height:1';
    document.body.appendChild(host);
    const r = {};
    for (const n of names) {
      const probe = probes[n];
      host.innerHTML = `<span style="font-family:'${n}'">${probe}</span>`;
      const box = host.firstChild.getBoundingClientRect();
      host.innerHTML =
        `<span style="font-family:'${n}';font-synthesis:none">${probe}</span>` +
        `<span style="font-family:'${n}';font-style:italic;` +
        `font-synthesis:none">${probe}</span>`;
      const [a, c] = host.children;
      r[n] = {
        lineBox: Math.round(box.height),
        width: Math.round(box.width),
        italicWidthDiff: Math.abs(a.getBoundingClientRect().width -
                                  c.getBoundingClientRect().width) > 0.5
      };
    }
    return r;
  }, spec);
  console.log(JSON.stringify(out));
  await b.close();
})();
"""


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    arabic = "--arabic" in sys.argv
    if not args:
        sys.exit(__doc__)

    base = CFG["type"]["display"]["family"]
    names = [base] + [a for a in args if a != base]
    print(f"installing {len(names)} candidates from npm…")
    install(names, arabic)

    faces, has_italic = [], {}
    missing = []
    for n in names:
        fs = files_for(n)
        # Pick the subset that actually contains the probe glyphs. A
        # fontsource package ships cyrillic, greek, vietnamese and latin
        # subsets; sorted() puts cyrillic first, and loading that gives a
        # face with correct METRICS and no Latin glyphs — so the line box
        # measures true and the text silently falls back.
        # The reference face has no Arabic subset, and that is the whole
        # point of the comparison: its LATIN line box is what the density
        # scale was built on.
        is_ref = (n == base)
        want = "latin" if (not arabic or is_ref) else "arabic"

        def pick(italic):
            c = [f for f in fs
                 if want in f.name
                 and ("-ext-" not in f.name and "-ext." not in f.name)
                 and (("italic" in f.name) == italic)]
            if not c:
                c = [f for f in fs if want in f.name
                     and (("italic" in f.name) == italic)]
            return c

        latin, ital = pick(False), pick(True)
        if not latin:
            missing.append(n)
            continue
        faces.append({"name": n, "style": "normal", "weight": "400",
                      "path": str(latin[0])})
        if ital:
            faces.append({"name": n, "style": "italic", "weight": "400",
                          "path": str(ital[0])})
            has_italic[n] = True
    if missing:
        print(f"  not on npm as @fontsource: {', '.join(missing)}")
        names = [n for n in names if n not in missing]
    if len(names) < 2:
        sys.exit("need the display face plus at least one candidate")

    probes = {n: ("Handgloves" if (not arabic or n == base) else "الكفاءة")
              for n in names}
    spec = {"faces": faces, "names": names, "probes": probes,
            "html": "/tmp/_measure.html"}
    sp = pathlib.Path("/tmp/_fontspec.json")
    sp.write_text(json.dumps(spec))
    js = pathlib.Path("/tmp/_measure.js")
    js.write_text(JS)
    r = subprocess.run(["node", str(js), str(sp)],
                       capture_output=True, text=True, cwd=ROOT)
    if r.returncode:
        sys.exit(r.stderr[-1200:])
    d = json.loads(r.stdout)
    import os
    if os.environ.get("DEBUG"): print(json.dumps(d, indent=1))

    ref = d[base]["lineBox"]
    print(f"\nat 100px · reference is {base} "
          f"({probes[base]!r}), line box {ref}\n")
    print(f"{'face':28} {'line box':>9} {'vs ref':>8} {'width':>7}  italic")
    print("-" * 62)
    for n in names:
        v = d[n]
        pct = (v["lineBox"] / ref - 1) * 100
        flag = ""
        if n != base and abs(pct) > 15:
            flag = "  <- breaks a density scale"
        # Width is only comparable within one script — the probe differs
        # across them, so a cross-script percentage would be noise.
        wpct = None if (arabic and n != base) else \
            (v["width"] / d[base]["width"] - 1) * 100
        print(f"{n:28} {v['lineBox']:>9} {pct:>+7.0f}% "
              f"{(f'{wpct:+.0f}%' if wpct is not None else '—'):>6}  "
              f"{'yes' if has_italic.get(n) else 'NO'}{flag}")
    print("\nA face more than ~15% off the reference line box will change "
          "every row\nheight you have specified. A face with no italic "
          "cannot be asked for one:\nthe browser slants the roman and "
          "ships it.")


if __name__ == "__main__":
    main()
