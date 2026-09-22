#!/usr/bin/env python3
"""Forge one Agent Skill into a GitHub-ready repository plus dist/skill.zip.

Reads a Skill folder, SKILL.md, markdown draft, or ZIP; audits it; then writes
a repository containing the untouched Skill under skills/<name>/, a
byte-reproducible dist/skill.zip, a standalone validator, tests, CI and docs.
Never executes code from the source Skill.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import skill_rules as sr  # noqa: E402
from audit_skill import Findings, extract_zip_safely, find_skill_roots, inspect_root, select_root  # noqa: E402

TEMPLATE = HERE.parent / "assets" / "repo-template"
LICENSE_NAMES = ("LICENSE", "LICENSE.txt", "LICENSE.md", "COPYING", "COPYING.txt")

MIT_TEMPLATE = """MIT License

Copyright (c) {year} {holder}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

PROPRIETARY_TEMPLATE = """Copyright (c) {year} {holder}. All rights reserved.

No license to use, copy, modify, publish, distribute, sublicense, or sell this
work is granted by this file. Use is subject to a separate written agreement
with the copyright holder.
"""

TARGET_LABEL = {
    "all": "Agent Skills spec + Claude + OpenAI/Codex rules",
    "portable": "Agent Skills spec",
    "claude": "Agent Skills spec + Claude rules",
    "openai": "Agent Skills spec + OpenAI/Codex rules",
}


class ForgeError(Exception):
    pass


# ---------------------------------------------------------------------------
# Source staging
# ---------------------------------------------------------------------------

def _copy_skill(src: Path, dst: Path) -> List[str]:
    """Copy a Skill without caches, symlinks or credential files. Returns skipped sensitive paths."""
    skipped: List[str] = []

    def ignore(directory: str, names: List[str]) -> set:
        d = Path(directory)
        out = set()
        for n in names:
            if sr.is_sensitive(n) and (d / n).is_file():
                skipped.append((d / n).relative_to(src).as_posix())
                out.add(n)
            elif sr.excluded(n) or (d / n).is_symlink():
                out.add(n)
        return out
    shutil.copytree(src, dst, symlinks=False, ignore=ignore)
    return skipped


def _pick(roots: List[Path], base: Path, select: Optional[str], where: str) -> Path:
    if select:
        chosen = select_root(roots, base, select)
        if chosen is None:
            raise ForgeError(f"No Skill matching --select '{select}' in {where}. Candidates: "
                             + ", ".join(r.relative_to(base).as_posix() if r != base else "." for r in roots))
        return chosen
    if len(roots) != 1:
        raise ForgeError(f"Expected exactly one Skill in {where}, found {len(roots)}. Pick one with --select: "
                         + ", ".join(r.relative_to(base).as_posix() if r != base else "." for r in roots[:20]))
    return roots[0]


def _declared_name(skill_md: Path) -> str:
    fields, _, _ = sr.parse_frontmatter(skill_md.read_text(encoding="utf-8", errors="replace"))
    name = (fields or {}).get("name")
    return name if isinstance(name, str) and sr.NAME_RE.fullmatch(name) and len(name) <= sr.MAX_NAME else ""


def materialize_source(source: Path, staging: Path, select: Optional[str] = None) -> Tuple[Path, Optional[str], List[str], List[str]]:
    """Copy the selected Skill into staging/<name>.

    Returns (root, original_folder_name, notes, excluded_sensitive_files).
    """
    notes: List[str] = []
    work = staging / "src"
    work.mkdir(parents=True)
    original: Optional[str] = None
    if source.is_dir():
        picked = _pick(find_skill_roots(source), source, select, str(source))
        original = picked.name
    elif source.is_file() and source.suffix.lower() == ".zip":
        pre = Findings()
        extracted = work / "unzipped"
        extracted.mkdir()
        if not extract_zip_safely(source, extracted, pre):
            raise ForgeError("ZIP failed safety inspection: " + "; ".join(f["message"] for f in pre))
        picked = _pick(find_skill_roots(extracted), extracted, select, source.name)
        original = picked.name if picked != extracted else None
    elif source.is_file() and source.name == "SKILL.md":
        picked, original = source.parent, source.parent.name
    elif source.is_file() and source.suffix.lower() in {".md", ".txt"}:
        picked = work / "draft"
        picked.mkdir()
        shutil.copy2(source, picked / "SKILL.md")
        notes.append(f"Wrapped markdown draft {source.name} as SKILL.md")
    else:
        raise ForgeError("Expected a Skill folder, SKILL.md, markdown draft, or ZIP")

    name = _declared_name(picked / "SKILL.md") if (picked / "SKILL.md").is_file() else ""
    dest = staging / "skill" / (name or "unnamed-skill")
    skipped = _copy_skill(picked, dest)
    if name and original and original != name:
        notes.append(f"Skill folder '{original}' is placed at skills/{name}/ to match its frontmatter name")
    return dest, original, notes, skipped


