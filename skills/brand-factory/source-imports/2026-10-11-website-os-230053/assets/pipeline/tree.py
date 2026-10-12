#!/usr/bin/env python3
"""The brand's token tree — the one structure every v2 generator reads.

    from tree import build_tree, resolve
    cfg, _, analysis = config.load(path)
    t = build_tree(cfg, analysis)
    t["tokens"]["color.accent"]   # {value, type, description, provenance, json_pointer, ...}
    resolve("{color.accent}", t)  # "#1231D6"

A library, not a step: dtcg.py and designmd.py import it.

Names are exactly the names config.ref_targets() promises a {reference}
may use, plus the extras no component references: color.tint.*,
color.retired.* (deprecated), font.*, breakpoint.*. A ref target whose
value is a gap is NOT a token — it is listed in tree["_gaps"] instead, so
the union of tokens, gaps and components is ref_targets() exactly.

Every token carries provenance resolved from analysis["provenance"] (the
nearest leaf pointer). A composite (type.<role>, elevation.<level>) takes
the WEAKEST confidence of its parts, so a role whose size is a default is
never reported as stated just because its weight is.

Nothing here invents a value. Where the config writes a bare role name
("bg", "border") where a reference belongs, it is read as {color.<name>}
when that colour exists, and recorded in tree["_notes"] so the config can
be fixed.

Standard library only. Python 3.9+.
"""
import re

REF = re.compile(r"^\{([a-zA-Z0-9_.-]+)\}$")
HEX = re.compile(r"^#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$")
RGBA = re.compile(r"^rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+%?)\s*)?\)$")
# Strongest first. "empty" never reaches a token.
CONF_ORDER = ("high", "medium", "derived", "default", "guess", "gap")
CSS_EASE = {"linear": [0, 0, 1, 1], "ease": [0.25, 0.1, 0.25, 1],
            "ease-in": [0.42, 0, 1, 1], "ease-out": [0, 0, 0.58, 1],
            "ease-in-out": [0.42, 0, 0.58, 1]}
FONT_KEYS = ("display", "text", "mono", "arabic")


def live(d):
    return [k for k in (d or {}) if not str(k).startswith("$")]


def _esc(k):
    return str(k).replace("~", "~0").replace("/", "~1")


# ── provenance ──────────────────────────────────────────────────────────
class Prov:
    def __init__(self, analysis):
        self.p = analysis.get("provenance", {})
        self.keys = sorted(self.p)

    def at(self, ptr, prefer=("hex", "value")):
        """The provenance of a pointer: the leaf itself; else a preferred
        child leaf (hex, value); else the nearest descendant leaf; else
        walk up to the parent and try again."""
        cur = ptr
        while cur:
            if cur in self.p:
                return self._clean(self.p[cur])
            for k in prefer:
                if f"{cur}/{k}" in self.p:
                    return self._clean(self.p[f"{cur}/{k}"])
            pre = cur + "/"
            kids = [k for k in self.keys if k.startswith(pre)]
            if kids:
                kids.sort(key=lambda k: (k.count("/"), k))
                return self._clean(self.p[kids[0]])
            cur = cur.rsplit("/", 1)[0]
        return None

    @staticmethod
    def _clean(e):
        out = {"src": e.get("src"), "conf": e.get("conf")}
        if e.get("gap"):
            out["gap"] = e["gap"]
        return out


def weakest(provs):
    provs = [p for p in provs if p]
    if not provs:
        return None
    rank = {c: i for i, c in enumerate(CONF_ORDER)}
    return max(provs, key=lambda p: rank.get(p.get("conf"), len(CONF_ORDER)))


# ── colour parsing ──────────────────────────────────────────────────────
def parse_color(v):
    """'#RRGGBB' / '#RGB' / '#RRGGBBAA' / 'rgba(r,g,b,a)' → (r, g, b, alpha|None)
    with r, g, b in 0–255. None if it is not a colour literal."""
    if not isinstance(v, str):
        return None
    s = v.strip()
    if HEX.match(s):
        h = s[1:]
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        a = int(h[6:8], 16) / 255 if len(h) == 8 else None
        return (r, g, b, a)
    m = RGBA.match(s)
    if m:
        r, g, b = (float(m.group(i)) for i in (1, 2, 3))
        a = m.group(4)
        if a is not None:
            a = float(a[:-1]) / 100 if a.endswith("%") else float(a)
        return (r, g, b, a)
    return None


