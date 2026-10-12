#!/usr/bin/env python3
"""The shared kit behind components.py and patterns.py — a library, not a step.

    from uikit import Ctx, Sheet, gates
    ctx = Ctx.load()                    # config + token tree
    ctx.color("{color.accent}")         # 'var(--color-accent)'
    ctx.border({"width": 1, "style": "solid", "color": "{color.border}"})

Every value a generated stylesheet carries goes through Ctx: a reference
becomes the custom property tokens_css.py emits for it, a keyword stays a
keyword, a number becomes px. Anything else is passed through UNCHANGED so
the literal gate below sees it and fails — a value is never quietly fixed.

Ctx also records which tokens each component binds (ctx.used), which config
references did not resolve (ctx.problems), and the copy keys a page uses.

The gates both generators run:
  literal_gate   no hex/rgb()/hsl()/oklch()/color() colour and no named font
                 family in any generated CSS or HTML (tokens.css is exempt:
                 it is the one place literals live)
  vars_gate      every var(--x) is defined in out/tokens/tokens.css
  check_gate     build/check.py (effects.policy, retired colours, banned
                 words, bare @media) on every output
  render_gate    build/render_gate.js — Playwright at 375/768/1280

Standard library only. Python 3.9+.
"""
import html, json, os, pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from config import load, ConfigError  # noqa: E402
from tree import build_tree, REF  # noqa: E402
from tokens_css import css_var  # noqa: E402

ROOT = HERE.parent
OUT = ROOT / "out"
LUCIDE = pathlib.Path(os.environ.get("LUCIDE_ICONS", "/home/claude/refs/lucide-icons_lucide/icons"))
KEYWORDS = {"none", "transparent", "currentColor", "currentcolor", "inherit", "underline", "initial"}
WIDTHS = (375, 768, 1280)


def esc(s):
    return html.escape(str(s), quote=True)


def px(n):
    return f"{float(n):g}px"


def live(d):
    return [k for k in (d or {}) if not str(k).startswith("$")] if isinstance(d, dict) else []


# ── a tiny stylesheet builder: deterministic output, one rule per selector ──
class Sheet:
    def __init__(self):
        self.blocks = []

    def rule(self, sel, decls):
        decls = [d for d in decls if d and d[1] not in (None, "")]
        if decls:
            body = "".join(f"  {p}: {v};\n" for p, v in decls)
            self.blocks.append(f"{sel} {{\n{body}}}")

    def media(self, query, inner):
        """inner: another Sheet."""
        if inner.blocks:
            body = "\n".join("  " + b.replace("\n", "\n  ") for b in inner.blocks)
            self.blocks.append(f"@media {query} {{\n{body}\n}}")

    def raw(self, text):
        self.blocks.append(text.strip())

    def extend(self, other):
        self.blocks += other.blocks

    def css(self):
        return "\n".join(self.blocks) + "\n"


