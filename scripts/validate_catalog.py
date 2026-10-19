#!/usr/bin/env python3
"""Validate inventory, anonymisation, archive safety and release reproducibility."""

from __future__ import annotations

import hashlib
import json
import re
import stat
import sys
import zipfile
from pathlib import Path, PurePosixPath

from build_distributions import PORTABLE_DIRS, ZIP_TIME, portable_files

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog.json"
ALLOWED_IDS = {
    "brand-factory", "competitor-scan", "content-ideas", "content-radar",
    "content-radar-setup", "newsjacking", "prompt-optimizer", "seo-aeo-geo",
    "skill-repo-forge", "trend-radar", "vibe-prompt-architect",
    "visual-prompt-scout", "which-ai-model",
}
ALLOWED_ONBOARDING = {"profile", "intake"}
FORBIDDEN_DIRECTORY_PARTS = {"archives", "originals", "private", "source-imports"}
ATTRIBUTION_FILES = {
    "CONTRIBUTING.md", "LICENSE", "README.md", "SECURITY.md", "STANDARD.md",
    "RELEASE-SAFETY.md",
}
PUBLISHER_PATTERN = re.compile(r"house\s+of\s+ichigo|houseofichigo|\bHOI\b", re.I)
OWNER_PATTERN = re.compile(r"\bsabr(?:i|y)\b", re.I)
EMAIL_PATTERN = re.compile(r"(?<![\w.+-])([\w.+-]+@[\w.-]+\.[A-Za-z]{2,})(?![\w.-])")
ABSOLUTE_PATH_PATTERN = re.compile(
    r"(?:/Users/[A-Za-z0-9._-]+/|/home/[A-Za-z0-9._-]+/|[A-Za-z]:\\\\Users\\\\[^\\\s]+)"
)
INTERNAL_RUNTIME_PATTERN = re.compile(
    r"workspaces/hoi-" + r"company|systems/hoi-os-" + r"runtime|\.secrets(?:/|\\)|internal implementation " + r"brief",
    re.I,
)
SECRET_PATTERNS = [
    re.compile(r"BEGIN " + r"(?:RSA |OPENSSH |EC )?PRIVATE KEY"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[opusr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
    re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]\s*['\"]?"
        r"(?!<|\$\{|\$[A-Z_]|YOUR_|EXAMPLE_|REDACTED|CHANGEME)[A-Za-z0-9_./+=-]{12,}"
    ),
]
LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
TEXT_SUFFIXES = {
    ".css", ".html", ".js", ".json", ".md", ".py", ".sh", ".svg",
    ".toml", ".txt", ".yaml", ".yml",
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---", 4)
    return "" if end < 0 else text[4:end]


def frontmatter_value(text: str, field: str) -> str | None:
    match = re.search(rf"^{re.escape(field)}:\s*['\"]?([^'\"\n]+)", frontmatter(text), re.M)
    return match.group(1).strip() if match else None


def archive_member_is_safe(name: str) -> bool:
    path = PurePosixPath(name)
    return bool(name) and not path.is_absolute() and ".." not in path.parts and "\\" not in name


def zip_payload(path: Path, skill_id: str) -> dict[str, bytes] | None:
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        return None
    with archive:
        result: dict[str, bytes] = {}
        for info in archive.infolist():
            if not archive_member_is_safe(info.filename):
                return None
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                return None
            if info.is_dir():
                continue
            parts = PurePosixPath(info.filename).parts
            if not parts or parts[0] != skill_id:
                return None
            relative = PurePosixPath(*parts[1:]).as_posix()
            if not relative or relative in result or info.date_time != ZIP_TIME:
                return None
            result[relative] = archive.read(info)
        return result


def source_payload(source: Path) -> dict[str, bytes]:
    return {path.relative_to(source).as_posix(): path.read_bytes() for path in portable_files(source)}


def find_sensitive_issues(text: str, relative: str, attribution_is_allowed: bool) -> list[str]:
    issues: list[str] = []
    if not attribution_is_allowed and PUBLISHER_PATTERN.search(text):
        issues.append("operational publisher coupling")
    if OWNER_PATTERN.search(text):
        issues.append("owner-identifying name")
    if ABSOLUTE_PATH_PATTERN.search(text):
        issues.append("machine-specific absolute path")
    if INTERNAL_RUNTIME_PATTERN.search(text):
        issues.append("private/internal runtime reference")
    for email in EMAIL_PATTERN.findall(text):
        domain = email.rsplit("@", 1)[1].lower()
        if domain not in {"example.com", "example.org", "example.net"}:
            issues.append("non-fictional email address")
            break
    if any(pattern.search(text) for pattern in SECRET_PATTERNS):
        issues.append("possible credential or private key")
    return [f"{issue} in {relative}" for issue in issues]


def attribution_allowed(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if relative.as_posix() in {"catalog.json", "scripts/validate_catalog.py", "tests/test_release.py"}:
        return True
    if relative.name == "LICENSE.txt":
        return True
    return relative.name in ATTRIBUTION_FILES and not any(part in PORTABLE_DIRS for part in relative.parts)


def validate_tree_safety(errors: list[str]) -> None:
    for path in ROOT.rglob("*"):
        if ".git" in path.parts:
            continue
        relative = path.relative_to(ROOT)
        if path.is_symlink():
            fail(errors, f"symlink is not allowed: {relative}")
            continue
        if "dist" in relative.parts:
            dist_index = relative.parts.index("dist")
            if path.is_dir() and len(relative.parts) > dist_index + 1:
                fail(errors, f"expanded content is not allowed under dist/: {relative}")
            if path.is_file() and path.suffix.lower() != ".zip":
                fail(errors, f"only ZIP artifacts are allowed under dist/: {relative}")
        if any(part.lower() in FORBIDDEN_DIRECTORY_PARTS for part in relative.parts):
            fail(errors, f"forbidden public directory: {relative}")
        if not path.is_file() or "dist" in relative.parts:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"LICENSE", ".gitignore"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for issue in find_sensitive_issues(text, relative.as_posix(), attribution_allowed(path)):
            fail(errors, issue)


def validate_links(errors: list[str]) -> None:
    for markdown in ROOT.rglob("*.md"):
        if ".git" in markdown.parts or "dist" in markdown.parts:
            continue
        for raw in LINK_PATTERN.findall(markdown.read_text(encoding="utf-8")):
            target = raw.split("#", 1)[0]
            if not target or "://" in target or target.startswith(("mailto:", "codex:")):
                continue
            if not (markdown.parent / target).resolve().exists():
                fail(errors, f"broken local link in {markdown.relative_to(ROOT)}: {raw}")


def validate_skill(errors: list[str], record: dict[str, str]) -> None:
    skill_id = record["id"]
    source = ROOT / record["source"]
    distribution = ROOT / record["distribution"]
    skill_file = source / "SKILL.md"
    if record.get("onboarding") not in ALLOWED_ONBOARDING:
        fail(errors, f"invalid onboarding class for {skill_id}")
    if not skill_file.is_file():
        fail(errors, f"missing SKILL.md for {skill_id}: {skill_file.relative_to(ROOT)}")
        return
    text = skill_file.read_text(encoding="utf-8")
    if frontmatter_value(text, "name") != skill_id:
        fail(errors, f"frontmatter name mismatch for {skill_id}")
    if frontmatter_value(text, "license") != "MIT":
        fail(errors, f"frontmatter license must be MIT for {skill_id}")
    if not (source / "LICENSE.txt").is_file():
        fail(errors, f"missing LICENSE.txt for {skill_id}")
    if not (source / "agents/openai.yaml").is_file():
        fail(errors, f"missing agents/openai.yaml for {skill_id}")
    if record["onboarding"] == "profile" and not re.search(r"profile|onboard|intake", text, re.I):
        fail(errors, f"profile onboarding is not discoverable in {skill_id}")
    if record["onboarding"] == "intake" and not re.search(r"ask|intake|assum|clarif", text, re.I):
        fail(errors, f"task intake behavior is not discoverable in {skill_id}")
    if not distribution.is_file():
        fail(errors, f"missing distribution for {skill_id}: {distribution.relative_to(ROOT)}")
        return
    archived = zip_payload(distribution, skill_id)
    if archived is None:
        fail(errors, f"unsafe, malformed or non-deterministic ZIP for {skill_id}")
    elif archived != source_payload(source):
        fail(errors, f"distribution/source mismatch for {skill_id}")


def main() -> int:
    errors: list[str] = []
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    records = data.get("skills", [])
    ids = [record.get("id") for record in records]
    if set(ids) != ALLOWED_IDS or len(ids) != len(ALLOWED_IDS):
        fail(errors, f"catalogue must contain exactly the approved IDs: {sorted(ALLOWED_IDS)}")
    if len(ids) != len(set(ids)):
        fail(errors, "catalogue contains duplicate skill IDs")

    expected_packages = {record["package"] for record in records}
    actual_packages = {str(path.relative_to(ROOT)) for path in (ROOT / "skills").iterdir() if path.is_dir()}
    if expected_packages != actual_packages:
        fail(errors, f"package set mismatch: expected {sorted(expected_packages)}, found {sorted(actual_packages)}")
    sources = [record["source"] for record in records]
    if len(sources) != len(set(sources)):
        fail(errors, "catalogue contains duplicate source paths")
    for record in records:
        validate_skill(errors, record)

    validate_tree_safety(errors)
    validate_links(errors)
    repository_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in ROOT.rglob("*.md")
        if ".git" not in path.parts and "dist" not in path.parts
    )
    if "unpublished local draft" in repository_text.lower():
        fail(errors, "public repository contains an 'unpublished local draft' claim")

    if errors:
        print("Validation failed:")
        for error in sorted(set(errors)):
            print(f"- {error}")
        return 1
    digest = hashlib.sha256(CATALOG.read_bytes()).hexdigest()
    print(f"Validated {len(records)} reusable skill IDs across {len(expected_packages)} packages.")
    print("Validated anonymisation, licence, link, archive-safety and ZIP/source parity gates.")
    print(f"catalog.json sha256: {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