def hex_of(rgb):
    return "#" + "".join(f"{max(0, min(255, round(c))):02X}" for c in rgb[:3])


# ── the builder ─────────────────────────────────────────────────────────
class _Builder:
    def __init__(self, cfg, analysis):
        self.cfg, self.a = cfg, analysis
        self.prov = Prov(analysis)
        self.tokens, self.gaps, self.notes, self.components = {}, [], [], {}
        self.C = cfg.get("color", {})

    # helpers
    def gap(self, name, ptr, why, part=None):
        g = {"name": name, "pointer": ptr, "gap": why}
        if part:
            g["part"] = part
        self.gaps.append(g)

    def note(self, ptr, msg):
        self.notes.append({"pointer": ptr, "note": msg})

    def add(self, name, value, typ, ptr, description="", prov=None, **extra):
        p = prov or self.prov.at(ptr)
        if p and p.get("conf") == "gap":
            self.gap(name, ptr, p.get("gap") or "gap")
            return
        tok = {"value": value, "type": typ, "description": description or "",
               "provenance": p, "json_pointer": ptr}
        tok.update({k: v for k, v in extra.items() if v not in (None, {}, [])})
        self.tokens[name] = tok

    def desc(self, node, *keys):
        if not isinstance(node, dict):
            return ""
        for k in keys or ("role", "use", "label", "rule", "$note"):
            v = node.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
        return ""

    def bare_color(self, v, ptr):
        """A bare role name where a reference belongs → its reference."""
        if isinstance(v, str) and not REF.match(v) and v in live(self.C.get("roles")):
            self.note(ptr, f"bare role name '{v}' read as {{color.{v}}} — write the reference")
            return "{color." + v + "}"
        if isinstance(v, dict) and "color" in v and "alpha" in v:
            # {color, alpha}: a translucent use of a token. DTCG has no alias
            # with alpha, so it resolves to the literal with the alpha applied.
            m = REF.match(str(v["color"]))
            role = m.group(1).split(".", 1)[1] if m and m.group(1).startswith("color.") else None
            node = (self.C.get("roles") or {}).get(role) if role and "." not in role else None
            hx = node.get("hex") if isinstance(node, dict) else None
            if not hx:
                self.note(ptr, f"{v['color']} with alpha could not be resolved")
                return None
            r, g, b = (int(hx[i:i + 2], 16) for i in (1, 3, 5))
            return f"rgba({r},{g},{b},{v['alpha']})"
        return v

    # colours
    def color(self, name, node, ptr, extra_desc=None):
        if isinstance(node, str):
            node = {"value": node}
            leaf = ptr
        else:
            leaf = None
        if not isinstance(node, dict):
            return
        if node.get("alias_of"):
            target = node["alias_of"]
            ref = target if REF.match(str(target)) else "{color." + str(target) + "}"
            hx = node.get("hex")
            ext = {k: node[k] for k in ("name", "token", "label", "framework", "hex") if k in node}
            self.add(name, ref, "color", f"{ptr}/hex" if hx else f"{ptr}/alias_of",
                     self.desc(node), alias=ref, extensions=ext)
            return
        raw, sub = (node.get("hex"), "hex") if "hex" in node else (node.get("value"), "value")
        p = leaf or f"{ptr}/{sub}"
        if raw is None:
            pr = self.prov.at(p)
            why = (pr or {}).get("gap") or node.get("$gap") or node.get("policy") or "no value"
            if (pr or {}).get("conf") == "gap" or node.get("$gap"):
                self.gap(name, p, why)
            return
        if isinstance(raw, str) and REF.match(raw):
            self.add(name, raw, "color", p, extra_desc or self.desc(node), alias=raw)
            return
        if parse_color(raw) is None:
            self.note(p, f"'{raw}' is not a colour literal or reference — not emitted")
            self.gap(name, p, f"unparseable colour '{raw}'")
            return
        ext = {k: node[k] for k in ("name", "token", "label", "framework", "derive",
                                     "component_name", "on", "rule") if k in node}
        self.add(name, raw, "color", p, extra_desc or self.desc(node), extensions=ext)

    def colors(self):
        C = self.C
        for k in live(C.get("roles")):
            self.color(f"color.{k}", C["roles"][k], f"/color/roles/{_esc(k)}")
        for k in live(C.get("states")):
            self.color(f"color.state.{k}", C["states"][k], f"/color/states/{_esc(k)}")
        for k in live(C.get("accents")):
            self.color(f"color.pillar.{k}", C["accents"][k], f"/color/accents/{_esc(k)}")
        for k in live(C.get("semantic")):
            v = C["semantic"][k]
            if isinstance(v, dict) and v.get("hex"):
                self.color(f"color.semantic.{k}", v, f"/color/semantic/{_esc(k)}")
            elif isinstance(v, dict) and (v.get("$gap") or (self.prov.at(f"/color/semantic/{k}/hex") or {}).get("conf") == "gap"):
                self.gap(f"color.semantic.{k}", f"/color/semantic/{_esc(k)}/hex",
                         v.get("$gap") or (self.prov.at(f"/color/semantic/{k}/hex") or {}).get("gap"))
        chart = (C.get("dataviz") or {}).get("chart") or {}
        for k in live(chart):
            self.color(f"color.dataviz.chart.{k}", chart[k], f"/color/dataviz/chart/{_esc(k)}")
        tints = C.get("tints") or {}
        for base in live(tints.get("stated")):
            for pct in live(tints["stated"][base]):
                self.color(f"color.tint.{base}.{pct}", tints["stated"][base][pct],
                           f"/color/tints/stated/{_esc(base)}/{_esc(pct)}",
                           extra_desc=tints.get("rule"))
        ret = C.get("retired") or {}
        why = ret.get("$comment") or "retired"
        for k in live(ret):
            v = ret[k]
            ptr = f"/color/retired/{_esc(k)}"
            if isinstance(v, dict) and v.get("retired_role_only"):
                self.note(ptr, "retired_role_only: a retired ROLE, not a retired colour — "
                               "no DTCG form; not emitted as a token")
                continue
            hx = v if isinstance(v, str) else (v or {}).get("hex")
            if not hx:
                continue
            p = ptr if isinstance(v, str) else f"{ptr}/hex"
            self.add(f"color.retired.{k}", hx, "color", p,
                     self.desc(v) if isinstance(v, dict) else "", deprecated=why)

    # shape, space, motion, breakpoints
    def scalars(self):
        cfg = self.cfg
        shape = cfg.get("shape", {})
        for k in ("surface", "control", "floating"):
            v = shape.get(k)
            if isinstance(v, (int, float)):
                self.add(f"radius.{k}", {"value": v, "unit": "px"}, "dimension", f"/shape/{k}")
            else:
                self.gap(f"radius.{k}", f"/shape/{k}", "no numeric radius")
        steps = cfg.get("layout", {}).get("spacing", {}).get("steps", {})
        uses = cfg.get("layout", {}).get("spacing", {}).get("uses", {})
        for k in live(steps):
            v = steps[k]
            if isinstance(v, dict):
                v = v.get("value")
            if isinstance(v, (int, float)):
                self.add(f"space.{k}", {"value": v, "unit": "px"}, "dimension",
                         f"/layout/spacing/steps/{_esc(k)}", uses.get(str(v), ""))
            else:
                self.gap(f"space.{k}", f"/layout/spacing/steps/{_esc(k)}", "no numeric step")
        M = cfg.get("motion", {})
        for k in live(M.get("durations_ms")):
            v = M["durations_ms"][k]
            self.add(f"motion.{k}", {"value": v, "unit": "ms"}, "duration",
                     f"/motion/durations_ms/{_esc(k)}")
        for k in live(M.get("easing")):
            v = M["easing"][k]
            ptr = f"/motion/easing/{_esc(k)}"
            pts = None
            if isinstance(v, list) and len(v) == 4:
                pts = [float(x) for x in v]
            elif isinstance(v, str):
                m = re.match(r"^cubic-bezier\(([^)]*)\)$", v.strip())
                if m:
                    pts = [float(x) for x in m.group(1).split(",")]
                elif v.strip() in CSS_EASE:
                    pts = CSS_EASE[v.strip()]
            if pts and len(pts) == 4:
                self.add(f"ease.{k}", [round(x, 6) for x in pts], "cubicBezier", ptr,
                         extensions={"css": v} if isinstance(v, str) else None)
            else:
                self.note(ptr, f"easing '{v}' is not a cubic-bezier — not representable")
                self.gap(f"ease.{k}", ptr, f"easing '{v}' not a cubic-bezier")
        bp = cfg.get("layout", {}).get("breakpoints", {})
        for k in bp.get("order", []):
            v = (bp.get("min") or {}).get(k)
            if isinstance(v, (int, float)):
                self.add(f"breakpoint.{k}", {"value": v, "unit": "px"}, "dimension",
                         f"/layout/breakpoints/min/{_esc(k)}", "lower bound (min-width)")

    def fonts(self):
        F = self.cfg.get("type", {}).get("families", {})
        for k in FONT_KEYS:
            f = F.get(k)
            if not isinstance(f, dict) or not f.get("family"):
                continue
            stack = [f["family"]] + [x.strip().strip("'\"") for x in
                                      str(f.get("fallback") or "").split(",") if x.strip()]
            w = f.get("weights")
            self.add(f"font.{k}", stack, "fontFamily", f"/type/families/{k}/family",
                     self.desc(f, "use"),
                     extensions={"weights": w} if w else None)

    # typography
    def typography(self):
        T = self.cfg.get("type", {})
        order = self.cfg.get("layout", {}).get("breakpoints", {}).get("order", [])
        bands = T.get("tracking", {}).get("bands", [])
        for i, r in enumerate(T.get("scale", {}).get("roles", [])):
            name, ptr = f"type.{r['role']}", f"/type/scale/roles/{i}"
            px = {k: v for k, v in (r.get("px") or {}).items()
                  if not str(k).startswith("$") and isinstance(v, (int, float))}
            if not px:
                self.gap(name, f"{ptr}/px", "no size at any breakpoint")
                continue
            default_bp = "desktop" if "desktop" in px else \
                next((b for b in reversed(order) if b in px), sorted(px)[0])
            fam = r.get("family")
            parts = {}
            val = {}
            if fam:
                val["fontFamily"] = "{font." + fam + "}"
                parts["fontFamily"] = f"{ptr}/family"
            if isinstance(r.get("weight"), (int, float)):
                val["fontWeight"] = r["weight"]
                parts["fontWeight"] = f"{ptr}/weight"
            val["fontSize"] = {"value": px[default_bp], "unit": "px"}
            parts["fontSize"] = f"{ptr}/px/{default_bp}"
            if isinstance(r.get("lh"), (int, float)):
                val["lineHeight"] = r["lh"]
                parts["lineHeight"] = f"{ptr}/lh"

            def track(size):
                if r.get("tracking") is not None:
                    return r["tracking"], f"{ptr}/tracking"
                cands = [(j, b) for j, b in enumerate(bands)
                         if b.get("family", "display") == fam and b.get("min_px", 0) <= size]
                if not cands:
                    return None, None
                j, b = max(cands, key=lambda x: x[1].get("min_px", 0))
                return b.get("value"), f"/type/tracking/bands/{j}/value"

            ls, lsp = track(px[default_bp])
            missing = []
            if ls is not None:
                val["letterSpacing"] = ls
                parts["letterSpacing"] = lsp
            else:
                missing.append("letterSpacing")
                self.gap(name, ptr, f"no tracking band for family '{fam}' and no "
                         f"role tracking", part="letterSpacing")
            for need in ("fontFamily", "fontWeight", "lineHeight"):
                if need not in val:
                    missing.append(need)
                    self.gap(name, ptr, f"role states no {need}", part=need)
            by_bp = {}
            for b in order:
                if b in px and b != default_bp:
                    t, tp = track(px[b])
                    by_bp[b] = {"fontSize": {"value": px[b], "unit": "px"}}
                    if t is not None:
                        by_bp[b]["letterSpacing"] = t
            fallback = {b: next((x for x in reversed(order[:order.index(b)]) if x in px), default_bp)
                        for b in order if b not in px}
            part_prov = {k: self.prov.at(p) for k, p in parts.items()}
            prov = weakest(part_prov.values())
            ext = {"breakpoints": by_bp, "fallback": fallback, "default_breakpoint": default_bp,
                   "parts": part_prov}
            for k in ("html", "case", "use"):
                if k in r:
                    ext[k] = r[k]
            if missing:
                ext["incomplete"] = missing
            self.add(name, val, "typography", ptr, r.get("use", ""), prov=prov, extensions=ext)

    # elevation
    def elevation(self):
        E = self.cfg.get("elevation", {})
        for k in live(E.get("levels")):
            lv, ptr = E["levels"][k], f"/elevation/levels/{_esc(k)}"
            if not isinstance(lv, dict):
                continue
            val, parts = {}, {}
            for slot in ("surface", "scrim"):
                v = lv.get(slot)
                if v is None:
                    continue
                v = self.bare_color(v, f"{ptr}/{slot}")
                val[slot] = v
                parts[slot] = self.prov.at(f"{ptr}/{slot}")
            b = lv.get("border")
            if isinstance(b, dict):
                bv = {"width": {"value": b.get("width"), "unit": "px"},
                      "color": self.bare_color(b.get("color"), f"{ptr}/border/color")}
                if b.get("style"):
                    bv["style"] = b["style"]
                val["border"] = bv
                parts["border"] = weakest([self.prov.at(f"{ptr}/border/width"),
                                           self.prov.at(f"{ptr}/border/color")])
            elif b is not None:
                val["border"] = b
                parts["border"] = self.prov.at(f"{ptr}/border")
            sh = lv.get("shadow")
            if sh is not None:
                val["shadow"] = sh
                parts["shadow"] = self.prov.at(f"{ptr}/shadow")
            self.add(f"elevation.{k}", val, "elevation", ptr, self.desc(lv, "use", "name"),
                     prov=weakest(parts.values()) or self.prov.at(ptr),
                     extensions={"name": lv.get("name"), "parts": parts})

    def comps(self):
        comps = self.cfg.get("components", {}) or {}
        for k in live(comps):
            self.components[f"component.{k}"] = {
                "value": comps[k], "json_pointer": f"/components/{_esc(k)}",
                "provenance": self.prov.at(f"/components/{_esc(k)}")}

    def build(self):
        self.colors()
        self.scalars()
        self.fonts()
        self.typography()
        self.elevation()
        self.comps()
        # every colour that is a reference must resolve; a broken alias is a gap
        tree = {"brand": self.cfg.get("brand"), "version": self.cfg.get("version"),
                "mode": self.cfg.get("mode"),
                "tokens": dict(self.tokens),            # config order: meaningful, and stable
                "components": dict(sorted(self.components.items())),
                "_gaps": sorted(self.gaps, key=lambda g: (g["name"], g.get("part", ""), g["pointer"])),
                "_notes": sorted(self.notes, key=lambda n: (n["pointer"], n["note"]))}
        for name, t in tree["tokens"].items():
            if t.get("alias") and resolve(t["alias"], tree) is None:
                tree["_notes"].append({"pointer": t["json_pointer"],
                                       "note": f"{name}: alias {t['alias']} does not resolve"})
        return tree


