#!/usr/bin/env python3
"""Audit one Agent Skill and write a distributable ZIP (no repository).

The ZIP holds a single <name>/ folder, is byte-reproducible, and leaves out
caches and credential files. Refuses to package when the audit finds
blockers unless --allow-blockers is given.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import skill_rules as sr  # noqa: E402
from audit_skill import inspect_root  # noqa: E402
from build_repo import ForgeError, materialize_source  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="Skill folder, SKILL.md, markdown draft, or ZIP")
    ap.add_argument("--out", required=True, help="path of the ZIP to write, e.g. my-skill.zip")
    ap.add_argument("--target", default="all", help="all (default), portable, claude, or openai")
    ap.add_argument("--select", help="when the source holds several Skills, the one to package")
    ap.add_argument("--force", action="store_true", help="overwrite an existing ZIP")
    ap.add_argument("--allow-blockers", action="store_true")
    args = ap.parse_args()
    out = Path(args.out).expanduser().resolve()
    try:
        target = sr.normalize_target(args.target)
        if out.exists() and not args.force:
            raise ForgeError(f"{out} already exists; pass --force to overwrite it")
        with tempfile.TemporaryDirectory(prefix="skill-repo-forge-pkg-") as td:
            staged, _, notes, sensitive = materialize_source(Path(args.source).expanduser().resolve(), Path(td), args.select)
            audit = inspect_root(staged, target)
            if audit["status"] == "fail" and not args.allow_blockers:
                print(json.dumps({"packaged": False, "reason": "audit_blockers", "notes": notes, "audit": audit}, indent=2))
                return 2
            name = audit["frontmatter"].get("name")
            if not isinstance(name, str) or not sr.NAME_RE.fullmatch(name):
                raise ForgeError("SKILL.md needs a valid `name` before packaging")
            files = sr.build_zip(staged, out, name)
    except (ForgeError, ValueError) as e:
        print(json.dumps({"packaged": False, "reason": "error", "error": str(e)}, indent=2))
        return 2
    warnings = [f"Excluded credential-like file '{s}'; delete it from the source and rotate it if it holds a real secret" for s in sensitive]
    print(json.dumps({"packaged": True, "zip": str(out), "skill_name": name, "files": len(files),
                      "release_ready": audit["status"] == "pass" and not warnings, "warnings": warnings, "notes": notes,
                      "finding_counts": audit["finding_counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
