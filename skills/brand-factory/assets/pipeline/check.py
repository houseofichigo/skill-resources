#!/usr/bin/env python3
"""Brand checker. Scans any text output against out/tokens.json.

    python3 build/check.py page.html [more...]
    python3 build/check.py page.html --allow "#8A929C"

Exits non-zero on a violation. Errors are hard failures; warnings are
judgement calls worth a look. It catches mechanical failures only — it
cannot tell you whether the margin is right.
"""
import json, os, re, sys, math

HERE = os.path.dirname(os.path.abspath(__file__))
# This file runs from two places: build/ in the repo, and scripts/ inside
# the packaged skill. Look in both rather than assuming one.
CANDIDATES = [os.path.join(HERE, "..", "out", "tokens.json"),
              os.path.join(HERE, "..", "references", "tokens.json"),
              os.path.join(HERE, "..", "tokens.json")]
TOKENS = next((p for p in CANDIDATES if os.path.exists(p)), None)
if TOKENS is None:
    sys.exit("cannot find tokens.json — looked in:\n  "
             + "\n  ".join(os.path.normpath(p) for p in CANDIDATES))
T = json.load(open(TOKENS, encoding="utf-8"))
C = T["color"]


def hexes(d, out=None):
    out = set() if out is None else out
    if isinstance(d, dict):
        for k, v in d.items():
            if not str(k).startswith("$"):
                hexes(v, out)
    elif isinstance(d, list):
        for v in d:
            hexes(v, out)
    elif isinstance(d, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", d):
        out.add(d.upper())
    return out


RETIRED = {h.upper() for h in hexes(C.get("retired", {}))}
PALETTE = (hexes(C) | hexes(T["ramp"])) - RETIRED | {"#FFFFFF", "#000000"}
FONTS_OK = {T["type"][k]["family"].lower()
            for k in ("display", "text", "mono")}
FONTS_OK |= {"system-ui", "-apple-system", "sans-serif", "serif",
             "monospace", "ui-monospace", "inherit", "currentcolor",
             "arial", "helvetica"}
if "ar" in T.get("locales", []):
    FONTS_OK.add(T["type"]["arabic"]["family"].lower())
BANNED = [w.lower() for w in T["voice"]["banned"] if not w.startswith("$")]
MAX_RADIUS = T["shape"]["floating"]


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def grey(h):
    r, g, b = rgb(h)
    return max(r, g, b) - min(r, g, b) <= 12


def tint_of(h, tol=9):
    r, g, b = rgb(h)
    for base in PALETTE:
        br, bg, bb = rgb(base)
        if (br, bg, bb) in ((255, 255, 255), (0, 0, 0)):
            continue
        for pct in range(4, 101, 4):
            f = pct / 100
            t = (round(br + (255 - br) * (1 - f)),
                 round(bg + (255 - bg) * (1 - f)),
                 round(bb + (255 - bb) * (1 - f)))
            if all(abs(x - y) <= tol for x, y in zip((r, g, b), t)):
                return base
    return None


# A rule file documents the prohibitions, so it trips every rule it
# states. Skip them rather than teaching people to ignore output.
SELF = {"tokens.css", "tokens.json", "brand.md", "check.py",
        "patterns.html", "skill.md"}
SELF_PREFIX = ("brand-book-",)


def check(path, allow):
    base = os.path.basename(path).lower()
    if base in SELF or base.startswith(SELF_PREFIX):
        print(f"\n=== {os.path.basename(path)}\n"
              f"  skipped — this is a rule file, not output")
        return False
    raw = open(path, encoding="utf-8", errors="ignore").read()
    txt = re.sub(r"data:[^;]+;base64,[A-Za-z0-9+/=]+", "", raw)
    err, warn = [], []

    found = {"#" + m.group(1).upper()
             for m in re.finditer(r"#([0-9A-Fa-f]{6})\b", txt)}
    for h in sorted(found & RETIRED):
        err.append(f"RETIRED COLOUR {h} — its presence identifies old material")
    for h in sorted(found - PALETTE - RETIRED - set(allow)):
        if grey(h) or tint_of(h):
            continue
        err.append(f"OFF-PALETTE {h}")

    # [^;}]+ not [^;}"']+ — stopping at the first quote makes every
    # quoted family name invisible, which is most of them.
    for m in re.finditer(r"font-family\s*:\s*([^;}]+)", txt, re.I):
        for f in m.group(1).split(","):
            f = f.strip().strip("'\"").lower()
            if f and not f.startswith("var(") and f not in FONTS_OK:
                err.append(f"UNAPPROVED FONT '{f}'")

    if "fonts.googleapis.com" in txt:
        err.append("fonts.googleapis.com link — fonts are self-hosted. A "
                   "page that links a font service renders in a fallback "
                   "face without failing loudly.")

    if not T["type"]["display"].get("has_italic", True):
        # Rule blocks AND inline style attributes. An agent writing HTML
        # reaches for style="..." far more often than a rule block, and
        # scanning only {...} let a fake italic through a negative test.
        blocks = [m.group(0) for m in re.finditer(r"\{[^}]*\}", txt)]
        blocks += [m.group(1) for m in
                   re.finditer(r'style\s*=\s*"([^"]*)"', txt, re.I)]
        for b in blocks:
            if "font-style" in b and "italic" in b and (
                    "var(--display)" in b
                    or T["type"]["display"]["family"].lower() in b.lower()):
                err.append("SYNTHESISED ITALIC on the display face — it has "
                           "no italic")
                break
    # tokens.css sets font-synthesis-weight/style:none on body, so a file
    # that LINKS it already carries the guard. Warning anyway trains people
    # to ignore the checker, which is worse than the thing it warns about.
    inherits_guard = re.search(r'<link[^>]+tokens\.css', txt, re.I)
    if re.search(r"@font-face|var\(--display\)", txt) \
            and "font-synthesis" not in txt and not inherits_guard:
        warn.append("no font-synthesis:none — the browser may fake a "
                    "missing weight or italic")

    for m in re.finditer(r"@media\s*\(\s*(?:max|min)-width", txt):
        err.append("bare @media (max-width:…) — must be `@media screen and "
                   "(…)`, or it fires during PDF export and collapses every "
                   "column")
        break

    if re.search(r"logo|mark", txt, re.I) and "<img" in txt:
        if "align-self" not in txt:
            err.append("logo images present with no align-self guard — the "
                       "mark will stretch")

    if re.search(r"linear-gradient|radial-gradient", txt):
        err.append("GRADIENT — prohibited")
    if re.search(r"box-shadow\s*:\s*(?!none)", txt):
        err.append("BOX-SHADOW — prohibited; elevation is border + scrim")
    for m in re.finditer(r"border-radius\s*:\s*([\d.]+)px", txt):
        if float(m.group(1)) > MAX_RADIUS:
            err.append(f"BORDER-RADIUS {m.group(1)}px — max {MAX_RADIUS}px")
            break

    low = txt.lower()
    for w in BANNED:
        if re.search(rf"\b{re.escape(w)}\b", low):
            warn.append(f"banned word '{w}'")

    name = os.path.basename(path)
    print(f"\n=== {name}")
    if not err and not warn:
        print("  clean")
    for e in dict.fromkeys(err):
        print(f"  ERROR    {e}")
    for w in dict.fromkeys(warn):
        print(f"  warning  {w}")
    return bool(err)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    allow = []
    if "--allow" in sys.argv:
        allow = sys.argv[sys.argv.index("--allow") + 1].split(",")
    if not args:
        sys.exit(__doc__)
    bad = any(check(p, [a.strip().upper() for a in allow]) for p in args)
    sys.exit(1 if bad else 0)
