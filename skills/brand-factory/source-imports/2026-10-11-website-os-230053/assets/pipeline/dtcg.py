#!/usr/bin/env python3
"""brand.config.json → out/tokens/design-tokens.json, W3C Design Tokens
Format 2025.10.

    python3 build/dtcg.py                       # the project's config
    python3 build/dtcg.py path/to/brand.config.json

Reads the token tree (tree.py); never the JSON directly.

  · colours are {colorSpace: "srgb", components, alpha?, hex}
  · a config value that is itself a reference stays an alias: "{color.fg}"
  · every token carries $extensions["brand-factory"] = {provenance, pointer};
    the build fails if one does not
  · color.ramps: an OKLCH 50–900 ramp per listed colour, computed here,
    under $extensions["brand-factory"].ramp on the base colour — never a
    token, so nothing can reference a step the brand does not have
  · retired colours are NOT tokens: they sit under the root
    $extensions["brand-factory"].retired as a denylist (hex, why, pointer),
    so no token pipeline can emit one as a custom property
  · letterSpacing in em is converted to px at the role's size (DTCG
    dimensions are px or rem only); the em value rides in $extensions

Standard library only. Python 3.9+. Byte-for-byte idempotent.
"""
import collections, json, math, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
from tree import build_tree, parse_color, hex_of, REF  # noqa: E402

EXT = "brand-factory"
# The ramp's lightness ends. Website-os defaults, stated in the output.
RAMP_L_LIGHT, RAMP_L_DARK = 0.97, 0.25