# ── the context ──────────────────────────────────────────────────────────
class Ctx:
    def __init__(self, cfg, tree):
        self.cfg, self.t = cfg, tree
        self.tokens = tree["tokens"]
        # one-level colour roles with a literal value carry an immutable
        # --palette-* twin in tokens.css; [data-surface=ink] remaps the roles
        # but never the palette, so an absolute use points at the palette.
        self.palette = {n for n, tok in self.tokens.items()
                        if n.startswith("color.") and n.count(".") == 1
                        and not (isinstance(tok["value"], str) and REF.match(tok["value"]))}
        self.used, self.problems, self.copy_keys = set(), [], set()
        self.comps = {k: v for k, v in (cfg.get("components") or {}).items()
                      if not k.startswith("$")}
        M = cfg.get("motion") or {}
        hg = M.get("hover_gating")
        self.hover_q = (hg.get("value") if isinstance(hg, dict) else hg) or "(hover: hover)"
        self.mmap = M.get("map") or {}
        self.assign = M.get("assign") or {}
        self.policy = ((cfg.get("effects") or {}).get("policy")) or {}
        bp = (cfg.get("layout") or {}).get("breakpoints") or {}
        self.bp = {k: (bp.get("min") or {}).get(k) for k in bp.get("order", [])}
        self.target = (cfg.get("a11y") or {}).get("target_min_px", 44)
        ic = cfg.get("icons") or {}
        self.icon_stroke = ic.get("stroke") or (ic.get("library") or {}).get("stroke") or 2
        self.icon_map = ((ic.get("set") or {}).get("map")) or {}
        self.icon_mirror = {i["name"] for i in ((ic.get("ui_set") or {}).get("list") or [])
                            if isinstance(i, dict) and i.get("mirror")}
        self.icon_missing = set()
        self.copy = cfg.get("copy") or {}
        self._symbols = {}
        # the page language: "en" renders the bilingual fixture form (EN text,
        # data-fr twins); any other locale renders that locale's strings only
        self.lang = "en"
        self.fallbacks = set()   # keys a non-EN page had to take from EN
        self.links = {}          # page name → href, set by patterns.py

    @classmethod
    def load(cls, path=None, strict=True):
        cfg, _, a = load(path, strict=strict)
        return cls(cfg, build_tree(cfg, a))

    # references ---------------------------------------------------------
    def has(self, name):
        return name in self.tokens

    def var(self, v, absolute=False):
        """A {reference} → var(--…). Non-references come back unchanged."""
        if not isinstance(v, str):
            return v
        m = REF.match(v.strip())
        if not m:
            return v
        name = m.group(1)
        if name.startswith("component."):
            return v
        if name not in self.tokens:
            self.problems.append(f"{v} does not resolve to a token (a gap, or not emitted)")
            return None
        self.used.add(name)
        if absolute and name in self.palette:
            return f"var({css_var(name).replace('--color-', '--palette-')})"
        return f"var({css_var(name)})"

    def color(self, v, absolute=False):
        if v is None:
            return None
        if isinstance(v, dict) and "color" in v and "alpha" in v:
            base = self.color(v["color"], absolute)
            if base is None:
                return None
            return f"color-mix(in srgb, {base} {float(v['alpha']) * 100:g}%, transparent)"
        if isinstance(v, str) and v.strip() in KEYWORDS:
            return "transparent" if v.strip() == "none" else v.strip()
        return self.var(v, absolute)

    def border(self, v, absolute=False):
        if v is None:
            return None
        if isinstance(v, str):
            return "none" if v.strip() == "none" else self.var(v, absolute)
        if isinstance(v, dict) and "width" in v:
            c = self.color(v.get("color", "currentColor"), absolute)
            return f"{px(v['width'])} {v.get('style', 'solid')} {c}"
        return str(v)

    def outline(self, v, absolute=False):
        if isinstance(v, dict) and "width" in v:
            out = [("outline", self.border(v, absolute))]
            if "offset" in v:
                out.append(("outline-offset", px(v["offset"])))
            return out
        if v == "none":
            return [("outline", "none")]
        return []

    def length(self, v):
        """{space.x}/{radius.x} → var; number → px; else unchanged."""
        if isinstance(v, (int, float)):
            return px(v)
        return self.var(v)

    def type_decls(self, ref):
        """{type.role} → the five declarations tokens.css splits it into."""
        if not isinstance(ref, str):
            return []
        m = REF.match(ref.strip())
        if not m or not m.group(1).startswith("type.") or m.group(1) not in self.tokens:
            if m:
                self.problems.append(f"{ref} is not a typography token")
            return []
        name = m.group(1)
        self.used.add(name)
        b = css_var(name)
        out = [("font-family", f"var({b}-family)"), ("font-size", f"var({b}-size)"),
               ("font-weight", f"var({b}-weight)"), ("line-height", f"var({b}-lh)"),
               ("letter-spacing", f"var({b}-tracking)")]
        case = (self.tokens[name].get("extensions") or {}).get("case")
        if case == "upper":
            out.append(("text-transform", "uppercase"))
        return out

    def elev_decls(self, ref):
        m = REF.match(str(ref or "").strip())
        if not m or m.group(1) not in self.tokens:
            if ref:
                self.problems.append(f"{ref} is not an elevation token")
            return []
        name = m.group(1)
        self.used.add(name)
        b = css_var(name)
        return [("background-color", f"var({b}-surface)"), ("border", f"var({b}-border)")]

    def scrim(self, ref):
        m = REF.match(str(ref or "").strip())
        if m and m.group(1) in self.tokens:
            self.used.add(m.group(1))
            return f"var({css_var(m.group(1))}-scrim)"
        return None

    def comp(self, name):
        if isinstance(name, str):
            m = REF.match(name.strip())
            if m and m.group(1).startswith("component."):
                name = m.group(1).split(".", 1)[1]
        return self.comps.get(name)

    # paint: the style slots every component shares ----------------------
    def paint(self, node, absolute=False, edge="inline-start", rule="block-end"):
        if not isinstance(node, dict):
            return []
        d = []
        for k, v in node.items():
            if k.startswith("$"):
                continue
            if k == "bg":
                d.append(("background-color", self.color(v, absolute)))
            elif k in ("fg", "color"):
                d.append(("color", self.color(v, absolute)))
            elif k == "border":
                d.append(("border", self.border(v, absolute)))
            elif k == "outline":
                d += self.outline(v, absolute)
            elif k == "edge":
                d.append((f"border-{edge}", self.border(v, absolute)))
            elif k == "rule":
                d.append((f"border-{rule}", self.border(v, absolute)))
            elif k == "decoration":
                d.append(("text-decoration-line", v))
            elif k == "cursor":
                d.append(("cursor", v))
            elif k == "weight":
                d.append(("font-weight", v))
            elif k == "radius":
                d.append(("border-radius", self.length(v)))
            elif k == "type":
                d += self.type_decls(v)
            elif k == "underline_offset_em":
                d.append(("text-underline-offset", f"{v:g}em"))
            elif k == "underline_thickness_px":
                d.append(("text-decoration-thickness", px(v)))
            elif k == "tracking":
                d.append(("letter-spacing", v))
            elif k == "size" and isinstance(v, (int, float)):
                d.append(("font-size", px(v)))
        return d

    def focus(self, which="ring", node=None):
        f = node if isinstance(node, dict) else (self.comp(node) if node else None) or self.comp("focus") or {}
        ring = f.get(which) or f.get("ring")
        if isinstance(ring, dict):
            return self.outline(ring, absolute=(which != "ring"))
        return [("outline", "2px solid var(--color-focus)"), ("outline-offset", "2px")]

    # motion ---------------------------------------------------------------
    PROPS = ("background-color", "border-color", "outline-color", "stroke-dashoffset",
             "color", "opacity", "transform")

    def _map_entry(self, key):
        for k, v in self.mmap.items():
            if k.startswith("$") or not isinstance(v, dict):
                continue
            if key in [x.strip() for x in k.split(",")]:
                if "same as" in v:
                    return self._map_entry(v["same as"])
                return v
        return None

    def transition(self, key, part=None, exclude=()):
        """motion.map[key] → a transition list. Never 'all'. 'instant' or
        'none' → none. Opacity rides --motion-opacity-* so reduced motion
        keeps it (tokens.css)."""
        e = self._map_entry(key)
        if e is None:
            a = self.assign.get("colour_opacity")
            if isinstance(a, list) and len(a) >= 2 and part is None:
                e = {"background-color, color, border-color": [a[0].strip("{}").split(".")[-1],
                                                               a[1].strip("{}").split(".")[-1]]}
            else:
                return None
        items = []
        for phrase, spec in e.items():
            if phrase.startswith("$") or not isinstance(spec, list) or not spec:
                continue
            if part and part not in phrase:
                continue
            if any(x in phrase for x in exclude):
                continue
            dur = spec[0]
            if dur in ("instant", "none"):
                continue
            props = [p for p in self.PROPS if re.search(rf"(?<![\w-]){re.escape(p)}(?![\w-])", phrase)]
            if "translate" in phrase or "scale" in phrase or "rotate" in phrase:
                props.append("transform")
            if "outline" == phrase.strip():
                props.append("outline-color")
            ease = spec[1] if len(spec) > 1 else "standard"
            for p in dict.fromkeys(props):
                dv = f"motion.{dur}"
                if dv not in self.tokens:
                    continue
                self.used.add(dv)
                ev = f"ease.{ease}"
                if ev in self.tokens:
                    self.used.add(ev)
                dvar = css_var(dv).replace("--motion-", "--motion-opacity-") if p == "opacity" else css_var(dv)
                items.append(f"{p} var({dvar}) var({css_var(ev)})" if ev in self.tokens
                             else f"{p} var({dvar})")
        return ", ".join(dict.fromkeys(items)) or None

    # state selectors --------------------------------------------------------
    def states(self, sheet, base, state, decls):
        """Write one state for a base selector, real pseudo-class and the
        forced twin the fixture uses. Hover is gated; forced hover is not."""
        decls = [d for d in decls if d and d[1] not in (None, "")]
        if not decls:
            return
        if self.policy.get("opacity_hover") is False and state == "hover":
            decls = [d for d in decls if d[0] != "opacity"]
        if self.policy.get("transform_on_press") is False and state == "active":
            decls = [d for d in decls if d[0] != "transform"]
        f = f'{base}[data-force~="{state}"]'
        if state == "hover":
            sheet.rule(f, decls)
            inner = Sheet()
            inner.rule(f"{base}:hover:not(:disabled):not([aria-disabled=\"true\"])", decls)
            sheet.media(f"{self.hover_q}", inner)
        elif state == "active":
            sheet.rule(f"{base}:active:not(:disabled), {f}", decls)
        elif state == "focus":
            sheet.rule(f"{base}:focus-visible, {f}", decls)
        elif state == "disabled":
            sheet.rule(f"{base}:disabled, {base}[aria-disabled=\"true\"]", decls)
        elif state == "selected":
            sheet.rule(f"{base}[aria-selected=\"true\"], {base}[aria-current]:not([aria-current=\"false\"]), "
                       f"{base}[aria-pressed=\"true\"], {f}", decls)
        elif state == "error":
            sheet.rule(f"{base}[aria-invalid=\"true\"], {f}", decls)
        elif state == "loading":
            sheet.rule(f"{base}[aria-busy=\"true\"], {f}", decls)
        else:
            sheet.rule(f, decls)

    def mq(self, bp):
        v = self.bp.get(bp)
        return f"screen and (min-width: {v}px)" if v else None

    # copy -------------------------------------------------------------------
    def _lookup(self, lang, key):
        if not key:
            return None
        node = self.copy.get(lang)
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        return node

    def s(self, key, default=None):
        """The string for a copy key in the page language (EN when the page
        language has none — recorded in ctx.fallbacks), or the default."""
        if self.lang != "en":
            v = self._lookup(self.lang, key)
            if isinstance(v, str):
                self.copy_keys.add(key)
                return v
        v = self._lookup("en", key)
        if isinstance(v, str):
            self.copy_keys.add(key)
            if self.lang != "en":
                self.fallbacks.add(key)
            return v
        return default

    def node(self, key):
        """A copy subtree (dict or list) in the page language, else EN."""
        v = self._lookup(self.lang, key) if self.lang != "en" else None
        if v is None:
            v = self._lookup("en", key)
            if v is not None and self.lang != "en":
                self.fallbacks.add(key)
        if v is not None:
            self.copy_keys.add(key)
        return v

    def ident(self, path, value):
        """Identity text (identity.*) for the page: copy.<lang>.identity.<path>
        when the config has it; otherwise the identity value, marked lang="en"
        on a non-EN page. → (escaped html, attrs)."""
        if self.lang != "en":
            v = self._lookup(self.lang, "identity." + path)
            if isinstance(v, str):
                return esc(v), ""
            if value:
                self.fallbacks.add("identity." + path)
                return esc(value), ' lang="en"'
        return esc(value or ""), ""

    def href(self, name, default="#"):
        return self.links.get(name, default)

    def factory(self, key):
        """The factory's own frame labels (never brand copy)."""
        d = FACTORY.get(key) or {}
        return d.get(self.lang) or d.get("en") or key

    def fr(self, key):
        v = self._lookup("fr", key)
        return v if isinstance(v, str) else None

    def tx(self, key, default=None, accent=False, fmt=None):
        """(inner_html, attrs) for a translatable text node."""
        if self.lang != "en":
            v = self.s(key, default)
            if v is None:
                return "", ""
            if fmt:
                v = v.format(**fmt)
            return (accent_html(v) if accent else esc(v)), ""
        en = self.s(key, default)
        if en is None:
            return "", ""
        fr = self.fr(key) if self._lookup("en", key) is not None else None
        if fmt:
            en = en.format(**fmt)
            fr = fr.format(**fmt) if fr else None
        h_en = accent_html(en) if accent else esc(en)
        if fr:
            h_fr = accent_html(fr) if accent else esc(fr)
            return h_en, f' data-en="{esc(h_en)}" data-fr="{esc(h_fr)}"'
        return h_en, ""

    def el(self, tag, key, default=None, cls=None, attrs="", accent=False, fmt=None):
        inner, a = self.tx(key, default, accent, fmt)
        c = f' class="{cls}"' if cls else ""
        return f"<{tag}{c}{attrs}{a}>{inner}</{tag}>"

    def aria(self, key, default=None, attr="aria-label", short="al"):
        en = self.s(key, default)
        if en is None:
            return ""
        if self.lang != "en":
            return f' {attr}="{esc(en)}"'
        fr = self.fr(key)
        out = f' {attr}="{esc(en)}"'
        if fr:
            out += f' data-en-{short}="{esc(en)}" data-fr-{short}="{esc(fr)}"'
        return out

    # icons ------------------------------------------------------------------
    def icon(self, name, size=16, cls=""):
        if not name or name == "none":
            return ""
        lucide = self.icon_map.get(name, name)
        body = None
        for p in (OUT / "assets" / "icons" / f"{name}.svg", OUT / "assets" / "icons" / f"{lucide}.svg",
                  LUCIDE / f"{lucide}.svg"):
            if p.exists():
                t = p.read_text(encoding="utf-8")
                m = re.search(r"<svg[^>]*>(.*)</svg>", t, re.S)
                if m:
                    body = re.sub(r"<!--.*?-->", "", m.group(1), flags=re.S)
                    body = re.sub(r"\s+", " ", body).strip()
                    break
        if body is None:
            self.icon_missing.add(name)
            return ""
        mir = " c-icon--mirror" if lucide in self.icon_mirror or name in self.icon_mirror else ""
        extra = f" {cls}" if cls else ""
        return (f'<svg class="c-icon{mir}{extra}" width="{size}" height="{size}" viewBox="0 0 24 24" '
                f'fill="none" stroke="currentColor" stroke-width="{self.icon_stroke:g}" '
                f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
                f'{body}</svg>')