# ---------------------------------------------------------------------------
# Licensing
# ---------------------------------------------------------------------------

def resolve_license(skill: Path, fm_license: Optional[str], choice: str, holder: Optional[str], repo: Path) -> Tuple[str, List[str], List[str]]:
    """Returns (readme_status, warnings, recommendations). May write LICENSE files."""
    warnings: List[str] = []
    recs: List[str] = []
    bundled = next((skill / n for n in LICENSE_NAMES if (skill / n).is_file()), None)
    year = datetime.now(timezone.utc).year

    if choice == "preserve":
        if bundled:
            shutil.copy2(bundled, repo / "LICENSE")
            label = f" (`{fm_license}`)" if fm_license else ""
            if not fm_license:
                recs.append("Add a `license:` line to the SKILL.md frontmatter so hosts can display it")
            return f"Licensed under the terms in [`LICENSE`](LICENSE){label}, also bundled with the Skill as `{bundled.name}`.", warnings, recs
        if fm_license:
            warnings.append(f"SKILL.md declares license `{fm_license}` but no license text is bundled; add the full text as LICENSE.txt in the Skill before publishing")
            return f"Declared in `SKILL.md` as `{fm_license}`. The full license text is not bundled yet.", warnings, recs
        warnings.append("No license: without one, nobody may legally reuse, modify or redistribute this Skill. Choose one with --license")
        return "No license has been chosen yet. Until one is added, all rights are reserved by the author.", warnings, recs

    if choice == "none":
        warnings.append("Built with --license none: the repository grants no reuse rights")
        return "No license. All rights reserved by the author.", warnings, recs

    # Explicit MIT / proprietary: never relicense work that already declares terms.
    existing = [x for x in ((bundled.name if bundled else None), fm_license) if x]
    same = fm_license and fm_license.strip().lower() == choice.lower() and not bundled
    if existing and not same:
        raise ForgeError(
            f"The source already declares license terms ({', '.join(existing)}). Relicensing is the rights holder's "
            "decision; rebuild with --license preserve, or remove the existing terms first if you own the Skill."
        )
    if not holder:
        raise ForgeError(f"--license {choice} needs a copyright holder: pass --copyright-holder (or --owner)")
    text = (MIT_TEMPLATE if choice == "MIT" else PROPRIETARY_TEMPLATE).format(year=year, holder=holder)
    (skill / "LICENSE.txt").write_text(text, encoding="utf-8")
    (repo / "LICENSE").write_text(text, encoding="utf-8")
    if fm_license is None:
        spdx = "MIT" if choice == "MIT" else "Proprietary. LICENSE.txt has complete terms"
        recs.append(f"Add `license: {spdx}` to the SKILL.md frontmatter so hosts can display it")
    status = ("Released under the [MIT License](LICENSE)." if choice == "MIT"
              else "Proprietary. See [`LICENSE`](LICENSE).")
    return status + " The license text is bundled with the Skill as `LICENSE.txt`.", warnings, recs


# ---------------------------------------------------------------------------
# Repository files
# ---------------------------------------------------------------------------

def copy_template(repo: Path, name: str, target: str) -> None:
    for src in sorted(TEMPLATE.rglob("*")):
        if not src.is_file() or any(p in sr.EXCLUDE_PARTS for p in src.parts) or src.suffix in sr.EXCLUDE_SUFFIXES:
            continue
        rel_parts = ["." + p[4:] if p.startswith("dot-") else p for p in src.relative_to(TEMPLATE).parts]
        if rel_parts[-1].endswith(".tmpl"):  # keeps template tests out of test discovery
            rel_parts[-1] = rel_parts[-1][: -len(".tmpl")]
        dst = repo.joinpath(*rel_parts)
        dst.parent.mkdir(parents=True, exist_ok=True)
        text = src.read_text(encoding="utf-8")
        dst.write_text(text.replace("__NAME__", name).replace("__TARGET__", target), encoding="utf-8")
    shutil.copy2(HERE / "skill_rules.py", repo / "scripts" / "skill_rules.py")
    for p in (repo / "scripts").glob("*.py"):
        p.chmod(0o755)


