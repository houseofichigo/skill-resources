#!/usr/bin/env python3
"""Validate the public reusable-skill catalogue without third-party dependencies."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog.json"
ALLOWED_ONBOARDING = {"profile", "intake"}
OPS_DIRS = {"agents", "assets", "references", "scripts"}
PUBLISHER_PATTERN = re.compile(r"house\s+of\s+ichigo|houseofichigo|\bHOI\b", re.I)
LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def frontmatter_name(text: str) -> str | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    match = re.search(r"^name:\s*['\"]?([^'\"\n]+)", text[4:end], re.M)
    return match.group(1).strip() if match else None


def zip_skill_bytes(path: Path, skill_id: str) -> bytes | None:
    with zipfile.ZipFile(path) as archive:
        matches = [n for n in archive.namelist() if n.rstrip("/").endswith(f"{skill_id}/SKILL.md") or n == "SKILL.md"]
        if len(matches) != 1:
            return None
        return archive.read(matches[0])


def validate_links(errors: list[str]) -> None:
    for markdown in (ROOT / "README.md", ROOT / "CONTRIBUTING.md", ROOT / "STANDARD.md"):
        for raw in LINK_PATTERN.findall(markdown.read_text(encoding="utf-8")):
            target = raw.split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            if not (markdown.parent / target).resolve().exists():
                fail(errors, f"broken local link in {markdown.relative_to(ROOT)}: {raw}")


def validate_neutrality(errors: list[str], source: Path) -> None:
    candidates = [source / "SKILL.md"]
    for dirname in OPS_DIRS:
        folder = source / dirname
        if folder.exists():
            candidates.extend(p for p in folder.rglob("*") if p.is_file())
    for path in candidates:
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".zip", ".pdf", ".pptx"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if PUBLISHER_PATTERN.search(text):
            fail(errors, f"operational publisher coupling in {path.relative_to(ROOT)}")


def main() -> int:
    errors: list[str] = []
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    records = data.get("skills", [])
    ids = [record.get("id") for record in records]
    if len(ids) != 13 or len(ids) != len(set(ids)):
        fail(errors, "catalogue must contain exactly 13 unique skill IDs")
    if any(path.name.startswith("hoi-") for path in (ROOT / "skills").iterdir() if path.is_dir()):
        fail(errors, "general catalogue contains an HOI-prefixed top-level package")
    expected_packages = {record["package"] for record in records}
    actual_packages = {str(path.relative_to(ROOT)) for path in (ROOT / "skills").iterdir() if path.is_dir()}
    if expected_packages != actual_packages:
        fail(errors, f"package set mismatch: expected {sorted(expected_packages)}, found {sorted(actual_packages)}")

    for record in records:
        skill_id = record["id"]
        source = ROOT / record["source"]
        dist = ROOT / record["distribution"]
        skill_file = source / "SKILL.md"
        if record.get("onboarding") not in ALLOWED_ONBOARDING:
            fail(errors, f"invalid onboarding class for {skill_id}")
        if not skill_file.is_file():
            fail(errors, f"missing SKILL.md for {skill_id}: {skill_file.relative_to(ROOT)}")
            continue
        source_bytes = skill_file.read_bytes()
        if frontmatter_name(source_bytes.decode("utf-8")) != skill_id:
            fail(errors, f"frontmatter name mismatch for {skill_id}")
        if not dist.is_file():
            fail(errors, f"missing distribution for {skill_id}: {dist.relative_to(ROOT)}")
        else:
            try:
                archived = zip_skill_bytes(dist, skill_id)
            except zipfile.BadZipFile:
                archived = None
            if archived != source_bytes:
                fail(errors, f"distribution SKILL.md mismatch for {skill_id}")
        validate_neutrality(errors, source)

    validate_links(errors)
    repository_text = "\n".join(
        p.read_text(encoding="utf-8", errors="ignore")
        for p in ROOT.rglob("*.md")
        if ".git" not in p.parts
    )
    if "unpublished local draft" in repository_text.lower():
        fail(errors, "public repository contains an 'unpublished local draft' claim")

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    digest = hashlib.sha256(CATALOG.read_bytes()).hexdigest()
    print(f"Validated {len(records)} reusable skill IDs across {len(expected_packages)} packages.")
    print(f"catalog.json sha256: {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
