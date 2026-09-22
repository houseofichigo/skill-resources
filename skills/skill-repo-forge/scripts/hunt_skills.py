#!/usr/bin/env python3
"""Best-effort local discovery of Agent Skills via the skills CLI and GitHub CLI.

Read-only. Prints raw candidate data as JSON for the agent to inspect; it does
not rank, download, or install anything.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess


def run(cmd: list, timeout: int = 60) -> dict:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        out = {"command": " ".join(cmd), "returncode": p.returncode, "stdout": p.stdout[-12000:], "stderr": p.stderr[-4000:]}
        if p.stdout.strip().startswith(("[", "{")):
            try:
                out["data"] = json.loads(p.stdout)
                del out["stdout"]
            except json.JSONDecodeError:
                pass
        return out
    except Exception as e:  # noqa: BLE001 - discovery must never crash
        return {"command": " ".join(cmd), "error": str(e)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", help="capability to search for, e.g. 'invoice ocr'")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--no-npx", action="store_true", help="skip the skills CLI search")
    ap.add_argument("--no-gh", action="store_true", help="skip GitHub search")
    args = ap.parse_args()

    out = {"query": args.query, "sources": [], "notes": []}
    if args.no_npx:
        pass
    elif shutil.which("npx"):
        out["sources"].append({"source": "skills-cli", "result": run(["npx", "--yes", "skills", "find", args.query])})
    else:
        out["notes"].append("npx is not available; skipped the skills CLI search")

    if args.no_gh:
        pass
    elif shutil.which("gh"):
        out["sources"].append({
            "source": "github-code",
            "result": run(["gh", "search", "code", args.query, "--filename", "SKILL.md", "--limit", str(args.limit),
                           "--json", "repository,path,url"]),
        })
        out["sources"].append({
            "source": "github-repositories",
            "result": run(["gh", "search", "repos", f"{args.query} skill", "--sort", "updated", "--limit", str(args.limit),
                           "--json", "fullName,description,updatedAt,stargazersCount,license,url"]),
        })
    else:
        out["notes"].append("gh is not available; use the host's GitHub or web search tools instead")

    out["next_step"] = "Inspect each promising SKILL.md before recommending it; never run candidate scripts to find out what they do."
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
