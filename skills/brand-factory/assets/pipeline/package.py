#!/usr/bin/env python3
"""Everything a client should receive, in dist/."""
import json, pathlib, shutil, subprocess, sys, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = json.loads((ROOT / "out" / "tokens.json").read_text(encoding="utf-8"))
OUT, DIST = ROOT / "out", ROOT / "dist"
SLUG = T["slug"]


def zipdir(src, dest, arcroot):
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(src.rglob("*")):
            if p.is_file():
                z.write(p, pathlib.Path(arcroot) / p.relative_to(src))


def pdf(book, dest):
    js = f"""const {{chromium}}=require('playwright');(async()=>{{
      const b=await chromium.launch();const p=await b.newPage();
      await p.goto('file://{book}',{{waitUntil:'load'}});
      await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(900);
      await p.pdf({{path:'{dest}',printBackground:true,preferCSSPageSize:true}});
      await b.close();}})();"""
    t = pathlib.Path("/tmp/_pdf.js")
    t.write_text(js)
    return subprocess.run(["node", str(t)], capture_output=True).returncode == 0


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    skill = OUT / f"{SLUG}-brand"
    if not skill.exists():
        sys.exit("run build/skill.py first")

    zipdir(skill, DIST / f"{SLUG}-brand-skill.zip", skill.name)
    book = next(OUT.glob("*-brand-book-*.html"))
    shutil.copy(book, DIST / book.name)
    if pdf(book.resolve(), (DIST / book.with_suffix('.pdf').name).resolve()):
        print("  pdf rendered")
    for f in ("BRAND.md", "tokens.json", "tokens.css"):
        shutil.copy(OUT / f, DIST / f)
    fonts = OUT / "fonts"
    if fonts.exists():
        stage = OUT / "_fontpkg"
        if stage.exists():
            shutil.rmtree(stage)
        stage.mkdir()
        shutil.copytree(fonts, stage / "fonts")
        for f in ("fonts-embedded.css", "fonts-linked.css"):
            shutil.copy(OUT / f, stage / f)
        zipdir(stage, DIST / "fonts.zip", "fonts")
        shutil.rmtree(stage)

    (DIST / "README.md").write_text(f"""# {T['brand']} — brand system {T['version']}

{T['positioning']}

Generated from one source. Every value lives in `tokens.json`; the book,
the stylesheet, the rules and the skill are built from it and cannot
disagree with it.

| File | For | What it is |
|---|---|---|
| `{SLUG}-brand-skill.zip` | **An AI** | Unzip into a skills folder. |
| `{book.name}` | **People** | Self-contained, fonts embedded, no network. |
| `{book.with_suffix('.pdf').name}` | **Sending** | Print-ready. |
| `BRAND.md` | **An AI, or a fast read** | The rules, for a tool that takes no skills. |
| `tokens.json` | **Code** | Every value, with measured contrast. |
| `tokens.css` | **Web and product** | Custom properties and base classes. |
| `fonts.zip` | **A web developer** | woff2 files plus both stylesheets. |

Type: {' · '.join(T['type'][k]['family'] for k in ('display','text','mono'))}.
Self-hosted — never link a font service.
""", encoding="utf-8")

    n = len(list(DIST.iterdir()))
    print(f"dist/ · {n} items")


if __name__ == "__main__":
    main()
