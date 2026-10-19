#!/usr/bin/env python3
"""Validate the exact public catalogue, neutral content and ZIP parity."""
import hashlib, json, re, stat, sys, zipfile
from pathlib import Path, PurePosixPath
from build_distributions import PORTABLE_DIRS, ZIP_TIME, portable_files

ROOT = Path(__file__).resolve().parents[1]
APPROVED_IDS = {
"agent-sdk-brief","agent-skill-brief","api-integration-brief","apps-script-brief","assistant-builder",
"brand-factory","business-process-mapper","chatgpt-skill-brief","code-assistant-brief","codex-cli-brief",
"codex-sdk-brief","competitor-scan","content-ideas","content-radar","content-radar-setup","crewai-brief",
"custom-code-brief","dust-brief","make-brief","meeting-brief-builder","n8n-brief","newsjacking",
"pipedream-brief","production-skill-kit","prompt-documenter","prompt-optimizer","seo-aeo-geo",
"skill-repo-forge","sop-deck-builder","strategic-brief-builder","trend-radar","vibe-prompt-architect",
"visual-prompt-scout","which-ai-model","zapier-brief"}
ROOT_FILES = {".gitattributes",".gitignore","CHANGELOG.md","CONTRIBUTING.md","LICENSE","README.md",
"RELEASE-SAFETY.md","SECURITY.md","STANDARD.md","catalog.json"}
ROOT_DIRS = {".github","dist","scripts","skills","tests"}
SKILL_FILES, SKILL_DIRS = {"SKILL.md","LICENSE.txt"}, {"agents","assets","references","scripts"}
FORBIDDEN_PARTS = {"archives","originals","private","source-imports"}
PUBLISHER = re.compile(r"house\s+of\s+ichigo|houseofichigo|\bHOI\b", re.I)
OWNER = re.compile(r"\bsabr(?:i|y)\b", re.I)
EMAIL = re.compile(r"(?<![\w.+-])([\w.+-]+@[\w.-]+\.[A-Za-z]{2,})(?![\w.-])")
ABS_PATH = re.compile(r"(?:/Users/[A-Za-z0-9._-]+/|/home/[A-Za-z0-9._-]+/|[A-Za-z]:\\\\Users\\\\[^\\s]+)")
INTERNAL = re.compile(
    r"workspaces/hoi-" + r"company|systems/hoi-os-" + r"runtime|\.secrets(?:/|\\)|internal implementation " + r"brief",
    re.I,
)
SECRETS = [re.compile(x) for x in [r"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY",r"\bAKIA[0-9A-Z]{16}\b",
r"\bgh[opusr]_[A-Za-z0-9]{30,}\b",r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b",r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"]]
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
TEXT_SUFFIXES = {".css",".html",".js",".json",".md",".py",".sh",".svg",".toml",".txt",".yaml",".yml"}

def fm_value(text, field):
    if not text.startswith("---\n"): return None
    end = text.find("\n---", 4)
    if end < 0: return None
    match = re.search("^" + re.escape(field) + r":\s*['\"]?([^'\"\n]+)", text[4:end], re.M)
    return match.group(1).strip() if match else None

def safe_member(name):
    p = PurePosixPath(name)
    return bool(name) and not p.is_absolute() and ".." not in p.parts and "\\" not in name

def zip_payload(path, skill_id):
    try: archive = zipfile.ZipFile(path)
    except (FileNotFoundError, zipfile.BadZipFile): return None
    with archive:
        out = {}
        for info in archive.infolist():
            if not safe_member(info.filename) or stat.S_ISLNK(info.external_attr >> 16): return None
            if info.is_dir(): continue
            parts = PurePosixPath(info.filename).parts
            if not parts or parts[0] != skill_id or info.date_time != ZIP_TIME: return None
            rel = PurePosixPath(*parts[1:]).as_posix()
            if not rel or rel in out: return None
            out[rel] = archive.read(info)
        return out

def source_payload(source):
    return {p.relative_to(source).as_posix(): p.read_bytes() for p in portable_files(source)}

def attribution_allowed(path):
    rel = path.relative_to(ROOT)
    return rel.as_posix() in {"catalog.json","scripts/validate_catalog.py","tests/test_release.py"} or rel.name == "LICENSE.txt" or len(rel.parts) == 1

def sensitive(text, rel, allow_publisher):
    out = []
    if not allow_publisher and PUBLISHER.search(text): out.append("operational publisher coupling")
    if OWNER.search(text): out.append("owner-identifying name")
    if ABS_PATH.search(text): out.append("machine-specific absolute path")
    if INTERNAL.search(text): out.append("private/internal runtime reference")
    if any(e.rsplit("@",1)[1].lower() not in {"example.com","example.org","example.net"} for e in EMAIL.findall(text)):
        out.append("non-fictional email address")
    if any(p.search(text) for p in SECRETS): out.append("possible credential or private key")
    return [x + " in " + rel for x in out]

