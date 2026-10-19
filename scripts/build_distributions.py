#!/usr/bin/env python3
"""Build all public skill ZIPs deterministically."""
import argparse, io, json, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORTABLE_FILES = {"SKILL.md", "LICENSE.txt"}
PORTABLE_DIRS = {"agents", "assets", "references", "scripts"}
ZIP_TIME = (2020, 1, 1, 0, 0, 0)

def portable_files(source):
    out = []
    for path in source.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(source)
        if rel.name == ".DS_Store" or "__pycache__" in rel.parts:
            continue
        if (len(rel.parts) == 1 and rel.name in PORTABLE_FILES) or rel.parts[0] in PORTABLE_DIRS:
            out.append(path)
    return sorted(out, key=lambda p: p.relative_to(source).as_posix())

def skill_archive(skill_id, source):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in portable_files(source):
            rel = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(skill_id + "/" + rel, date_time=ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            payload = path.read_bytes()
            info.external_attr = (0o755 if payload.startswith(b"#!") else 0o644) << 16
            info.create_system = 3
            archive.writestr(info, payload)
    return output.getvalue()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    records = json.loads((ROOT / "catalog.json").read_text())["skills"]
    expected_paths = {ROOT / r["distribution"] for r in records}
    dist = ROOT / "dist"
    ok = True
    actual_paths = set(dist.glob("*.zip")) if dist.is_dir() else set()
    if args.check:
        for extra in sorted(actual_paths - expected_paths):
            print("unexpected distribution:", extra.relative_to(ROOT)); ok = False
    else:
        dist.mkdir(exist_ok=True)
        for extra in sorted(actual_paths - expected_paths):
            extra.unlink(); print("removed stale", extra.relative_to(ROOT))
    for record in records:
        source, target = ROOT / record["source"], ROOT / record["distribution"]
        expected = skill_archive(record["id"], source)
        if args.check:
            if not target.is_file() or target.read_bytes() != expected:
                print("distribution drift:", target.relative_to(ROOT)); ok = False
        else:
            target.write_bytes(expected); print("built", target.relative_to(ROOT))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