# The factory's own labels for what the config does not hold: frames that
# say "this is not copy yet". Never brand copy, never styled as live copy.
FACTORY = {
    "content": {"en": "Content to come", "fr": "Contenu à venir"},
    "image": {"en": "Image to come", "fr": "Image à venir"},
    "screenshot": {"en": "Screenshot to come", "fr": "Capture d’écran à venir"},
}


def accent_html(text):
    """One accent word: the last word of the heading, punctuation kept outside."""
    m = re.match(r"^(.*?)([\w’'\-À-ÿ]+)([^\w]*)$", text, re.S | re.U)
    if not m or not m.group(1).strip():
        return esc(text)
    return f'{esc(m.group(1))}<span class="c-accent">{esc(m.group(2))}</span>{esc(m.group(3))}'


# ── gates ────────────────────────────────────────────────────────────────
NAMED_COLOURS = ("aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue "
                 "blueviolet brown burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk "
                 "crimson cyan darkblue darkcyan darkgoldenrod darkgray darkgreen darkgrey darkkhaki "
                 "darkmagenta darkolivegreen darkorange darkorchid darkred darksalmon darkseagreen "
                 "darkslateblue darkslategray darkturquoise darkviolet deeppink deepskyblue dimgray "
                 "dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite gold goldenrod "
                 "gray green greenyellow grey honeydew hotpink indianred indigo ivory khaki lavender "
                 "lawngreen lemonchiffon lightblue lightcoral lightcyan lightgray lightgreen lightgrey "
                 "lightpink lightsalmon lightseagreen lightskyblue lightslategray lightsteelblue "
                 "lightyellow lime limegreen linen magenta maroon mediumblue mediumorchid mediumpurple "
                 "midnightblue mintcream mistyrose moccasin navajowhite navy oldlace olive olivedrab orange "
                 "orangered orchid palegreen paleturquoise palevioletred papayawhip peachpuff peru pink plum "
                 "powderblue purple rebeccapurple red rosybrown royalblue saddlebrown salmon sandybrown "
                 "seagreen seashell sienna silver skyblue slateblue slategray snow springgreen steelblue tan "
                 "teal thistle tomato turquoise violet wheat white whitesmoke yellow yellowgreen").split()
