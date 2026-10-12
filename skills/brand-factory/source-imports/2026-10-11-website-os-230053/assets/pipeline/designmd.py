#!/usr/bin/env python3
"""brand.config.json → out/DESIGN.md (Google design.md format, spec
version "alpha", CLI v0.4.0) and out/design.ext.json (what its front matter
cannot hold).

    python3 build/designmd.py                       # the project's config
    python3 build/designmd.py path/to/brand.config.json
    python3 build/designmd.py --no-lint ...         # write only (tests)

Front matter: only the keys the spec's schema names — version, name,
description, colors, typography, rounded, spacing, components. Token
names are the tree's, hyphenated (color.state.accent_hover →
colors.state-accent-hover). Components are flattened the way the spec
shows variants (button-primary, button-primary-hover) and use only its
eight sub-tokens.

Body: the spec's eight sections in its order, then three it preserves as
unknown sections — Responsive, Known Gaps, Provenance. Every sentence is
a config string (role, rule, use, $note, $comment, principles, policy,
prohibitions) or a table of config values; this file writes no brand prose
of its own.

Gate: `npx -y @google/design.md lint out/DESIGN.md`. Errors fail (exit 1);
warnings are printed. No npx → exit 2, never a claimed pass.

Standard library only. Python 3.9+. Byte-for-byte idempotent.
"""
import collections, json, pathlib, re, shutil, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
from tree import build_tree, resolve, REF  # noqa: E402

SPEC_VERSION = "alpha"
SUB_TOKENS = ("backgroundColor", "textColor", "typography", "rounded",
              "padding", "size", "height", "width")
# "transparent" on a background is no fill; the linter would read it as
# #00000000 and report a false contrast failure, so it is omitted like none.
KEYWORD_COLORS = set()
SKIP_KEYWORDS = {"none", "transparent", "currentColor", "inherit", "underline"}
# Container keys that group variants or states; the spec names entries
# button-primary / button-primary-hover, so these never appear in a name.
DROP_SEGMENTS = {"rest", "variants", "states"}


# ── names ───────────────────────────────────────────────────────────────
def h(s):
    return re.sub(r"[^a-z0-9-]+", "-", str(s).lower().replace("_", "-")).strip("-")


def dm_name(tree_name):
    """tree name → (group, key) in the front matter, or None."""
    p = tree_name.split(".")
    if p[0] == "color":
        if len(p) == 2:
            return "colors", h(p[1])
        if p[1] in ("state", "pillar", "semantic") and len(p) == 3:
            return "colors", f"{p[1]}-{h(p[2])}"
        if p[1] == "dataviz" and len(p) == 4:
            return "colors", f"chart-{h(p[3])}"
        if p[1] == "tint" and len(p) == 4:
            return "colors", f"tint-{h(p[2])}-{h(p[3])}"
        return None
    if p[0] == "type" and len(p) == 2:
        return "typography", h(p[1])
    if p[0] == "radius" and len(p) == 2:
        return "rounded", h(p[1])
    if p[0] == "space" and len(p) == 2:
        return "spacing", h(p[1])
    return None


def dm_ref(ref, tree):
    m = REF.match(ref.strip()) if isinstance(ref, str) else None
    if not m:
        return None
    n = dm_name(m.group(1))
    if n is None or m.group(1) not in tree["tokens"]:
        return None
    return "{" + f"{n[0]}.{n[1]}" + "}"


def px(n):
    if isinstance(n, (int, float)):
        return f"{_num(n)}px"
    return None


def _num(n):
    return int(n) if isinstance(n, float) and n.is_integer() else n


def em(s):
    """'.2em' → '0.2em', '-.035em' → '-0.035em', '0' → '0em'."""
    s = str(s).strip()
    m = re.match(r"^(-?)(\d*\.?\d+)(em|px|rem)?$", s)
    if not m:
        return None
    sign, n, unit = m.groups()
    n = float(n)
    n = int(n) if n.is_integer() else n
    return f"{sign if n else ''}{n}{unit or 'em'}"


# ── YAML (the subset needed: maps, strings, numbers) ────────────────────
def ykey(k):
    k = str(k)
    return k if re.match(r"^[A-Za-z0-9][A-Za-z0-9_-]*$", k) and not k.isdigit() else json.dumps(k)