def payload_tree(skill: Path, name: str) -> str:
    lines = [f"skills/{name}/"]
    files = [rel for rel, _ in sr.payload_files(skill)]
    for rel in files[:40]:
        lines.append("  " + rel)
    if len(files) > 40:
        lines.append(f"  … {len(files) - 40} more files")
    return "\n".join(lines)


def build_readme(name: str, desc: str, owner: Optional[str], repo_name: str, license_status: str,
                 target: str, skill: Path) -> str:
    title = " ".join(w.capitalize() for w in name.split("-"))
    src = f"{owner}/{repo_name}" if owner else "<owner>/<repo>"
    return f"""# {title}

{desc or 'An Agent Skill.'}

This repository packages the **`{name}`** Agent Skill in the open [`SKILL.md` format](https://agentskills.io/specification), so it can be used by Claude, Codex/ChatGPT, Cursor and other agents that support Agent Skills.

## Install

### Any supported agent (recommended)

```bash
npx skills add {src} --skill {name}
```

Target a specific agent with `--agent`, for example `--agent claude-code`, `--agent codex` or `--agent cursor`. Add `-g` to install for your user instead of the current project. Try it without installing:

```bash
npx skills use {src} --skill {name}
```

### Manual install

| Host | Where the Skill goes |
|------|----------------------|
| Claude Code | copy `skills/{name}/` to `~/.claude/skills/{name}/` (personal) or `.claude/skills/{name}/` (project) |
| Claude apps (claude.ai / desktop) | upload `dist/skill.zip` in Claude's Skills settings |
| Claude API | upload the Skill folder through the `/v1/skills` endpoints |
| Codex | copy `skills/{name}/` to `~/.agents/skills/{name}/` (personal) or `.agents/skills/{name}/` (repository) |
| Other agents | unzip `dist/skill.zip` into the agent's skills directory |

## What's inside

```text
{payload_tree(skill, name)}
dist/skill.zip        # the same Skill, zipped, for upload-based hosts
```

Everything outside `skills/{name}/` is repository tooling and is not part of the Skill.

## Validate

```bash
python3 scripts/validate_skill.py          # {TARGET_LABEL[target]}
python3 scripts/build_dist.py --check      # dist/skill.zip matches the Skill folder
python3 -m unittest discover -s tests
```

These checks need only Python 3.9+ and run in CI on every push. They verify structure and host rules, not the Skill's runtime behavior, which depends on the host, model, tools and permissions available.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). After editing the Skill, run `python3 scripts/build_dist.py` and commit the rebuilt `dist/skill.zip`.

## License

{license_status}
"""


def changelog() -> str:
    return """# Changelog

All notable changes to this Skill are documented here. This project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

- Initial repository.
"""


def create_repo_zip(repo: Path, zip_path: Path) -> None:
    import zipfile
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(repo.rglob("*")):
            if not p.is_file() or any(x in sr.EXCLUDE_PARTS for x in p.relative_to(repo).parts) or p.suffix in sr.EXCLUDE_SUFFIXES:
                continue
            zi = zipfile.ZipInfo(f"{repo.name}/{p.relative_to(repo).as_posix()}", date_time=sr.ZIP_DATE)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.create_system = 3
            zi.external_attr = (0o100000 | sr._mode(p)) << 16
            zf.writestr(zi, p.read_bytes())


# ---------------------------------------------------------------------------