def build_tree(cfg, analysis):
    return _Builder(cfg, analysis).build()


def resolve(ref, tree, _seen=None):
    """'{color.accent}' → its literal value, following aliases. A non-reference
    string is returned unchanged; an unknown or circular reference is None.
    {component.x} returns the component's config node."""
    if not isinstance(ref, str):
        return ref
    m = REF.match(ref.strip())
    if not m:
        return ref
    name = m.group(1)
    seen = _seen or set()
    if name in seen:
        return None
    seen.add(name)
    if name in tree.get("components", {}):
        return tree["components"][name]["value"]
    t = tree["tokens"].get(name)
    if t is None:
        return None
    v = t["value"]
    if isinstance(v, str) and REF.match(v):
        return resolve(v, tree, seen)
    return v


def token_names(tree):
    """Token names plus gap names plus component names — what ref_targets() lists."""
    return set(tree["tokens"]) | {g["name"] for g in tree["_gaps"]} | set(tree["components"])


if __name__ == "__main__":
    import json, pathlib, sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import config
    cfg, _, a = config.load(sys.argv[1] if len(sys.argv) > 1 else None)
    t = build_tree(cfg, a)
    print(json.dumps({"tokens": len(t["tokens"]), "gaps": t["_gaps"], "notes": t["_notes"]},
                     indent=1, ensure_ascii=False))