COLOUR_PROPS = r"(?:color|background(?:-color)?|border(?:-[a-z-]+)?|outline(?:-color)?|fill|stroke|stop-color|" \
               r"text-decoration(?:-color)?|caret-color|accent-color|column-rule(?:-color)?)"


def css_parts(path, text):
    """The CSS a file carries: all of a .css; <style> blocks, style="" and
    SVG paint attributes of an .html."""
    if str(path).endswith(".css"):
        return [text]
    parts = re.findall(r"<style[^>]*>(.*?)</style>", text, re.S | re.I)
    parts += re.findall(r'\sstyle="([^"]*)"', text)
    parts += [f"{a}: {v}" for a, v in re.findall(
        r'\s(fill|stroke|stop-color|color|flood-color|lighting-color)="([^"]*)"', text)]
    parts += [f"font-family: {v}" for v in re.findall(r'\sfont-family="([^"]*)"', text)]
    return parts


def literal_gate(paths):
    """→ list of 'file: problem'. tokens.css is never passed in."""
    bad = []
    named = "|".join(NAMED_COLOURS)
    for p in paths:
        text = pathlib.Path(p).read_text(encoding="utf-8")
        for css in css_parts(p, text):
            css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
            css = re.sub(r"url\([^)]*\)", "url()", css)
            for m in re.finditer(r"#[0-9A-Fa-f]{3,8}\b", css):
                bad.append(f"{pathlib.Path(p).name}: literal colour {m.group(0)}")
            for m in re.finditer(r"\b(rgba?|hsla?|oklch|oklab|lab|lch|hwb|color)\(", css):
                bad.append(f"{pathlib.Path(p).name}: literal colour {m.group(1)}()")
            for m in re.finditer(rf"(?<![\w-]){COLOUR_PROPS}\s*:\s*([^;{{}}]*)", css):
                for w in re.findall(r"[a-zA-Z]+", re.sub(r"var\([^)]*\)", "", m.group(1))):
                    if w.lower() in NAMED_COLOURS:
                        bad.append(f"{pathlib.Path(p).name}: named colour '{w}'")
            for m in re.finditer(r"(?<![\w-])font-family\s*:\s*([^;{}]*)", css):
                v = m.group(1).strip()
                if v and not re.fullmatch(r"(var\(--[\w-]+\)|inherit)", v):
                    bad.append(f"{pathlib.Path(p).name}: literal font family '{v}'")
            for m in re.finditer(r"(?<![\w-])font\s*:\s*([^;{}]*)", css):
                if m.group(1).strip() not in ("inherit",):
                    bad.append(f"{pathlib.Path(p).name}: font shorthand '{m.group(1).strip()}'")
    return list(dict.fromkeys(bad))