def forge(args) -> dict:
    target = sr.normalize_target(args.target)
    source = Path(args.source).expanduser().resolve()
    repo = Path(args.out).expanduser().resolve()
    if not source.exists():
        raise ForgeError(f"Source does not exist: {source}")
    if repo.exists() and (not repo.is_dir() or any(repo.iterdir())):
        raise ForgeError(f"Output path is not an empty directory: {repo}")
    source_dir = source if source.is_dir() else (source.parent if source.name == "SKILL.md" else None)
    if source_dir is not None and (repo == source_dir or source_dir in repo.parents):
        raise ForgeError("Output directory must not be inside the source Skill folder")
    repo_zip = Path(args.repo_zip).expanduser().resolve() if args.repo_zip else None
    if repo_zip:
        if repo_zip.exists() and not args.force:
            raise ForgeError(f"{repo_zip} already exists; pass --force to overwrite it")
        if repo == repo_zip or repo in repo_zip.parents:
            raise ForgeError("--repo-zip must be outside the output directory")
    created_repo = not repo.exists()

    with tempfile.TemporaryDirectory(prefix="skill-repo-forge-build-") as td:
        staged, _original, notes, sensitive = materialize_source(source, Path(td), getattr(args, "select", None))
        audit = inspect_root(staged, target)
        if audit["status"] == "fail" and not args.allow_blockers:
            return {"built": False, "reason": "audit_blockers", "notes": notes, "audit": audit}
        fields, _, _ = sr.parse_frontmatter((staged / "SKILL.md").read_text(encoding="utf-8", errors="replace"))
        fields = fields or {}
        name = fields.get("name") if isinstance(fields.get("name"), str) and sr.NAME_RE.fullmatch(fields.get("name", "")) else None
        if not name:
            return {"built": False, "reason": "missing_or_invalid_skill_name", "notes": notes, "audit": audit}
        desc = fields.get("description") if isinstance(fields.get("description"), str) else ""
        fm_license = fields.get("license") if isinstance(fields.get("license"), str) else None
        repo_name = args.repo_name or name

        repo.mkdir(parents=True, exist_ok=True)
        skill_dest = repo / "skills" / name
        _copy_skill(staged, skill_dest)
        try:
            status, lic_warn, recs = resolve_license(skill_dest, fm_license, args.license,
                                                     args.copyright_holder or args.owner, repo)
        except ForgeError:
            if created_repo:
                shutil.rmtree(repo)
            else:
                for child in list(repo.iterdir()):
                    shutil.rmtree(child) if child.is_dir() else child.unlink()
            raise

    copy_template(repo, name, target)
    (repo / "README.md").write_text(build_readme(name, desc, args.owner, repo_name, status, target, skill_dest), encoding="utf-8")
    (repo / "CHANGELOG.md").write_text(changelog(), encoding="utf-8")
    sr.build_zip(skill_dest, repo / "dist" / "skill.zip", name)

    from verify_repo import verify  # local import keeps module load light
    verification = verify(repo, target=target, run_checks=False)
    if repo_zip:
        repo_zip.parent.mkdir(parents=True, exist_ok=True)
        create_repo_zip(repo, repo_zip)

    sensitive_warn = [f"Excluded credential-like file '{s}' from the repository and skill.zip; delete it from the source and rotate it if it holds a real secret" for s in sensitive]
    install = f"npx skills add {args.owner}/{repo_name} --skill {name}" if args.owner else f"npx skills add ./{repo.name} --skill {name}"
    return {
        "built": True,
        "release_ready": (audit["status"] == "pass" and verification["status"] == "pass"
                          and args.license != "none" and not lic_warn and not sensitive_warn),
        "skill_name": name,
        "target": target,
        "repo_dir": str(repo),
        "repo_zip": str(repo_zip) if repo_zip else None,
        "skill_zip": str(repo / "dist" / "skill.zip"),
        "install_command": install,
        "license_status": status,
        "warnings": lic_warn + sensitive_warn,
        "recommendations": recs,
        "notes": notes,
        "audit": audit,
        "verification": verification,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="Skill folder, SKILL.md, markdown draft, or ZIP")
    ap.add_argument("--out", required=True, help="new, empty directory for the repository")
    ap.add_argument("--select", help="when the source holds several Skills, the folder path or name of the one to forge")
    ap.add_argument("--owner", help="GitHub user or organization (used for install instructions)")
    ap.add_argument("--repo-name", help="repository name (default: the Skill name)")
    ap.add_argument("--target", default="all", help="host rules to enforce: all (default), portable, claude, openai")
    ap.add_argument("--license", choices=["preserve", "MIT", "proprietary", "none"], default="preserve",
                    help="preserve (default) keeps the source's terms; MIT/proprietary only for Skills you own")
    ap.add_argument("--copyright-holder", help="name for the copyright line (default: --owner)")
    ap.add_argument("--repo-zip", help="also write a ZIP of the whole repository to this path")
    ap.add_argument("--force", action="store_true", help="overwrite an existing --repo-zip file")
    ap.add_argument("--allow-blockers", action="store_true", help="build even with audit blockers; output is marked not release-ready")
    args = ap.parse_args()
    try:
        result = forge(args)
    except (ForgeError, ValueError) as e:
        print(json.dumps({"built": False, "reason": "error", "error": str(e)}, indent=2))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result.get("built") else 2


if __name__ == "__main__":
    raise SystemExit(main())
