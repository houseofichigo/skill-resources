#!/usr/bin/env python3
"""Bounded static inspector for one Agent Skill folder, ZIP, or SKILL.md.

Never executes code from the inspected Skill. Checks structure and
cross-host frontmatter rules (via skill_rules.py), archive safety, size
bounds, secrets, dangerous shell patterns, and unreferenced scripts.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import skill_rules as sr  # noqa: E402

MAX_FILES = 1000
MAX_TOTAL_BYTES = 100 * 1024 * 1024
MAX_FILE_BYTES = 25 * 1024 * 1024
MAX_ZIP_BYTES = 30 * 1024 * 1024
MAX_DEPTH = 32
MAX_TEXT_SCAN_BYTES = 1_000_000

TEXT_EXTENSIONS = {
    ".md", ".txt", ".py", ".sh", ".bash", ".zsh", ".yaml", ".yml", ".json",
    ".toml", ".ini", ".cfg", ".conf", ".csv", ".tsv", ".xml", ".html", ".css",
    ".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".ps1", ".bat", ".cmd",
    ".rb", ".go", ".java", ".c", ".h", ".cpp", ".hpp", ".env",
}
TEXT_NAMES = {".env", ".envrc", ".gitignore", "makefile", "dockerfile"}
CODE_EXTENSIONS = {".py", ".sh", ".bash", ".zsh", ".js", ".mjs", ".cjs", ".ts", ".ps1", ".bat", ".cmd", ".rb"}
PROSE_EXTENSIONS = {".md", ".txt", ".html"}

# High-confidence provider token formats: always a blocker.
TOKEN_PATTERNS = [
    ("private_key", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
    ("anthropic_key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}")),
    ("openai_key", re.compile(r"\bsk-(?:proj-|svcacct-|admin-)?(?!ant-)[A-Za-z0-9_-]{32,}")),
    ("github_token", re.compile(r"\b(?:github_pat_|gh[pousr]_)[A-Za-z0-9_]{30,}")),
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("google_api_key", re.compile(r"\bAIza[A-Za-z0-9_-]{35}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}")),
    ("stripe_live_key", re.compile(r"\b[sr]k_live_[A-Za-z0-9]{20,}")),
]
# Heuristic "key = value" assignment: blocker in code/config, warning in prose.
GENERIC_SECRET = re.compile(
    r"(?i)\b(api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|refresh[_-]?token|secret[_-]?key|password)\b"
    r"\s*[:=]\s*['\"]?([A-Za-z0-9_./+=:-]{12,})"
)
PLACEHOLDER_VALUE = re.compile(r"(?i)(your|example|sample|dummy|placeholder|changeme|replace|xxxx|\.\.\.|<|\$\{|\{\{|env\.|os\.environ|getenv|process\.env)")

DANGEROUS_PATTERNS = [
    ("remote_content_to_shell", re.compile(r"\b(?:curl|wget)\b[^\n|;]*\|\s*(?:sudo\s+)?(?:ba|z|k)?sh\b", re.I)),
    ("remote_content_to_powershell", re.compile(r"\b(?:curl|wget|iwr|irm)\b[^\r\n|;]*\|\s*(?:iex|invoke-expression|powershell|pwsh)\b", re.I)),
    ("recursive_root_delete", re.compile(r"\b(?:sudo\s+)?rm\b[^\n]*(?:-rf|-fr|--recursive)[^\n]*(?:\s/\s|\s/\*|\s/$|\s~(?:/|\s|$)|\$HOME)", re.I | re.M)),
    ("raw_disk_write", re.compile(r"\bdd\b[^\n]*\bof\s*=\s*/dev/", re.I)),
    ("filesystem_format", re.compile(r"\bmkfs(?:\.\w+)?\b", re.I)),
    ("fork_bomb", re.compile(r":\s*\(\s*\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:")),
]

PLACEHOLDER_BODY = [
    re.compile(r"(?im)^\s*(?:[-*]\s*)?(?:TODO|FIXME|XXX)\b"),
    re.compile(r"<[^>\n]*(?:placeholder|fill this|replace me)[^>\n]*>", re.I),
]


class Findings(list):
    def add(self, severity: str, code: str, message: str, path: Optional[str] = None) -> None:
        self.append({"severity": severity, "code": code, "message": message, "path": path})


def is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS or path.name.lower() in TEXT_NAMES or path.name.lower().startswith(".env")


def safe_zip_member(name: str) -> bool:
    norm = name.replace("\\", "/")
    p = PurePosixPath(norm)
    return bool(name) and not p.is_absolute() and ".." not in p.parts and not re.match(r"^[A-Za-z]:", norm)


def extract_zip_safely(path: Path, dest: Path, findings: Findings) -> bool:
    """Validate every member before extracting anything."""
    if path.stat().st_size > MAX_ZIP_BYTES:
        findings.add("blocker", "zip_too_large", f"ZIP exceeds {MAX_ZIP_BYTES} bytes", str(path.name))
        return False
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        findings.add("blocker", "bad_zip", "File is not a valid ZIP archive", str(path.name))
        return False
    with zf:
        infos = zf.infolist()
        if len(infos) > MAX_FILES:
            findings.add("blocker", "too_many_zip_members", f"ZIP contains {len(infos)} members; limit is {MAX_FILES}")
            return False
        total = 0
        seen = {}
        for info in infos:
            key = info.filename.replace("\\", "/").rstrip("/").lower()
            if key in seen:
                findings.add("blocker", "zip_duplicate_entry",
                             f"ZIP lists '{info.filename}' more than once (or twice with different case); tools disagree on which copy wins")
                return False
            seen[key] = info.filename
            if not safe_zip_member(info.filename):
                findings.add("blocker", "unsafe_zip_path", f"Unsafe ZIP member path: {info.filename}")
                return False
            if len(PurePosixPath(info.filename).parts) > MAX_DEPTH:
                findings.add("blocker", "zip_too_deep", f"ZIP member nested deeper than {MAX_DEPTH}: {info.filename}")
                return False
            if stat.S_ISLNK((info.external_attr >> 16) & 0xFFFF):
                findings.add("blocker", "zip_symlink", f"Symlink is not allowed in a Skill package: {info.filename}")
                return False
            if info.file_size > MAX_FILE_BYTES:
                findings.add("blocker", "zip_member_too_large", f"ZIP member exceeds per-file limit: {info.filename}")
                return False
            total += info.file_size
            if total > MAX_TOTAL_BYTES:
                findings.add("blocker", "zip_uncompressed_too_large", "ZIP uncompressed content exceeds inspection limit")
                return False
        # Extract member by member with a hard byte cap, in case headers lie.
        dest_root = dest.resolve()
        try:
            for info in infos:
                target = (dest / info.filename.replace("\\", "/")).resolve()
                target.relative_to(dest_root)  # belt and braces: never write outside dest
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                written = 0
                with zf.open(info) as src, open(target, "wb") as out:
                    while True:
                        chunk = src.read(65536)
                        if not chunk:
                            break
                        written += len(chunk)
                        if written > MAX_FILE_BYTES:
                            findings.add("blocker", "zip_member_too_large", f"ZIP member expands beyond limit: {info.filename}")
                            return False
                        out.write(chunk)
        except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as e:
            findings.add("blocker", "bad_zip", f"ZIP could not be extracted safely: {type(e).__name__}: {e}")
            return False
    # Drop macOS resource-fork noise so it cannot masquerade as a second Skill.
    shutil.rmtree(dest / "__MACOSX", ignore_errors=True)
    return True


def find_skill_roots(base: Path) -> List[Path]:
    if base.is_file() and base.name == "SKILL.md":
        return [base.parent]
    if base.is_dir() and (base / "SKILL.md").is_file():
        return [base]
    roots = []
    if base.is_dir():
        for p in base.rglob("SKILL.md"):
            rel = p.relative_to(base)
            if any(part in sr.EXCLUDE_PARTS for part in rel.parts):
                continue
            if len(rel.parts) <= MAX_DEPTH:
                roots.append(p.parent)
    roots = sorted(set(roots), key=lambda r: len(r.parts))
    # A SKILL.md inside another Skill's folder (e.g. a template in assets/) is content, not a second Skill.
    top: List[Path] = []
    for r in roots:
        if not any(r != o and o in r.parents for o in top):
            top.append(r)
    return sorted(top)


def bounded_files(root: Path, findings: Findings) -> List[Path]:
    files: List[Path] = []
    total = 0
    for current, dirs, names in os.walk(root, followlinks=False):
        rel = Path(current).relative_to(root)
        if len(rel.parts) > MAX_DEPTH:
            findings.add("blocker", "tree_too_deep", f"Directory depth exceeds {MAX_DEPTH}", rel.as_posix())
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if d not in sr.EXCLUDE_PARTS and not (Path(current) / d).is_symlink()]
        for name in names:
            p = Path(current) / name
            if p.is_symlink() or name in sr.EXCLUDE_PARTS or p.suffix in sr.EXCLUDE_SUFFIXES:
                continue
            size = p.stat().st_size
            if size > MAX_FILE_BYTES:
                findings.add("blocker", "file_too_large", f"File exceeds {MAX_FILE_BYTES} bytes", p.relative_to(root).as_posix())
            total += size
            files.append(p)
            if len(files) > MAX_FILES:
                findings.add("blocker", "too_many_files", f"Skill exceeds {MAX_FILES} files")
                return files
            if total > MAX_TOTAL_BYTES:
                findings.add("blocker", "tree_too_large", f"Skill exceeds {MAX_TOTAL_BYTES} total bytes")
                return files
    return files


def scan_text(path: Path) -> str:
    try:
        data = path.read_bytes()[:MAX_TEXT_SCAN_BYTES]
    except OSError:
        return ""
    if b"\x00" in data:
        return ""
    return data.decode("utf-8", errors="replace")


def scan_secrets(rel: str, suffix: str, content: str, findings: Findings) -> None:
    for code, pat in TOKEN_PATTERNS:
        if pat.search(content):
            findings.add("blocker", f"secret_{code}", "Credential-like token detected; remove it and rotate it if it was real", rel)
            return
    for m in GENERIC_SECRET.finditer(content):
        if PLACEHOLDER_VALUE.search(m.group(0)):
            continue
        sev = "warning" if suffix in PROSE_EXTENSIONS else "blocker"
        findings.add(sev, "secret_generic_assignment",
                     f"Possible hard-coded {m.group(1)}; confirm it is an example, not a real value", rel)
        return


FENCE_RE = re.compile(r"(?ms)^[ \t]*(```|~~~)[^\n]*\n(.*?)^[ \t]*\1")
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")


def scan_dangerous(rel: str, content: str, findings: Findings, prose: bool = False) -> None:
    if prose:
        # Instructions the agent may copy and run: fenced blocks and inline code.
        text = "\n".join([m.group(2) for m in FENCE_RE.finditer(content)] + INLINE_CODE_RE.findall(content))
    else:
        text = "\n".join(ln for ln in content.splitlines() if "re.compile(" not in ln and not ln.lstrip().startswith("#"))
    for code, pat in DANGEROUS_PATTERNS:
        if pat.search(text):
            if prose:
                findings.add("warning", f"dangerous_{code}",
                             "Instructions include a potentially destructive or remote-execution command; confirm it is intended and safe", rel)
            else:
                findings.add("blocker", f"dangerous_{code}", "Potentially destructive or unsafe command; manual review required", rel)
            return


def inspect_root(root: Path, target: str = "all", check_dir_name: bool = True) -> dict:
    target = sr.normalize_target(target)
    findings = Findings()
    files = bounded_files(root, findings)
    fields, rule_findings = sr.validate_skill_dir(root, target, check_dir_name=check_dir_name)
    for sev, code, msg, path in rule_findings:
        findings.add(sev, code, msg, path)

    skill_md = root / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8", errors="replace") if skill_md.is_file() else ""
    if text and any(p.search(text) for p in PLACEHOLDER_BODY):
        findings.add("warning", "unfinished_placeholder", "SKILL.md appears to contain TODO or placeholder content", "SKILL.md")

    scripts_dir = root / "scripts"
    if text and scripts_dir.is_dir():
        for p in sorted(scripts_dir.rglob("*")):
            if not p.is_file() or p.suffix in sr.EXCLUDE_SUFFIXES or any(x in sr.EXCLUDE_PARTS for x in p.parts):
                continue
            rel = p.relative_to(root).as_posix()
            if rel not in text and p.name not in text:
                findings.add("warning", "orphan_script", "Bundled script is never mentioned in SKILL.md", rel)

    if (root / "README.md").is_file():
        findings.add("note", "readme_inside_skill", "README.md inside the Skill ships to every user; repository docs belong outside the Skill folder", "README.md")

    for p in files:
        if not is_text_file(p):
            continue
        rel = p.relative_to(root).as_posix()
        content = scan_text(p)
        if not content:
            continue
        scan_secrets(rel, p.suffix.lower(), content, findings)
        if p.suffix.lower() in CODE_EXTENSIONS:
            scan_dangerous(rel, content, findings)
        elif p.suffix.lower() == ".md":
            scan_dangerous(rel, content, findings, prose=True)

    return result_dict(root, target, fields, len(files), findings)


def result_dict(root: Path, target: str, fm: dict, file_count: int, findings: list) -> dict:
    counts = {"blocker": 0, "warning": 0, "note": 0}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    order = {"blocker": 0, "warning": 1, "note": 2}
    return {
        "schema_version": 2,
        "rules_version": sr.RULES_VERSION,
        "status": "fail" if counts["blocker"] else "pass",
        "target": target,
        "skill_root": str(root),
        "frontmatter": {k: fm.get(k) for k in ("name", "description", "license") if fm and k in fm},
        "file_count": file_count,
        "finding_counts": counts,
        "findings": sorted(findings, key=lambda f: order.get(f["severity"], 3)),
        "limitations": [
            "Static inspection does not prove runtime behavior or host compatibility.",
            "Secret and dangerous-command scanning is heuristic and non-exhaustive.",
        ],
    }


def select_root(roots: List[Path], base: Path, select: Optional[str]) -> Optional[Path]:
    """Pick one Skill by its folder path relative to the input, or by its folder name."""
    if not select:
        return None
    sel = select.strip("/").replace("\\", "/")
    for r in roots:
        rel = r.relative_to(base).as_posix() if r != base else "."
        if rel == sel or r.name == sel or rel.endswith("/" + sel):
            return r
    return None


def inspect_path(path, target: str = "all", select: Optional[str] = None) -> dict:
    target = sr.normalize_target(target)
    src = Path(path).expanduser().resolve()
    pre = Findings()
    tmp: Optional[tempfile.TemporaryDirectory] = None
    base = src
    check_dir_name = True
    try:
        if not src.exists():
            pre.add("blocker", "input_not_found", f"Input does not exist: {src}")
            return result_dict(src, target, {}, 0, pre)
        if src.is_file() and src.suffix.lower() == ".zip":
            tmp = tempfile.TemporaryDirectory(prefix="skill-repo-forge-audit-")
            base = Path(tmp.name)
            if not extract_zip_safely(src, base, pre):
                return result_dict(src, target, {}, 0, pre)
        elif src.is_file() and src.name != "SKILL.md":
            if src.suffix.lower() not in {".md", ".txt"}:
                pre.add("blocker", "unsupported_input", "Expected a Skill folder, SKILL.md, markdown draft, or ZIP", src.name)
                return result_dict(src, target, {}, 0, pre)
            tmp = tempfile.TemporaryDirectory(prefix="skill-repo-forge-draft-")
            base = Path(tmp.name) / "draft"
            base.mkdir()
            shutil.copy2(src, base / "SKILL.md")
            check_dir_name = False
            pre.add("note", "draft_input", "Audited a loose markdown draft; the folder-name check was skipped")
        elif src.is_file() and src.name == "SKILL.md":
            base = src.parent

        roots = find_skill_roots(base)
        if not roots:
            pre.add("blocker", "no_skill_found", "No SKILL.md entrypoint found", src.name)
            return result_dict(src, target, {}, 0, pre)
        if select:
            chosen = select_root(roots, base, select)
            if chosen is None:
                pre.add("blocker", "selected_skill_not_found", f"No Skill matching '{select}'", src.name)
                result = result_dict(src, target, {}, 0, pre)
                result["candidate_roots"] = [r.relative_to(base).as_posix() if r != base else "." for r in roots]
                return result
            roots = [chosen]
        if len(roots) > 1:
            pre.add("blocker", "multiple_skills_found", f"Found {len(roots)} Skills; pick one with --select <path>", src.name)
            result = result_dict(src, target, {}, 0, pre)
            result["candidate_roots"] = [r.relative_to(base).as_posix() for r in roots]
            return result
        if src.suffix.lower() == ".zip" and roots[0] == base:
            check_dir_name = False
            pre.add("warning", "zip_without_top_folder",
                    "SKILL.md sits at the ZIP root; hosts such as Claude expect a single <skill-name>/ folder inside the ZIP")
        result = inspect_root(roots[0], target, check_dir_name=check_dir_name)
        if tmp:
            result["skill_root"] = f"{src.name}:{roots[0].relative_to(base).as_posix() if roots[0] != base else '.'}"
        if pre:
            merged = list(pre) + result["findings"]
            return result_dict(Path(result["skill_root"]), target, result["frontmatter"], result["file_count"], merged) | {"skill_root": result["skill_root"]}
        return result
    finally:
        if tmp is not None:
            tmp.cleanup()


def render_text(result: dict) -> str:
    lines = [
        f"Status: {result['status'].upper()}   Target: {result['target']}   Rules: {result.get('rules_version')}",
        f"Skill:  {result.get('frontmatter', {}).get('name') or 'unknown'}   Files: {result.get('file_count', 0)}",
        "",
    ]
    findings = result.get("findings", [])
    if not findings:
        lines.append("No static findings.")
    for f in findings:
        loc = f" [{f['path']}]" if f.get("path") else ""
        lines.append(f"- {f['severity'].upper()} {f['code']}{loc}: {f['message']}")
    for c in result.get("candidate_roots", []):
        lines.append(f"  candidate: {c}")
    c = result.get("finding_counts", {})
    lines += ["", f"Findings: {c.get('blocker', 0)} blockers, {c.get('warning', 0)} warnings, {c.get('note', 0)} notes."]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", help="Skill folder, SKILL.md, markdown draft, or ZIP")
    parser.add_argument("--target", default="all", help="all (default), portable, claude, or openai")
    parser.add_argument("--select", help="when the input holds several Skills, the folder path or name of the one to audit")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()
    try:
        result = inspect_path(args.path, args.target, args.select)
    except ValueError as e:
        parser.error(str(e))
    print(json.dumps(result, indent=2) if args.json else render_text(result))
    return 2 if result["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
