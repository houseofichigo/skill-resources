#!/usr/bin/env python3
"""Scaffold a brand project from this Skill.

The generators expect to sit in `build/` with the config beside them, one
level up. That layout is what makes `brand.config.json` the single source
and everything else disposable, so rather than teach the generators to
live anywhere, this copies them into a project that has the shape they
need.

    python3 scripts/init.py ~/work/acme-brand

Creates:

    acme-brand/
      brand.config.json     the only file you edit
      build/                the generators and the gates
      skill-template/       the brand skill's fixed parts
      source/               what the client sent you
      out/ dist/            generated, safe to delete

Nothing is overwritten. Re-running it on an existing project adds only
what is missing, so a project whose config you have filled in survives.

Standard library only. Python 3.9+.
"""
import argparse, pathlib, shutil, sys

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent
ASSETS = SKILL / "assets"


def copy(src: pathlib.Path, dst: pathlib.Path, log: list) -> None:
    """Copy, skipping anything already there. Never clobbers."""
    if dst.exists():
        log.append(f"  kept    {dst.name}{'/' if dst.is_dir() else ''}")
        return
    if src.is_dir():
        shutil.copytree(src, dst)
        n = sum(1 for _ in dst.rglob("*") if _.is_file())
        log.append(f"  created {dst.name}/ ({n} files)")
    else:
        shutil.copy2(src, dst)
        log.append(f"  created {dst.name}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Scaffold a brand project from the brand-factory Skill.")
    ap.add_argument("target", help="directory to create the project in")
    ap.add_argument("--force", action="store_true",
                    help="replace build/ and skill-template/ with this "
                         "Skill's copies, keeping brand.config.json and "
                         "source/. Use after updating the Skill.")
    a = ap.parse_args()

    for required in (ASSETS / "pipeline", ASSETS / "brand.config.json",
                     ASSETS / "skill-template"):
        if not required.exists():
            print(f"this Skill is incomplete — {required.name} is missing",
                  file=sys.stderr)
            return 1

    root = pathlib.Path(a.target).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    log: list = []

    if a.force:
        for stale in ("build", "skill-template"):
            p = root / stale
            if p.exists():
                shutil.rmtree(p)
                log.append(f"  replaced {stale}/")

    copy(ASSETS / "pipeline", root / "build", log)
    copy(ASSETS / "brand.config.json", root / "brand.config.json", log)
    copy(ASSETS / "skill-template", root / "skill-template", log)
    for d in ("source", "out", "dist"):
        copy_dir = root / d
        if not copy_dir.exists():
            copy_dir.mkdir()
            log.append(f"  created {d}/")
        else:
            log.append(f"  kept    {d}/")

    gi = root / ".gitignore"
    if not gi.exists():
        gi.write_text(
            "# generated — reproducible from brand.config.json\n"
            "out/\ndist/\n.fonts/\nnode_modules/\npackage-lock.json\n"
            "__pycache__/\n*.pyc\n\n"
            "# the client's material. keep it out of a public repo.\nsource/\n",
            encoding="utf-8")
        log.append("  created .gitignore")

    print(f"{root}")
    print("\n".join(log))
    print(f"""
Next:

  cd {root}
  npm install playwright && npx playwright install chromium
  python3 build/all.py          # builds a 9-page book for a fictional
                                # company, renders it, measures it

Playwright is not optional — it is how the build catches a clipped page
and a font that silently fell back. Then edit brand.config.json, which is
the only file you ever edit by hand, and run build/all.py again.

The Skill's references/ explain what to put through it: sop.md for the
twelve steps, intake.md for what to ask the client, contents.md for what
a finished book actually contains.""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
