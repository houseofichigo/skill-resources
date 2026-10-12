#!/usr/bin/env python3
"""House of Ichigo brand checker — v3.3

    python scripts/brand_check.py output.html [more files...]
    python scripts/brand_check.py out.html --allow "#8A929C"

Checks any text output (HTML, CSS, SVG, JSX, JSON) against BRAND.md.
Exits 1 if a violation is found. Errors are hard failures; warnings are
judgement calls worth a look.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
T = json.load(open(os.path.join(HERE, "..", "references", "tokens.json"), encoding="utf-8"))

def hexes(d, out=None):
    out = set() if out is None else out
    if isinstance(d, dict):
        for v in d.values(): hexes(v, out)
    elif isinstance(d, list):
        for v in d: hexes(v, out)
    elif isinstance(d, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", d):
        out.add(d.upper())
    return out

RETIRED = {h.upper() for h in hexes(T["color"]["retired"])}
PALETTE = (hexes(T["color"]) - RETIRED) | {"#FFFFFF", "#000000"}
FONTS_OK = {"manrope", "inter tight", "jetbrains mono", "serif",
            "sans-serif", "monospace", "system-ui", "-apple-system", "courier new",
            "arial", "helvetica", "inherit", "currentcolor",
            # the Arabic face (Section 09) and the generic keywords slides fall back to
            "ibm plex sans arabic", "ui-monospace", "ui-sans-serif"}
BANNED = [w.lower() for w in T["voice"]["banned"]]

def rgb(h): return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
def grey(h):
    r, g, b = rgb(h); return max(r, g, b) - min(r, g, b) <= 12
def tint_of(h, tol=9):
    r, g, b = rgb(h)
    for base in PALETTE:
        br, bg, bb = rgb(base)
        if (br, bg, bb) in ((255, 255, 255), (0, 0, 0)): continue
        for pct in range(4, 101, 4):
            f = pct / 100
            t = (round(br + (255-br)*(1-f)), round(bg + (255-bg)*(1-f)), round(bb + (255-bb)*(1-f)))
            if all(abs(x-y) <= tol for x, y in zip((r, g, b), t)): return base
    return None

# Rule files document the prohibitions, so they trip every rule they state.
SELF = {"brand.md", "tokens.json", "brand_check.py", "patterns.html",
        "tokens.css", "skill.md"}
SELF_PREFIX = ("brand-book-",)

# 5b slides (3.3). Static half only: this reads source. Whether a title runs
# into the mark, a figure is clipped, or the contrast holds depends on layout,
# and only `node scripts/slide_gate.js` measures a rendered slide.
def slide_rules(txt, err, warn):
    if 'class="sl ' not in txt and "class='sl " not in txt:
        return
    for m in re.finditer(r"font-size\s*:\s*(\d+(?:\.\d+)?)px", txt):
        if float(m.group(1)) < 16:
            err.append(f"SLIDE TYPE {m.group(1)}px — the footer floor is 16px "
                       "(body 24, secondary 20, labels 18); 3.2's 12px eyebrow was unreadable from row three")
            break
    parts = re.split(r'(?=<div[^>]*class="sl )', txt)[1:]
    for i, s in enumerate(parts, 1):
        kind = re.search(r'data-kind="([^"]+)"', s.split(">", 1)[0])
        k = kind.group(1) if kind else f"slide {i}"
        s = re.split(r'(?=<div[^>]*class="sl )', s[10:])[0] if False else s
        discs = s.count("data-disc")
        if discs > 1:
            err.append(f"{k}: {discs} marks on one slide — one per slide")
        if discs and kind and k not in ("cover", "divider", "close"):
            err.append(f"{k}: carries the mark — cover, divider and close only")
    accents = [i for i, s in enumerate(parts) if 'class="acc"' in s]
    for a, b in zip(accents, accents[1:]):
        if b - a < 5:
            warn.append(f"accent phrases on slides {a + 1} and {b + 1} — one per five slides")
    eyebrows = sum(1 for s in parts if re.search(r'class="[^"]*\beyebrow\b', s))
    if len(parts) >= 4 and eyebrows >= len(parts) * 0.6:
        warn.append("an eyebrow above most slide titles — retired in 3.3 as the default generated-deck tell")
    if re.search(r"--(?:learn|build|lead|cobalt)-8\b", txt):
        warn.append("an 8% tinted panel on a slide — retired for statistics in 3.3; a statistic is a numeral at scale")
    warn.append("static check only: run `node scripts/slide_gate.js` to measure clipping, the type floor, "
                "text against the mark, and contrast on the rendered slide")

def check(path, allow):
    base = os.path.basename(path).lower()
    if base in SELF or base.startswith(SELF_PREFIX):
        print(f"\n=== {os.path.basename(path)}\n  skipped — this is a rule file, not output")
        return False
    raw = open(path, encoding="utf-8", errors="ignore").read()
    txt = re.sub(r"data:image/[^;]+;base64,[A-Za-z0-9+/=]+", "", raw)
    err, warn = [], []

    # 1 colour
    found = {"#" + m.group(1).upper() for m in re.finditer(r"#([0-9A-Fa-f]{6})\b", txt)}
    for h in sorted(found & RETIRED):
        err.append(f"RETIRED COLOUR {h} — removed in 3.0, identifies 1.0 material")
    for h in sorted(found - PALETTE - RETIRED - set(allow)):
        if grey(h) or tint_of(h): continue
        err.append(f"OFF-PALETTE {h}")

    # 2 type
    # [^;}]+ not [^;}"']+ — stopping at the first quote made every quoted
    # family name invisible to this check, which is most of them.
    for m in re.finditer(r"font-family\s*:\s*([^;}]+)", txt, re.I):
        for f in m.group(1).split(","):
            f = f.strip().strip("'\"").lower()
            if f and not f.startswith("var(") and f not in FONTS_OK:
                err.append(f"UNAPPROVED FONT '{f}'")
    if re.search(r"['\"]Fraunces['\"]|font-variation-settings\s*:\s*['\"]opsz", txt):
        err.append("Fraunces or the opsz axis — retired in 3.2, identifies 3.1 material")
    if "fonts.googleapis.com" in txt:
        err.append("fonts.googleapis.com link — fonts are self-hosted; a linked page "
                   "renders in a fallback face without failing loudly")
    # Manrope has no italic, so any italic on the display face is synthesised
    for m in re.finditer(r"\{[^}]*\}", txt):
        blk = m.group(0)
        if "font-style" in blk and "italic" in blk and (
                "var(--d)" in blk or "manrope" in blk.lower()):
            err.append("SYNTHESISED ITALIC on the display face — Manrope has no italic")
            break
    if re.search(r"\.acc\b[^{]*\{[^}]*font-style\s*:\s*italic", txt):
        err.append("accent word set in italic — it is weight 800 in Cobalt")
    if re.search(r"@font-face|var\(--d\)", txt) and "font-synthesis" not in txt:
        warn.append("no font-synthesis:none — the browser may fake Manrope's missing italic")
    for m in re.finditer(r"letter-spacing\s*:\s*-([\d.]+)em", txt):
        if float(m.group(1)) > 0.05:
            warn.append(f"tracking -{m.group(1)}em — tighter than the -.035em display bucket")

    # 2b print viewport — a bare breakpoint fires during PDF export
    for m in re.finditer(r"@media\s*\(\s*(?:max|min)-width", txt):
        err.append("bare @media (max-width:…) — must be `@media screen and (…)`, "
                   "or it fires during PDF export and collapses every column")
        break

    # 3 logo guard
    if re.search(r"logo|mark", txt, re.I) and "<img" in txt:
        if "align-self" not in txt:
            err.append("logo images present but no align-self guard — the mark will stretch")
        if "aspect-ratio" not in txt:
            warn.append("no aspect-ratio on logo classes — second line of defence missing")

    # 4 prohibited CSS
    if re.search(r"linear-gradient|radial-gradient", txt): err.append("GRADIENT — prohibited")
    if re.search(r"box-shadow\s*:\s*(?!none)", txt):       err.append("BOX-SHADOW — prohibited")
    for m in re.finditer(r"border-radius\s*:\s*([\d.]+)px", txt):
        if float(m.group(1)) > 2:
            err.append(f"BORDER-RADIUS {m.group(1)}px — max 2px, buttons only"); break

    # 5 prohibited pairings
    if re.search(r"background\s*:\s*#FFC411[^;}\"']*;[^}\"']*color\s*:\s*#(FFF|FFFFFF)", txt, re.I):
        err.append("white on Warning — 1.60:1")
    if re.search(r"background\s*:\s*#0A0E27[^}\"']*color\s*:\s*#5A6478", txt, re.I):
        err.append("Slate on Ink — 2.59:1, use white at 55-60%")

    slide_rules(txt, err, warn)

    # 6 voice
    body = re.sub(r"<[^>]+>", " ", txt).lower()
    for w in BANNED:
        if re.search(rf"\b{re.escape(w)}\b", body):
            warn.append(f"banned word '{w}'")

    print(f"\n=== {os.path.basename(path)}")
    for e in dict.fromkeys(err):  print(f"  ERROR    {e}")
    for w in dict.fromkeys(warn): print(f"  warning  {w}")
    if not err and not warn: print("  clean")
    elif not err:            print("  no errors")
    return bool(err)

if __name__ == "__main__":
    args = sys.argv[1:]
    allow = []
    if "--allow" in args:
        i = args.index("--allow"); allow = [a.strip().upper() for a in args[i+1].split(",")]
        del args[i:i+2]
    if not args:
        print(__doc__); sys.exit(2)
    sys.exit(1 if any(check(p, allow) for p in args) else 0)