# ── OKLCH, pure Python ──────────────────────────────────────────────────
def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _gam(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def srgb_to_oklab(r, g, b):
    """r, g, b in 0–1 (gamma-encoded sRGB) → (L, a, b)."""
    r, g, b = _lin(r), _lin(g), _lin(b)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (math.copysign(abs(x) ** (1 / 3), x) for x in (l, m, s))
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def oklab_to_srgb(L, a, b):
    """(L, a, b) → linear-to-gamma sRGB in 0–1, unclipped."""
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    return tuple(_gam(x) if x >= 0 else -_gam(-x) for x in (r, g, bb))


def hex_to_oklch(h):
    r, g, b, _ = parse_color(h)
    L, A, B = srgb_to_oklab(r / 255, g / 255, b / 255)
    C = math.hypot(A, B)
    H = math.degrees(math.atan2(B, A)) % 360
    return L, C, H


def oklch_to_rgb(L, C, H):
    a, b = C * math.cos(math.radians(H)), C * math.sin(math.radians(H))
    return oklab_to_srgb(L, a, b)


def _in_gamut(rgb, eps=1e-6):
    return all(-eps <= x <= 1 + eps for x in rgb)


def oklch_to_hex(L, C, H):
    """Gamut-clip by reducing chroma (binary search), hue and lightness held."""
    rgb = oklch_to_rgb(L, C, H)
    if not _in_gamut(rgb):
        lo, hi = 0.0, C
        for _ in range(40):
            mid = (lo + hi) / 2
            if _in_gamut(oklch_to_rgb(L, mid, H)):
                lo = mid
            else:
                hi = mid
        C = lo
        rgb = oklch_to_rgb(L, C, H)
    return hex_of([max(0.0, min(1.0, x)) * 255 for x in rgb]), C


def ramp(hexv, steps):
    """steps (e.g. 50…900) → {step: {hex, oklch}}. The brand hex sits,
    unchanged, at the step whose lightness is nearest its own; the other
    steps interpolate lightness between it and the ends, at the brand's
    hue and chroma, gamut-clipped by chroma."""
    L0, C0, H0 = hex_to_oklch(hexv)
    n = len(steps)
    even = [RAMP_L_LIGHT + (RAMP_L_DARK - RAMP_L_LIGHT) * i / (n - 1) for i in range(n)]
    anchor = min(range(n), key=lambda i: (abs(even[i] - L0), i))
    out = {}
    for i, s in enumerate(steps):
        if i == anchor:
            L, hx, C = L0, hexv.upper(), C0
        else:
            if i < anchor:
                L = RAMP_L_LIGHT + (L0 - RAMP_L_LIGHT) * (i / anchor if anchor else 0)
            else:
                L = L0 + (RAMP_L_DARK - L0) * ((i - anchor) / (n - 1 - anchor))
            hx, C = oklch_to_hex(L, C0, H0)
        out[str(s)] = {"hex": hx, "oklch": [round(L, 4), round(C, 4), round(H0, 2)]}
    return out, steps[anchor]


# ── DTCG values ─────────────────────────────────────────────────────────
def color_value(v):
    if isinstance(v, str) and REF.match(v):
        return v
    r, g, b, a = parse_color(v)
    out = {"colorSpace": "srgb",
           "components": [round(r / 255, 6), round(g / 255, 6), round(b / 255, 6)]}
    if a is not None and a != 1:
        out["alpha"] = round(a, 6)
    out["hex"] = hex_of((r, g, b))
    return out


def em_to_px(v, size_px):
    """'-.035em' at 88px → {-3.08 px}. '0' → 0px. Already px → as is."""
    s = str(v).strip()
    if s.endswith("em") and not s.endswith("rem"):
        return {"value": round(float(s[:-2]) * size_px, 4), "unit": "px"}
    if s.endswith("px"):
        return {"value": float(s[:-2]), "unit": "px"}
    if s.endswith("rem"):
        return {"value": float(s[:-3]), "unit": "rem"}
    return {"value": float(s), "unit": "px"}


def ext(tok, **more):
    e = {"provenance": {k: tok["provenance"][k] for k in ("src", "conf")},
         "pointer": tok["json_pointer"]}
    e.update({k: v for k, v in more.items() if v not in (None, {}, [])})
    return {EXT: e}


def dtcg_token(name, tok):
    """One tree token → one DTCG token (or, for elevation, a group)."""
    typ, v = tok["type"], tok["value"]
    x = tok.get("extensions") or {}
    out = {}
    if typ == "color":
        out = {"$type": "color", "$value": color_value(v)}
        more = {k: x[k] for k in sorted(x)}
        if isinstance(v, str) and not REF.match(v) and v.strip().lower().startswith("rgb"):
            more["css"] = v
        out["$extensions"] = ext(tok, **more)
    elif typ in ("dimension", "duration"):
        out = {"$type": typ, "$value": v, "$extensions": ext(tok)}
    elif typ == "cubicBezier":
        out = {"$type": typ, "$value": v, "$extensions": ext(tok, **x)}
    elif typ == "fontFamily":
        out = {"$type": typ, "$value": v, "$extensions": ext(tok, **x)}
    elif typ == "typography":
        size = v["fontSize"]["value"]
        val = {k: v[k] for k in ("fontFamily", "fontSize", "fontWeight", "lineHeight") if k in v}
        bp = {}
        for b, d in sorted((x.get("breakpoints") or {}).items()):
            bp[b] = {"fontSize": d["fontSize"]}
            if "letterSpacing" in d:
                bp[b]["letterSpacing"] = em_to_px(d["letterSpacing"], d["fontSize"]["value"])
                bp[b]["letterSpacing_css"] = d["letterSpacing"]
        more = {"breakpoints": bp, "fallback": x.get("fallback"),
                "default_breakpoint": x.get("default_breakpoint"),
                "parts": x.get("parts"), "incomplete": x.get("incomplete")}
        for k in ("html", "case", "use"):
            if k in x:
                more[k] = x[k]
        if "letterSpacing" in v:
            val["letterSpacing"] = em_to_px(v["letterSpacing"], size)
            more["letterSpacing_css"] = v["letterSpacing"]
        out = {"$type": "typography", "$value": val, "$extensions": ext(tok, **more)}
    elif typ == "elevation":
        # No DTCG elevation type. A group: surface / scrim colours, border
        # width and colour as separate tokens (the config's borders carry
        # no style, which a DTCG border composite requires).
        g = {}
        parts = x.get("parts") or {}
        for slot in ("surface", "scrim"):
            if slot in v and v[slot] not in ("none", None):
                pt = dict(tok, value=v[slot], provenance=parts.get(slot) or tok["provenance"],
                          json_pointer=f"{tok['json_pointer']}/{slot}")
                g[slot] = {"$type": "color", "$value": color_value(v[slot]),
                           "$extensions": ext(pt)}
        b = v.get("border")
        bp = dict(tok, provenance=parts.get("border") or tok["provenance"],
                  json_pointer=f"{tok['json_pointer']}/border")
        if isinstance(b, dict):
            if b.get("style"):
                g["border"] = {"$type": "border", "$value": {
                    "color": color_value(b["color"]), "width": b["width"], "style": b["style"]},
                    "$extensions": ext(bp)}
            else:
                g["border-width"] = {"$type": "dimension", "$value": b["width"],
                                     "$extensions": ext(dict(bp, json_pointer=bp["json_pointer"] + "/width"))}
                g["border-color"] = {"$type": "color", "$value": color_value(b["color"]),
                                     "$extensions": ext(dict(bp, json_pointer=bp["json_pointer"] + "/color"))}
        group_more = {"name": x.get("name")}
        for slot in ("surface", "scrim", "border", "shadow"):
            if v.get(slot) == "none":
                group_more[slot] = "none"
        if tok.get("description"):
            g["$description"] = tok["description"]
        g["$extensions"] = ext(tok, **group_more)
        return g
    else:
        raise ValueError(f"{name}: no DTCG mapping for type '{typ}'")
    if tok.get("description"):
        out["$description"] = tok["description"]
    if tok.get("deprecated"):
        out["$deprecated"] = tok["deprecated"]
    return out


def build(cfg, analysis):
    tree = build_tree(cfg, analysis)
    doc = collections.OrderedDict()
    errors = []

    def put(path, node):
        cur = doc
        for i, k in enumerate(path[:-1]):
            nxt = cur.setdefault(k, {})
            if "$value" in nxt:
                errors.append(f"{'.'.join(path)}: '{'.'.join(path[:i + 1])}' is a token, cannot be a group")
                return
            cur = nxt
        if path[-1] in cur:
            errors.append(f"{'.'.join(path)}: name collision")
            return
        cur[path[-1]] = node

    # ramps on their base colours
    R = (cfg.get("color") or {}).get("ramps") or {}
    ramp_for = {}
    if R.get("for"):
        steps = R.get("steps") or [50, 100, 200, 300, 400, 500, 600, 700, 800, 900]
        roles = live_keys((cfg["color"].get("roles")))
        accents = live_keys(cfg["color"].get("accents"))
        for base in R["for"]:
            name = f"color.{base}" if base in roles else (f"color.pillar.{base}" if base in accents else None)
            tok = tree["tokens"].get(name) if name else None
            if not tok or not isinstance(tok["value"], str) or REF.match(tok["value"]):
                errors.append(f"color.ramps.for: '{base}' names no literal colour")
                continue
            r, anchor = ramp(tok["value"], steps)
            prov_src = analysis["provenance"].get("/color/ramps/method", {}).get("src", "WO")
            ramp_for[name] = {"method": R.get("method", "oklch"), "steps": r, "anchor_step": anchor,
                              "lightness_ends": [RAMP_L_LIGHT, RAMP_L_DARK],
                              "provenance": {"src": prov_src, "conf": "derived"},
                              "pointer": "/color/ramps"}
            if R.get("surface_use"):
                ramp_for[name]["surface_use"] = R["surface_use"]

    retired = []
    for name, tok in tree["tokens"].items():
        if name.startswith("color.retired."):
            v = tok["value"]
            retired.append({"name": name.split(".", 2)[2], "hex": v if isinstance(v, str) else None,
                            "why": tok.get("deprecated") or tok.get("description") or "retired",
                            "pointer": tok.get("json_pointer"),
                            "provenance": {k: (tok.get("provenance") or {}).get(k) for k in ("src", "conf")}})
            continue
        if not tok.get("provenance") or not tok["provenance"].get("src") or not tok["provenance"].get("conf"):
            errors.append(f"{name}: no provenance")
            continue
        node = dtcg_token(name, tok)
        if name in ramp_for:
            node["$extensions"][EXT]["ramp"] = ramp_for[name]
        put(name.split("."), node)

    root_ext = {"brand": cfg.get("brand"), "version": cfg.get("version"), "mode": cfg.get("mode"),
                "format": "DTCG 2025.10", "generator": "brand-factory build/dtcg.py",
                "gaps": tree["_gaps"]}
    if retired:
        root_ext["retired"] = {"$comment": "A denylist, not tokens: these colours must never be emitted. "
                                           "build/check.py fails any output that carries one.", "colors": retired}
    doc["$description"] = f"{cfg.get('brand')} {cfg.get('version')} — design tokens"
    doc["$extensions"] = {EXT: root_ext}
    return doc, tree, errors, ramp_for


def live_keys(d):
    return [k for k in (d or {}) if not str(k).startswith("$")]


def walk_tokens(doc, path=()):
    """Yield (dotted name, token) for every DTCG token in a document."""
    for k, v in doc.items():
        if k.startswith("$") or not isinstance(v, dict):
            continue
        if "$value" in v:
            yield ".".join(path + (k,)), v
        else:
            yield from walk_tokens(v, path + (k,))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        cfg, _, analysis = config.load(path)
    except config.ConfigError as e:
        sys.exit("config gate failed — run build/config.py for the report:\n  "
                 + str(e).replace("\n", "\n  "))
    cfg_path = pathlib.Path(path).resolve() if path else config.path_default()
    doc, tree, errors, ramps = build(cfg, analysis)
    toks = list(walk_tokens(doc))
    for name, t in toks:
        p = ((t.get("$extensions") or {}).get(EXT) or {}).get("provenance") or {}
        if not p.get("src") or not p.get("conf"):
            errors.append(f"{name}: emitted without provenance")
    if errors:
        print("FAILED")
        for e in errors:
            print("  ·", e)
        sys.exit(1)
    out = cfg_path.parent / "out" / "tokens"
    out.mkdir(parents=True, exist_ok=True)
    (out / "design-tokens.json").write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    by_type = collections.Counter(t["$type"] for _, t in toks)
    by_conf = collections.Counter(t["$extensions"][EXT]["provenance"]["conf"] for _, t in toks)
    dep = len(((doc.get("$extensions") or {}).get(EXT) or {}).get("retired", {}).get("colors", []))
    print("types  " + " ".join(f"{k}:{v}" for k, v in sorted(by_type.items())))
    print("conf   " + " ".join(f"{k}:{v}" for k, v in sorted(by_conf.items())))
    print(f"out/tokens/design-tokens.json written · {len(toks)} tokens, "
          f"{len(ramps)} ramps, {dep} retired colours in the denylist (not tokens), {len(tree['_gaps'])} gaps omitted, "
          f"all with provenance")


if __name__ == "__main__":
    main()