def validate_skill(errors, record):
    sid, source, dist = record["id"], ROOT / record["source"], ROOT / record["distribution"]
    if record["source"] != "skills/" + sid or record["distribution"] != "dist/" + sid + ".zip":
        errors.append("non-canonical path for " + sid)
    if record.get("onboarding") not in {"profile","intake"}: errors.append("invalid onboarding for " + sid)
    skill = source / "SKILL.md"
    if not skill.is_file(): errors.append("missing SKILL.md for " + sid); return
    text = skill.read_text()
    if fm_value(text,"name") != sid: errors.append("frontmatter name mismatch for " + sid)
    if fm_value(text,"license") != "MIT": errors.append("frontmatter licence must be MIT for " + sid)
    if not (source / "LICENSE.txt").is_file(): errors.append("missing LICENSE.txt for " + sid)
    if record["onboarding"] == "profile" and not re.search(r"profile|onboard|intake", text, re.I):
        errors.append("profile onboarding not discoverable for " + sid)
    if record["onboarding"] == "intake" and not re.search(r"ask|intake|assum|clarif|input", text, re.I):
        errors.append("task intake not discoverable for " + sid)
    ui = source / "agents/openai.yaml"
    if not ui.is_file(): errors.append("missing agents/openai.yaml for " + sid)
    else:
        data = ui.read_text()
        short = re.search(r'^\s*short_description:\s*"([^"]+)"\s*$', data, re.M)
        prompt = re.search(r'^\s*default_prompt:\s*"([^"]+)"\s*$', data, re.M)
        display = re.search(r'^\s*display_name:\s*"([^"]+)"\s*$', data, re.M)
        if not display: errors.append("missing quoted display_name for " + sid)
        if not short or not 25 <= len(short.group(1)) <= 64: errors.append("invalid short_description for " + sid)
        if not prompt or "$" + sid not in prompt.group(1): errors.append("default_prompt must mention $" + sid)
    archived = zip_payload(dist, sid)
    if archived is None: errors.append("unsafe, missing or non-deterministic ZIP for " + sid)
    elif archived != source_payload(source): errors.append("ZIP/source mismatch for " + sid)

def main():
    errors = []
    data = json.loads((ROOT / "catalog.json").read_text())
    records, ids = data.get("skills",[]), [x.get("id") for x in data.get("skills",[])]
    if data.get("skill_count") != 35 or set(ids) != APPROVED_IDS or len(ids) != 35:
        errors.append("catalogue does not match the exact 35-skill allowlist")
    if len(ids) != len(set(ids)): errors.append("duplicate catalogue ID")
    actual = {p.name for p in (ROOT/"skills").iterdir() if p.is_dir()}
    if actual != APPROVED_IDS: errors.append("skills/ does not match the exact allowlist")
    root_files = {p.name for p in ROOT.iterdir() if p.is_file() and p.name != ".DS_Store"}
    root_dirs = {p.name for p in ROOT.iterdir() if p.is_dir() and p.name != ".git"}
    if root_files != ROOT_FILES: errors.append("root file set mismatch")
    if root_dirs != ROOT_DIRS: errors.append("root directory set mismatch")
    for d in (ROOT/"skills").iterdir():
        if not d.is_dir(): errors.append("non-directory under skills/: " + d.name); continue
        files, dirs = {p.name for p in d.iterdir() if p.is_file()}, {p.name for p in d.iterdir() if p.is_dir()}
        if files - SKILL_FILES: errors.append("unexpected root files in " + d.name + ": " + repr(sorted(files-SKILL_FILES)))
        if dirs - SKILL_DIRS: errors.append("unexpected root dirs in " + d.name + ": " + repr(sorted(dirs-SKILL_DIRS)))
    for record in records: validate_skill(errors, record)
    expected_zips = {x["id"] + ".zip" for x in records}
    actual_zips = {p.name for p in (ROOT/"dist").glob("*.zip")} if (ROOT/"dist").is_dir() else set()
    if actual_zips != expected_zips: errors.append("dist/ does not match the exact allowlist")
    for path in ROOT.rglob("*"):
        if ".git" in path.parts or "__pycache__" in path.parts or not path.is_file(): continue
        rel = path.relative_to(ROOT)
        if any(x.lower() in FORBIDDEN_PARTS for x in rel.parts): errors.append("forbidden path: " + str(rel))
        if rel.parts[0] == "dist": continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in {"LICENSE",".gitignore"}:
            text = path.read_text(errors="ignore")
            errors.extend(sensitive(text, rel.as_posix(), attribution_allowed(path)))
            if path.suffix.lower() == ".json":
                try: json.loads(text)
                except json.JSONDecodeError as e: errors.append("invalid JSON in " + str(rel) + ": " + str(e))
            if path.suffix.lower() == ".md":
                for raw in LINK.findall(text):
                    target = raw.split("#",1)[0]
                    if target and "://" not in target and not target.startswith(("mailto:","codex:")) and "<" not in target and not (path.parent/target).resolve().exists():
                        errors.append("broken link in " + str(rel) + ": " + raw)
    if errors:
        print("Validation failed:")
        for e in sorted(set(errors)): print("-",e)
        return 1
    digest = hashlib.sha256((ROOT/"catalog.json").read_bytes()).hexdigest()
    print("Validated 35 reusable skills in 35 canonical folders.")
    print("Validated neutral content, licences, links, metadata, layout and ZIP/source parity.")
    print("catalog.json sha256:", digest)
    return 0

if __name__ == "__main__":
    sys.exit(main())
