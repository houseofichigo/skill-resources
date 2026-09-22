#!/usr/bin/env python3
"""Classify untrusted prompt text without printing the payload."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str


BLOCKED_PATTERNS = (
    (
        "hierarchy_override",
        re.compile(
            r"\bignore\s+(?:all\s+|any\s+|the\s+|your\s+)?(?:previous|prior|above)\b.{0,80}\b(?:instruction|message|prompt|rule)s?\b",
            re.I | re.S,
        ),
        "Attempts to override prior instructions.",
    ),
    (
        "prompt_disclosure",
        re.compile(
            r"\b(?:reveal|print|show|expose|repeat)\b.{0,80}\b(?:system|developer|hidden)\b.{0,30}\b(?:prompt|message|instruction)s?\b",
            re.I | re.S,
        ),
        "Requests hidden or privileged instructions.",
    ),
    (
        "sensitive_data_access",
        re.compile(
            r"\b(?:read|open|upload|send|exfiltrate|reveal|steal)\b.{0,100}\b(?:\.env|credential|api[ _-]?key|secret|token|password|local file|memory|conversation history|private data)s?\b",
            re.I | re.S,
        ),
        "Requests access to or transmission of sensitive data.",
    ),
    (
        "tool_execution",
        re.compile(
            r"\b(?:run|execute|invoke|call|launch)\b.{0,60}\b(?:shell|terminal|command|tool|script|installer|powershell|bash|curl|wget)\b",
            re.I | re.S,
        ),
        "Attempts to trigger tools or command execution.",
    ),
    (
        "external_action",
        re.compile(
            r"\b(?:upload|publish|post|email|message|submit|send)\b.{0,80}\b(?:file|form|data|content|secret|credential|third[- ]party|server)\b",
            re.I | re.S,
        ),
        "Attempts to cause an external side effect.",
    ),
)

SUSPICIOUS_PATTERNS = (
    (
        "role_prefix",
        re.compile(r"(?im)^\s*(?:system|developer|assistant)\s*:\s*"),
        "Contains a role-prefixed message.",
    ),
    (
        "instruction_address",
        re.compile(
            r"\b(?:follow these instructions|do not tell the user|you are now|act as the system)\b",
            re.I,
        ),
        "Contains language directed at the agent.",
    ),
    (
        "active_content",
        re.compile(r"<(?:script|iframe|object|embed)\b|javascript:|data:text/html", re.I),
        "Contains active or executable web content.",
    ),
    (
        "shell_fragment",
        re.compile(r"(?im)^\s*(?:curl|wget|bash|sh|powershell|cmd(?:\.exe)?)\s+"),
        "Contains a command-like line.",
    ),
)

URL_PATTERN = re.compile(r"https?://[^\s<>\]\)\"']+", re.I)
BASE64_PATTERN = re.compile(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{160,}={0,2}(?![A-Za-z0-9+/])")
CONTROL_NAMES = ("ZERO WIDTH", "RIGHT-TO-LEFT", "LEFT-TO-RIGHT", "WORD JOINER")


def normalise(text: str) -> str:
    return unicodedata.normalize("NFKC", text).replace("\r\n", "\n").replace("\r", "\n")


def scan(text: str, allowed_domains: set[str]) -> dict[str, object]:
    clean = normalise(text)
    findings: list[Finding] = []

    for code, pattern, message in BLOCKED_PATTERNS:
        if pattern.search(clean):
            findings.append(Finding("blocked", code, message))

    for code, pattern, message in SUSPICIOUS_PATTERNS:
        if pattern.search(clean):
            findings.append(Finding("suspicious", code, message))

    if BASE64_PATTERN.search(clean):
        findings.append(
            Finding("suspicious", "encoded_blob", "Contains a long encoded-looking payload.")
        )

    if "<!--" in clean or "-->" in clean:
        findings.append(
            Finding("suspicious", "html_comment", "Contains hidden HTML comment markup.")
        )

    hidden = sorted(
        {
            unicodedata.name(char, "UNKNOWN")
            for char in clean
            if any(marker in unicodedata.name(char, "") for marker in CONTROL_NAMES)
        }
    )
    if hidden:
        findings.append(
            Finding(
                "suspicious",
                "unicode_control",
                "Contains hidden or bidirectional Unicode controls: " + ", ".join(hidden),
            )
        )

    urls = URL_PATTERN.findall(clean)
    unapproved: list[str] = []
    for url in urls:
        host = (urlparse(url).hostname or "").lower().rstrip(".")
        if not any(host == domain or host.endswith("." + domain) for domain in allowed_domains):
            unapproved.append(url)
    if unapproved:
        findings.append(
            Finding(
                "suspicious",
                "unapproved_url",
                f"Contains {len(unapproved)} URL(s) outside the supplied allowlist.",
            )
        )

    severities = {finding.severity for finding in findings}
    status = "blocked" if "blocked" in severities else "suspicious" if findings else "safe"
    score = sum(100 if f.severity == "blocked" else 25 for f in findings)
    return {
        "status": status,
        "risk_score": min(score, 100),
        "sha256": hashlib.sha256(clean.encode("utf-8")).hexdigest(),
        "length": len(clean),
        "url_count": len(urls),
        "unapproved_url_count": len(unapproved),
        "findings": [asdict(finding) for finding in findings],
        "limitations": [
            "Pattern matching cannot detect every prompt-injection technique.",
            "A safe result does not authorize tool use, secret access, or external actions.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--stdin", action="store_true", help="Read prompt text from stdin")
    source.add_argument("--file", type=Path, help="Read prompt text from a UTF-8 file")
    source.add_argument("--text", help="Scan the supplied prompt text")
    parser.add_argument(
        "--allow-domain",
        action="append",
        default=[],
        help="Domain allowed inside prompt content; repeat as needed",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.stdin:
        text = sys.stdin.read()
    elif args.file:
        text = args.file.read_text(encoding="utf-8")
    else:
        text = args.text
    result = scan(text, {domain.lower().rstrip(".") for domain in args.allow_domain})
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return {"safe": 0, "suspicious": 2, "blocked": 3}[result["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
