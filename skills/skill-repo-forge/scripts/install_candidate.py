#!/usr/bin/env python3
"""Plan or execute installation of an Agent Skill through the open `skills` CLI.

Plan-only by default: prints the exact command. Pass --execute only after the
user has asked for the installation. The target agent must be named explicitly.
Agent ids come from the skills CLI, e.g. claude-code, codex, cursor, opencode.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

AGENT_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def build_command(source: str, skills, agents, global_scope: bool, link: bool) -> list:
    cmd = ["npx", "--yes", "skills", "add", source]
    for s in skills or []:
        cmd += ["--skill", s]
    for a in agents:
        cmd += ["--agent", a]
    if global_scope:
        cmd.append("--global")
    if not link:
        cmd.append("--copy")
    cmd.append("--yes")
    return cmd


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="owner/repo, GitHub URL, local path, or other source the skills CLI accepts")
    ap.add_argument("--skill", action="append", help="Skill name inside the source (repeatable)")
    ap.add_argument("--agent", action="append", required=True, help="target agent id, e.g. claude-code, codex, cursor (repeatable)")
    ap.add_argument("--global", dest="global_scope", action="store_true", help="install for the user instead of the project")
    ap.add_argument("--link", action="store_true", help="symlink instead of copying (default is --copy)")
    ap.add_argument("--project-dir", default=".", help="project directory for project-scope installs")
    ap.add_argument("--execute", action="store_true", help="actually install; without it, print the plan only")
    args = ap.parse_args()

    bad = [a for a in args.agent if not AGENT_RE.fullmatch(a)]
    if bad:
        ap.error(f"invalid agent id(s): {', '.join(bad)}")
    project = Path(args.project_dir).expanduser().resolve()
    source = args.source
    local = Path(source).expanduser()
    if source.startswith((".", "/", "~")) or local.exists():
        if not local.exists():
            ap.error(f"local source does not exist: {source}")
        source = str(local.resolve())  # the CLI runs in --project-dir, so pass an absolute path
    cmd = build_command(source, args.skill, args.agent, args.global_scope, args.link)
    result = {
        "source": source,
        "skills": args.skill or [],
        "agents": args.agent,
        "scope": "global" if args.global_scope else "project",
        "project_dir": None if args.global_scope else str(project),
        "command": cmd,
        "executed": False,
    }
    if not args.execute:
        result["note"] = "Plan only. Re-run with --execute once the user has asked for this installation."
        print(json.dumps(result, indent=2))
        return 0
    if not shutil.which("npx"):
        result["error"] = "npx is not available; install Node.js or copy the Skill folder manually"
        print(json.dumps(result, indent=2))
        return 2
    if not args.global_scope and not project.is_dir():
        result["error"] = f"project directory does not exist: {project}"
        print(json.dumps(result, indent=2))
        return 2
    try:
        p = subprocess.run(cmd, cwd=project if not args.global_scope else None, capture_output=True,
                           text=True, check=False, timeout=600)
    except subprocess.TimeoutExpired:
        result["error"] = "installation timed out after 600 seconds"
        print(json.dumps(result, indent=2))
        return 2
    result.update({
        "executed": True,
        "returncode": p.returncode,
        "stdout": p.stdout[-12000:],
        "stderr": p.stderr[-6000:],
        "success": p.returncode == 0,
        "next_step": "Confirm the Skill appears in `npx skills list` or the agent's skills directory, then audit the installed copy.",
    })
    print(json.dumps(result, indent=2))
    return 0 if p.returncode == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
