#!/usr/bin/env python3
"""Build every catalogue ZIP deterministically from its reviewed source."""

from __future__ import annotations

import argparse
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog.json"
PORTABLE_FILES = {"SKILL.md", "LICENSE.txt"}
PORTABLE_DIRS = {"agents", "assets", "references", "scripts"}
ZIP_TIME = (2020, 1, 1, 0, 0, 0)


def portable_files(source: Path) -> list[Path]:
    files: list[Path] = []
    for path in source.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        if relative.name == ".DS_Store" or "__pycache__" in relative.parts:
            continue
        if len(relative.parts) == 1 and relative.name in PORTABLE_FILES:
            files.append(path)
        elif relative.parts[0] in PORTABLE_DIRS:
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(source).as_posix())


def zip_bytes(entries: list[tuple[str, Path]]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for archive_name, source in sorted(entries):
            info = zipfile.ZipInfo(archive_name, date_time=ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            payload = source.read_bytes()
            mode = 0o755 if payload.startswith(b"#!") else 0o644
            info.external_attr = mode << 16
            info.create_system = 3
            archive.writestr(info, payload)
    return output.getvalue()


def skill_archive(skill_id: str, source: Path) -> bytes:
    return zip_bytes(
        [(f"{skill_id}/{path.relative_to(source).as_posix()}", path) for path in portable_files(source)]
    )


def suite_archive(records: list[dict[str, str]]) -> bytes:
    entries: list[tuple[str, Path]] = []
    for record in records:
        source = ROOT / record["source"]
        skill_id = record["id"]
        for path in portable_files(source):
            relative = path.relative_to(source).as_posix()
            entries.append((f"content-radar-skills/skills/{skill_id}/{relative}", path))
    profile = ROOT / "skills/content-radar-skills/resources/profile.template.md"
    entries.append(("content-radar-skills/resources/profile.template.md", profile))
    return zip_bytes(entries)


def write_or_check(path: Path, expected: bytes, check: bool) -> bool:
    if check:
        if not path.is_file() or path.read_bytes() != expected:
            print(f"distribution drift: {path.relative_to(ROOT)}")
            return False
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(expected)
    print(f"built {path.relative_to(ROOT)}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail instead of rewriting when a ZIP differs")
    args = parser.parse_args()

    records = json.loads(CATALOG.read_text(encoding="utf-8"))["skills"]
    ok = True
    for record in records:
        source = ROOT / record["source"]
        target = ROOT / record["distribution"]
        ok = write_or_check(target, skill_archive(record["id"], source), args.check) and ok

    radar_records = [record for record in records if record["package"] == "skills/content-radar-skills"]
    suite = ROOT / "skills/content-radar-skills/dist/content-radar-skills.zip"
    ok = write_or_check(suite, suite_archive(radar_records), args.check) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
