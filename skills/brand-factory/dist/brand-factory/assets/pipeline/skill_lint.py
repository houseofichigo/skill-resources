#!/usr/bin/env python3
"""Validate SKILL.md before an installer sees it.

The description limit lives in the installer, not in the file. A real
skill grew past it over six revisions and simply would not install, with
no warning from anything in the build. Hence this.
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = json.loads((ROOT / "out" / "tokens.json").read_text(encoding="utf-8"))
SKILL = ROOT / "out" / f"{T['slug']}-brand" / "SKILL.md"
LIMITS = {"description": 1024, "name": 64}
REQUIRED = ["BRAND.md", "references/tokens.json", "references/tokens.css",
            "scripts/check.py"]


def main():
    if not SKILL.exists():
        sys.exit(f"no {SKILL} — run build/skill.py first")
    t = SKILL.read_text(encoding="utf-8")
    if not t.startswith("---"):
        sys.exit("SKILL.md has no frontmatter")
    fm = t[3:t.index("\n---", 3)]
    fields = {m.group(1): m.group(2).strip() for m in
              re.finditer(r"^([a-z_]+):\s*(.*?)(?=\n[a-z_]+:|\Z)",
                          fm, re.S | re.M)}
    fails = []
    for k, lim in LIMITS.items():
        if k not in fields:
            fails.append(f"missing field: {k}")
        elif len(fields[k]) > lim:
            fails.append(f"{k} is {len(fields[k])} chars, limit {lim} "
                         f"(over by {len(fields[k]) - lim})")
    name = fields.get("name", "")
    if name and not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name):
        fails.append(f"name {name!r} is not lowercase kebab-case")
    if name and SKILL.parent.name != name:
        fails.append(f"folder {SKILL.parent.name!r} != name {name!r}")
    if "{{" in t:
        fails.append("an unfilled {{placeholder}} survived")
    for r in REQUIRED:
        if not (SKILL.parent / r).exists():
            fails.append(f"missing required file: {r}")
    if fails:
        print("SKILL.md FAILED:")
        for f in fails:
            print("  ·", f)
        sys.exit(1)
    print(f"SKILL.md ok · name {name!r} · description "
          f"{len(fields['description'])}/{LIMITS['description']}")


if __name__ == "__main__":
    main()
