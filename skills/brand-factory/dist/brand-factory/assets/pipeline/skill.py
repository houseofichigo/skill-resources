#!/usr/bin/env python3
"""Assemble the AI skill from skill-template/ plus the generated files."""
import json, pathlib, shutil, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = json.loads((ROOT / "out" / "tokens.json").read_text(encoding="utf-8"))
TPL, OUT = ROOT / "skill-template", ROOT / "out"
DST = OUT / f"{T['slug']}-brand"


def fill(text):
    for k in ("brand", "slug", "version", "date", "supersedes", "positioning"):
        text = text.replace("{{" + k + "}}", str(T[k]))
    retired = ", ".join(f"`{v}`" for k, v in T["color"].get("retired", {}).items()
                        if not k.startswith("$"))
    text = text.replace("{{retired}}", retired or "nothing")
    faces = " · ".join(T["type"][k]["family"] for k in ("display", "text", "mono"))
    return text.replace("{{faces}}", faces)


def main():
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(TPL, DST)
    for p in DST.rglob("*"):
        if p.suffix in (".md", ".html", ".py") and p.is_file():
            p.write_text(fill(p.read_text(encoding="utf-8")), encoding="utf-8")

    ref = DST / "references"
    ref.mkdir(exist_ok=True)
    for f in ("tokens.json", "tokens.css", "BRAND.md",
              "fonts-embedded.css", "fonts-linked.css"):
        src = OUT / f
        if src.exists():
            shutil.copy(src, DST / "BRAND.md" if f == "BRAND.md" else ref / f)
    if (OUT / "fonts").exists():
        shutil.copytree(OUT / "fonts", ref / "fonts", dirs_exist_ok=True)
    book = next(OUT.glob("*-brand-book-*.html"), None)
    if book:
        shutil.copy(book, ref / book.name)
    shutil.copy(ROOT / "build" / "check.py", DST / "scripts" / "check.py")

    n = sum(1 for _ in DST.rglob("*") if _.is_file())
    print(f"{DST.relative_to(ROOT)} · {n} files")


if __name__ == "__main__":
    main()
