#!/usr/bin/env python3
"""Microcopy → out/copy/microcopy.<locale>.json, one file per locale.

(Named microcopy.py, not copy.py: every build/ script runs with build/ first on
sys.path, so a copy.py there would shadow the standard library module that
jsonschema and attrs import.)

    python3 build/microcopy.py

Writes config `copy.<locale>` for every locale in locales.list, nested keys
kept, `$`-prefixed keys (notes) dropped. A locale with no strings is written
as {"$gap": "<reason>"} rather than omitted, so a consumer finds the hole
instead of a missing file.

Gate (exit 1):
  · every key of the default locale exists in every other locale that has
    strings (missing keys reported per locale, with key paths);
  · no voice.banned.list word (case-insensitive, whole word) in any string;
  · French (any locale "fr*"): no ASCII or curly double quotes where « » are
    required; « is followed, and » : ; ? ! are preceded, by U+202F or U+00A0
    (voice.locale_format.<locale>.quotes naming « … » switches this on);
  · no "!" anywhere when voice.never.list forbids exclamation marks.
Placeholder mismatches between locales ({email}) are warnings.
Standard library only.
"""
import json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from config import load, ConfigError  # noqa: E402

ROOT = HERE.parent
OUT = ROOT / "out" / "copy"
NBSP = (" ", " ")


def clean(node):
    if isinstance(node, dict):
        return {k: clean(v) for k, v in node.items() if not k.startswith("$")}
    if isinstance(node, list):
        return [clean(v) for v in node]
    return node


def flat(node, path=""):
    """{key path: string}; list items are path[i]."""
    out = {}
    if isinstance(node, dict):
        for k, v in node.items():
            out.update(flat(v, f"{path}.{k}" if path else k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out.update(flat(v, f"{path}[{i}]"))
    elif isinstance(node, str):
        out[path] = node
    return out


def strip_placeholders(s):
    return re.sub(r"\{[^{}]*\}", "", s)


def fr_violations(s):
    """Typographic problems in one French string, as short messages."""
    bad = []
    t = strip_placeholders(s)
    if '"' in t:
        bad.append('ASCII " (use « »)')
    if re.search(r"[“”]", t):
        bad.append("curly quotes (use « »)")
    for m in re.finditer("«", t):
        nxt = t[m.end():m.end() + 1]
        if nxt not in NBSP:
            bad.append("« not followed by U+202F/U+00A0")
    for m in re.finditer("»", t):
        if t[max(0, m.start() - 1):m.start()] not in NBSP:
            bad.append("» not preceded by U+202F/U+00A0")
    for m in re.finditer(r"[:;?!]", t):
        i, ch = m.start(), m.group(0)
        prev, nxt = t[i - 1:i], t[i + 1:i + 2]
        if ch == ":" and (nxt == "/" or (prev.isdigit() and nxt.isdigit())):
            continue                    # a URL, a time
        if ch in "?!:;" and nxt and not nxt.isspace() and nxt not in "»  .,)…\"'":
            continue                    # inside a token (a query string)
        if prev not in NBSP:
            bad.append(f"'{ch}' not preceded by U+202F/U+00A0")
    return bad


def check(cfg, copy):
    """Return (errors, warnings). copy is {locale: cleaned dict or None}."""
    errs, warns = [], []
    loc = cfg["locales"]
    default = loc["default"]
    voice = cfg.get("voice") or {}
    flats = {l: flat(copy[l]) for l in loc["list"] if copy.get(l)}
    base = flats.get(default, {})

    for l, f in flats.items():
        if l == default:
            continue
        miss = sorted(set(base) - set(f))
        if miss:
            errs.append(f"{l}: {len(miss)} key(s) present in {default} and missing: "
                        + ", ".join(miss))
        for k in sorted(set(base) & set(f)):
            a = sorted(re.findall(r"\{[^{}]*\}", base[k]))
            b = sorted(re.findall(r"\{[^{}]*\}", f[k]))
            if a != b:
                warns.append(f"{l}.{k}: placeholders {b} differ from {default} {a}")

    banned = [w for w in ((voice.get("banned") or {}).get("list") or []) if isinstance(w, str)]
    if banned:
        rx = re.compile(r"(?<!\w)(" + "|".join(re.escape(w) for w in banned) + r")(?!\w)", re.I)
        for l, f in flats.items():
            for k, s in f.items():
                for m in rx.finditer(s):
                    errs.append(f"{l}.{k}: banned word '{m.group(0)}'")

    never = " ".join(str(x) for x in ((voice.get("never") or {}).get("list") or [])).lower()
    if "exclamation" in never:
        for l, f in flats.items():
            for k, s in f.items():
                if "!" in s:
                    errs.append(f"{l}.{k}: exclamation mark (voice.never)")

    fmt = voice.get("locale_format") or {}
    for l, f in flats.items():
        if not l.lower().startswith("fr"):
            continue
        q = num((fmt.get(l) or fmt.get("fr") or {}).get("quotes")) or ""
        if "«" not in str(q):
            continue
        for k, s in f.items():
            for msg in sorted(set(fr_violations(s))):
                errs.append(f"{l}.{k}: {msg}")
    return errs, warns


def num(v):
    return v.get("value") if isinstance(v, dict) else v


def main():
    try:
        cfg, _, a = load()
    except ConfigError as e:
        sys.exit(f"config gate failed:\n  {e}")
    raw = cfg.get("copy") or {}
    locales = cfg["locales"]["list"]
    copy = {}
    for l in locales:
        node = raw.get(l)
        node = clean(node) if isinstance(node, dict) else None
        copy[l] = node or None
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("microcopy.*.json"):
        old.unlink()
    counts = {}
    for l in locales:
        if copy[l]:
            body, counts[l] = copy[l], len(flat(copy[l]))
        else:
            reason = (raw.get(f"$gap_{l}") or (raw.get(l) or {}).get("$gap") if isinstance(raw.get(l), dict) else None) \
                or f"config copy.{l} has no strings"
            body, counts[l] = {"$gap": reason}, 0
        (OUT / f"microcopy.{l}.json").write_text(
            json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    errs, warns = check(cfg, copy)
    for w in warns:
        print("  warning · " + w)
    summary = " · ".join(f"{l} {n}" + (" (gap)" if not n else "") for l, n in counts.items())
    if errs:
        print(f"FAILED · copy ({summary}):\n  " + "\n  ".join(errs))
        sys.exit(1)
    print(f"out/copy/ written · strings per locale: {summary} · keys complete, no banned word, French typography clean")


if __name__ == "__main__":
    main()