def yval(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(_num(v))
    return json.dumps(str(v), ensure_ascii=False)


def yaml(d, ind=0):
    out = []
    for k, v in d.items():
        if isinstance(v, dict):
            out.append(" " * ind + f"{ykey(k)}:")
            out += yaml(v, ind + 2)
        else:
            out.append(" " * ind + f"{ykey(k)}: {yval(v)}")
    return out


# ── front matter ────────────────────────────────────────────────────────
def front_matter(cfg, tree, notes):
    T = tree["tokens"]
    fm = collections.OrderedDict()
    fm["version"] = SPEC_VERSION
    fm["name"] = f"{cfg.get('brand')} {cfg.get('version')}".strip()
    pos = (cfg.get("identity") or {}).get("positioning") or {}
    desc = pos.get("architecture") or pos.get("boundary") or cfg.get("positioning")
    if isinstance(desc, str) and desc.strip():
        fm["description"] = desc.strip()

    colors = collections.OrderedDict()
    for name, t in T.items():
        if t["type"] != "color" or t.get("deprecated"):
            continue
        n = dm_name(name)
        if not n:
            continue
        v = t["value"]
        if isinstance(v, str) and REF.match(v):
            r = dm_ref(v, tree)
            v = r if r else resolve(v, tree)
        colors[n[1]] = v
    if "primary" not in colors and "accent" in colors:
        colors = collections.OrderedDict([("primary", "{colors.accent}")] + list(colors.items()))
        notes.append("colors.primary is an alias of colors.accent: the spec requires a "
                     "`primary` and the config names its brand colour `accent`.")
    fm["colors"] = colors

    typo = collections.OrderedDict()
    for name, t in T.items():
        if t["type"] != "typography":
            continue
        v = t["value"]
        e = collections.OrderedDict()
        fam = resolve(v.get("fontFamily"), tree)
        if isinstance(fam, list) and fam:
            e["fontFamily"] = fam[0]
        e["fontSize"] = px(v["fontSize"]["value"])
        if "fontWeight" in v:
            e["fontWeight"] = v["fontWeight"]
        if "lineHeight" in v:
            e["lineHeight"] = v["lineHeight"]
        if "letterSpacing" in v and em(v["letterSpacing"]):
            e["letterSpacing"] = em(v["letterSpacing"])
        typo[dm_name(name)[1]] = e
    fm["typography"] = typo

    fm["rounded"] = collections.OrderedDict(
        (dm_name(n)[1], px(t["value"]["value"])) for n, t in T.items() if n.startswith("radius."))

    sp = collections.OrderedDict()
    for n, t in sorted(((n, t) for n, t in T.items() if n.startswith("space.")),
                       key=lambda x: (x[1]["value"]["value"], x[0])):
        sp[dm_name(n)[1]] = px(t["value"]["value"])
    L = cfg.get("layout", {})
    for bp in L.get("breakpoints", {}).get("order", []):
        g = (L.get("grid") or {}).get(bp)
        if not isinstance(g, dict):
            continue
        if isinstance(g.get("columns"), (int, float)):
            sp[f"columns-{h(bp)}"] = g["columns"]
        for k in ("gutter", "margin", "max"):
            if isinstance(g.get(k), (int, float)):
                sp[f"{k}-{h(bp)}"] = px(g[k])
    cmax = (L.get("containers") or {}).get("max")
    if isinstance(cmax, (int, float)):
        sp["container-max"] = px(cmax)
    fm["spacing"] = sp

    comps, skipped = components(cfg, tree)
    fm["components"] = comps
    return fm, skipped


def components(cfg, tree):
    """Flatten config components into the spec's variant entries."""
    out = collections.OrderedDict()
    skipped = []
    C = cfg.get("components") or {}

    def conv(key, v, ptr):
        if key in ("bg", "fg"):
            if isinstance(v, str) and v in KEYWORD_COLORS:
                return v
            if isinstance(v, str) and v in SKIP_KEYWORDS:
                return None
            r = dm_ref(v, tree) if isinstance(v, str) else None
            if r is None:
                skipped.append((ptr, v))
            return r
        if key in ("radius", "type"):
            r = dm_ref(v, tree) if isinstance(v, str) else None
            if r is None and v is not None:
                skipped.append((ptr, v))
            return r
        if key in ("height", "width", "size", "padding"):
            if isinstance(v, (int, float)):
                return px(v)
            if isinstance(v, str) and REF.match(v):
                return dm_ref(v, tree)
        return None

    # `size` and `padding` are not mapped: in the config `size` is a font
    # size override (table.header.size) and padding is per axis (pad_x), so
    # neither means the spec's single Dimension.
    MAP = {"bg": "backgroundColor", "fg": "textColor", "type": "typography",
           "radius": "rounded", "height": "height", "width": "width"}

    def walk(node, path, ptr, base):
        own = collections.OrderedDict()
        for k, v in node.items():
            if k.startswith("$") or k not in MAP:
                continue
            if isinstance(v, dict):
                if k in ("bg", "fg"):
                    skipped.append((f"{ptr}/{k}", v))     # {color, alpha}: no design.md form
                continue
            if isinstance(v, list):
                continue
            c = conv(k, v, f"{ptr}/{k}")
            if c is not None:
                own[MAP[k]] = c
        is_root = len(path) == 1
        if is_root:
            base = collections.OrderedDict((k, v) for k, v in own.items()
                                           if k in ("rounded", "typography"))
        if own:
            props = collections.OrderedDict()
            if is_root or path[-1] == "rest" or not _is_state(path[-1]):
                props.update(base)
            props.update(own)
            name = "-".join(h(p) for p in path if p not in DROP_SEGMENTS)
            out.setdefault(name, collections.OrderedDict()).update(props)
        for k, v in node.items():
            if k.startswith("$") or k in MAP or not isinstance(v, dict):
                continue
            if config.SLOT_RE.search(k) or k == "color":
                # a stroke composite {width, style, color}: no design.md form
                skipped.append((f"{ptr}/{k}", v))
                continue
            walk(v, path + [k], f"{ptr}/{k}", base)

    for k in C:
        if k.startswith("$") or not isinstance(C[k], dict):
            continue
        walk(C[k], [k], f"/components/{k}", collections.OrderedDict())
    return out, skipped


STATES = {"hover", "active", "pressed", "focus", "disabled", "selected", "error",
          "loading", "checked", "open", "current", "visited"}


def _is_state(seg):
    return seg in STATES


# ── body ────────────────────────────────────────────────────────────────
class Body:
    def __init__(self, cfg, tree, a):
        self.cfg, self.tree, self.a = cfg, tree, a
        self.P = a["provenance"]
        self.L = []

    def src(self, ptr):
        """Cite the source of a pointer (or of its nearest leaf)."""
        cur = ptr
        while cur:
            if cur in self.P:
                return self.P[cur].get("src")
            pre = cur + "/"
            kids = sorted((k for k in self.P if k.startswith(pre)), key=lambda k: (k.count("/"), k))
            if kids:
                return self.P[kids[0]].get("src")
            cur = cur.rsplit("/", 1)[0]          # a list of scalars is one leaf
        return None

    def cite(self, ptr):
        s = self.src(ptr)
        return f" ({s})" if s else ""

    def w(self, *lines):
        self.L.extend(lines)

    def section(self, title):
        if self.L and self.L[-1] != "":
            self.L.append("")
        self.L += [f"## {title}", ""]

    def sub(self, title):
        if self.L and self.L[-1] != "":
            self.L.append("")
        self.L += [f"### {title}", ""]

    def table(self, head, rows):
        if not rows:
            return
        cell = lambda x: str("—" if x is None or x == "" else x).replace("|", "\\|").replace("\n", " ")
        self.w("| " + " | ".join(head) + " |", "| " + " | ".join("---" for _ in head) + " |")
        for r in rows:
            self.w("| " + " | ".join(cell(x) for x in r) + " |")
        self.w("")


def txt(v):
    return v.strip() if isinstance(v, str) and v.strip() else None


def live(d):
    return [k for k in (d or {}) if not str(k).startswith("$")] if isinstance(d, dict) else []


def lst(v):
    if isinstance(v, dict):
        v = v.get("list", v.get("items", v.get("value")))
    return [x for x in v if isinstance(x, str)] if isinstance(v, list) else []


def body(cfg, tree, a, fm, fm_notes, skipped):
    B = Body(cfg, tree, a)
    T = tree["tokens"]
    C = cfg.get("color", {})
    brand = cfg.get("brand", "")
    B.w(f"# {brand} {cfg.get('version', '')} — DESIGN.md".replace("  ", " "), "",
        f"Generated by brand-factory `build/designmd.py` from `brand.config.json` "
        f"(mode: {cfg.get('mode')}). The front matter holds the tokens the design.md "
        f"spec allows; `design.ext.json` holds the rest. Do not edit — edit the config.")

    # Overview
    B.section("Overview")
    idn = (cfg.get("identity") or {}).get("positioning") or {}
    loc = cfg.get("locales") or {}
    tag = idn.get("tagline")
    if isinstance(tag, dict):
        tag = tag.get(loc.get("default", "en"))
    for label, v, ptr in (("Tagline", tag, "/identity/positioning/tagline"),
                          ("Architecture", idn.get("architecture"), "/identity/positioning/architecture"),
                          ("Boundary", idn.get("boundary"), "/identity/positioning/boundary"),
                          ("What it is", idn.get("what_it_is"), "/identity/positioning/what_it_is")):
        if txt(v):
            B.w(f"- **{label}:** {txt(v)}{B.cite(ptr)}")
    if loc.get("list"):
        B.w(f"- **Locales:** {', '.join(loc['list'])}; default {loc.get('default')}"
            + (f"; right-to-left: {', '.join(loc.get('rtl') or [])}" if loc.get("rtl") else "")
            + B.cite("/locales/list"))
    V = cfg.get("voice") or {}
    pr = (V.get("principles") or {}).get("list") or []
    if pr:
        B.sub("Voice")
        for i, p in enumerate(pr):
            if isinstance(p, dict) and txt(p.get("rule")):
                ex = f" — e.g. “{p['example']}”" if txt(p.get("example")) else ""
                B.w(f"- {p['rule']}{ex}{B.cite(f'/voice/principles/list/{i}/rule')}")
    tone = V.get("tone") or {}
    rows = [(k, tone[k].get("register"), tone[k].get("never")) for k in live(tone)
            if isinstance(tone[k], dict)]
    if rows:
        B.w("")
        B.table(["Surface", "Register", "Never"], rows)

    # Colors
    B.section("Colors")
    if txt(C.get("proportion", {}).get("rule")):
        B.w(f"{C['proportion']['rule']}{B.cite('/color/proportion/rule')}", "")
    for n in fm_notes:
        B.w(f"Note: {n}", "")
    rows = []
    for k in live(C.get("roles")):
        t = T.get(f"color.{k}")
        r = C["roles"][k]
        if not t:
            continue
        val = t["value"] if not t.get("alias") else t["alias"]
        rows.append((f"`{dm_name('color.' + k)[1]}`", r.get("name") if isinstance(r, dict) else "",
                     val, t["description"], t["provenance"]["src"]))
    B.sub("Roles")
    B.table(["Token", "Name", "Value", "Role", "Source"], rows)
    st = [(f"`{dm_name('color.state.' + k)[1]}`", T[f"color.state.{k}"]["value"],
           (C["states"][k] or {}).get("derive") if isinstance(C["states"][k], dict) else None)
          for k in live(C.get("states")) if f"color.state.{k}" in T]
    if st:
        B.sub("States")
        B.table(["Token", "Hex", "Derivation"], st)
    acc = C.get("accents") or {}
    if live(acc):
        B.sub("Pillar accents")
        if txt(acc.get("$comment")):
            B.w(acc["$comment"] + B.cite("/color/accents"), "")
        B.table(["Token", "Label", "Hex", "Note"],
                [(f"`{dm_name('color.pillar.' + k)[1]}`", acc[k].get("label"),
                  T[f"color.pillar.{k}"]["value"] if f"color.pillar.{k}" in T else None,
                  acc[k].get("$note") or (f"alias of {acc[k]['alias_of']}" if acc[k].get("alias_of") else ""))
                 for k in live(acc) if isinstance(acc[k], dict)])
    sem = C.get("semantic") or {}
    if live(sem):
        B.sub("Semantic")
        for k in live(sem):
            s = sem[k]
            if not isinstance(s, dict):
                continue
            ptr = f"/color/semantic/{k}"
            if s.get("hex"):
                bits = [x for x in (s.get("use"), s.get("rule")) if txt(x)]
                B.w(f"- **`{dm_name('color.semantic.' + k)[1]}` ({s['hex']}):** "
                    + "; ".join(bits) + B.cite(ptr + "/hex"))
            elif s.get("policy") == "none" and txt(s.get("rule")):
                B.w(f"- **{k}** takes no colour: {s['rule']}{B.cite(ptr)}")
            elif s.get("$gap"):
                B.w(f"- **{k}** — gap: {s['$gap']}")
        B.w("")
    tints = C.get("tints") or {}
    stated = tints.get("stated") or {}
    if live(stated):
        B.sub("Tints")
        if txt(tints.get("rule")):
            B.w(tints["rule"] + B.cite("/color/tints/rule"), "")
        pcts = sorted({p for b in live(stated) for p in live(stated[b])}, key=lambda x: -float(x))
        B.table(["Base"] + [f"{p}%" for p in pcts],
                [[b] + [stated[b].get(p) for p in pcts] for b in live(stated)])
    R = C.get("ramps") or {}
    if R.get("for"):
        B.w(f"OKLCH ramps ({', '.join(str(s) for s in R.get('steps', []))}) are computed for "
            f"{', '.join(R['for'])} and published only in `design.ext.json` and the DTCG export"
            + (f"; surface use: **{R['surface_use']}**" if R.get("surface_use") else "")
            + f".{B.cite('/color/ramps')}", "")
    dk = C.get("dark") or {}
    if dk:
        B.sub("Dark surfaces")
        if txt(dk.get("theme")):
            B.w(f"- Dark theme: {dk['theme']}{B.cite('/color/dark/theme')}")
        s = dk.get("surfaces") or {}
        if lst(s.get("where")):
            B.w(f"- Where: {'; '.join(lst(s['where']))}{B.cite('/color/dark/surfaces/where')}")
        if lst(s.get("never")):
            B.w(f"- Never: {'; '.join(lst(s['never']))}{B.cite('/color/dark/surfaces/never')}")
        if txt(s.get("cadence")):
            B.w(f"- {s['cadence']}{B.cite('/color/dark/surfaces/cadence')}")
        B.w("")
    dv = C.get("dataviz") or {}
    if dv:
        B.sub("Data visualisation")
        ms = dv.get("max_series")
        ms = ms.get("value") if isinstance(ms, dict) else ms
        if ms:
            B.w(f"- At most {ms} series{B.cite('/color/dataviz/max_series/value')}")
        for k in ("categorical", "sequential", "score"):
            n = dv.get(k)
            if isinstance(n, dict):
                s = n.get("rule") or n.get("$note")
                if txt(s):
                    B.w(f"- {k.capitalize()}: {s}{B.cite(f'/color/dataviz/{k}')}")
        if isinstance(dv.get("diverging"), dict) and dv["diverging"].get("$gap"):
            B.w(f"- Diverging: gap — {dv['diverging']['$gap']}")
        if live(dv.get("chart")):
            B.w(f"- Chart slots: " + ", ".join(f"`chart-{k}` {dv['chart'][k]}" for k in live(dv["chart"]))
                + B.cite("/color/dataviz/chart"))
        B.w("")
    ret = C.get("retired") or {}
    if live(ret):
        B.sub("Retired")
        if txt(ret.get("$comment")):
            B.w(ret["$comment"] + B.cite("/color/retired"), "")
        B.w(", ".join(f"{k} {ret[k] if isinstance(ret[k], str) else ret[k].get('hex')}"
                      + (" (role only)" if isinstance(ret[k], dict) and ret[k].get("retired_role_only") else "")
                      for k in live(ret)), "")

    # Typography
    B.section("Typography")
    TY = cfg.get("type") or {}
    F = TY.get("families") or {}
    for k in live(F):
        f = F[k]
        if not isinstance(f, dict) or not f.get("family"):
            continue
        w = f.get("weights")
        ws = ""
        if isinstance(w, dict) and "axis" in w:
            ws = f" Variable {w['axis'][0]}–{w['axis'][1]}."
        elif isinstance(w, dict) and "static" in w:
            ws = f" Static weights {', '.join(str(x) for x in w['static'])}."
        extra = " ".join(x for x in (txt(f.get("italic_rule")),
                                     f"Ceiling {f['ceiling_px']}px." if f.get("ceiling_px") else None) if x)
        B.w(f"- **{f['family']}** ({k}): " + " ".join(x for x in (txt(f.get("use")), ws.strip(), extra) if x)
            + B.cite(f"/type/families/{k}/family"))
    B.w("")
    rows = []
    for name, t in T.items():
        if t["type"] != "typography":
            continue
        v = t["value"]
        fam = resolve(v.get("fontFamily"), tree)
        rows.append((f"`{dm_name(name)[1]}`", fam[0] if isinstance(fam, list) else "",
                     v.get("fontWeight"), px(v["fontSize"]["value"]), v.get("lineHeight"),
                     em(v["letterSpacing"]) if "letterSpacing" in v else "gap",
                     t["description"], f"{t['provenance']['src']} · {t['provenance']['conf']}"))
    B.table(["Token", "Family", "Weight", "Size", "Line height", "Tracking", "Use", "Source · weakest"],
            rows)
    bands = (TY.get("tracking") or {}).get("bands") or []
    if bands:
        B.w("Tracking by size: " + "; ".join(
            f"{b.get('family', 'display')} ≥{b.get('min_px')}px {b.get('value')}" for b in bands)
            + B.cite("/type/tracking/bands") + ".", "")
    S = TY.get("setting") or {}
    for k in ("alignment", "case", "emphasis", "synthesis"):
        if txt(S.get(k)):
            B.w(f"- {k.capitalize()}: {S[k]}{B.cite(f'/type/setting/{k}')}")
    if isinstance(S.get("measure_ch"), list):
        B.w(f"- Measure: {S['measure_ch'][0]}–{S['measure_ch'][-1]}ch{B.cite('/type/setting/measure_ch')}")
    aw = S.get("accent_word") or {}
    if txt(aw.get("rule")):
        B.w(f"- Accent word: {aw['rule']}{B.cite('/type/setting/accent_word/rule')}")

    # Layout
    B.section("Layout")
    LY = cfg.get("layout") or {}
    spc = LY.get("spacing") or {}
    uses = spc.get("uses") or {}
    B.table(["Token", "Value", "Use"],
            [(f"`{dm_name(n)[1]}`", px(t["value"]["value"]), uses.get(str(_num(t["value"]["value"])), ""))
             for n, t in sorted(((n, t) for n, t in T.items() if n.startswith("space.")),
                                key=lambda x: x[1]["value"]["value"])])
    cont = LY.get("containers") or {}
    if cont.get("max"):
        B.w(f"- Container max {cont['max']}px" + (f"; prose measure {cont['prose_ch']}ch" if cont.get("prose_ch") else "")
            + B.cite("/layout/containers/max"))
    sr = LY.get("section_rhythm") or {}
    if live(sr):
        B.w("- Section rhythm: " + ", ".join(
            f"{k} {(sr[k].get('value') if isinstance(sr[k], dict) else sr[k])}px" for k in live(sr))
            + B.cite("/layout/section_rhythm"))
    rules = LY.get("rules") or {}
    for k in live(rules):
        r = rules[k]
        if isinstance(r, dict):
            B.w(f"- Rule `{k}`: {r.get('width')}px {r.get('color')}"
                + (f" — {r['use']}" if txt(r.get("use")) else "") + B.cite(f"/layout/rules/{k}"))
    ce = LY.get("ceilings") or {}
    if live(ce):
        B.w("- Ceilings: " + ", ".join(f"{k.replace('_', ' ')} {ce[k] if not isinstance(ce[k], list) else '–'.join(map(str, ce[k]))}"
                                       for k in live(ce)) + B.cite("/layout/ceilings"))
    B.w("", "Grid per breakpoint is under Responsive.")

    # Elevation
    B.section("Elevation & Depth")
    E = cfg.get("elevation") or {}
    pol = (cfg.get("effects") or {}).get("policy") or {}
    B.w(f"Elevation method: **{E.get('method', pol.get('elevation', '—'))}**{B.cite('/elevation/method')}; "
        f"shadows: **{pol.get('shadow', '—')}**{B.cite('/effects/policy/shadow')}.", "")
    rows = []
    for k in live(E.get("levels")):
        lv = E["levels"][k]
        b = lv.get("border")
        bs = b if isinstance(b, str) else f"{b.get('width')}px {b.get('color')}" if isinstance(b, dict) else "—"
        rows.append((f"`{k}`", lv.get("name"), lv.get("surface"), bs, lv.get("scrim"), lv.get("use")))
    B.table(["Level", "Name", "Surface", "Border", "Scrim", "Use"], rows)
    isc = E.get("image_scrim") or {}
    if isinstance(isc, dict) and isc.get("value"):
        B.w(f"Image scrim {isc['value']}" + (f": {isc['rule']}" if txt(isc.get("rule")) else "")
            + B.cite("/elevation/image_scrim/value"))

    # Shapes
    B.section("Shapes")
    SH = cfg.get("shape") or {}
    mp = SH.get("map") or {}
    B.table(["Token", "Radius", "Applies to"],
            [(f"`{k}`", px(SH.get(k)), ", ".join(x for x in live(mp) if mp[x] == k))
             for k in ("surface", "control", "floating") if isinstance(SH.get(k), (int, float))])
    if isinstance(pol.get("radius_max_px"), (int, float)):
        B.w(f"- No radius above {pol['radius_max_px']}px{B.cite('/effects/policy/radius_max_px')}")
    ci = SH.get("circle")
    if isinstance(ci, dict) and ci.get("value"):
        B.w(f"- {ci['value']} only for: {', '.join(lst(ci.get('allowed_for')))}{B.cite('/shape/circle/value')}")

    # Components
    B.section("Components")
    comps = fm.get("components", {})
    CC = cfg.get("components") or {}
    for k in live(CC):
        c = CC[k]
        if not isinstance(c, dict):
            continue
        names = [n for n in comps if n == h(k) or n.startswith(h(k) + "-")]
        note = txt(c.get("$note")) or txt(c.get("$comment")) or txt(c.get("rule"))
        val = c.get("value")
        line = f"- **{k}**"
        if isinstance(val, str):
            line += f" = `{val}`."
        if note:
            line += f" {note}"
        if names:
            line += " Entries: " + ", ".join(f"`{n}`" for n in names) + "."
        B.w(line + B.cite(f"/components/{k}"))
    if not live(CC):
        B.w("The config defines no components.")
    if skipped:
        B.w("", f"{len(skipped)} component values have no design.md form (composites, "
                "non-token references) and stay in brand.config.json; they are listed under Known Gaps.")

    # Do's and Don'ts
    B.section("Do's and Don'ts")
    dos = []
    if txt(C.get("proportion", {}).get("rule")):
        dos.append(f"Do: {C['proportion']['rule']}{B.cite('/color/proportion/rule')}")
    cola = ((cfg.get("a11y") or {}).get("colour_alone") or {})
    if isinstance(cola, dict) and txt(cola.get("rule")):
        dos.append(f"Do: {cola['rule']}{B.cite('/a11y/colour_alone/rule')}")
    a11y = cfg.get("a11y") or {}
    if txt(a11y.get("target")):
        fl = a11y.get("floors") or {}
        dos.append(f"Do meet {a11y['target']}: " + ", ".join(f"{k.replace('_', ' ')} {fl[k]}:1" for k in live(fl))
                   + B.cite("/a11y/target"))
    M = cfg.get("motion") or {}
    rm = M.get("reduced_motion") or {}
    if isinstance(rm, dict) and txt(rm.get("rule")):
        dos.append(f"Do: reduced motion — {rm['rule']}{B.cite('/motion/reduced_motion/rule')}")
    am = M.get("authored_moment") or {}
    if isinstance(am, dict) and txt(am.get("rule")):
        dos.append(f"Do: authored motion — {am.get('value')}. {am['rule']}{B.cite('/motion/authored_moment/value')}")
    gdd = (cfg.get("governance") or {}).get("do_dont") or {}
    for k in ("do", "dos"):
        dos += [f"Do: {x}{B.cite('/governance/do_dont')}" for x in lst(gdd.get(k))]
    donts = []
    for i, p in enumerate((C.get("pairings") or {}).get("prohibited") or []):
        ptr = f"/color/pairings/prohibited/{i}"
        if not isinstance(p, dict):
            continue
        if p.get("fg") and p.get("bg"):
            why = f"{p['ratio']}:1" if p.get("ratio") else ""
            why += (f", {p['why']}" if txt(p.get("why")) else "")
            donts.append(f"Don't set `{p['fg']}` on `{p['bg']}` ({why})"
                         + (f" — use `{p['instead']}`" if p.get("instead") else "") + B.cite(ptr))
        elif txt(p.get("rule")):
            donts.append(f"Don't: {p['rule']}"
                         + (f" (exception: {p['exception']})" if p.get("exception") else "")
                         + (f" — use `{p['instead']}`" if p.get("instead") else "") + B.cite(ptr))
    for i, x in enumerate(lst(M.get("prohibited"))):
        donts.append(f"Don't (motion): {x}{B.cite('/motion/prohibited')}")
    POL = {"shadow": "shadows", "gradient": "gradients", "blur": "blur", "filter": "CSS filters",
           "font_service_links": "font-service links"}
    for k, label in POL.items():
        if pol.get(k) == "none":
            donts.append(f"Don't use {label} (effects.policy.{k}: none){B.cite(f'/effects/policy/{k}')}")
    BOOL = {"transform_on_press": "transform on press", "opacity_hover": "opacity as a hover state",
            "scroll_linked_motion": "scroll-linked motion", "decorative_animation": "decorative animation",
            "card_grids": "card grids"}
    for k, label in BOOL.items():
        if pol.get(k) is False:
            donts.append(f"Don't use {label} (effects.policy.{k}: false){B.cite(f'/effects/policy/{k}')}")
    for k in live(F):
        f = F[k]
        if isinstance(f, dict) and f.get("ceiling_px"):
            donts.append(f"Don't set {f.get('family')} above {f['ceiling_px']}px{B.cite(f'/type/families/{k}/ceiling_px')}")
    ban = lst((V.get("banned") or {}))
    if ban:
        donts.append(f"Don't write: {', '.join(ban)}{B.cite('/voice/banned/list')}")
    nev = lst(V.get("never"))
    if nev:
        donts.append(f"Don't (copy): {'; '.join(nev)}{B.cite('/voice/never/list')}")
    mis = lst((cfg.get("logo") or {}).get("misuse"))
    if mis:
        donts.append(f"Don't (logo): {'; '.join(mis)}{B.cite('/logo/misuse/list')}")
    for k in ("dont", "donts", "don't"):
        donts += [f"Don't: {x}{B.cite('/governance/do_dont')}" for x in lst(gdd.get(k))]
    ret = C.get("retired") or {}
    rl = [f"{k} {ret[k] if isinstance(ret[k], str) else ret[k].get('hex')}" for k in live(ret)
          if not (isinstance(ret[k], dict) and ret[k].get("retired_role_only"))]
    if rl:
        donts.append("Don't use a retired colour — they are not tokens and no output may carry one: "
                     + ", ".join(rl) + B.cite("/color/retired"))
    for x in dos + donts:
        B.w(f"- {x}")

    # Responsive
    B.section("Responsive")
    bp = LY.get("breakpoints") or {}
    order = bp.get("order") or []
    if order:
        if txt(bp.get("$comment")):
            B.w(bp["$comment"] + B.cite("/layout/breakpoints/order"), "")
        grid = LY.get("grid") or {}
        B.table(["Breakpoint", "Min width", "Columns", "Gutter", "Margin", "Max"],
                [(b, px((bp.get("min") or {}).get(b)),
                  (grid.get(b) or {}).get("columns", "—"), px((grid.get(b) or {}).get("gutter")),
                  px((grid.get(b) or {}).get("margin")), px((grid.get(b) or {}).get("max")))
                 for b in order])
        if txt(bp.get("media_rule")):
            B.w(f"{bp['media_rule']}{B.cite('/layout/breakpoints/media_rule')}", "")
        rows = []
        for name, t in T.items():
            if t["type"] != "typography":
                continue
            x = t.get("extensions") or {}
            d = x.get("default_breakpoint")
            row = [f"`{dm_name(name)[1]}`"]
            for b in order:
                if b == d:
                    row.append(px(t["value"]["fontSize"]["value"]))
                elif b in (x.get("breakpoints") or {}):
                    row.append(px(x["breakpoints"][b]["fontSize"]["value"]))
                elif b in (x.get("fallback") or {}):
                    row.append(f"= {x['fallback'][b]}")
                else:
                    row.append("—")
            rows.append(row)
        B.w("Type size per breakpoint (tracking follows the size bands above):", "")
        B.table(["Token"] + order, rows)
    D = cfg.get("density") or {}
    sc = D.get("scales") or {}
    if live(sc):
        B.table(["Density", "Row", "Text", "Label", "Pad x", "Use"],
                [(k, px(sc[k].get("row")), px(sc[k].get("text")), px(sc[k].get("label")),
                  px(sc[k].get("pad_x")), sc[k].get("use")) for k in live(sc)])
    pc = D.get("phone_collapse")
    if isinstance(pc, dict) and txt(pc.get("rule")):
        B.w(f"Density collapse: {pc['rule']}{B.cite('/density/phone_collapse/rule')}")

    # Known gaps: every one — the token tree's, then every $gap leaf of the
    # config grouped by section, then every reconcile item still to confirm
    B.section("Known Gaps")
    gaps = tree["_gaps"]
    cg = list(a.get("gaps") or [])
    conf_n = len([i for i in a.get("reconcile", []) if i.get("status") == "confirm"])
    B.w(f"{len(gaps)} token gap(s), {len(cg)} config gap(s), {conf_n} question(s) for the brand owner. "
        "A builder reading only this file must learn all of them here.", "")
    B.sub("Tokens")
    if gaps:
        B.table(["Token", "Pointer", "Why"],
                [(f"`{g['name']}`" + (f" · {g['part']}" if g.get("part") else ""), f"`{g['pointer']}`", g["gap"])
                 for g in gaps])
    else:
        B.w("No token is a gap.", "")
    if cg:
        groups = collections.OrderedDict()
        for ptr, why in cg:
            top = str(ptr).strip("/").split("/")[0] or "(root)"
            groups.setdefault(top, []).append((ptr, why))
        for top, items in groups.items():
            B.sub(f"Config · {top} ({len(items)})")
            # leaves that share one reason under one node are one gap: name the
            # node (a node whose own value is the gap collapses whole; otherwise
            # one level down, so distinct gaps stay distinct)
            def node(ptr, d):
                return "/" + "/".join(str(ptr).strip("/").split("/")[:d])
            by_why = collections.OrderedDict()
            for ptr, why in items:
                by_why.setdefault((txt(why) or "not in the sources", node(ptr, 2)), []).append(str(ptr))
            for (why, n2), ptrs in by_why.items():
                if len(ptrs) > 3 and f"{n2}/value" in ptrs:
                    B.w(f"- `{n2}` ({len(ptrs)} leaves) — {why}")
                    continue
                sub = collections.OrderedDict()
                for x in ptrs:
                    sub.setdefault(node(x, 3), []).append(x)
                for n3, xs in sub.items():
                    if len(xs) > 1:
                        B.w(f"- `{n3}` ({len(xs)} leaves) — {why}")
                    else:
                        B.w(f"- `{xs[0]}` — {why}")
            B.w("")
    conf = [i for i in a.get("reconcile", []) if i.get("status") == "confirm"]
    if conf:
        B.w("Open questions for the brand owner (see out/CONFIRM.md):", "")
        for i in conf:
            B.w(f"- **{i.get('id')}** `{i.get('path')}` — {i.get('question', '')} "
                f"Using until answered: `{json.dumps(i.get('chosen'), ensure_ascii=False)}`.")
        B.w("")
    else:
        B.w("No reconcile item is waiting on the brand owner.", "")
    if tree["_notes"]:
        B.w("Config notes from the generators:", "")
        for n in tree["_notes"]:
            B.w(f"- `{n['pointer']}`: {n['note']}")
        B.w("")
    if skipped:
        B.w("Component values with no design.md form (kept in brand.config.json):", "")
        for ptr, v in skipped:
            B.w(f"- `{ptr}`: `{json.dumps(v, ensure_ascii=False)}`")

    # Provenance
    B.section("Provenance")
    srcs = cfg.get("sources") or {}
    B.table(["Id", "Kind", "Title", "Path"],
            [(k, s.get("kind"), s.get("title"), s.get("path")) for k, s in srcs.items()
             if isinstance(s, dict)])
    bc = a.get("by_conf") or {}
    B.w("Config values by confidence: " + ", ".join(f"{k} {bc[k]}" for k in config.CONF if bc.get(k)) + ".")
    tc = collections.Counter(t["provenance"]["conf"] for t in T.values())
    B.w("Tokens by confidence (a composite takes its weakest part): "
        + ", ".join(f"{k} {tc[k]}" for k in config.CONF if tc.get(k)) + ".")
    return "\n".join(B.L).rstrip() + "\n"


def ext_json(cfg, tree, ramps):
    def clean(n):
        if isinstance(n, dict):
            return {k: clean(v) for k, v in n.items() if not str(k).startswith("$")}
        if isinstance(n, list):
            return [clean(x) for x in n]
        return n

    M = cfg.get("motion") or {}
    L = cfg.get("layout") or {}
    E = cfg.get("elevation") or {}
    C = cfg.get("color") or {}
    pol = (cfg.get("effects") or {}).get("policy") or {}
    doc = collections.OrderedDict()
    doc["note"] = ("brand-factory design.ext.json — what DESIGN.md front matter "
                           "cannot hold. Generated; do not edit.")
    doc["brand"] = cfg.get("brand")
    doc["version"] = cfg.get("version")
    doc["motion"] = {k: clean(M.get(k)) for k in ("durations_ms", "easing", "assign", "prohibited",
                                                  "reduced_motion", "authored_moment", "max_ms")
                     if k in M}
    doc["breakpoints"] = clean(L.get("breakpoints"))
    doc["grid"] = clean(L.get("grid"))
    doc["elevation"] = {"levels": clean(E.get("levels")), "method": E.get("method"),
                        "policy": pol.get("elevation"), "shadows": clean(E.get("shadows")),
                        "image_scrim": clean(E.get("image_scrim"))}
    doc["ramps"] = ramps
    doc["dataviz"] = clean(C.get("dataviz"))
    for k in ("icons", "imagery", "seo", "density"):
        doc[k] = clean(cfg.get(k))
    doc["effects_policy"] = clean(pol)
    doc["locales"] = clean(cfg.get("locales"))
    doc["pointers"] = {"motion": "/motion", "breakpoints": "/layout/breakpoints", "grid": "/layout/grid",
                       "elevation": "/elevation", "ramps": "/color/ramps", "dataviz": "/color/dataviz",
                       "icons": "/icons", "imagery": "/imagery", "seo": "/seo", "density": "/density",
                       "effects_policy": "/effects/policy", "locales": "/locales"}
    doc = {k: v for k, v in doc.items() if v not in (None, {}, [])}
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def build(cfg, analysis):
    from dtcg import build as dtcg_build
    tree = build_tree(cfg, analysis)
    notes = []
    fm, skipped = front_matter(cfg, tree, notes)
    _, _, _, ramps = dtcg_build(cfg, analysis)
    fm = collections.OrderedDict((k, v) for k, v in fm.items() if v not in ({}, None, ""))
    md = "---\n" + "\n".join(yaml(fm)) + "\n---\n\n" + body(cfg, tree, analysis, fm, notes, skipped)
    return md, ext_json(cfg, tree, ramps), fm


def lint(path, cwd):
    npx = shutil.which("npx")
    if not npx:
        return None, "npx not found on PATH — DESIGN.md was written but NOT linted"
    try:
        r = subprocess.run([npx, "-y", "@google/design.md", "lint", str(path)], cwd=cwd,
                           capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return None, "npx @google/design.md lint timed out"
    try:
        return json.loads(r.stdout), None
    except ValueError:
        return None, f"lint produced no JSON (exit {r.returncode}): {(r.stdout + r.stderr)[:400]}"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    no_lint = "--no-lint" in sys.argv
    path = args[0] if args else None
    try:
        cfg, _, analysis = config.load(path)
    except config.ConfigError as e:
        sys.exit("config gate failed — run build/config.py for the report:\n  "
                 + str(e).replace("\n", "\n  "))
    cfg_path = pathlib.Path(path).resolve() if path else config.path_default()
    out = cfg_path.parent / "out"
    out.mkdir(exist_ok=True)
    md, ext, fm = build(cfg, analysis)
    (out / "DESIGN.md").write_text(md, encoding="utf-8")
    (out / "design.ext.json").write_text(ext, encoding="utf-8")
    counts = ", ".join(f"{len(fm.get(k, {}))} {k}" for k in ("colors", "typography", "rounded", "spacing", "components"))
    if no_lint:
        print(f"out/DESIGN.md + out/design.ext.json written · {counts} · lint skipped (--no-lint)")
        return
    res, err = lint(out / "DESIGN.md", cfg_path.parent)
    if res is None:
        print(f"FAILED · {err}")
        sys.exit(2)
    f = res.get("findings", [])
    errs = [x for x in f if x.get("severity") == "error"]
    warns = [x for x in f if x.get("severity") == "warning"]
    for x in warns:
        print(f"  warning · {x.get('rule')} · {x.get('path', '')} · {x.get('message')}")
    for x in errs:
        print(f"  error · {x.get('rule')} · {x.get('path', '')} · {x.get('message')}")
    s = res.get("summary", {})
    if errs:
        print(f"FAILED · design.md lint: {s.get('errors')} errors, {s.get('warnings')} warnings")
        sys.exit(1)
    print(f"out/DESIGN.md + out/design.ext.json written · {counts} · "
          f"design.md lint: 0 errors, {s.get('warnings', 0)} warnings, {s.get('infos', 0)} infos")


if __name__ == "__main__":
    main()
