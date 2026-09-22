#!/usr/bin/env python3
"""Single entry point for Skill Repo Forge.

  forge.py hunt <query>                       discover existing Skills (read-only)
  forge.py audit <path> [--target T]          static audit of a folder, SKILL.md, or ZIP
  forge.py install <source> --agent A         plan an install (add --execute to run it)
  forge.py package <path> --out FILE.zip      audit and zip one Skill (no repository)
  forge.py repo <path> --out DIR [...]        build a GitHub-ready repo + dist/skill.zip
  forge.py verify-repo <dir> [--run-checks]   verify a generated repository

Every sub-command accepts --help. Targets: all (default), portable, claude, openai.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMANDS = {
    "hunt": "hunt_skills.py",
    "audit": "audit_skill.py",
    "install": "install_candidate.py",
    "package": "package_skill.py",
    "repo": "build_repo.py",
    "build": "build_repo.py",
    "verify-repo": "verify_repo.py",
    "verify": "verify_repo.py",
}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0 if argv else 2
    cmd, rest = argv[0], argv[1:]
    script = COMMANDS.get(cmd)
    if not script:
        print(f"Unknown command '{cmd}'.\n{__doc__}", file=sys.stderr)
        return 2
    return subprocess.call([sys.executable, str(HERE / script), *rest])


if __name__ == "__main__":
    raise SystemExit(main())