def vars_gate(paths, tokens_css=None):
    tokens_css = tokens_css or (OUT / "tokens" / "tokens.css")
    defined = set(re.findall(r"(--[\w-]+)\s*:", tokens_css.read_text(encoding="utf-8")))
    bad = []
    for p in paths:
        used = set(re.findall(r"var\((--[\w-]+)", pathlib.Path(p).read_text(encoding="utf-8")))
        for v in sorted(used - defined):
            bad.append(f"{pathlib.Path(p).name}: var({v}) is not defined in tokens.css")
    return bad


def check_gate(paths):
    """build/check.py on every file. → (failed: bool, output)."""
    r = subprocess.run([sys.executable, str(HERE / "check.py")] + [str(p) for p in paths],
                       cwd=ROOT, capture_output=True, text=True)
    return r.returncode != 0, (r.stdout + r.stderr)


def render_gate(files, cfg, shots_prefix=None):
    """node build/render_gate.js. → (ok, output). Skipped (ok, note) only
    when BRAND_SKIP_RENDER=1 — used by the unit tests, never by all.py."""
    if os.environ.get("BRAND_SKIP_RENDER") == "1":
        return True, "render gate skipped (BRAND_SKIP_RENDER=1)"
    a11y = cfg.get("a11y") or {}
    floors = a11y.get("floors") or {}
    spec = {
        "root": str(ROOT), "widths": list(WIDTHS),
        "files": [f if isinstance(f, dict) else {"path": str(f[0]), "shot": f[1]} for f in files],
        "shadow": ((cfg.get("effects") or {}).get("policy") or {}).get("shadow", "none"),
        "target": a11y.get("target_min_px", 44),
        "body": floors.get("body_text", 4.5), "large": floors.get("large_text", 3.0),
        "families": [f["family"] for k, f in ((cfg.get("type") or {}).get("families") or {}).items()
                     if k in ("display", "text", "mono") and isinstance(f, dict) and f.get("family")],
    }
    r = subprocess.run(["node", str(HERE / "render_gate.js"), json.dumps(spec)], cwd=ROOT,
                       capture_output=True, text=True, timeout=3000)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def page(title, body, css_links, lang="en", extra_head="", script="", scripts=()):
    links = "".join(f'<link rel="stylesheet" href="{h}">\n' for h in css_links)
    ext = "".join(f'<script src="{esc(s)}" defer></script>\n' for s in scripts)
    return (f'<!doctype html>\n<html lang="{lang}" dir="ltr">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f"<title>{esc(title)}</title>\n{links}{extra_head}{ext}</head>\n<body>\n{body}\n"
            + (f"<script>\n{script}\n</script>\n" if script else "") + "</body>\n</html>\n")


TOGGLE_JS = """(function () {
  var d = document.documentElement;
  function swap(l) {
    d.lang = l;
    document.querySelectorAll('[data-' + l + ']').forEach(function (e) {
      e.innerHTML = e.getAttribute('data-' + l);
    });
    [['al', 'aria-label'], ['ph', 'placeholder']].forEach(function (p) {
      document.querySelectorAll('[data-' + l + '-' + p[0] + ']').forEach(function (e) {
        e.setAttribute(p[1], e.getAttribute('data-' + l + '-' + p[0]));
      });
    });
    document.querySelectorAll('[data-lang-btn]').forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.getAttribute('data-lang-btn') === l));
    });
  }
  document.querySelectorAll('[data-lang-btn]').forEach(function (b) {
    b.addEventListener('click', function () { swap(b.getAttribute('data-lang-btn')); });
  });
  document.querySelectorAll('[data-dir-btn]').forEach(function (b) {
    b.addEventListener('click', function () {
      var rtl = d.dir !== 'rtl';
      d.dir = rtl ? 'rtl' : 'ltr';
      b.setAttribute('aria-pressed', String(rtl));
    });
  });
})();"""


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
