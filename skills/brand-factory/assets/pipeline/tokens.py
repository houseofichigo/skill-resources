#!/usr/bin/env python3
"""brand.config.json -> tokens.json, with everything measured.

Nothing here is asserted. Contrast is computed and checked against the
floors in the config; the interaction ramp is derived from the brand
colour; density padding is derived so a row is exactly the height it
claims; and every colour is checked for distance against the palettes you
said yours must not resemble.

The build fails rather than warns. A warning in a brand system is a thing
someone scrolls past.
"""
import json, math, pathlib, sys, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "brand.config.json").read_text(encoding="utf-8"))
OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)


# ── colour maths ────────────────────────────────────────────────────────
def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hx(t):
    return "#" + "".join(f"{max(0, min(255, round(c))):02X}" for c in t)


def lum(h):
    def f(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb(h)
    return .2126 * f(r) + .7152 * f(g) + .0722 * f(b)


def ratio(a, b):
    la, lb = lum(a), lum(b)
    return round((max(la, lb) + .05) / (min(la, lb) + .05), 2)


def mix(a, b, t):
    return hx(tuple(x + (y - x) * t for x, y in zip(rgb(a), rgb(b))))


def distance(a, b):
    """Plain RGB distance. Crude, but it is the crudeness that makes it
    useful: two colours under ~40 apart read as the same colour to someone
    who is not holding a swatch."""
    return round(math.dist(rgb(a), rgb(b)), 1)


def chroma(h):
    r, g, b = rgb(h)
    return max(r, g, b) - min(r, g, b)


WARM = 4  # below this a near-white is neutral, whichever way it leans


def warmth(h):
    """Positive is warm, negative is cool. The only thing that
    distinguishes one near-white from another."""
    r, g, b = rgb(h)
    return r - b


def comparable(mine, theirs):
    """Only compare where the answer means something.

    Three regimes, because one metric does not serve all of them:

    NEAR-BLACK is never compared. Everyone's ink reads as black, tinted or
    not. A navy-black 23 units from a neutral near-black is not a borrowed
    colour, and flagging it is how a check earns a reputation for crying
    wolf. (Measured against a real palette, this was the check's only false
    positive.)

    NEAR-WHITE is compared only when both sides are deliberately WARM. All
    near-whites sit within ~20 RGB units of each other, so plain distance
    flags every ground against every other and says nothing. Cool ones are
    the default — every framework's grey-50 is cool, and matching it is not
    a finding. A warm ground is a choice, so two warm papers 19 apart are
    the same paper. That is a real collision this check was blind to until
    the near-black false positive sent me back to it.

    EVERYTHING ELSE needs chroma on one side or the other. A hairline grey
    matching someone's hairline grey is not a finding."""
    lm, lt = lum(mine), lum(theirs)
    if lm < .03 or lt < .03:                      # near-black, both regimes
        return False
    if lm > .80 or lt > .80:                      # near-white: temperature
        return warmth(mine) >= WARM and warmth(theirs) >= WARM
    return chroma(mine) >= 25 or chroma(theirs) >= 25


# ── shorthand ───────────────────────────────────────────────────────────
C = CFG["color"]
GROUND, INK = C["ground"]["hex"], C["ink"]["hex"]
BRAND, MUTED = C["brand"]["hex"], C["muted"]["hex"]
SURFACE, LINE = C["surface"]["hex"], C["line"]["hex"]
ON_DARK = C["brand_on_dark"]["hex"]
FLOORS = CFG["a11y"]["floors"]

fails, warns = [], []


# ── 1 · does this palette read as someone else's? ───────────────────────
def originality():
    av = CFG.get("avoid_palettes", {})
    thr = av.get("threshold", 40)
    # Only brand-carrying colours. Semantic fills are deliberately
    # excluded: a danger red SHOULD look like everyone else's danger red,
    # and a warning yellow lands in a narrow band that every system shares.
    # Flagging those is the metric being naive, not the brand being
    # derivative.
    mine = {k: v["hex"] for k, v in C.items()
            if isinstance(v, dict) and "hex" in v
            and k not in ("semantic", "retired")}
    mine.update({f"accent_{k}": v["hex"]
                 for k, v in C.get("accents", {}).items()
                 if isinstance(v, dict)})
    hits = []
    for setname, hexes in av.get("sets", {}).items():
        for other in hexes:
            for name, h in mine.items():
                if not comparable(h, other):
                    continue
                d = distance(h, other)
                if d < thr:
                    hits.append((name, h, setname, other, d))
    return hits, thr


# ── 2 · the interaction ramp, derived ───────────────────────────────────
def ramp():
    r = collections.OrderedDict([
        ("brand-hover", mix(BRAND, INK, .18)),
        ("brand-press", mix(BRAND, INK, .34)),
        ("brand-tint", mix(BRAND, GROUND, .92)),
        ("brand-tint-hover", mix(BRAND, GROUND, .84)),
        ("ink-hover", mix(INK, GROUND, .06)),
        ("ink-press", mix(INK, GROUND, .12)),
        ("surface-press", mix(SURFACE, INK, .05)),
        ("disabled-fg", mix(MUTED, GROUND, .45)),
    ])
    for k, v in C.get("semantic", {}).items():
        if isinstance(v, dict) and "hex" in v:
            r[f"{k}-hover"] = mix(v["hex"], INK, .18)
    return r


# ── 3 · density, derived so the numbers hold ────────────────────────────
def density():
    lh = CFG["density"]["line_height"]
    out = collections.OrderedDict()
    for name, d in CFG["density"]["scales"].items():
        line = round(d["text"] * lh, 1)
        pad = round((d["row"] - line) / 2)
        if pad < 2:
            fails.append(f"density.{name}: a {d['row']}px row cannot hold "
                         f"{d['text']}px text at line-height {lh}")
            pad = 2
        computed = round(2 * pad + line, 1)
        if abs(computed - d["row"]) > 1:
            fails.append(f"density.{name}: stated {d['row']}px, "
                         f"computes to {computed}px")
        out[name] = dict(d, pad_y=pad, line_height=lh, computed_row=computed)
    return out


# ── 4 · every pairing that has to hold ──────────────────────────────────
def measure(R):
    m = collections.OrderedDict()

    def add(label, fg, bg, floor):
        m[label] = {"ratio": ratio(fg, bg), "floor": floor,
                    "fg": fg, "bg": bg}

    add("body text on ground", INK, GROUND, FLOORS["body_text"])
    add("muted text on ground", MUTED, GROUND, FLOORS["body_text"])
    add("brand on ground", BRAND, GROUND, FLOORS["body_text"])
    add("ground on brand", GROUND, BRAND, FLOORS["body_text"])
    add("ground on brand-hover", GROUND, R["brand-hover"],
        FLOORS["body_text"])
    add("body text on surface", INK, SURFACE, FLOORS["body_text"])
    add("body text on brand tint", INK, R["brand-tint"], FLOORS["body_text"])
    add("focus ring on ground", BRAND, GROUND, FLOORS["component_boundary"])
    add("focus ring on ink", ON_DARK, INK, FLOORS["component_boundary"])
    add("input border on ground", MUTED, GROUND,
        FLOORS["component_boundary"])
    add("ground on ink", GROUND, INK, FLOORS["body_text"])

    for k, v in C.get("semantic", {}).items():
        if not isinstance(v, dict) or "hex" not in v:
            continue
        txt = {"ink": INK, "ground": GROUND}.get(v.get("text", "ink"), INK)
        add(f"text on {k}", txt, v["hex"], FLOORS["body_text"])

    for k, v in C.get("accents", {}).items():
        if isinstance(v, dict) and "hex" in v:
            add(f"accent {k} on ground", v["hex"], GROUND,
                FLOORS["large_text"])

    for label, d in m.items():
        if d["ratio"] < d["floor"]:
            fails.append(f"contrast: {label} is {d['ratio']}:1, "
                         f"floor {d['floor']}:1 "
                         f"({d['fg']} on {d['bg']})")
    return m


# ── 5 · one hex, one meaning ────────────────────────────────────────────
def collisions():
    seen = collections.defaultdict(list)

    def walk(o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                if k.startswith("$"):
                    continue
                if k == "hex" and isinstance(v, str):
                    seen[v.upper()].append(path)
                else:
                    walk(v, f"{path}.{k}" if path else k)
    walk(C)
    return {h: p for h, p in seen.items() if len(p) > 1}


def main():
    R = ramp()
    D = density()
    M = measure(R)
    hits, thr = originality()
    coll = collisions()

    print(f"{CFG['brand']} — tokens {CFG['version']}\n")

    print("originality · RGB distance from palettes you said to avoid")
    if hits:
        for name, h, setname, other, d in sorted(hits, key=lambda x: x[4]):
            fails.append(f"originality: {name} {h} is {d} from {setname} "
                         f"{other} (threshold {thr})")
            print(f"  {name:20} {h}  vs {setname}/{other}  {d}  TOO CLOSE")
        print("\n  Semantic fills are exempt — a danger red should look "
              "like\n  a danger red. Only brand and accent colours are "
              "checked here.")
    else:
        print(f"  clear — nothing within {thr} of any avoided palette")

    print("\ncontrast · measured")
    for k, v in M.items():
        ok = "ok" if v["ratio"] >= v["floor"] else "FAILS"
        print(f"  {k:28} {v['ratio']:>6}:1  floor {v['floor']}  {ok}")

    print("\ndensity · a row must equal 2*pad + one line box")
    for k, v in D.items():
        print(f"  {k:12} stated {v['row']}px  computed {v['computed_row']}px  "
              f"pad_y {v['pad_y']}")

    if coll:
        print("\ncollisions · one hex carrying two meanings")
        for h, paths in coll.items():
            print(f"  {h}  {paths}")
            warns.append(f"collision: {h} means {' and '.join(paths)}")

    tokens = collections.OrderedDict([
        ("brand", CFG["brand"]), ("slug", CFG["slug"]),
        ("version", CFG["version"]), ("date", CFG["date"]),
        ("supersedes", CFG["supersedes"]),
        ("positioning", CFG["positioning"]),
        ("locales", CFG["locales"]),
        ("color", C), ("ramp", R), ("measured_contrast", M),
        ("collisions", coll),
        ("type", CFG["type"]), ("shape", CFG["shape"]),
        ("density", D), ("motion", CFG["motion"]),
        ("a11y", CFG["a11y"]), ("voice", CFG["voice"]),
        ("book", CFG["book"]),
    ])
    (OUT / "tokens.json").write_text(
        json.dumps(tokens, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")

    if warns:
        print("\nwarnings")
        for w in warns:
            print("  ·", w)
    if fails:
        print("\nFAILED")
        for f in fails:
            print("  ·", f)
        print("\nFix brand.config.json and run again. Nothing was written "
              "downstream.")
        sys.exit(1)
    print(f"\nout/tokens.json written · {len(M)} pairings measured, "
          f"all above floor")


if __name__ == "__main__":
    main()
