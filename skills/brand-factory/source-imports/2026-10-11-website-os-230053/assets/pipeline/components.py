#!/usr/bin/env python3
"""The brand's interface, made visible: every component in every state.

    python3 build/components.py

Writes
  out/components.css            one class family per config component (.c-*)
  out/components.html           the fixture: every component, every state the
                                config names, side by side, forced states
                                labelled with their token bindings
  out/components.manifest.json  per component: group, states, classes, tokens,
                                $src, and the 3.4 proposal id where one links
  out/shots/components-<w>.png  the render gate's screenshots

Every paint value comes from the config through uikit.Ctx, so it is a
var(--…) from tokens.css, a keyword or a composite of those. Lengths are
tokens, or px where the config itself holds the number. A component the
config does not have is not rendered; a component this file has no renderer
for is listed, with its slots, and reported.

Gates (exit 1 on any): literal values, undefined var(), build/check.py,
the Playwright render gate. Standard library only (node for the render).
"""
import json, re, sys
from uikit import (Ctx, Sheet, OUT, ROOT, esc, px, live, accent_html, literal_gate, vars_gate,
                   check_gate, render_gate, page, TOGGLE_JS, write, ConfigError, REF)

GROUPS = ["Actions", "Inputs", "Navigation", "Content", "Feedback", "Overlays", "Data", "Platform"]
STATE_ORDER = ["rest", "hover", "active", "focus", "selected", "disabled", "loading", "error", "empty"]
EXTRA_STATES = ["open", "dragover", "success", "blocked", "omitted", "done", "todo", "external"]
SYNONYM = {"current": "selected", "on": "selected", "checked": "selected", "pressed": "active", "uploading": "loading",
           "sending": "loading", "saving": "loading", "scrolled": "rest", "closed": "rest", "today": "selected",
           "range": "selected", "outside": "disabled", "sort": "rest", "trigger": "rest"}
R = {}

# The quadrant's example set comes from the config (patterns.quadrant.examples);
# without one, neutral labels ("Use case A"…) at illustrative positions.


def comp(name, group):
    def deco(fn):
        R[name] = (group, fn)
        return fn
    return deco


class Out:
    def __init__(self, ctx, name):
        self.ctx, self.name, self.css, self.specs, self.states, self.notes = ctx, name, Sheet(), [], [], []

    def spec(self, state, html, bind="", wide=False, ink=False, frame=None):
        words = [w.strip().lower() for w in re.split(r"·", state)]
        got = [SYNONYM.get(w, w.split(" ")[0]) for w in words]
        got = [g for g in got if g in STATE_ORDER or g in EXTRA_STATES] or [words[0].split(" ")[0]]
        self.states += got
        self.specs.append((state, html, bind, wide, ink, frame))


def bind(node, keys=None):
    """'bg color.accent · fg color.accent_on' from a config node."""
    if isinstance(node, str):
        return node.replace("{", "").replace("}", "")
    if not isinstance(node, dict):
        return ""
    out = []
    for k, v in node.items():
        if k.startswith("$") or (keys and k not in keys):
            continue
        if isinstance(v, str) and (REF.match(v) or v in ("none", "transparent", "underline")):
            out.append(f"{k} {v.strip('{}')}")
        elif isinstance(v, dict) and "width" in v and "color" in v:
            out.append(f"{k} {v['width']:g} {v.get('style', 'solid')} {str(v['color']).strip('{}')}")
        elif isinstance(v, dict) and "alpha" in v:
            out.append(f"{k} {str(v['color']).strip('{}')}@{v['alpha']:g}")
        elif isinstance(v, (int, float)) and not isinstance(v, bool) and k in ("height", "pad_x", "size", "width"):
            out.append(f"{k} {v:g}px")
    return " · ".join(out)


def resolve_path(cfg, p):
    """'voice.naming.platform_stages' → the node, list unwrapped."""
    node = cfg
    for part in str(p).split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    if isinstance(node, dict) and "list" in node:
        return node["list"]
    return node


def uid(ctx, prefix):
    ctx._n = getattr(ctx, "_n", 0) + 1
    return f"{prefix}-{ctx._n}"


# ── shared markup the patterns reuse ─────────────────────────────────────
def btn(ctx, variant, text, key=None, icon=None, href=None, attrs="", cls="", icon_end=False,
        size=None):
    inner, a = ctx.tx(key, text) if key else (esc(text), "")
    ic = ctx.icon(icon, 20) if icon and not icon_end else ""
    tail = ""
    if variant == "tertiary" or icon_end:
        arrow = ctx.icon(icon or "arrow-right", 16)
        tail = f'<span class="c-button__arrow">{arrow}</span>' if arrow else ""
        ic = ""
    c = f"c-button c-button--{variant}{' ' + cls if cls else ''}"
    lbl = f'<span class="c-button__label"{a}>{inner}</span>'
    if href is not None:
        return f'<a class="{c}" href="{esc(href)}"{attrs}>{ic}{lbl}{tail}</a>'
    return f'<button class="{c}" type="button"{attrs}>{ic}{lbl}{tail}</button>'


def mark_svg(ctx, size, label=None):
    """The brand mark as an inline symbol reference (defined once per page)."""
    if "mark" not in ctx._symbols:
        f = (ctx.cfg.get("logo") or {}).get("files") or {}
        p = (f.get("mark_vector") or {}).get("path")
        node = None
        if p and (ROOT / p).exists():
            t = (ROOT / p).read_text(encoding="utf-8")
            m = re.search(r"<svg([^>]*)>(.*)</svg>", t, re.S)
            vb = re.search(r'viewBox="([^"]+)"', m.group(1)) if m else None
            if m and vb and not re.search(r'fill="#|stroke="#', t):
                node = (vb.group(1), re.sub(r"\s+", " ", m.group(2)))
        ctx._symbols["mark"] = node
    node = ctx._symbols["mark"]
    if not node:
        return ""
    lab = f' role="img" aria-label="{esc(label)}"' if label else ' aria-hidden="true"'
    return (f'<svg class="c-mark" width="{size}" height="{size}" viewBox="{node[0]}"{lab}>'
            f'<use href="#brand-mark"></use></svg>')


def mark_symbol(ctx):
    node = ctx._symbols.get("mark")
    if not node:
        return ""
    return (f'<svg width="0" height="0" class="c-sr" aria-hidden="true"><symbol id="brand-mark" '
            f'viewBox="{node[0]}">{node[1]}</symbol></svg>')


def pillars(ctx):
    acc = (ctx.cfg.get("color") or {}).get("accents") or {}
    out = []
    for k in live(acc):
        n = acc[k]
        if isinstance(n, dict) and n.get("label") and ctx.has(f"color.pillar.{k}"):
            out.append({"key": k, "label": n["label"], "framework": n.get("framework"),
                        "subtitle": n.get("subtitle")})
    return out


def pillar_subtitle(ctx, p, tag="p", cls="c-hero__sub"):
    """A pillar whose config carries a subtitle shows it wherever its name
    is a heading (brand rule: the subtitle travels with the name)."""
    if not p.get("subtitle"):
        return ""
    h, a = ctx.tx("pillars.build_subtitle", p["subtitle"])
    return f'<{tag} class="{cls}"{a}>{h}</{tag}>'


def stages(ctx):
    for name in ("stepper", "stage_strip"):
        n = ctx.comp(name)
        if n and isinstance(n.get("stages"), str):
            v = resolve_path(ctx.cfg, n["stages"])
            if isinstance(v, list):
                return v
    return []


def examples(ctx):
    q = ((ctx.cfg.get("patterns") or {}).get("quadrant") or {})
    ex = q.get("examples")
    if isinstance(ex, list) and ex:
        note = q.get("$note_examples") or "Illustrative positions (patterns.quadrant.examples)"
        return [(e["name"], e["readiness"], e["impact"], e.get("score", e["impact"])) for e in ex], note
    return [(f"Use case {c}", r, i, i) for c, r, i in (("A", 80, 80), ("B", 58, 70), ("C", 30, 50),
                                                        ("D", 70, 35))], "Illustrative positions"


def zone(ctx, r, i):
    q = ((ctx.cfg.get("patterns") or {}).get("quadrant") or {})
    c, L = q.get("cuts") or {}, q.get("labels") or {}
    f, s, imp = c.get("readiness_foundations", 50), c.get("readiness_start", 65), c.get("impact", 60)
    if r < f:
        k = "foundational-rebuilds"
    elif i < imp:
        k = "tactical-improvements"
    elif r < s:
        k = "strategic-projects"
    else:
        k = "quick-wins"
    return k, L.get(k, k)


def quadrant_html(ctx, authored=False, selected=None, blocked=None, loading=False, empty=False, cap=True, static=False):
    """The quadrant: SVG axes and the engine's partition, HTML dots that are
    buttons. Never mirrors (dir=ltr on the chart)."""
    q = ((ctx.cfg.get("patterns") or {}).get("quadrant") or {})
    c = q.get("cuts") or {}
    f, s, imp = c.get("readiness_foundations", 50), c.get("readiness_start", 65), c.get("impact", 60)
    data, note = examples(ctx)
    X = lambda r: r  # noqa: E731  viewBox 0..100
    Y = lambda i: 100 - i  # noqa: E731
    seg = [(X(f), 0, X(f), 100), (X(f), Y(imp), 100, Y(imp)), (X(s), Y(imp), X(s), 0)]
    lines = "".join(f'<line class="c-quad__cut" data-seg="{n + 1}" x1="{a:g}" y1="{b:g}" x2="{c2:g}" y2="{d:g}" '
                    f'vector-effect="non-scaling-stroke"></line>' for n, (a, b, c2, d) in enumerate(seg))
    axes = ('<line class="c-quad__axis" x1="0" y1="100" x2="0" y2="0" vector-effect="non-scaling-stroke"></line>'
            '<line class="c-quad__axis" x1="0" y1="100" x2="100" y2="100" vector-effect="non-scaling-stroke"></line>')
    zl = []
    pos = {"foundational-rebuilds": ("start", "top"), "strategic-projects": ("mid", "top"),
           "quick-wins": ("end", "top"), "tactical-improvements": ("end", "bottom")}
    for n, k in enumerate(("foundational-rebuilds", "tactical-improvements", "strategic-projects", "quick-wins")):
        h, a = ctx.tx(f"platform.quadrant.zones.{k}", (q.get("labels") or {}).get(k, k))
        x, yv = pos[k]
        zl.append(f'<span class="c-quad__zone c-quad__zone--{x}-{yv}" data-z="{n}"{a}>{h}</span>')
    dots = []
    if not loading and not empty:
        for n, (name, r, i, sc) in enumerate(sorted(data, key=lambda d: -d[3])):
            sel = ' aria-pressed="true"' if selected == name else ' aria-pressed="false"'
            bl = " c-quad__dot--blocked" if blocked == name else ""
            open_lbl = ctx.s("platform.quadrant.open", "Open {name}").format(name=name)
            fl = " c-quad__dot--end" if r > 60 else ""
            if static:
                # a marketing page: the chart shows, it does not open anything
                dots.append(f'<span class="c-quad__dot{bl}{fl}" data-d="{n}" '
                            f'style="inset-inline-start: {r:g}%; inset-block-end: {i:g}%">'
                            f'<span class="c-quad__label"><span class="c-quad__name">{esc(name)}</span> '
                            f'<span class="c-quad__score">{sc}</span></span></span>')
                continue
            dots.append(f'<button class="c-quad__dot{bl}{fl}" type="button" data-d="{n}" '
                        f'style="inset-inline-start: {r:g}%; inset-block-end: {i:g}%"{sel} '
                        f'aria-label="{esc(open_lbl)} · {sc}"><span class="c-quad__label"><span class="c-quad__name">{esc(name)}</span> '
                        f'<span class="c-quad__score">{sc}</span></span></button>')
    xh, xa = ctx.tx("platform.quadrant.x", (q.get("axes") or {}).get("x", "readiness"))
    yh, ya = ctx.tx("platform.quadrant.y", (q.get("axes") or {}).get("y", "impact"))
    emp = ""
    if empty:
        emp = (f'<div class="c-quad__empty">{ctx.el("p", "platform.empty.dashboard.title", "", "c-quad__empty-title")}'
               f'{btn(ctx, "primary", "Map a use case", "platform.empty.dashboard.action")}</div>')
    au = ' data-authored="quadrant"' if authored else ""
    busy = ' aria-busy="true"' if loading else ""
    # the caption is the brand's caption (copy.<lang>.offer.quadrant_caption),
    # never the factory's provenance note on the example set
    capt = offer(ctx, "quadrant_caption")
    caption = f'<p class="c-quad__note">{esc(capt)}</p>' if cap and capt and not empty and not loading else ""
    return (f'<figure class="c-quad"{au}{busy}><div class="c-quad__plot" dir="ltr">'
            f'<svg class="c-quad__svg" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">{axes}{lines}</svg>'
            f'{"".join(zl)}{"".join(dots)}{emp}</div>'
            f'<span class="c-quad__axis-title c-quad__axis-title--x"{xa}>{xh}</span>'
            f'<span class="c-quad__axis-title c-quad__axis-title--y"{ya}>{yh}</span>'
            f'{caption}</figure>')


def score_list(ctx, rows=None, static=False):
    """The ranked list beside (or, on a phone, instead of) the quadrant. A
    name too long for its column ends in an ellipsis; the full name is in title."""
    data, _ = examples(ctx)
    items = []
    for name, r, i, sc in sorted(data, key=lambda d: -d[3]):
        k, lab = zone(ctx, r, i)
        zh, za = ctx.tx(f"platform.quadrant.zones.{k}", lab)
        nm = (f'<span class="c-scorelist__name" title="{esc(name)}">{esc(name)}</span>' if static else
              f'<a class="c-scorelist__name c-hit" href="#" title="{esc(name)}">{esc(name)}</a>')
        items.append(f'<li class="c-scorelist__row">{nm}'
                     f'<span class="c-scorelist__zone"{za}>{zh}</span><span class="c-scorelist__score">{sc}</span></li>')
    return f'<ol class="c-scorelist">{"".join(items[:rows] if rows else items)}</ol>'


_LANG = {"ctx": None}


def slot(label, words=None, tag="p", cls="", brief=None):
    """Content the config does not hold: a labelled frame that says so —
    "Content to come · <what>" — never invented, never styled as live copy.
    The factory's description of the slot rides in data-brief (an attribute,
    not page text)."""
    ctx = _LANG["ctx"]
    head = ctx.factory("content") if ctx else "Content to come"
    w = f" · ≤{words}" if words else ""
    b = f' data-brief="{esc(brief)}"' if brief else ""
    tag = "div" if tag == "p" else tag
    return (f'<{tag} class="c-slot{" " + cls if cls else ""}" data-contrast="exempt"{b}>'
            f'<span class="c-slot__label">{esc(head)}{" · " + esc(label) if label else ""}{esc(w)}</span></{tag}>')


def frame(label, ratio="16 / 9", cls="", kind="image", brief=None):
    """An image the brand has not supplied: a labelled frame, never a stand-in."""
    ctx = _LANG["ctx"]
    head = ctx.factory(kind) if ctx else "Image to come"
    text = f"{head} · {label}" if label else head
    b = f' data-brief="{esc(brief)}"' if brief else ""
    return (f'<div class="c-frame{" " + cls if cls else ""}" style="aspect-ratio: {ratio}" role="img" '
            f'aria-label="{esc(text)}"{b}><span class="c-frame__label">{esc(text)}</span></div>')


# ── base ─────────────────────────────────────────────────────────────────
def base_css(ctx):
    S = Sheet()
    S.raw("/* base: the reset every generated page shares */")
    S.rule("*, *::before, *::after", [("box-sizing", "border-box")])
    body = [("margin", "0"), ("background-color", "var(--color-bg)"), ("color", "var(--color-fg)")]
    body += ctx.type_decls("{type.body}") or [("font-family", "var(--font-text)")]
    body += [("font-synthesis", "none"), ("-webkit-font-smoothing", "antialiased"),
             ("text-rendering", "optimizeLegibility")]
    S.rule("body", body)
    S.rule("h1, h2, h3, h4, h5, h6, p, ul, ol, li, figure, figcaption, blockquote, dl, dd, fieldset, legend",
           [("margin", "0"), ("padding", "0")])
    S.rule("ul, ol", [("list-style", "none")])
    S.rule("button, input, select, textarea", [("font", "inherit"), ("color", "inherit"), ("letter-spacing", "inherit")])
    S.rule("button", [("background-color", "transparent"), ("border", "0"), ("padding", "0"), ("cursor", "pointer")])
    S.rule("a", [("color", "inherit")])
    S.rule("img, svg", [("display", "block")])
    S.rule(".c-icon", [("display", "inline-block"), ("flex", "none"), ("vertical-align", "middle")])
    S.rule('[dir="rtl"] .c-icon--mirror', [("transform", "scaleX(-1)")])
    S.rule(".c-mark", [("color", ctx.color("{color.accent}")), ("flex", "none")])
    acc = (((ctx.cfg.get("type") or {}).get("families") or {}).get("display") or {}).get("accent_weight")
    S.rule(".c-accent", [("color", "var(--color-accent-text)"), ("font-weight", acc)])
    S.rule(".c-sr", [("position", "absolute"), ("inline-size", "1px"), ("block-size", "1px"), ("overflow", "hidden"),
                     ("clip-path", "inset(50%)"), ("white-space", "nowrap"), ("margin", "-1px"), ("padding", "0"),
                     ("border", "0")])
    # the hit-area extension: a control drawn under the target size keeps a
    # target-size hit area (a11y.target_min_px) — the dense-row exception
    S.rule(".c-hit", [("position", "relative")])
    S.rule(".c-hit::after", [("content", '""'), ("position", "absolute"),
                             ("inset-block", "min(0px, calc(50% - var(--target-min) / 2))"),
                             ("inset-inline", "min(0px, calc(50% - var(--target-min) / 2))")])
    S.rule(".p-container", [("inline-size", "100%"), ("max-inline-size", "var(--container-max)"), ("margin-inline", "auto"),
                            ("padding-inline", "var(--grid-phone-margin)")])
    for bp in ("tablet", "desktop"):
        m = ctx.mq(bp)
        if m:
            i = Sheet()
            i.rule(".p-container", [("padding-inline", f"var(--grid-{bp}-margin)")])
            S.media(m, i)
    sp = (ctx.cfg.get("motion") or {}).get("spinner") or {}
    S.raw("@keyframes c-spin { to { transform: rotate(1turn); } }")
    S.rule(".c-spinner", [("animation", f"c-spin {sp.get('period_ms', 800)}ms {sp.get('easing', 'linear')} infinite")])
    S.raw("@keyframes c-pulse { 50% { opacity: 0.5; } }")
    # copy slots and image frames: what the config does not hold, labelled
    dash = ctx.border({"width": 1, "style": "dashed", "color": "{color.border_input}"}) if ctx.has("color.border_input") else "1px dashed currentColor"
    S.rule(".c-slot", [("display", "flex"), ("align-items", "center"), ("border", dash), ("min-block-size", "var(--target-min)"),
                       ("padding", "var(--space-sp-2) var(--space-sp-3)"), ("color", ctx.color("{color.muted}")),
                       ("background-color", ctx.color("{color.surface}"))])
    S.rule(".c-slot__label", ctx.type_decls("{type.eyebrow}") + [("font-size", "var(--density-dense-label)"), ("letter-spacing", "0.08em")])
    S.rule(".c-frame", [("position", "relative"), ("display", "flex"), ("align-items", "flex-end"),
                        ("background-color", ctx.color("{color.surface}")), ("inline-size", "100%"),
                        ("border", ctx.border({"width": 1, "style": "solid", "color": "{color.border}"})),
                        ("padding", "var(--space-sp-3)")])
    S.rule(".c-frame__label", ctx.type_decls("{type.eyebrow}") + [("color", ctx.color("{color.muted}"))])
    S.rule(".c-check__text", ctx.type_decls("{type.caption}"))
    return S


# ── Actions ──────────────────────────────────────────────────────────────
@comp("button", "Actions")
def c_button(ctx, n, o):
    S = o.css
    sizes = n.get("sizes") or {}
    md = sizes.get("md") or next((sizes[k] for k in live(sizes)), {})
    gap = ((ctx.cfg.get("icons") or {}).get("pairing") or {}).get("gap_px")
    base = [("display", "inline-flex"), ("align-items", "center"), ("justify-content", "center"),
            ("gap", px(gap) if gap else "var(--space-sp-1)"),
            ("min-block-size", px(md["height"]) if md.get("height") else "var(--target-min)"),
            ("min-inline-size", "var(--target-min)"),
            ("padding-inline", px(md["pad_x"]) if "pad_x" in md else "var(--space-sp-4)"),
            ("padding-block", "0"),
            ("border-radius", ctx.length(n.get("radius", "{radius.control}"))),
            ("text-decoration-line", "none"), ("white-space", "nowrap"), ("cursor", "pointer"),
            ("touch-action", n.get("touch_action")), ("transition", ctx.transition("button"))]
    S.rule(".c-button", base + ctx.type_decls(n.get("type")))
    for k in live(sizes):
        if k != "md":
            S.rule(f".c-button--{k}", [("min-block-size", px(sizes[k].get("height"))) if sizes[k].get("height") else None,
                                       ("padding-inline", px(sizes[k]["pad_x"])) if "pad_x" in sizes[k] else None])
    var = n.get("variants") or {}
    for v in live(var):
        node = var[v]
        absolute = "on_dark" in v
        sel = f".c-button--{v}"
        rest = node.get("rest") or {}
        S.rule(sel, ctx.paint(rest, absolute) + ([("padding-inline", px(rest["pad_x"]))] if "pad_x" in rest else []))
        for st in ("hover", "active", "disabled"):
            if isinstance(node.get(st), dict):
                nd = node[st]
                if st == "active" and nd == node.get("hover"):
                    # active = hover in the config: use a stated <x>_active state
                    # when the token tree has one; otherwise record the gap
                    alt = {k: (str(x).replace("_hover}", "_active}") if isinstance(x, str) else x) for k, x in nd.items()}
                    refs = [str(x).strip("{}") for x in alt.values() if isinstance(x, str) and x.startswith("{")]
                    if alt != nd and all(ctx.has(r) for r in refs):
                        nd = alt
                    else:
                        o.notes.append(f"GAP: {v} active equals {v} hover in the config — no distinct pressed state "
                                       f"(add color.states.<x>_active to the config)")
                ctx.states(S, sel, st, ctx.paint(nd, absolute))
        hv = node.get("hover") or {}
        if hv.get("arrow_shift_px"):
            sh = px(hv["arrow_shift_px"])
            S.rule(f"{sel} .c-button__arrow", [("display", "inline-flex"),
                                               ("transition", ctx.transition("button_tertiary_arrow"))])
            S.rule(f'{sel}[data-force~="hover"] .c-button__arrow', [("transform", f"translateX({sh})")])
            S.rule(f'[dir="rtl"] {sel}[data-force~="hover"] .c-button__arrow', [("transform", f"translateX(-{sh})")])
            inner = Sheet()
            inner.rule(f"{sel}:hover .c-button__arrow", [("transform", f"translateX({sh})")])
            inner.rule(f'[dir="rtl"] {sel}:hover .c-button__arrow', [("transform", f"translateX(-{sh})")])
            S.media(ctx.hover_q, inner)
    S.rule('.c-button:disabled, .c-button[aria-disabled="true"]', [("cursor", "not-allowed")])
    # loading: the label stays, the spinner joins it, the width does not move
    # the spinner's slot is held at rest (visibility, not display), so the
    # width never moves when it appears — "the spinner replaces nothing" (p76)
    S.rule(".c-button .c-spinner", [("visibility", "hidden")])
    S.rule('.c-button[aria-busy="true"]', [("cursor", "progress")])
    S.rule('.c-button[aria-busy="true"] .c-spinner', [("visibility", "visible")])
    S.rule(".c-button__stack", [("display", "inline-grid")])
    S.rule(".c-button__stack > *", [("grid-area", "1 / 1")])
    S.rule(".c-button__busy", [("visibility", "hidden")])
    S.rule('.c-button[aria-busy="true"] .c-button__busy', [("visibility", "visible")])
    S.rule('.c-button[aria-busy="true"] .c-button__stack > .c-button__label', [("visibility", "hidden")])
    S.rule(".c-button__suffix", [("visibility", "hidden")])
    S.rule('.c-button[aria-busy="true"] .c-button__suffix', [("visibility", "visible")])
    suffix = n.get("loading_label_suffix", "…")
    states = [("rest", ""), ("hover", ' data-force="hover"'), ("active", ' data-force="active"'),
              ("focus", ' data-force="focus"'), ("disabled", " disabled"), ("loading", ' aria-busy="true"')]
    labels = {"primary": ("cta.primary", "Book a scoping call"), "secondary": ("cta.catalogue", "See the catalogue"),
              "tertiary": ("cta.read", "Read"), "secondary_on_dark": ("cta.catalogue", "See the catalogue")}
    for v in live(var):
        key, default = labels.get(v, (None, v.replace("_", " ").capitalize()))
        if v == "destructive":
            default = ctx.s("platform.confirm.discard", "Discard {n} components").format(n=8)
            key = None
        for st, attr in states:
            if st not in var[v] and st not in ("rest", "loading", "focus"):
                continue
            inner, a = ctx.tx(key, default) if key else (esc(default), "")
            spin = ctx.icon("loader-circle", 16, "c-spinner")
            tail = ""
            if v == "tertiary":
                tail = f'<span class="c-button__arrow">{ctx.icon((var[v].get("rest") or {}).get("icon", "arrow-right"), 16)}</span>'
            h = (f'<button class="c-button c-button--{v}" type="button"{attr}>{spin}'
                 f'<span><span class="c-button__label"{a}>{inner}</span><span class="c-button__suffix" aria-hidden="true">'
                 f'{esc(suffix)}</span></span>{tail}</button>')
            node = var[v].get(st) if st != "rest" else var[v].get("rest")
            b = bind(node) if isinstance(node, dict) else ("component.focus" if st == "focus" else
                                                          (n.get("loading") or {}).get("$note", "") if st == "loading" else "")
            o.spec(f"{st} · {v}", h, b, ink="on_dark" in v)


@comp("link", "Actions")
def c_link(ctx, n, o):
    S = o.css
    S.rule(".c-link", ctx.paint(n.get("rest") or {}) + [("transition", ctx.transition("link"))])
    for st in ("hover", "active"):
        ctx.states(S, ".c-link", st, ctx.paint(n.get(st) or {}))
    od = n.get("on_dark") or {}
    if od:
        S.rule('[data-surface="ink"] .c-link', ctx.paint(od, absolute=True))
    S.rule(".c-link--standalone", [("display", "inline-flex"), ("align-items", "center"), ("min-block-size", "var(--target-min)")])
    S.rule(".c-link__ext", [("display", "inline-block"), ("margin-inline-start", "var(--space-sp-1)"),
                            ("vertical-align", "-0.125em")])
    line = ctx.s("contact.faster", "Faster: book a scoping call.")
    pre, _, rest = line.partition(":")
    def sentence(attr=""):
        if rest:
            return (f'<p class="fx-prose">{esc(pre)}: <a class="c-link" href="#"{attr}>{esc(rest.strip().rstrip("."))}</a>.</p>')
        return f'<p class="fx-prose"><a class="c-link" href="#"{attr}>{esc(line)}</a></p>'
    o.spec("rest", sentence(), bind(n.get("rest")))
    o.spec("hover", sentence(' data-force="hover"'), bind(n.get("hover")))
    o.spec("active", sentence(' data-force="active"'), bind(n.get("active")))
    o.spec("focus", sentence(' data-force="focus"'), "component.focus")
    if od:
        o.spec("rest · on dark", sentence(), bind(od), ink=True)
    ext = n.get("external") or {}
    if ext:
        lab = ctx.s("footer.linkedin", "External")
        o.spec("external", f'<p class="fx-prose"><a class="c-link c-link--standalone" href="#" rel="noopener">{esc(lab)}'
                           f'<span class="c-link__ext">{ctx.icon(ext.get("icon", "external-link"), ext.get("icon_px", 16))}</span></a></p>',
               f'icon {ext.get("icon")} {ext.get("icon_px", 16)}px')


@comp("skip_link", "Actions")
def c_skip(ctx, n, o):
    S = o.css
    S.rule(".c-skip", [("position", "absolute"), ("z-index", "10"),
                       ("inset-block-start", "var(--space-sp-3)"), ("inset-inline-start", "var(--space-sp-3)")])
    S.rule('.c-skip:not(:focus):not([data-force~="focus"])',
           [("clip-path", "inset(50%)"), ("inline-size", "1px"), ("block-size", "1px"), ("overflow", "hidden"),
            ("white-space", "nowrap"), ("padding", "0"), ("min-block-size", "0"), ("min-inline-size", "0")])
    v = n.get("variant", "primary")
    href = n.get("target", "#main")
    for st, attr in (("rest", ""), ("focus", ' data-force="focus"')):
        inner, a = ctx.tx("nav.skip", "Skip to content")
        h = (f'<div class="fx-skipstage"><a class="c-skip c-button c-button--{v}" href="{esc(href)}"{attr}>'
             f'<span{a}>{inner}</span></a></div>')
        o.spec(st, h, n.get("hidden", "") if st == "rest" else f"button {v} · first focusable")


# ── Inputs ───────────────────────────────────────────────────────────────
def field_css(ctx, n, S):
    dens = n.get("density", "comfortable")
    base = [("display", "block"), ("inline-size", "100%"), ("max-inline-size", "100%"),
            ("min-block-size", f"var(--density-{dens}-row)"),
            ("padding-inline", f"var(--density-{dens}-pad-x)"), ("padding-block", "0"),
            ("border-radius", ctx.length(n.get("radius", "{radius.control}"))),
            ("font-size", f"var(--density-{dens}-text)"),
            ("transition", ctx.transition("input"))]
    S.rule(".c-input", base + ctx.paint(n.get("rest") or {}))
    S.rule("textarea.c-input", [("padding-block", f"var(--density-{dens}-pad-y)"), ("resize", "vertical")])
    S.rule(".c-input::placeholder", [("color", ctx.color("{color.muted}")), ("opacity", "1")])
    if n.get("mobile_font_min_px"):
        S.rule(".c-input", [("font-size", f"max({px(n['mobile_font_min_px'])}, var(--density-{dens}-text))")])
    ctx.states(S, ".c-input", "hover", ctx.paint(n.get("hover") or {}))
    f = n.get("focus") or {}
    S.rule('.c-input:focus-visible, .c-input[data-force~="focus"]', ctx.paint(f))
    ctx.states(S, ".c-input", "disabled", ctx.paint(n.get("disabled") or {}) + [("cursor", "not-allowed")])
    e = n.get("error") or {}
    ctx.states(S, ".c-input", "error", ctx.paint({k: v for k, v in e.items() if k == "border"}))
    S.rule(".c-field", [("display", "grid"), ("gap", "var(--space-sp-2)"), ("align-content", "start")])
    S.rule(".c-field__label", [("font-family", "var(--font-text)"), ("font-size", f"var(--density-{dens}-label)"),
                               ("font-weight", "600"), ("line-height", "var(--type-caption-lh)")])
    S.rule(".c-field__opt", [("font-weight", "400"), ("color", ctx.color("{color.muted}"))])
    S.rule(".c-field__help", ctx.type_decls("{type.caption}") + [("color", ctx.color(n.get("help_fg", "{color.muted}")))])
    S.rule(".c-field__msg", ctx.type_decls("{type.caption}") +
           [("color", ctx.color(e.get("message_fg"))), ("display", "flex"), ("gap", "var(--space-sp-1)"),
            ("align-items", "flex-start")])
    S.rule(".c-field__msg .c-icon", [("margin-block-start", "var(--space-sp-1)")])
    S.rule(".c-field__msg[hidden]", [("display", "none")])


def field(ctx, key_label, default_label, name, typ="text", state="rest", help_key=None, help_default=None,
          optional=False, width_ch=None, placeholder=None, control="input", options=None, rows=None,
          err_key=None, err_default=None, autocomplete=None, value=None, ph_key=None,
          required=False, maxlength=None, choose=None, live_msg=False):
    """One labelled field. required/maxlength go on the control; a select
    opens on a disabled placeholder option (`choose`), never on a real answer;
    live_msg reserves the hidden error line the page script fills."""
    i = uid(ctx, f"f-{name}")
    lab_h, lab_a = ctx.tx(key_label, default_label)
    opt = ""
    if optional:
        oh, oa = ctx.tx("library.optional", "optional")
        opt = f' <span class="c-field__opt"{oa}>({oh})</span>'
    hlp = ""
    desc = []
    if help_key or help_default:
        hh, ha = ctx.tx(help_key, help_default) if help_key else (esc(help_default), "")
        if hh:
            hlp = f'<p class="c-field__help" id="{i}-h"{ha}>{hh}</p>'
            desc.append(f"{i}-h")
    attrs = f' id="{i}" name="{esc(name)}"'
    if autocomplete:
        attrs += f' autocomplete="{esc(autocomplete)}"'
    if typ == "email":
        attrs += ' inputmode="email" spellcheck="false"'
    if required:
        attrs += " required"
    if maxlength and control in ("input", "textarea"):
        attrs += f' maxlength="{int(maxlength)}"'
    if state == "disabled":
        attrs += " disabled"
    if state in ("hover", "focus"):
        attrs += f' data-force="{state}"'
    msg = ""
    if state == "error":
        mh, ma = ctx.tx(err_key, err_default) if err_key else (esc(err_default or ""), "")
        attrs += ' aria-invalid="true"'
        msg = f'<p class="c-field__msg" id="{i}-e">{ctx.icon("circle-alert", 16)}<span{ma}>{mh}</span></p>'
        desc.append(f"{i}-e")
    elif live_msg:
        msg = f'<p class="c-field__msg" id="{i}-e" hidden>{ctx.icon("circle-alert", 16)}<span></span></p>'
    if desc:
        attrs += f' aria-describedby="{" ".join(desc)}"'
    if placeholder or ph_key:
        attrs += ctx.aria(ph_key, placeholder, attr="placeholder", short="ph") if ph_key else f' placeholder="{esc(placeholder)}"'
    st = f' style="inline-size: {width_ch}ch"' if width_ch else ""
    if value is not None and control == "input":
        attrs += f' value="{esc(value)}"'
    if state == "loading":
        ctl = (f'<div class="c-skel c-skel--field" aria-busy="true"{st}></div>'
               f'<input class="c-sr" type="{typ}"{attrs} tabindex="-1">')
    elif control == "select":
        first = f'<option value="" disabled selected>{esc(choose)}</option>' if choose else ""
        opts = first + "".join(f'<option value="{esc(x)}">{esc(x)}</option>' for x in (options or []))
        ctl = f'<span class="c-select"{st}><select class="c-input"{attrs}>{opts}</select>{ctx.icon("chevron-down", 16, "c-select__icon")}</span>'
    elif control == "textarea":
        ctl = f'<textarea class="c-input" rows="{rows or 4}"{attrs}{st}></textarea>'
    else:
        ctl = f'<input class="c-input" type="{typ}"{attrs}{st}>'
    return (f'<div class="c-field"><label class="c-field__label" for="{i}"><span{lab_a}>{lab_h}</span>{opt}</label>'
            f'{hlp}{ctl}{msg}</div>')


def choose_label(ctx, scope, label_key):
    """The select's placeholder option: copy.<scope>.choose / form.choose if
    the config has one, else the field's own label with an ellipsis."""
    for k in (f"{scope}.choose", "form.choose", "form_errors.choose"):
        v = ctx.s(k)
        if v:
            return v
    # no placeholder copy: the brand's empty-value mark, never a real answer
    return ctx.s("platform.table.empty_cell", "–")


def submit_btn(ctx, variant, key, default, busy=False):
    """A submit whose 'Sending…' state keeps its width: both labels share one
    grid cell; the spinner's slot is reserved at rest."""
    inner, a = ctx.tx(key, default)
    bh, ba = ctx.tx("cta.sending", "Sending…")
    b = ' aria-busy="true" disabled' if busy else ""
    return (f'<button class="c-button c-button--{variant} c-button--submit" type="submit"{b}>{ctx.icon("loader-circle", 16, "c-spinner")}'
            f'<span class="c-button__stack"><span class="c-button__label"{a}>{inner}</span>'
            f'<span class="c-button__busy" aria-hidden="true"{ba}>{bh}</span></span></button>')


def form_messages(ctx, field_labels):
    """data-msg-* on the form: the copy the page script shows, never typed in JS."""
    out = []
    for k in ("required", "email", "max", "consent", "generic", "focus_first"):
        v = ctx.s(f"form_errors.{k}")
        if v:
            out.append(f' data-msg-{k.replace("_", "-")}="{esc(v)}"')
    return "".join(out)


@comp("input", "Inputs")
def c_input(ctx, n, o):
    field_css(ctx, n, o.css)
    S = o.css
    S.rule(".c-skel--field", [("min-block-size", f"var(--density-{n.get('density', 'comfortable')}-row)")])
    for st in ("rest", "hover", "focus", "disabled", "error", "loading", "empty"):
        h = field(ctx, "library.email", "Work email", "email", "email", st if st != "empty" else "rest",
                  "library.email_help", None, width_ch=32, autocomplete="email",
                  err_key="form_errors.email", err_default="Enter a valid value.",
                  value=None if st in ("empty", "error") else ("name@company.com" if st != "loading" else None),
                  placeholder=None)
        if st == "error":
            h = h.replace('aria-invalid="true"', 'aria-invalid="true" value="name@"')
        b = {"rest": bind(n.get("rest")), "hover": bind(n.get("hover")), "focus": bind(n.get("focus")),
             "disabled": bind(n.get("disabled")), "error": bind(n.get("error")),
             "loading": "skeleton bar, never a spinner", "empty": "no placeholder: an example or nothing"}[st]
        o.spec(st, h, b)


@comp("select", "Inputs")
def c_select(ctx, n, o):
    S = o.css
    S.rule(".c-select", [("position", "relative"), ("display", "block"), ("max-inline-size", "100%")])
    S.rule(".c-select .c-input", [("appearance", "none"), ("padding-inline-end", "var(--space-sp-5)"), ("cursor", "pointer")])
    S.rule(".c-select__icon", [("position", "absolute"), ("inset-inline-end", "var(--space-sp-3)"),
                               ("inset-block-start", "50%"), ("translate", "0 -50%"), ("pointer-events", "none")])
    lst = [("min-inline-size", "100%"), ("border-radius", "var(--radius-floating)"),
           ("max-block-size", f"calc({n.get('visible_max', 8)} * var(--density-comfortable-row))"),
           ("overflow-y", "auto"), ("padding-block", "var(--space-sp-1)")]
    S.rule(".c-listbox", ctx.elev_decls(n.get("list_elevation", "{elevation.e2}")) + lst)
    S.rule(".c-option", [("display", "flex"), ("align-items", "center"), ("justify-content", "space-between"),
                         ("gap", "var(--space-sp-2)"), ("min-block-size", "var(--target-min)"),
                         ("padding-inline", "var(--density-comfortable-pad-x)"), ("cursor", "pointer"),
                         ("transition", ctx.transition("row"))])
    row = ctx.comp("row") or {}
    ctx.states(S, ".c-option", "hover", ctx.paint({"bg": (row.get("hover") or {}).get("bg")}))
    ctx.states(S, ".c-option", "selected", ctx.paint({"bg": (row.get("selected") or {}).get("bg")}))
    S.rule(".c-option .c-icon", [("visibility", "hidden")])
    S.rule('.c-option[aria-selected="true"] .c-icon', [("visibility", "visible")])
    topics = ctx._lookup("en", "contact.topics") or ["One", "Two", "Three"]
    fr = ctx._lookup("fr", "contact.topics") or []
    for st in ("rest", "hover", "focus", "disabled"):
        h = field(ctx, "contact.topic", "Topic", "topic", state=st, control="select", options=topics, width_ch=24)
        o.spec(f"{st} · closed", h, "closed = component.input")
    opts = []
    for k, t in enumerate(topics):
        a = f' data-en="{esc(t)}" data-fr="{esc(fr[k])}"' if k < len(fr) else ""
        sel = ' aria-selected="true"' if k == 0 else ' aria-selected="false"'
        frc = ' data-force="hover"' if k == 2 else ""
        opts.append(f'<li class="c-option" role="option"{sel}{frc} tabindex="-1"><span{a}>{esc(t)}</span>{ctx.icon("check", 16)}</li>')
    lab = ctx.s("contact.topic", "Topic")
    o.spec("open · selected + hover", f'<ul class="c-listbox" role="listbox" aria-label="{esc(lab)}">{"".join(opts)}</ul>',
           f'list {str(n.get("list_elevation")).strip("{}")} · visible max {n.get("visible_max")} · search from {n.get("search_from")}')


@comp("checkbox", "Inputs")
def c_checkbox(ctx, n, o):
    S = o.css
    inp = ctx.comp("input") or {}
    rest_b = (inp.get("rest") or {}).get("border")
    S.rule(".c-check", [("position", "relative"), ("display", "inline-flex"), ("align-items", "center"),
                        ("gap", "var(--space-sp-2)"), ("min-block-size", px(n.get("target", 44)) if n.get("target") else "var(--target-min)"),
                        ("min-inline-size", "var(--target-min)"), ("cursor", "pointer")])
    box = "calc(var(--space-sp-3) + var(--space-sp-1))"
    S.rule(".c-check__box", [("appearance", "none"), ("margin", "0"), ("flex", "none"), ("inline-size", box),
                             ("block-size", box), ("border", ctx.border(rest_b)), ("border-radius", "var(--radius-control)"),
                             ("background-color", ctx.color("{color.bg}")), ("cursor", "pointer"),
                             ("transition", ctx.transition("input"))])
    S.rule(".c-check__box:checked", [("background-color", ctx.color(n.get("checked_bg"))),
                                     ("border-color", ctx.color(n.get("checked_bg")))])
    S.rule(".c-check__mark", [("position", "absolute"), ("inset-inline-start", "calc(var(--space-sp-1) / 2)"), ("inset-block-start", "50%"), ("translate", "0 -50%"),
                              ("color", ctx.color("{color.accent_on}")), ("opacity", "0"), ("pointer-events", "none"),
                              ("transition", ctx.transition("checkbox"))])
    S.rule(".c-check__box:checked + .c-check__mark", [("opacity", "1")])
    S.rule(".c-check__box:disabled", [("background-color", ctx.color("{color.state.disabled_bg}")),
                                      ("border-color", ctx.color("{color.border}")), ("cursor", "not-allowed")])
    S.rule(".c-check__box:disabled:checked", [("background-color", ctx.color("{color.state.disabled_fg}")),
                                              ("border-color", ctx.color("{color.state.disabled_fg}"))])
    S.rule('.c-check:has(:disabled)', [("color", ctx.color("{color.state.disabled_fg}")), ("cursor", "not-allowed")])
    ctx.states(S, ".c-check__box", "hover", [("border-color", ctx.color("{color.fg}"))])
    S.rule(".c-check__box:focus-visible, .c-check__box[data-force~=\"focus\"]", ctx.focus())
    S.rule(".c-fieldset", [("border", "0"), ("display", "grid"), ("gap", "var(--space-sp-1)")])
    S.rule(".c-fieldset legend", ctx.type_decls("{type.eyebrow}") + [("color", ctx.color("{color.muted}")),
                                                                   ("margin-block-end", "var(--space-sp-2)")])
    lab_h, lab_a = ctx.tx("library.consent", "I agree")
    for st, a in (("rest", ""), ("selected", " checked"), ("hover", ' data-force="hover"'), ("focus", ' data-force="focus"'),
                  ("disabled", " disabled"), ("disabled · checked", " disabled checked")):
        i = uid(ctx, "cb")
        h = (f'<label class="c-check" for="{i}"><input class="c-check__box" type="checkbox" id="{i}"{a}>'
             f'{ctx.icon("check", 16, "c-check__mark")}<span class="c-check__text"{lab_a}>{lab_h}</span></label>')
        o.spec(st, h, f"checked_bg {str(n.get('checked_bg')).strip('{}')} · target {n.get('target')}px" if "checked" in a
               else f"border = input.rest · target {n.get('target')}px")
    o.notes.append(n.get("$note", ""))


@comp("toggle", "Inputs")
def c_toggle(ctx, n, o):
    S = o.css
    inp = ctx.comp("input") or {}
    S.rule(".c-toggle", [("display", "inline-flex"), ("align-items", "center"), ("gap", "var(--space-sp-2)"),
                         ("min-block-size", "var(--target-min)"), ("text-align", "start")])
    tw, th = "var(--space-sp-5)", "var(--space-sp-4)"
    S.rule(".c-toggle__track", [("position", "relative"), ("flex", "none"), ("inline-size", tw), ("block-size", th),
                                ("border", ctx.border((inp.get("rest") or {}).get("border"))),
                                ("border-radius", "var(--radius-control)"), ("background-color", ctx.color("{color.bg}")),
                                ("transition", ctx.transition("toggle", "track"))])
    S.rule(".c-toggle__thumb", [("position", "absolute"), ("inset-block-start", "50%"), ("translate", "0 -50%"),
                                ("inset-inline-start", "calc(var(--space-sp-1) / 2)"),
                                ("inline-size", "var(--space-sp-3)"), ("block-size", "var(--space-sp-3)"),
                                ("border-radius", "var(--radius-control)"), ("background-color", ctx.color("{color.border_input}")),
                                ("transition", ctx.transition("toggle", "thumb"))])
    on = '.c-toggle[aria-checked="true"]'
    S.rule(f"{on} .c-toggle__track", [("background-color", ctx.color(n.get("on_bg"))), ("border-color", ctx.color(n.get("on_bg")))])
    S.rule(f"{on} .c-toggle__thumb", [("background-color", ctx.color("{color.accent_on}")),
                                      ("transform", "translateX(var(--space-sp-3))")])
    S.rule(f'[dir="rtl"] {on} .c-toggle__thumb', [("transform", "translateX(calc(-1 * var(--space-sp-3)))")])
    S.rule(".c-toggle:disabled", [("color", ctx.color("{color.state.disabled_fg}")), ("cursor", "not-allowed")])
    S.rule(".c-toggle:disabled .c-toggle__track", [("background-color", ctx.color("{color.state.disabled_bg}")),
                                                   ("border-color", ctx.color("{color.border}"))])
    S.rule(".c-toggle:disabled .c-toggle__thumb", [("background-color", ctx.color("{color.state.disabled_fg}"))])
    lab_h, lab_a = ctx.tx("cookie.accept", "Setting")
    for st, a in (("rest", ' aria-checked="false"'), ("selected", ' aria-checked="true"'),
                  ("focus", ' aria-checked="true" data-force="focus"'), ("disabled", ' aria-checked="false" disabled')):
        h = (f'<button class="c-toggle" type="button" role="switch"{a}><span class="c-toggle__track">'
             f'<span class="c-toggle__thumb"></span></span><span class="c-check__text"{lab_a}>{lab_h}</span></button>')
        o.spec(st if st != "selected" else "on", h, f"on_bg {str(n.get('on_bg')).strip('{}')} · applies immediately")
    o.notes.append("thumb and off-track colours: generator choice (config states on_bg only)")


@comp("slider", "Inputs")
def c_slider(ctx, n, o):
    S = o.css
    tr, th = n.get("track") or {}, n.get("thumb") or {}
    tw = px(tr.get("width", 2))
    S.rule(".c-slider", [("position", "relative"), ("display", "grid"), ("grid-template-columns", "1fr auto"),
                         ("align-items", "center"), ("gap", "var(--space-sp-3)"), ("max-inline-size", "100%")])
    S.rule(".c-slider__rail", [("position", "relative"), ("display", "flex"), ("align-items", "center")])
    S.rule(".c-slider__rail::before", [("content", '""'), ("position", "absolute"), ("inset-inline", "0"),
                                       ("block-size", tw), ("background-color", ctx.color(tr.get("color")))])
    S.rule(".c-slider__fill", [("position", "absolute"), ("inset-inline-start", "0"), ("block-size", tw),
                               ("background-color", ctx.color(n.get("fill")))])
    S.rule(".c-slider input", [("appearance", "none"), ("position", "relative"), ("inline-size", "100%"),
                               ("block-size", "var(--target-min)"), ("margin", "0"), ("background-color", "transparent"),
                               ("cursor", "pointer")])
    thumb = [("appearance", "none"), ("inline-size", px(th.get("size", 20))), ("block-size", px(th.get("size", 20))),
             ("border", "0"), ("border-radius", ctx.length(th.get("radius", "{radius.control}"))),
             ("background-color", ctx.color(th.get("bg")))]
    S.rule(".c-slider input::-webkit-slider-thumb", thumb)
    S.rule(".c-slider input::-moz-range-thumb", thumb)
    S.rule(".c-slider input:focus-visible, .c-slider input[data-force~=\"focus\"]", [("outline", "none")])
    S.rule(".c-slider input:focus-visible::-webkit-slider-thumb, .c-slider input[data-force~=\"focus\"]::-webkit-slider-thumb", ctx.focus())
    S.rule(".c-slider input:disabled::-webkit-slider-thumb", [("background-color", ctx.color("{color.state.disabled_fg}"))])
    S.rule(".c-slider:has(:disabled) .c-slider__fill", [("background-color", ctx.color("{color.state.disabled_fg}"))])
    S.rule(".c-slider__out", ctx.type_decls("{type.mono}") + [("font-variant-numeric", "tabular-nums"), ("min-inline-size", "3ch"), ("text-align", "end")])
    lab_h, lab_a = ctx.tx("platform.quadrant.y", "Value")
    cut = (((ctx.cfg.get("patterns") or {}).get("quadrant") or {}).get("cuts") or {}).get("impact", 60)
    for st, a in (("rest", ""), ("focus", ' data-force="focus"'), ("disabled", " disabled")):
        i = uid(ctx, "sl")
        h = (f'<div class="c-field"><label class="c-field__label" for="{i}"{lab_a}>{lab_h}</label><div class="c-slider">'
             f'<div class="c-slider__rail"><span class="c-slider__fill" style="inline-size: {cut}%"></span>'
             f'<input type="range" id="{i}" min="0" max="100" value="{cut}"{a}></div>'
             f'<output class="c-slider__out" for="{i}">{cut}</output></div></div>')
        o.spec(st, h, bind({"track": tr, "fill": n.get("fill")}) + f" · thumb {th.get('size')}px {str(th.get('bg')).strip('{}')}")


@comp("calendar", "Inputs")
def c_calendar(ctx, n, o):
    import datetime
    S = o.css
    S.rule(".c-cal", [("display", "inline-grid"), ("gap", "var(--space-sp-2)")])
    S.rule(".c-cal__head", ctx.type_decls("{type.heading_sm}"))
    S.rule(".c-cal table", [("border-collapse", "collapse")])
    S.rule(".c-cal th", ctx.type_decls("{type.eyebrow}") + [("font-size", "var(--density-dense-label)"), ("color", ctx.color("{color.muted}")),
                                                         ("block-size", "var(--space-sp-5)"), ("font-weight", "500")])
    S.rule(".c-cal .c-cal__wk", ctx.type_decls("{type.mono}") + [("font-size", "var(--density-dense-label)"), ("color", ctx.color("{color.muted}")),
                                                              ("padding-inline-end", "var(--space-sp-2)")])
    S.rule(".c-cal__day", ctx.type_decls("{type.mono}") + [("inline-size", "var(--target-min)"), ("block-size", "var(--target-min)"),
                                                        ("font-variant-numeric", "tabular-nums"), ("border-radius", "var(--radius-control)"),
                                                        ("transition", ctx.transition("row"))])
    row = ctx.comp("row") or {}
    ctx.states(S, ".c-cal__day", "hover", ctx.paint({"bg": (row.get("hover") or {}).get("bg")}))
    S.rule('.c-cal__day[aria-current="date"]', [("border-block-end", ctx.border(n.get("today_rule")))])
    S.rule('.c-cal__day[data-range]', ctx.paint(n.get("range") or {}))
    S.rule('.c-cal__day[aria-pressed="true"]', ctx.paint(n.get("selected") or {}))
    S.rule('.c-cal__day[data-outside]', ctx.paint(n.get("outside_month") or {}))
    m = (ctx.mq("tablet"))
    S.rule(".c-cal .c-cal__wk", [("display", "none")])
    inner = Sheet()
    inner.rule(".c-cal .c-cal__wk", [("display", "table-cell")])
    if m:
        S.media(m, inner)
    # the month the config is dated; today, a selected range: illustrative
    yr, mo = 2026, 10
    dm = re.match(r"(\w+)\s+(\d{4})", str(ctx.cfg.get("date", "")))
    if dm:
        try:
            mo = datetime.datetime.strptime(dm.group(1)[:3], "%b").month
            yr = int(dm.group(2))
        except ValueError:
            pass
    first = datetime.date(yr, mo, 1)
    start = first - datetime.timedelta(days=first.weekday() if n.get("week_start", "monday") == "monday" else (first.weekday() + 1) % 7)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] if n.get("week_start", "monday") == "monday" else \
        ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    rows = []
    d = start
    for w in range(6):
        cells = [f'<th class="c-cal__wk" scope="row">W{d.isocalendar()[1]}</th>'] if n.get("week_numbers") else []
        for k in range(7):
            attrs = ""
            if d.month != mo:
                attrs += ' data-outside aria-disabled="true"'
            elif d.day == 12:
                attrs += ' aria-current="date"'
            if d.month == mo and d.day in (14, 18):
                attrs += ' aria-pressed="true"'
            elif d.month == mo and 14 < d.day < 18:
                attrs += " data-range"
            if d.month == mo and d.day == 21:
                attrs += ' data-force="hover"'
            if d.month == mo and d.day == 22:
                attrs += ' data-force="focus"'
            cells.append(f'<td><button class="c-cal__day" type="button"{attrs}>{d.day}</button></td>')
            d += datetime.timedelta(days=1)
        rows.append(f"<tr>{''.join(cells)}</tr>")
        if d.month != mo and d > first:
            break
    head = ("<th class=\"c-cal__wk\" aria-hidden=\"true\"></th>" if n.get("week_numbers") else "") + \
        "".join(f'<th scope="col">{x}</th>' for x in days)
    h = (f'<div class="c-cal"><p class="c-cal__head">{first.strftime("%B %Y")}</p><table><thead><tr>{head}</tr></thead>'
         f'<tbody>{"".join(rows)}</tbody></table></div>')
    o.spec("today · selected · range · outside · hover · focus", h,
           bind({"today_rule": n.get("today_rule")}) + " · selected " + bind(n.get("selected")) +
           f" · week {n.get('week_start')} · W-numbers", wide=True)
    o.notes.append("today and the selected range are illustrative")


@comp("file_upload", "Inputs")
def c_upload(ctx, n, o):
    S = o.css
    dz = n.get("dropzone") or {}
    S.rule(".c-drop", [("display", "flex"), ("flex-wrap", "wrap"), ("align-items", "center"), ("gap", "var(--space-sp-3)"),
                       ("padding", ctx.length(dz.get("padding", "{space.sp-5}"))),
                       ("border-radius", ctx.length(dz.get("radius", "{radius.control}"))),
                       ("transition", ctx.transition("input"))] + ctx.paint({k: dz[k] for k in ("border", "bg") if k in dz}))
    ctx.states(S, ".c-drop", "hover", ctx.paint(dz.get("hover") or {}))
    S.rule('.c-drop[data-state="dragover"]', ctx.paint(dz.get("dragover") or {}))
    S.rule(".c-drop:focus-within, .c-drop[data-force~=\"focus\"]", ctx.focus())
    S.rule(".c-drop__text", [("color", ctx.color("{color.fg}"))])
    fr = n.get("file_row") or {}
    S.rule(".c-file", [("display", "grid"), ("grid-template-columns", "minmax(0, 1fr) auto auto"), ("align-items", "center"),
                       ("gap", "var(--space-sp-3)"), ("min-block-size", "var(--density-comfortable-row)"),
                       ("border-block-end", ctx.border(fr.get("rule")))])
    S.rule(".c-file__name", [("overflow", "hidden"), ("white-space", "nowrap"), ("text-overflow", "ellipsis")])
    S.rule(".c-file__size, .c-file__pct", ctx.type_decls("{type.mono}") + [("color", ctx.color("{color.muted}")),
                                                                        ("font-variant-numeric", "tabular-nums")])
    pr = fr.get("progress") or {}
    tk = pr.get("track") or {}
    S.rule(".c-progress", [("grid-column", "1 / -1"), ("display", "flex"), ("align-items", "center"), ("gap", "var(--space-sp-2)")])
    S.rule(".c-progress__bar", [("position", "relative"), ("flex", "1"), ("block-size", px(tk.get("width", 2))),
                                ("background-color", ctx.color(tk.get("color")))])
    S.rule(".c-progress__fill", [("position", "absolute"), ("inset", "0"), ("background-color", ctx.color(pr.get("fill"))),
                                 ("transform-origin", "left"), ("transition", ctx.transition("progress_bar"))])
    S.rule(".c-iconbtn", [("display", "inline-flex"), ("align-items", "center"), ("justify-content", "center"),
                          ("inline-size", "var(--target-min)"), ("block-size", "var(--target-min)"),
                          ("border-radius", "var(--radius-control)"), ("color", "inherit"), ("transition", ctx.transition("button"))])
    ctx.states(S, ".c-iconbtn", "hover", [("background-color", ctx.color("{color.state.surface_hover}"))])
    S.rule('[data-surface="ink"] .c-iconbtn[data-force~="hover"]', [("background-color", ctx.color({"color": "{color.bg}", "alpha": 0.08}, True))])
    ctl = n.get("control") or {}
    help_h, help_a = ctx.tx("platform.upload.help", (n.get("help") or {}).get("content", ""))
    drop_h, drop_a = ctx.tx("platform.upload.drop", "Drop files here, or")
    def zone(attr=""):
        i = uid(ctx, "up")
        ch, ca = ctx.tx("platform.upload.choose", ctl.get("label", "Choose a file"))
        return (f'<div class="c-field"><p class="c-field__help"{help_a}>{help_h}</p><div class="c-drop"{attr}>'
                f'<span class="c-drop__text"{drop_a}>{drop_h}</span>'
                f'<input class="c-sr" type="file" id="{i}" multiple>'
                f'<label class="c-button c-button--{ctl.get("variant", "secondary")}" for="{i}">{ctx.icon(ctl.get("icon"), 20)}'
                f'<span{ca}>{ch}</span></label></div></div>')
    o.spec("rest", zone(), bind(dz, ("border", "bg")))
    o.spec("hover", zone(' data-force="hover"'), bind(dz.get("hover")))
    o.spec("dragover", zone(' data-state="dragover"'), bind(dz.get("dragover")))
    o.spec("focus", zone(' data-force="focus"'), "component.focus (focus-within)")
    rm = ctx.aria("platform.upload.remove", "Remove")
    up = (f'<div class="c-file"><span class="c-file__name" title="Use-Case-Portfolio-export-2026.xlsx">Use-Case-Portf…-2026.xlsx</span>'
          f'<span class="c-file__size">4.2 MB</span><button class="c-iconbtn" type="button"{rm}>{ctx.icon("trash", 20)}</button>'
          f'<div class="c-progress"><span class="c-progress__bar"><span class="c-progress__fill" style="transform: scaleX(0.42)"></span></span>'
          f'<span class="c-file__pct">42%</span></div></div>')
    o.spec("loading · uploading", up, bind({"track": tk, "fill": pr.get("fill")}))
    em = ctx.s("platform.upload.too_large", "{name} is too large.").format(name="AI-Capability-Plan.pdf")
    err = (f'<div class="c-file"><span class="c-file__name">AI-Capability-Plan.pdf</span><span class="c-file__size">31 MB</span>'
           f'<button class="c-iconbtn" type="button"{rm}>{ctx.icon("trash", 20)}</button></div>'
           f'<div class="c-msg c-msg--inline" role="alert"><p class="c-msg__line">{esc(em)}</p>'
           f'{btn(ctx, (fr.get("retry") or {}).get("variant", "tertiary"), "Try again", "platform.upload.retry")}</div>')
    o.spec("error", err, "error = component.inline_message · retry keeps the queue")


@comp("settings_form", "Inputs")
def c_settings(ctx, n, o):
    S = o.css
    S.rule(".c-settings", [("display", "grid"), ("gap", "var(--space-sp-5)"), ("max-inline-size", px(n.get("max_width", 560)))])
    S.rule(".c-settings__section", [("display", "grid"), ("gap", "var(--space-sp-3)"), ("padding-block-start", "var(--space-sp-3)"),
                                    ("border-block-start", ctx.border(n.get("section_rule")))])
    S.rule(".c-settings__head", ctx.type_decls("{type.heading_sm}"))
    o.spec("rest", settings_html(ctx, n), bind(n, ("section_rule",)) + f" · {n.get('density')} · max {n.get('max_width')}px", wide=True)
    o.spec("loading · saving", settings_html(ctx, n, saving=True), (n.get("save") or {}).get("state", ""), wide=True)


def settings_html(ctx, n, saving=False):
    langs = [ctx.s("lang.en", "EN"), ctx.s("lang.fr", "FR")]
    lab = {"EN": "English", "FR": "Français"}
    sel = field(ctx, "platform.settings.language", "Language", "language", control="select",
                options=[lab.get(x, x) for x in langs], width_ch=20,
                help_key=None).replace('class="c-field__label"', 'class="c-sr"', 1)
    df_h, df_a = ctx.tx("platform.settings.date_format", "")
    lang_h, lang_a = ctx.tx("platform.settings.language", "Language")
    tg_h, tg_a = ctx.tx("cookie.accept", "Accept analytics")
    pol_h, pol_a = ctx.tx("footer.cookie_settings", "Cookie choices")
    save = n.get("save") or {}
    b = btn(ctx, save.get("variant", "primary"), save.get("label", "Save changes"), "platform.settings.save",
            attrs=' aria-busy="true" disabled' if saving else "")
    return (f'<form class="c-settings" action="#" novalidate><div class="c-settings__section">'
            f'<h3 class="c-settings__head"{lang_a}>{lang_h}</h3>{sel}<p class="c-field__help"{df_a}>{df_h}</p></div>'
            f'<div class="c-settings__section"><h3 class="c-settings__head"{pol_a}>{pol_h}</h3>'
            f'<button class="c-toggle" type="button" role="switch" aria-checked="true"><span class="c-toggle__track">'
            f'<span class="c-toggle__thumb"></span></span><span class="c-check__text"{tg_a}>{tg_h}</span></button></div>'
            f'<div>{b}</div></form>')


# ── Navigation ───────────────────────────────────────────────────────────
def web_labels(ctx):
    nav = ctx.comp("nav") or {}
    labels = (nav.get("web") or {}).get("labels") or []
    return [(l, f"nav.{l.lower()}") for l in labels]


@comp("nav", "Navigation")
def c_nav(ctx, n, o):
    S = o.css
    it = n.get("item") or {}
    S.rule(".c-nav-item", [("display", "flex"), ("align-items", "center"), ("gap", "var(--space-sp-2)"),
                           ("min-block-size", "var(--target-min)"), ("padding-inline", "var(--space-sp-3)"),
                           ("text-decoration-line", "none"), ("border-inline-start", ctx.border({**(it.get("selected") or {}).get("edge", {"width": 2, "style": "solid"}), "color": "transparent"})),
                           ("transition", ctx.transition("nav_item"))] + ctx.type_decls("{type.button}") + ctx.paint(it.get("rest") or {}))
    for st in ("hover", "selected", "disabled"):
        ctx.states(S, ".c-nav-item", st, ctx.paint(it.get(st) or {}, edge="inline-start"))
    sb = n.get("sidebar") or {}
    if sb:
        w = sb.get("width") or {}
        S.rule(".c-sidebar", [("display", "flex"), ("flex-direction", "column"), ("gap", "var(--space-sp-1)"),
                              ("inline-size", px(w.get("expanded", 232))), ("flex", "none"), ("padding-block", "var(--space-sp-3)"),
                              ("background-color", ctx.color(sb.get("bg"), True)), ("color", ctx.color(sb.get("item_rest"), True))])
        S.rule('.c-sidebar[data-collapsed]', [("inline-size", px(w.get("collapsed", 64)))])
        S.rule('.c-sidebar[data-collapsed] .c-sidebar__label', [("position", "absolute"), ("inline-size", "1px"), ("block-size", "1px"),
                                                                 ("overflow", "hidden"), ("clip-path", "inset(50%)")])
        S.rule('.c-sidebar[data-collapsed] .c-sidebar__item', [("justify-content", "center"), ("padding-inline", "0")])
        S.rule(".c-sidebar__brand", [("display", "flex"), ("align-items", "center"), ("min-block-size", "var(--target-min)"),
                                     ("padding-inline", "var(--space-sp-4)"), ("margin-block-end", "var(--space-sp-3)")])
        S.rule('.c-sidebar[data-collapsed] .c-sidebar__brand', [("justify-content", "center"), ("padding-inline", "0")])
        cur = sb.get("item_current") or {}
        S.rule(".c-sidebar__item", [("display", "flex"), ("align-items", "center"), ("gap", "var(--space-sp-3)"),
                                    ("min-block-size", "var(--target-min)"), ("padding-inline", "var(--space-sp-4)"),
                                    ("text-decoration-line", "none"), ("color", ctx.color(sb.get("item_rest"), True)),
                                    ("border-inline-start", ctx.border({**cur.get("edge", {"width": 2, "style": "solid"}), "color": "transparent"})),
                                    ("transition", ctx.transition("nav_item"))] + ctx.type_decls("{type.button}"))
        ctx.states(S, ".c-sidebar__item", "hover", [("color", ctx.color(cur.get("fg"), True))])
        ctx.states(S, ".c-sidebar__item", "selected", ctx.paint(cur, True, edge="inline-start"))
        S.rule(".c-sidebar__item:focus-visible, .c-sidebar__item[data-force~=\"focus\"]", ctx.focus("on_dark") + [("outline-offset", px(((ctx.comp("focus") or {}).get("inset_offset", -2))))])
        S.rule(".c-sidebar__foot", [("margin-block-start", "auto")])
    # fixture: web items, vertical
    items = web_labels(ctx)[:4] or [("Item", None)]
    for st, a in (("rest", ""), ("hover", ' data-force="hover"'), ("selected", ' aria-current="page"'),
                  ("focus", ' data-force="focus"'), ("disabled", ' aria-disabled="true"')):
        lab, key = items[0] if st == "rest" else items[min(len(items) - 1, 1)]
        inner, aa = ctx.tx(key, lab)
        o.spec(st, f'<a class="c-nav-item" href="#"{a}><span{aa}>{inner}</span></a>', bind(it.get(st) or (it.get("rest") if st == "rest" else "component.focus")))
    if sb:
        o.spec("sidebar · expanded", sidebar_html(ctx, current="use_cases", force={"hover": "scorecard", "focus": "roadmap"}),
               f"bg {str(sb.get('bg')).strip('{}')} · rest {bind({'item_rest': sb.get('item_rest')})} · current {bind(sb.get('item_current'))}", wide=False)
        o.spec("sidebar · collapsed", sidebar_html(ctx, current="use_cases", collapsed=True),
               f"{(sb.get('width') or {}).get('collapsed')}px · no intermediate width")


SCREENS = [("dashboard", "chart-scatter"), ("use_cases", "portfolio"), ("scorecard", "assess"),
           ("governance", "govern"), ("roadmap", "roadmap"), ("blueprints", "build")]


def sidebar_html(ctx, current=None, collapsed=False, force=None):
    force = force or {}
    items = []
    for key, ic in SCREENS:
        h, a = ctx.tx(f"platform.nav.{key}", key.replace("_", " ").capitalize())
        attrs = ' aria-current="page"' if key == current else ""
        for st, k in force.items():
            if k == key:
                attrs += f' data-force="{st}"'
        tip = f' title="{esc(ctx.s(f"platform.nav.{key}", key))}"' if collapsed else ""
        items.append(f'<a class="c-sidebar__item" href="#"{attrs}{tip}>{ctx.icon(ic, 20)}<span class="c-sidebar__label"{a}>{h}</span></a>')
    col = " data-collapsed" if collapsed else ""
    tg = ctx.aria("platform.nav.expand" if collapsed else "platform.nav.collapse", "Collapse sidebar")
    toggle = f'<button class="c-sidebar__item c-sidebar__foot" type="button"{tg}>{ctx.icon("panel-left", 20)}</button>'
    home = ctx.aria("nav.home", "Home")
    return (f'<nav class="c-sidebar" data-surface="ink"{col}{ctx.aria("nav.main_nav", "Main")}>'
            f'<a class="c-sidebar__brand" href="#"{home}>{mark_svg(ctx, 32)}</a>{"".join(items)}{toggle}</nav>')


@comp("header", "Navigation")
def c_header(ctx, n, o):
    S = o.css
    hgt = n.get("height") or {}
    nav = n.get("nav") or {}
    S.rule(".c-header", [("position", "sticky"), ("inset-block-start", "0"), ("z-index", "5"),
                         ("background-color", ctx.color(n.get("bg"))), ("border-block-end", ctx.border({**(n.get("rule") or {"width": 1, "style": "solid"}), "color": "transparent"}))])
    S.rule(".c-header[data-scrolled]", [("border-block-end", ctx.border(n.get("rule")))])
    S.rule(".c-header__bar", [("display", "flex"), ("align-items", "center"), ("gap", "var(--space-sp-3)"),
                              ("block-size", px(hgt.get("phone", hgt.get("desktop", 64))))])
    S.rule(".c-header__home", [("display", "inline-flex"), ("align-items", "center"), ("justify-content", "center"),
                               ("min-inline-size", "var(--target-min)"), ("min-block-size", "var(--target-min)")])
    S.rule(".c-header__nav", [("display", "none"), ("align-items", "stretch"), ("gap", ctx.length(nav.get("gap"))),
                              ("margin-inline-start", "var(--space-sp-6)"), ("align-self", "stretch")])
    S.rule(".c-header__spacer", [("flex", "1")])
    S.rule(".c-header__cta, .c-header .c-lang", [("display", "none")])
    edge = nav.get("current_edge") or {}
    side = nav.get("current_edge_side", "block-end").replace("block-end", "block-end")
    S.rule(".c-header__item", [("display", "inline-flex"), ("align-items", "center"), ("justify-content", "center"),
                               ("min-block-size", "var(--target-min)"), ("min-inline-size", "var(--target-min)"),
                               ("text-decoration-line", "none"),
                               (f"border-{side}", ctx.border({**edge, "color": "transparent"})),
                               ("transition", ctx.transition("nav_item"))] + ctx.type_decls(nav.get("type")) +
           ctx.paint(((ctx.comp("nav") or {}).get("item") or {}).get("rest") or {}))
    it = (ctx.comp("nav") or {}).get("item") or {}
    ctx.states(S, ".c-header__item", "hover", ctx.paint(it.get("hover") or {}))
    ctx.states(S, ".c-header__item", "selected", ctx.paint({"fg": (it.get("selected") or {}).get("fg")}) +
               [(f"border-{side}-color", ctx.color(edge.get("color")))])
    for p in pillars(ctx):
        S.rule(f'.c-header[data-pillar="{p["key"]}"] .c-header__item[aria-current="page"]',
               [(f"border-{side}-color", ctx.color("{color.pillar.%s}" % p["key"]))])
    S.rule(".c-menubtn", [("display", "inline-flex"), ("align-items", "center"), ("gap", "var(--space-sp-2)"),
                          ("min-block-size", "var(--target-min)"), ("min-inline-size", "var(--target-min)"),
                          ("padding-inline", "var(--space-sp-2)"), ("border-radius", "var(--radius-control)"),
                          ("transition", ctx.transition("button"))] + ctx.type_decls(nav.get("type")))
    ctx.states(S, ".c-menubtn", "hover", [("background-color", ctx.color("{color.state.surface_hover}"))])
    tab, desk = ctx.mq("tablet"), ctx.mq(n.get("breakpoint_collapse", "desktop"))
    if tab:
        i = Sheet()
        i.rule(".c-header__bar", [("block-size", px(hgt.get("tablet", hgt.get("desktop", 64))))])
        i.rule(".c-header__cta, .c-header .c-lang", [("display", "inline-flex")])
        S.media(tab, i)
    if desk:
        i = Sheet()
        i.rule(".c-header__bar", [("block-size", px(hgt.get("desktop", 64)))])
        i.rule(".c-header__nav", [("display", "flex")])
        i.rule(".c-menubtn", [("display", "none")])
        S.media(desk, i)
    o.spec("rest · current page", header_html(ctx, current="Learn"), f"bg {str(n.get('bg')).strip('{}')} · edge {bind({'e': edge})[2:]} {side}", wide=True)
    o.spec("scrolled · hover · focus", header_html(ctx, current="Platform", scrolled=True, force={"hover": "Build", "focus": "Lead"}),
           "rule " + bind({"r": n.get("rule")})[2:] + " once scrolled · no transition", wide=True)
    if pillars(ctx):
        o.spec("pillar page", header_html(ctx, current="Lead", pillar="lead"), "current edge takes the pillar colour", wide=True)


def nav_href(ctx, key):
    k = str(key).split(".")[-1]
    if k in {p["key"] for p in pillars(ctx)}:
        return ctx.href("pillar-" + k)
    return ctx.href(k)


def header_html(ctx, current=None, scrolled=False, pillar=None, force=None, cta_key="cta.talk", drawer=False):
    n = ctx.comp("header") or {}
    force = force or {}
    items = []
    for lab, key in web_labels(ctx):
        h, a = ctx.tx(key, lab)
        at = ' aria-current="page"' if lab == current else ""
        for st, k in force.items():
            if k == lab:
                at += f' data-force="{st}"'
        items.append(f'<a class="c-header__item" href="{esc(nav_href(ctx, key))}"{at}><span{a}>{h}</span></a>')
    cta = n.get("cta") or {}
    menu = (ctx.comp("mobile_nav") or {}).get("trigger") or {}
    mh, ma = ctx.tx("nav.menu", menu.get("label", "Menu"))
    sc = " data-scrolled" if scrolled else ""
    pl = f' data-pillar="{pillar}"' if pillar else ""
    logo = (n.get("logo") or {})
    ctl = ' aria-controls="mnav"' if drawer else ""
    return (f'<header class="c-header"{sc}{pl}><div class="p-container c-header__bar">'
            f'<a class="c-header__home" href="{esc(ctx.href("home"))}"{ctx.aria("nav.home", logo.get("label", "Home"))}>{mark_svg(ctx, logo.get("px", 40))}</a>'
            f'<nav class="c-header__nav"{ctx.aria("nav.main_nav", "Main")}>{"".join(items)}</nav>'
            f'<span class="c-header__spacer"></span>{lang_html(ctx)}'
            f'{btn(ctx, cta.get("variant", "primary"), cta.get("label", "Talk to us"), cta_key, href=ctx.href("contact"), cls="c-header__cta")}'
            f'<button class="c-menubtn" type="button" aria-expanded="false"{ctl}>{ctx.icon(menu.get("icon", "menu"), menu.get("icon_px", 20))}'
            f'<span{ma}>{mh}</span></button></div></header>')


def lang_html(ctx, cls=""):
    """The language switch. On a page, each item links to that page in the
    other language (ctx.links['lang-<l>']); the current language is marked."""
    if not ctx.comp("language_switch"):
        return ""
    locs = [l for l in ((ctx.cfg.get("locales") or {}).get("list") or []) if l in ctx.copy]
    if len(locs) < 2:
        return ""
    parts = []
    for k, l in enumerate(locs):
        if k:
            parts.append('<span class="c-lang__sep" aria-hidden="true">·</span>')
        cur = ' aria-current="true"' if l == ctx.lang else ""
        lab = ctx._lookup(l, "lang." + l) or ctx._lookup("en", "lang." + l) or l.upper()
        sw = ctx._lookup(l, f"lang.switch_to_{l}")
        al = f' aria-label="{esc(sw)}"' if sw and l != ctx.lang else ""
        parts.append(f'<a class="c-lang__item" href="{esc(ctx.href("lang-" + l))}" lang="{l}" hreflang="{l}"{cur}{al}>{esc(lab)}</a>')
    return f'<span class="c-lang{" " + cls if cls else ""}">{"".join(parts)}</span>'


@comp("language_switch", "Navigation")
def c_lang(ctx, n, o):
    S = o.css
    S.rule(".c-lang", [("display", "inline-flex"), ("align-items", "center")] + ctx.type_decls(n.get("type")))
    S.rule(".c-lang__item", [("display", "inline-flex"), ("align-items", "center"), ("justify-content", "center"),
                             ("min-inline-size", "var(--target-min)"), ("min-block-size", "var(--target-min)"),
                             ("text-decoration-line", "none"), ("transition", ctx.transition("link"))] + ctx.paint(n.get("other") or {}))
    S.rule('.c-lang__item[aria-current="true"]', ctx.paint(n.get("current") or {}))
    ctx.states(S, ".c-lang__item", "hover", ctx.paint(n.get("hover") or {}))
    S.rule(".c-lang__sep", [("color", ctx.color("{color.muted}"))])
    S.rule('[data-surface="ink"] .c-lang__item', [("color", ctx.color("{color.muted_on_dark}", True))])
    S.rule('[data-surface="ink"] .c-lang__item[aria-current="true"]', [("color", ctx.color("{color.bg}", True))])
    h = lang_html(ctx)
    o.spec("rest · current EN", h, f"current {bind(n.get('current'))} · other {bind(n.get('other'))}")
    o.spec("hover", h.replace('class="c-lang__item" href="#" lang="fr"', 'class="c-lang__item" data-force="hover" href="#" lang="fr"'), bind(n.get("hover")))
    o.spec("focus", h.replace('class="c-lang__item" href="#" lang="fr"', 'class="c-lang__item" data-force="focus" href="#" lang="fr"'), "component.focus")
    o.spec("on dark", h, "muted_on_dark / bg", ink=True)


@comp("breadcrumbs", "Navigation")
def c_crumbs(ctx, n, o):
    S = o.css
    S.rule(".c-crumbs ol", [("display", "flex"), ("flex-wrap", "wrap"), ("align-items", "center"), ("gap", ctx.length(n.get("gap")))])
    S.rule(".c-crumbs li", [("display", "inline-flex"), ("align-items", "center"), ("gap", ctx.length(n.get("gap"))),
                            ("min-inline-size", "0")] + ctx.type_decls(n.get("type")))
    S.rule(".c-crumbs a", [("display", "inline-flex"), ("align-items", "center"), ("min-block-size", "var(--target-min)"),
                           ("min-inline-size", "var(--target-min)"),
                           ("text-decoration-line", "none"), ("transition", ctx.transition("link"))] + ctx.paint(n.get("item") or {}))
    ctx.states(S, ".c-crumbs a", "hover", ctx.paint(n.get("item_hover") or {}))
    S.rule('.c-crumbs [aria-current="page"]', ctx.paint(n.get("current") or {}) +
           [("overflow", "hidden"), ("text-overflow", "ellipsis"), ("white-space", "nowrap"), ("max-inline-size", f"{n.get('truncate_ch', 32)}ch")])
    S.rule('[data-surface="ink"] .c-crumbs a', ctx.paint(n.get("on_dark") or {}, True))
    S.rule('[data-surface="ink"] .c-crumbs [aria-current="page"]', [("color", ctx.color("{color.bg}", True))])
    S.rule(".c-crumbs__back", [("display", "inline-flex"), ("gap", "var(--space-sp-1)")])
    S.rule(".c-crumbs ol", [("display", "none")])
    m = ctx.mq("tablet")
    if m:
        i = Sheet()
        i.rule(".c-crumbs ol", [("display", "flex")])
        i.rule(".c-crumbs .c-crumbs__back", [("display", "none")])
        S.media(m, i)
    trail = [("not_found.links.home", "Home"), ("footer.training", "Training"), (None, "Learn AI")]
    o.spec("rest · hover · current", crumbs_html(ctx, trail, force_hover=1), f"item {bind(n.get('item'))} · hover {bind(n.get('item_hover'))} · current {bind(n.get('current'))}")
    o.spec("on dark · platform", crumbs_html(ctx, [("platform.nav.dashboard", "Dashboard"), ("platform.nav.use_cases", "Use cases"), (None, "Invoice extraction")]),
           bind(n.get("on_dark")), ink=True)
    o.notes.append(n.get("phone", ""))


def crumbs_html(ctx, trail, force_hover=None):
    n = ctx.comp("breadcrumbs") or {}
    sep = (n.get("separator") or {})
    sp = f'<span aria-hidden="true">{ctx.icon(sep.get("icon", "chevron-right"), sep.get("icon_px", 16))}</span>'
    lis = []
    for k, (key, d) in enumerate(trail):
        h, a = ctx.tx(key, d) if key else (esc(d), "")
        if k == len(trail) - 1:
            lis.append(f'<li><span aria-current="page"{a}>{h}</span></li>')
        else:
            f = ' data-force="hover"' if force_hover == k else ""
            lis.append(f'<li><a href="#"{f}><span{a}>{h}</span></a>{sp}</li>')
    pk, pd = trail[-2] if len(trail) > 1 else trail[0]
    ph, pa = ctx.tx(pk, pd) if pk else (esc(pd), "")
    back = f'<a class="c-crumbs__back" href="#">{ctx.icon("arrow-left", 16)}<span{pa}>{ph}</span></a>'
    return f'<nav class="c-crumbs"{ctx.aria("nav.breadcrumb", "Breadcrumb")}>{back}<ol>{"".join(lis)}</ol></nav>'


@comp("tabs", "Navigation")
def c_tabs(ctx, n, o):
    S = o.css
    rule = n.get("current_rule") or {}
    S.rule(".c-tabs", [("display", "flex"), ("flex-wrap", "wrap"), ("gap", "var(--space-sp-4)"),
                       ("border-block-end", ctx.border({"width": 1, "style": "solid", "color": "{color.border}"}))])
    S.rule(".c-tab", [("display", "inline-flex"), ("align-items", "center"), ("justify-content", "center"), ("min-block-size", "var(--target-min)"),
                      ("min-inline-size", "var(--target-min)"),
                      ("text-decoration-line", "none"), ("border-block-end", ctx.border({**rule, "color": "transparent"})),
                      ("margin-block-end", "-1px"), ("transition", ctx.transition("row"))] + ctx.type_decls("{type.button}") +
           [("color", ctx.color("{color.muted}"))])
    ctx.states(S, ".c-tab", "hover", [("color", ctx.color("{color.fg}"))])
    ctx.states(S, ".c-tab", "selected", [("color", ctx.color("{color.fg}")), ("border-block-end-color", ctx.color(rule.get("color")))])
    o.spec("current · hover · focus", tabs_html(ctx, force={1: "hover", 2: "focus"}), f"current_rule {bind({'r': rule})[2:]} block-end · indicator instant", wide=True)


def tabs_html(ctx, force=None, link=False):
    force = force or {}
    labs = [("platform.filter.all", "All", None)] + [(None, p["label"], p["key"]) for p in pillars(ctx)]
    out = []
    for k, (key, d, pk) in enumerate(labs):
        h, a = ctx.tx(key, d) if key else (esc(d), "")
        sel = 'true' if k == 0 else 'false'
        f = f' data-force="{force[k]}"' if k in force else ""
        if link:
            cur = ' aria-current="page"' if k == 0 else ""
            out.append(f'<a class="c-tab" href="#"{cur}{f}><span{a}>{h}</span></a>')
        else:
            out.append(f'<button class="c-tab" role="tab" type="button" aria-selected="{sel}"{f}><span{a}>{h}</span></button>')
    role = "" if link else ' role="tablist"'
    return f'<div class="c-tabs"{role}>{"".join(out)}</div>'


@comp("pagination", "Navigation")
def c_pagination(ctx, n, o):
    S = o.css
    pg = n.get("pages") or {}
    S.rule(".c-pager", [("display", "flex"), ("flex-wrap", "wrap"), ("align-items", "center"), ("gap", "var(--space-sp-3)")])
    S.rule(".c-pager__sum", ctx.type_decls((n.get("summary") or {}).get("type")) + ctx.paint({k: v for k, v in (n.get("summary") or {}).items() if k == "fg"}) +
           [("font-variant-numeric", "tabular-nums"), ("margin-inline-end", "auto")])
    S.rule(".c-pager__pages", [("display", "none"), ("align-items", "center")])
    S.rule(".c-pager__sum", [("flex-basis", "100%")])
    S.rule(".c-pager__page", ctx.type_decls("{type.mono}") + [("display", "inline-flex"), ("align-items", "center"), ("justify-content", "center"),
                                                           ("min-inline-size", "var(--target-min)"), ("min-block-size", "var(--target-min)"),
                                                           ("text-decoration-line", "none"), ("font-variant-numeric", "tabular-nums"),
                                                           ("border-block-end", ctx.border({**((pg.get("current") or {}).get("rule") or {"width": 2, "style": "solid"}), "color": "transparent"})),
                                                           ("transition", ctx.transition("link"))] + ctx.paint(pg.get("other") or {}))
    ctx.states(S, ".c-pager__page", "hover", [("color", ctx.color("{color.fg}"))])
    S.rule('.c-pager__page[aria-current="page"]', ctx.paint(pg.get("current") or {}))
    S.rule(".c-pager__gap", ctx.type_decls("{type.mono}") + [("color", ctx.color("{color.muted}")), ("padding-inline", "var(--space-sp-2)")])
    S.rule('.c-pager .c-button[aria-disabled="true"]', [("color", ctx.color("{color.state.disabled_fg}")), ("border-color", ctx.color("{color.border}"))])
    S.rule(".c-pager__size", [("display", "none"), ("align-items", "center"), ("gap", "var(--space-sp-2)")])
    m = ctx.mq("tablet")
    if m:
        i = Sheet()
        i.rule(".c-pager__pages", [("display", "flex")])
        i.rule(".c-pager__sum", [("flex-basis", "auto")])
        S.media(m, i)
    dq = ctx.mq("desktop")
    if dq:
        i = Sheet()
        i.rule(".c-pager__size", [("display", "flex")])
        S.media(dq, i)
    o.spec("rest · current · hover · focus", pager_html(ctx, 1, 25, 312, current=1, force={2: "hover", 3: "focus"}),
           f"current {bind(pg.get('current'))} · other {bind(pg.get('other'))} · max {pg.get('max_visible')} visible", wide=True)
    o.spec("disabled · first page prev", pager_html(ctx, 1, 25, 312, current=1, size=False), "prev aria-disabled, stays focusable", wide=True)
    o.notes.append(n.get("phone", ""))


def pager_html(ctx, a, b, total, current=1, force=None, size=True, compact=False):
    n = ctx.comp("pagination") or {}
    force = force or {}
    pg = n.get("pages") or {}
    pn = n.get("prev_next") or {}
    icons = pn.get("icons") or ["chevron-left", "chevron-right"]
    sm = ctx.s("platform.pagination.summary", (n.get("summary") or {}).get("format", "{from}–{to} of {total}"))
    fr = ctx.fr("platform.pagination.summary")
    tot = f"{total:,}".replace(",", " ")
    fmt = dict(**{"from": a, "to": b, "total": tot})
    sa = f' data-en="{esc(sm.format(**fmt))}" data-fr="{esc(fr.format(**fmt))}"' if fr else ""
    last = max(1, -(-total // max(1, b - a + 1)))
    nums = [1, 2, 3, 4, 5, "…", last] if last > 7 else list(range(1, last + 1))
    pages = []
    for k in nums:
        if k == "…":
            pages.append(f'<span class="c-pager__gap" aria-hidden="true">{esc(pg.get("ellipsis", "…"))}</span>')
            continue
        cur = ' aria-current="page"' if k == current else ""
        f = f' data-force="{force[k]}"' if k in force else ""
        pages.append(f'<a class="c-pager__page" href="#"{cur}{f}>{k}</a>')
    prev_dis = ' aria-disabled="true"' if current == 1 else ""
    prev = btn(ctx, pn.get("variant", "secondary"), "Previous", "platform.pagination.prev", icon=icons[0], href="#", attrs=prev_dis)
    nxt_dis = ' aria-disabled="true"' if current >= last else ""
    nxt = btn(ctx, pn.get("variant", "secondary"), "Next", "platform.pagination.next", icon=icons[1], href="#", icon_end=True, attrs=nxt_dis)
    sz = ""
    ps = n.get("page_size") or {}
    if size and ps:
        i = uid(ctx, "ps")
        lh, la = ctx.tx("platform.pagination.per_page", "Rows per page")
        opts = "".join(f'<option{" selected" if x == ps.get("default") else ""}>{x}</option>' for x in ps.get("options", []))
        sz = (f'<span class="c-pager__size c-field--inline"><label class="c-field__label" for="{i}"{la}>{lh}</label>'
              f'<span class="c-select"><select class="c-input" id="{i}">{opts}</select>'
              f'{ctx.icon("chevron-down", 16, "c-select__icon")}</span></span>')
    return (f'<nav class="c-pager"{ctx.aria("platform.pagination.label", "Pagination")}><p class="c-pager__sum"{sa}>{esc(sm.format(**fmt))}</p>'
            f'{sz}{prev}<span class="c-pager__pages">{"".join(pages)}</span>{nxt}</nav>')


@comp("footer", "Navigation")
def c_footer(ctx, n, o):
    S = o.css
    S.rule(".c-footer", [("background-color", ctx.color(n.get("bg"))), ("color", ctx.color(n.get("fg"))),
                         ("border-block-start", ctx.border(n.get("rule"))),
                         ("padding-block", ctx.length(n.get("padding_block", "{space.sp-7}")))])
    S.rule(".c-footer__grid", [("display", "grid"), ("gap", "var(--space-sp-5)"), ("grid-template-columns", "minmax(0, 1fr)")])
    S.rule(".c-footer__brand", [("display", "grid"), ("gap", "var(--space-sp-3)"), ("align-content", "start")])
    lk = n.get("lockup") or {}
    S.rule(".c-footer__lockup", [("block-size", px(footer_lockup_px(ctx))), ("inline-size", "auto"), ("align-self", "flex-start")])
    S.rule(".c-footer__tagline", ctx.type_decls((n.get("tagline") or {}).get("type")) + ctx.paint({"fg": (n.get("tagline") or {}).get("fg")}))
    S.rule(".c-footer__head", ctx.type_decls((n.get("column_head") or {}).get("type")) + ctx.paint({"fg": (n.get("column_head") or {}).get("fg")}) +
           [("margin-block-end", "var(--space-sp-2)"), ("display", "flex"), ("align-items", "center"), ("min-block-size", "var(--target-min)")])
    S.rule(".c-footer__headlink", [("display", "inline-flex"), ("align-items", "center"), ("min-block-size", "var(--target-min)"),
                                   ("color", "inherit"), ("text-decoration-line", "none"), ("transition", ctx.transition("link"))])
    ctx.states(S, ".c-footer__headlink", "hover", [("text-decoration-line", "underline")])
    cl = n.get("column_link") or {}
    S.rule(".c-footer__link", ctx.type_decls(cl.get("type")) + [("display", "flex"), ("align-items", "center"),
                                                               ("min-block-size", "var(--target-min)"), ("color", ctx.color(cl.get("fg"))),
                                                               ("text-decoration-line", cl.get("decoration", "none")),
                                                               ("transition", ctx.transition("link"))])
    ctx.states(S, ".c-footer__link", "hover", [("text-decoration-line", (cl.get("hover") or {}).get("decoration", "underline"))])
    lg = n.get("legal_line") or {}
    S.rule(".c-footer__legal", ctx.type_decls(lg.get("type")) + [("font-size", px(lg["size"])) if lg.get("size") else None,
                                                                ("color", ctx.color(lg.get("fg"))),
                                                                ("border-block-start", ctx.border(lg.get("rule"))),
                                                                ("margin-block-start", "var(--space-sp-5)"),
                                                                ("display", "flex"), ("flex-wrap", "wrap"), ("align-items", "center"),
                                                                ("column-gap", "var(--space-sp-3)")])
    S.rule(".c-footer__legal a", [("display", "inline-flex"), ("align-items", "center"), ("min-block-size", "var(--target-min)"),
                                  ("min-inline-size", "var(--target-min)"), ("justify-content", "center"),
                                  ("color", "inherit"), ("text-decoration-line", "none")])
    ctx.states(S, ".c-footer__legal a", "hover", [("text-decoration-line", "underline")])
    S.rule(".c-footer__legal .c-lang", [("margin-inline-start", "auto")])
    m, d = ctx.mq("tablet"), ctx.mq("desktop")
    if m:
        i = Sheet()
        i.rule(".c-footer__grid", [("grid-template-columns", "repeat(3, minmax(0, 1fr))")])
        i.rule(".c-footer__brand", [("grid-column", "1 / -1")])
        S.media(m, i)
    if d:
        i = Sheet()
        i.rule(".c-footer__grid", [("grid-template-columns", "repeat(12, minmax(0, 1fr))"), ("column-gap", "var(--grid-desktop-gutter)")])
        i.rule(".c-footer__brand", [("grid-column", "1 / span 3")])
        i.rule(".c-footer__col", [("grid-column", "span 3")])
        S.media(d, i)
    o.spec("rest · hover · focus", footer_html(ctx, force=True), f"bg {str(n.get('bg')).strip('{}')} · rule {bind({'r': n.get('rule')})[2:]} · never Ink", wide=True)
    o.notes.append("$gap on footer.value is a container gap; the slots are filled (P-WEB-04)")


def footer_lockup_px(ctx):
    """Never at the floor: the lockup's minimum × 1.25 at least (p14 — a
    lockup at its minimum reads as a grey bar)."""
    lk = ((ctx.comp("footer") or {}).get("lockup") or {})
    mn = (((ctx.cfg.get("logo") or {}).get("minimum") or {}).get("lockup") or {}).get("px") or 0
    v = max(lk.get("px", 72), -(-mn * 5 // 4))
    return int(-(-v // 8) * 8)


def footer_html(ctx, force=False):
    n = ctx.comp("footer") or {}
    cols = n.get("columns") or {}
    keys = {"training": "footer.training", "advisory": "footer.advisory", "company": "footer.company"}
    nav_keys = {"Platform": "nav.platform", "Insights": "nav.insights", "About": "nav.about", "Contact": "nav.contact",
                "LinkedIn": "footer.linkedin"}
    pl = pillars(ctx)
    by_label = {p["label"]: p for p in pl}
    by_fw = {(p.get("framework") or ""): p for p in pl}
    colhtml = []
    for c, items in ((k, cols[k]) for k in live(cols)):
        hh, ha = ctx.tx(keys.get(c), c.capitalize())
        head_href = ctx.href(c, None)
        head = (f'<h2 class="c-footer__head"><a class="c-footer__headlink" href="{esc(head_href)}"{ha}>{hh}</a></h2>' if head_href
                else f'<h2 class="c-footer__head"{ha}>{hh}</h2>')
        lis = []
        for k, it in enumerate(items):
            if it in nav_keys:
                ih, ia = ctx.tx(nav_keys.get(it), it)
                href = ctx.href(nav_keys[it].split(".")[-1])
            elif it in by_label:
                ih, ia, href = esc(it), "", ctx.href("pillar-" + by_label[it]["key"])
            elif it in by_fw:
                ih, ia = esc(fw_name(ctx, by_fw[it]) or it), ""
                href = ctx.href("advisory") + (f'#fw-{by_fw[it]["key"]}' if ctx.links else "")
            else:
                ih, ia, href = esc(it), "", "#"
            f = ' data-force="hover"' if force and c == "training" and k == 1 else (' data-force="focus"' if force and c == "company" and k == 0 else "")
            lis.append(f'<li><a class="c-footer__link" href="{esc(href)}"{f}><span{ia}>{ih}</span></a></li>')
        colhtml.append(f'<div class="c-footer__col">{head}<ul>{"".join(lis)}</ul></div>')
    lk = (n.get("lockup") or {})
    files = ((ctx.cfg.get("logo") or {}).get("files") or {})
    lp = (files.get(lk.get("asset", "lockup")) or {}).get("path")
    logo = ""
    if lp:
        logo = (f'<img class="c-footer__lockup logo-lockup" src="{{ASSETS}}logos/{esc(pathlike(lp))}" '
                f'alt="{esc(ctx.cfg.get("brand", ""))}" height="{footer_lockup_px(ctx)}">')
    tag = ((ctx.cfg.get("identity") or {}).get("positioning") or {}).get("tagline") or {}
    if isinstance(tag, dict) and ctx.lang != "en" and tag.get(ctx.lang):
        th, ta = esc(tag[ctx.lang]), ""
    else:
        th = esc(tag.get("en", "")) if isinstance(tag, dict) else ""
        ta = f' data-en="{esc(tag.get("en"))}" data-fr="{esc(tag.get("fr"))}"' if isinstance(tag, dict) and tag.get("fr") and ctx.lang == "en" else ""
    legal = ctx._lookup("en", "footer.legal") or {}
    ll = []
    for k in live(legal):
        h, a = ctx.tx(f"footer.legal.{k}", legal[k])
        href = ctx.href("legal") + (f"#legal-{k}" if ctx.links else "")
        ll.append(f'<a href="{esc(href)}"><span{a}>{h}</span></a>')
    eh, ea = ctx.tx("footer.entity", ctx.cfg.get("brand", ""))
    yr = re.search(r"\d{4}", str(ctx.cfg.get("date", "")))
    return (f'<footer class="c-footer"><div class="p-container"><div class="c-footer__grid"><div class="c-footer__brand">{logo}'
            f'<p class="c-footer__tagline"{ta}>{th}</p></div>{"".join(colhtml)}</div>'
            f'<div class="c-footer__legal"><span{ea}>{eh}</span>{"".join(ll)}'
            f'<span>© {yr.group(0) if yr else ""}</span>{lang_html(ctx)}</div></div></footer>')


def pathlike(p):
    return pathlib_name(p)


def pathlib_name(p):
    return str(p).rsplit("/", 1)[-1]


@comp("mobile_nav", "Navigation")
def c_mobile_nav(ctx, n, o):
    S = o.css
    w = n.get("width") or {}
    S.rule(".c-mnav", [("display", "flex"), ("flex-direction", "column"), ("inline-size", "100%"), ("max-inline-size", "100%"),
                       ("margin-inline-start", "auto"), ("overflow-y", "auto"),
                       ("overscroll-behavior", "contain"), ("padding", "var(--space-sp-3) var(--space-sp-4) var(--space-sp-5)")] +
           ctx.elev_decls((ctx.comp("drawer") or {}).get("elevation", "{elevation.e3}")))
    S.rule(".c-mnav__top", [("display", "flex"), ("justify-content", "space-between"), ("align-items", "center"),
                            ("min-block-size", "var(--density-comfortable-row)")])
    S.rule(".c-mnav__group", [("display", "grid"), ("margin-block-start", "var(--space-sp-3)")])
    S.rule(".c-mnav__link", [("display", "flex"), ("align-items", "center"), ("min-block-size", f"var(--density-{n.get('density', 'comfortable')}-row)"),
                             ("border-block-end", ctx.border(n.get("row_rule"))), ("text-decoration-line", "none"),
                             ("transition", ctx.transition("row"))] + ctx.type_decls("{type.heading_sm}"))
    ctx.states(S, ".c-mnav__link", "hover", [("background-color", ctx.color("{color.state.surface_hover}"))])
    S.rule('.c-mnav__link[aria-current="page"]', [("border-inline-start", ctx.border(((ctx.comp("nav") or {}).get("item") or {}).get("selected", {}).get("edge"))),
                                                   ("padding-inline-start", "var(--space-sp-3)")])
    S.rule(".c-mnav .c-button", [("inline-size", "100%"), ("margin-block-start", "var(--space-sp-4)")])
    # on a page: a fixed layer the menu button opens (site.js); closed = hidden
    S.rule(".c-mnav-layer", [("position", "fixed"), ("inset", "0"), ("z-index", "20"), ("display", "flex"),
                             ("justify-content", "flex-end")])
    S.rule(".c-mnav-layer[hidden]", [("display", "none")])
    S.rule(".c-mnav-layer > .c-mnav", [("position", "relative"), ("block-size", "100%")])
    S.rule(".is-locked", [("overflow", "hidden")])
    m = ctx.mq("tablet")
    if m and isinstance(w.get("tablet"), (int, float)):
        i = Sheet()
        i.rule(".c-mnav", [("inline-size", px(w["tablet"]))])
        S.media(m, i)
    d = ctx.mq((ctx.comp("header") or {}).get("breakpoint_collapse", "desktop"))
    if d:
        i = Sheet()
        i.rule(".c-mnav-layer", [("display", "none")])
        S.media(d, i)
    o.spec("open (static) · hover", overlay_frame(ctx, mnav_html(ctx), scrim=True, side="end", tall=True),
           f"base drawer · {px(w.get('tablet', 420))} tablet, 100% phone · {n.get('behaviour', '')[:60]}", wide=True)


def mnav_html(ctx, current="Learn", page=False):
    """The drawer. page=True wraps it in the hidden layer the menu button
    opens (id mnav, a scrim that closes it) and drops the fixture's forced hover."""
    n = ctx.comp("mobile_nav") or {}
    cl = n.get("close") or {}
    links = []
    for k, (lab, key) in enumerate(web_labels(ctx)):
        h, a = ctx.tx(key, lab)
        cur = ' aria-current="page"' if lab == current else ""
        f = ' data-force="hover"' if k == 2 and not page else ""
        links.append(f'<a class="c-mnav__link" href="{esc(nav_href(ctx, key))}"{cur}{f}><span{a}>{h}</span></a>')
    g2 = []
    for g in n.get("groups") or []:
        if isinstance(g, list):
            for lab in g:
                if lab in [x for x, _ in web_labels(ctx)]:
                    continue
                h, a = ctx.tx(f"nav.{lab.lower()}", lab)
                cur = ' aria-current="page"' if lab == current else ""
                g2.append(f'<a class="c-mnav__link" href="{esc(nav_href(ctx, "nav." + lab.lower()))}"{cur}><span{a}>{h}</span></a>')
    # The Training page is linked from the footer and the hero CTA; the
    # drawer must reach it too, or it is unreachable on a phone.
    tr_h, tr_a = ctx.tx("footer.training", "")
    if tr_h and "training" in getattr(ctx, "pages", {"training"}) and not any('training' in x for x in g2):
        g2.insert(0, f'<a class="c-mnav__link" href="{esc(ctx.href("training"))}"><span{tr_a}>{tr_h}</span></a>')
    cta = (ctx.comp("header") or {}).get("cta") or {}
    close = " data-close" if page else ""
    panel = (f'<div class="c-mnav" role="dialog" aria-modal="true"{ctx.aria("nav.menu", "Menu")}><div class="c-mnav__top">'
             f'{mark_svg(ctx, 32)}<button class="c-iconbtn" type="button"{close}{ctx.aria("nav.close_menu", cl.get("label", "Close"))}>'
             f'{ctx.icon(cl.get("icon", "x"), 20)}</button></div><nav class="c-mnav__group"{ctx.aria("nav.main_nav", "Main")}>{"".join(links)}</nav>'
             f'<div class="c-mnav__group">{"".join(g2)}</div><div class="c-mnav__group">{lang_html(ctx)}</div>'
             f'{btn(ctx, cta.get("variant", "primary"), "Talk to us", "cta.talk", href=ctx.href("contact"))}</div>')
    if not page:
        return panel
    return f'<div class="c-mnav-layer" id="mnav" hidden><div class="c-scrim" data-close aria-hidden="true"></div>{panel}</div>'


def overlay_frame(ctx, inner, scrim=False, side="center", tall=False, top=None):
    s = '<div class="c-scrim" aria-hidden="true"></div>' if scrim else ""
    t = f' style="padding-block-start: {top}"' if top else ""
    return f'<div class="fx-oframe fx-oframe--{side}{" fx-oframe--tall" if tall else ""}"{t}>{s}{inner}</div>'


# ── Content ──────────────────────────────────────────────────────────────
@comp("card", "Content")
def c_card(ctx, n, o):
    S = o.css
    S.rule(".c-panel", ctx.elev_decls("{elevation.e1}") + [("border-radius", ctx.length("{radius.surface}")),
                                                         ("padding", "var(--space-sp-4)"), ("display", "grid"), ("gap", "var(--space-sp-2)")])
    S.rule(".c-ruled", [("border-block-start", ctx.border((((ctx.cfg.get("layout") or {}).get("rules") or {}).get("heavy"))) or "none"),
                        ("padding-block-start", "var(--space-sp-3)"), ("display", "grid"), ("gap", "var(--space-sp-2)")])
    S.rule(".c-panel__title, .c-ruled__title", ctx.type_decls("{type.heading_sm}"))
    pos = (ctx.cfg.get("identity") or {}).get("positioning") or {}
    wi = pos.get("what_it_is", "")
    o.spec(f"value {n.get('value')} · use the rule", f'<div class="c-ruled"><h3 class="c-ruled__title">{esc(pos.get("architecture", ""))}</h3><p class="fx-prose">{esc(wi)}</p></div>',
           "heavy rule · the rail · no 8px card")
    o.spec("where a section needs edges · e1", f'<div class="c-panel"><h3 class="c-panel__title">{esc(pos.get("architecture", ""))}</h3><p class="fx-prose">{esc(wi)}</p></div>',
           "elevation.e1 · radius.surface")


@comp("section", "Content")
def c_section(ctx, n, o):
    S = o.css
    pb = n.get("padding_block") or {}
    S.rule(".c-section", [("padding-block", ctx.length(pb.get("phone")))])
    for bp in ("tablet", "desktop"):
        m = ctx.mq(bp)
        if m and pb.get(bp):
            i = Sheet()
            i.rule(".c-section", [("padding-block", ctx.length(pb[bp]))])
            S.media(m, i)
    sf = n.get("surfaces") or {}
    S.rule('.c-section[data-surface="ink"]', ctx.paint(sf.get("ink") or {}, True))
    # two white sections meet with one gap, not two: the rhythm is the gap
    S.rule('[data-surface="white"] + .c-section[data-surface="white"]', [("padding-block-start", "0")])
    hd = n.get("heading") or {}
    S.rule(".c-section__head", [("display", "grid"), ("gap", "var(--space-sp-4)"), ("margin-block-end", "var(--space-sp-5)")])
    S.rule(".c-section__rule", [("border-block-start", ctx.border(hd.get("heavy_rule"))),
                                ("padding-block-start", "var(--space-sp-3)")] + ctx.type_decls("{type.eyebrow}") + [("color", ctx.color("{color.muted}"))])
    S.rule('[data-surface="ink"] .c-section__rule', [("border-block-start-color", ctx.color("{color.bg}", True)),
                                                     ("color", ctx.color("{color.muted_on_dark}", True))])
    S.rule(".c-section__title", ctx.type_decls(hd.get("type")) + [("text-wrap", "balance")])
    S.rule('[data-surface="ink"] .c-accent', [("color", ctx.color("{color.accent_on_dark}", True))])
    d = ctx.mq("desktop")
    if d:
        i = Sheet()
        i.rule(".c-section__head", [("grid-template-columns", "repeat(12, minmax(0, 1fr))"), ("column-gap", "var(--grid-desktop-gutter)")])
        i.rule(".c-section__head > .c-section__rule", [("grid-column", "1 / span 3"), ("align-self", "start")])
        i.rule(".c-section__head > .c-section__title", [("grid-column", "4 / -1")])
        S.media(d, i)
    t = (ctx.cfg.get("identity") or {}).get("positioning", {}).get("architecture", "Section")
    o.spec("white", section_head(ctx, "01", t), bind(sf.get("white")) + " · heavy rule block-start, rail width", wide=True)
    o.spec("ink", f'<div class="c-section" data-surface="ink" style="padding-block: var(--space-sp-5)"><div class="p-container">{section_head(ctx, "02", t)}</div></div>',
           bind(sf.get("ink")) + " · " + str(n.get("cadence", "")), wide=True, frame="bare")


def section_head(ctx, num, title, key=None, eyebrow=None):
    h, a = ctx.tx(key, title, accent=True) if key else (accent_html(title), "")
    return (f'<div class="c-section__head"><p class="c-section__rule">{esc(eyebrow or num)}</p>'
            f'<h2 class="c-section__title"{a}>{h}</h2></div>')


@comp("hero", "Content")
def c_hero(ctx, n, o):
    S = o.css
    h1 = n.get("h1") or {}
    S.rule(".c-hero", [("overflow-x", "clip"), ("padding-block", "var(--space-sp-6) var(--space-sp-5)")])
    S.rule(".c-hero__grid", [("display", "grid"), ("gap", "var(--space-sp-5)"), ("align-items", "center")])
    S.rule(".c-hero__text", [("display", "grid"), ("gap", "var(--space-sp-4)"), ("align-content", "start")])
    S.rule(".c-hero__h1", ctx.type_decls(h1.get("type")) + [("text-wrap", h1.get("wrap", "balance"))])
    S.rule(".c-hero__eyebrow", ctx.type_decls("{type.eyebrow}") + [("color", ctx.color("{color.muted}"))])
    S.rule(".c-hero__lead", ctx.type_decls((n.get("lead") or {}).get("type")) + [("max-inline-size", "44ch")])
    S.rule(".c-hero__ctas", [("display", "flex"), ("flex-wrap", "wrap"), ("gap", ctx.length((n.get("ctas") or {}).get("gap")))])
    S.rule(".c-hero__shot", [("display", "grid"), ("gap", "var(--space-sp-3)"), ("min-inline-size", "0")])
    S.rule(".c-hero__shot > .c-shot, .c-hero__shot > .c-frame", [("margin-inline-end", "calc(-1 * var(--grid-phone-margin))")])
    pr = n.get("proof") or {}
    S.rule(".c-hero__proof", ctx.type_decls(pr.get("type")) + [("color", ctx.color(pr.get("fg")))])
    t, d = ctx.mq("tablet"), ctx.mq("desktop")
    if t:
        i = Sheet()
        i.rule(".c-hero__shot > .c-shot, .c-hero__shot > .c-frame", [("margin-inline-end", "calc(-1 * var(--grid-tablet-margin))")])
        S.media(t, i)
    if d:
        i = Sheet()
        i.rule(".c-hero__grid", [("grid-template-columns", "repeat(12, minmax(0, 1fr))"), ("column-gap", "var(--grid-desktop-gutter)")])
        i.rule(".c-hero__text", [("grid-column", "1 / span 6")])
        i.rule(".c-hero__shot", [("grid-column", "8 / -1")])
        i.rule(".c-hero__shot > .c-shot, .c-hero__shot > .c-frame", [("margin-inline-end", "calc(-1 * var(--grid-desktop-margin) - var(--space-sp-6))")])
        S.media(d, i)
    # the product miniature (hero screenshot) — the platform, inert, small
    S.rule(".c-shot", [("min-inline-size", "0")])
    S.rule(".c-shot__frame", [("display", "flex"), ("border", ctx.border({"width": 1, "style": "solid", "color": "{color.border}"})),
                              ("background-color", ctx.color("{color.bg}")), ("min-block-size", "calc(var(--space-sp-8) * 2.6)"),
                              ("overflow", "hidden"), ("zoom", "0.62")])
    S.rule(".c-shot .c-sidebar", [("inline-size", "calc(var(--space-sp-8) + var(--space-sp-6))")])
    S.rule(".c-shot__main", [("flex", "1"), ("padding", "var(--space-sp-4)"), ("display", "grid"), ("gap", "var(--space-sp-3)"), ("min-inline-size", "calc(var(--space-sp-8) * 4)")])
    S.rule(".c-shot__eyebrow, .c-shot__label, .c-shot__sub, .c-shot__zone", ctx.type_decls("{type.eyebrow}") + [("color", ctx.color("{color.muted}"))])
    S.rule(".c-shot__kpi", ctx.type_decls("{type.display_lg}") + [("font-variant-numeric", "tabular-nums")])
    S.rule(".c-shot__top", [("display", "grid"), ("grid-template-columns", "minmax(0, 1fr) minmax(0, 1.4fr)"), ("gap", "var(--space-sp-4)"), ("align-items", "start")])
    S.rule(".c-shot__rows", [("display", "grid")])
    S.rule(".c-shot__row", [("display", "grid"), ("grid-template-columns", "minmax(0, 1fr) auto 4ch"), ("gap", "var(--space-sp-3)"), ("align-items", "center"),
                            ("min-block-size", "var(--density-compact-row)"), ("border-block-start", ctx.border({"width": 1, "style": "solid", "color": "{color.border}"}))] +
           ctx.type_decls("{type.caption}"))
    S.rule(".c-shot__num", ctx.type_decls("{type.mono}") + [("text-align", "end")])
    S.rule(".c-shot__name", [("overflow", "hidden"), ("text-overflow", "ellipsis"), ("white-space", "nowrap"), ("min-inline-size", "0")])
    o.spec("rest", hero_html(ctx), f"h1 {str(h1.get('type')).strip('{}')} · one accent word · lead {str((n.get('lead') or {}).get('type')).strip('{}')} · motion none", wide=True, frame="bare")


def hero_html(ctx, h1_key="hero.h1", lead_key="hero.lead", shot=None, primary=("cta.primary", "Book a scoping call"),
              secondary=("cta.catalogue", "See the catalogue"), rule_pillar=None, h1_text=None, lead_text=None, sec_href=None,
              lead_attr="", eyebrow=None, subtitle=None):
    """The hero: H1, lead, two CTAs, and the product. The proof line sits
    under the product only — under a frame it would be a line with nothing
    above it (p52: 'the proof is one line and the product above it')."""
    n = ctx.comp("hero") or {}
    if h1_text:
        h, a = esc(h1_text), ""
    else:
        h, a = ctx.tx(h1_key, "", accent=True)
    if lead_text is not None:
        lh, la = esc(lead_text), lead_attr
    else:
        lh, la = ctx.tx(lead_key, "")
    shot = shot if shot is not None else product_shot(ctx)
    proof = ctx.el("p", "hero.proof", ((ctx.comp("proof_line") or {}).get("format") or ""), "c-hero__proof") if 'class="c-shot"' in shot else ""
    pr = f' style="border-block-start: {ctx.border({"width": 2.4, "style": "solid", "color": "{color.pillar.%s}" % rule_pillar})}; padding-block-start: var(--space-sp-4)"' if rule_pillar else ""
    eb = f'<p class="c-hero__eyebrow">{esc(eyebrow)}</p>' if eyebrow else ""
    lead = f'<p class="c-hero__lead"{la}>{lh}</p>' if lh else ""
    return (f'<div class="c-hero"><div class="p-container c-hero__grid"><div class="c-hero__text"{pr}>'
            f'{eb}<h1 class="c-hero__h1"{a}>{h}</h1>{subtitle or ""}{lead}<div class="c-hero__ctas">'
            f'{btn(ctx, "primary", primary[1], primary[0], href=ctx.href("contact"))}'
            f'{btn(ctx, "secondary", secondary[1], secondary[0], href=sec_href or ctx.href("training"))}</div></div>'
            f'<div class="c-hero__shot">{shot}{proof}</div></div></div>')


def product_shot(ctx, screen="dashboard"):
    """The product, cropped at the edge: a live miniature of ONE platform
    screen — the dashboard (KPI, quadrant, ranked rows) — built from the same
    components, inert, and named for what it is. Never relabelled as another
    screen: a page that needs a different screen gets a labelled frame."""
    if not ctx.comp("quadrant") or screen != "dashboard":
        return frame(ctx.s(f"platform.nav.{screen}", screen), "4 / 3", kind="screenshot")
    data, _ = examples(ctx)
    rows = "".join(f'<li class="c-shot__row"><span class="c-shot__name">{esc(nm)}</span><span class="c-shot__zone">{esc(ctx.s("platform.quadrant.zones." + zone(ctx, r, i)[0], zone(ctx, r, i)[1]))}</span>'
                   f'<span class="c-shot__num">{sc}</span></li>' for nm, r, i, sc in sorted(data, key=lambda d: -d[3]))
    k1, a1 = ctx.tx("platform.kpi.scored", "use cases scored")
    k2 = ctx.s("platform.kpi.in_build", "{n} in build").format(n=7)
    k3 = ctx.s("platform.kpi.live", "{n} live").format(n=3)
    plat = offer(ctx, "platform.dashboard_label") or ctx.cfg.get("brand", "")
    title = ctx.s("platform.nav.dashboard", "Dashboard")
    return (f'<figure class="c-shot" role="img" aria-label="{esc(plat)} — {esc(title)}">'
            f'<div class="c-shot__frame" inert aria-hidden="true">{sidebar_html(ctx, current="dashboard")}'
            f'<div class="c-shot__main"><p class="c-shot__eyebrow">{esc(title)}</p><div class="c-shot__top">'
            f'<div><p class="c-shot__kpi">24</p><p class="c-shot__label">{k1}</p><p class="c-shot__sub">{esc(k2)} · {esc(k3)}</p></div>'
            f'{quadrant_html(ctx, cap=False)}</div><ol class="c-shot__rows">{rows}</ol></div></div></figure>')


@comp("pillar_block", "Content")
def c_pillar_block(ctx, n, o):
    S = o.css
    col = n.get("column") or {}
    S.rule(".c-pillars", [("display", "grid"), ("grid-template-columns", "minmax(0, 1fr)"), ("column-gap", "var(--grid-phone-gutter)")])
    S.rule(".c-pillar", [("display", "grid"), ("gap", "var(--space-sp-2)"), ("align-content", "start"),
                         ("padding-block", ctx.length(col.get("pad_block"))),
                         (f"border-{col.get('rule_side', 'block-start')}", ctx.border(col.get("rule")))])
    for p in pillars(ctx):
        S.rule(f'.c-pillar[data-pillar="{p["key"]}"]', [(f"border-{col.get('rule_side', 'block-start')}-color", ctx.color("{color.pillar.%s}" % p["key"]))])
    S.rule(".c-pillar__eyebrow", ctx.type_decls((col.get("eyebrow") or {}).get("type")) + [("color", ctx.color((col.get("eyebrow") or {}).get("fg")))])
    S.rule(".c-pillar__title", ctx.type_decls((col.get("title") or {}).get("type")) + [("color", ctx.color((col.get("title") or {}).get("fg")))])
    S.rule(".c-pillar__sub", ctx.type_decls("{type.caption}") + [("color", ctx.color("{color.muted}"))])
    S.rule(".c-pillar__body", ctx.type_decls((col.get("body") or {}).get("type")))
    S.rule(".c-pillar .c-button", [("justify-self", "start")])
    t, d = ctx.mq("tablet"), ctx.mq("desktop")
    if t:
        i = Sheet()
        i.rule(".c-pillars", [("grid-template-columns", "repeat(2, minmax(0, 1fr))"), ("column-gap", "var(--grid-tablet-gutter)")])
        S.media(t, i)
    if d:
        i = Sheet()
        i.rule(".c-pillars", [("grid-template-columns", "repeat(4, minmax(0, 1fr))"), ("column-gap", "var(--grid-desktop-gutter)")])
        S.media(d, i)
    o.spec("rest · tertiary link hover/focus", pillar_block_html(ctx, force=True),
           f"rule {bind({'r': col.get('rule')})[2:]} → color.pillar.<pillar> · no icons, no cards", wide=True)


def offer(ctx, path):
    """copy.<lang>.offer.<path> (EN fallback), or None."""
    return ctx.node("offer." + path)


def pillar_block_html(ctx, force=False):
    n = ctx.comp("pillar_block") or {}
    col = n.get("column") or {}
    sub_h, sub_a = ctx.tx("pillars.build_subtitle", "")
    lis = []
    for k, p in enumerate(pillars(ctx)):
        sub = f'<span class="c-pillar__sub"{sub_a}>{sub_h}</span>' if p.get("subtitle") else ""
        a = ' data-force="hover"' if force and k == 1 else (' data-force="focus"' if force and k == 2 else "")
        body = offer(ctx, f"pillars.{p['key']}.body")
        body_h = (f'<p class="c-pillar__body">{esc(body)}</p>' if isinstance(body, str) and body
                  else slot(p["label"], (col.get("body") or {}).get("max_words"), cls="c-pillar__body", brief="pillar_block.column.body"))
        fw = offer(ctx, f"frameworks.{p['key']}.name") or p.get("framework") or ""
        lis.append(f'<li class="c-pillar" data-pillar="{p["key"]}"><p class="c-pillar__eyebrow">{esc(fw)}</p>'
                   f'<h3 class="c-pillar__title">{esc(p["label"])}</h3>{sub}{body_h}'
                   f'{btn(ctx, "tertiary", p["label"], href=ctx.href("pillar-" + p["key"]), attrs=a)}</li>')
    return f'<ul class="c-pillars">{"".join(lis)}</ul>'


@comp("programme_list", "Content")
def c_programme(ctx, n, o):
    S = o.css
    rw = n.get("row") or {}
    S.rule(".c-prog", [("border-block-start", ctx.border(n.get("head_rule"))), ("padding-block-start", "var(--space-sp-3)")])
    for p in pillars(ctx):
        S.rule(f'.c-prog[data-pillar="{p["key"]}"]', [("border-block-start-color", ctx.color("{color.pillar.%s}" % p["key"]))])
    dl = n.get("delivery_line") or {}
    S.rule(".c-prog__delivery", ctx.type_decls(dl.get("type")) + [("color", ctx.color(dl.get("fg"))), ("margin-block-end", "var(--space-sp-4)")])
    S.rule(".c-prog__row", [("display", "grid"), ("gap", "var(--space-sp-2)"), ("padding-block", ctx.length(rw.get("pad_block"))),
                            ("border-block-end", ctx.border(rw.get("rule")))])
    S.rule(".c-prog__tier", ctx.type_decls((rw.get("tier") or {}).get("type")) + [("color", ctx.color((rw.get("tier") or {}).get("fg")))])
    S.rule(".c-prog__body", [("display", "grid"), ("gap", "var(--space-sp-2)"), ("justify-items", "start")])
    S.rule(".c-prog__title", ctx.type_decls((rw.get("title") or {}).get("type") or "{type.heading_md}"))
    S.rule(".c-prog__text", ctx.type_decls((rw.get("body") or {}).get("type") or "{type.body}") + [("max-inline-size", "var(--measure)")])
    S.rule(".c-prog__aud", ctx.type_decls((rw.get("audience") or {}).get("type") or "{type.caption}") +
           [("color", ctx.color((rw.get("audience") or {}).get("fg") or "{color.muted}"))])
    S.rule(".c-prog__name", ctx.type_decls("{type.heading_lg}") + [("margin-block-end", "var(--space-sp-2)")])
    S.rule(".c-prog__name a", [("display", "inline-flex"), ("align-items", "center"), ("min-block-size", "var(--target-min)"),
                               ("text-decoration-line", "none"), ("transition", ctx.transition("link"))])
    ctx.states(S, ".c-prog__name a", "hover", [("text-decoration-line", "underline")])
    d = ctx.mq("desktop")
    if d:
        i = Sheet()
        i.rule(".c-prog__row", [("grid-template-columns", "repeat(12, minmax(0, 1fr))"), ("column-gap", "var(--grid-desktop-gutter)")])
        i.rule(".c-prog__tier", [("grid-column", "1 / span 3")])
        i.rule(".c-prog__body", [("grid-column", "4 / -1")])
        S.media(d, i)
    pl = pillars(ctx)
    o.spec("rest", programme_html(ctx, pl[0] if pl else None), f"head_rule → page pillar · {dl.get('$note', '')}", wide=True)


def programme_html(ctx, pillar, head=None):
    """The three programmes of one pillar: tier, title, body, audience, one link.
    From copy.<lang>.offer.pillars.<pillar>.programmes; a tier the config does
    not fill is a labelled frame."""
    n = ctx.comp("programme_list") or {}
    rw = n.get("row") or {}
    tiers = (rw.get("tier") or {}).get("values") or []
    keys = ["briefing", "core", "applied"]
    progs = offer(ctx, f"pillars.{(pillar or {}).get('key')}.programmes") or {}
    rows = []
    for k, t in enumerate(tiers):
        tk = keys[k] if k < len(keys) else None
        h, a = ctx.tx(f"pillars.tier.{tk}" if tk else None, t)
        pr = progs.get(tk) if isinstance(progs, dict) and tk else None
        if isinstance(pr, dict) and pr.get("title"):
            body = (f'<h3 class="c-prog__title">{esc(pr["title"])}</h3>'
                    + (f'<p class="c-prog__text">{esc(pr["body"])}</p>' if pr.get("body") else "")
                    + (f'<p class="c-prog__aud">{esc(pr["audience"])}</p>' if pr.get("audience") else ""))
        else:
            body = slot(f"{(pillar or {}).get('label', '')} · {t}", None, brief="programme_list.row")
        rows.append(f'<li class="c-prog__row"><p class="c-prog__tier"{a}>{h}</p><div class="c-prog__body">{body}'
                    f'{btn(ctx, (rw.get("link") or {}).get("variant", "tertiary"), "Book a scoping call", "cta.primary", href=ctx.href("contact"))}</div></li>')
    dh, da = ctx.tx("pillars.delivery", (n.get("delivery_line") or {}).get("content", ""))
    pk = f' data-pillar="{pillar["key"]}"' if pillar else ""
    return f'<div class="c-prog"{pk}>{head or ""}<p class="c-prog__delivery"{da}>{dh}</p><ol>{"".join(rows)}</ol></div>'


@comp("framework_block", "Content")
def c_framework(ctx, n, o):
    S = o.css
    S.rule(".c-fw", [("display", "grid"), ("gap", "var(--space-sp-4)"), ("padding-block", "var(--space-sp-4) var(--space-sp-5)"),
                     ("border-block-start", ctx.border(n.get("rule")))])
    for p in pillars(ctx):
        S.rule(f'.c-fw[data-pillar="{p["key"]}"]', [("border-block-start-color", ctx.color("{color.pillar.%s}" % p["key"]))])
    S.rule(".c-fw__eyebrow", ctx.type_decls((n.get("eyebrow") or {}).get("type")) + [("color", ctx.color((n.get("eyebrow") or {}).get("fg")))])
    S.rule(".c-fw__title", ctx.type_decls((n.get("title") or {}).get("type")) + [("margin-block-start", "var(--space-sp-2)")])
    S.rule(".c-fw__lists", [("display", "grid"), ("gap", "var(--space-sp-4)")])
    S.rule(".c-fw__summary", ctx.type_decls("{type.body}") + [("margin-block-start", "var(--space-sp-2)"), ("max-inline-size", "32ch")])
    S.rule(".c-fw__head", ctx.type_decls((n.get("list_head") or {}).get("type")) + [("color", ctx.color((n.get("list_head") or {}).get("fg"))),
                                                                                  ("margin-block-end", "var(--space-sp-2)")])
    li = n.get("list_item") or {}
    S.rule(".c-fw__item", ctx.type_decls(li.get("type")) + [("padding-block", "var(--space-sp-2)"), ("border-block-end", ctx.border(li.get("rule")))])
    tl = n.get("terms_line") or {}
    S.rule(".c-fw__terms", ctx.type_decls(tl.get("type")) + [("color", ctx.color(tl.get("fg")))])
    S.rule(".c-fw__foot", [("display", "grid"), ("gap", "var(--space-sp-2)"), ("justify-items", "start")])
    S.rule(".c-fw__foot--row", [("margin-block-start", "var(--space-sp-4)")])
    t, d = ctx.mq("tablet"), ctx.mq("desktop")
    if t:
        i = Sheet()
        i.rule(".c-fw__lists", [("grid-template-columns", "repeat(2, minmax(0, 1fr))"), ("column-gap", "var(--grid-tablet-gutter)")])
        S.media(t, i)
    if d:
        i = Sheet()
        i.rule(".c-fw", [("grid-template-columns", "repeat(12, minmax(0, 1fr))"), ("column-gap", "var(--grid-desktop-gutter)")])
        i.rule(".c-fw__rail", [("grid-column", "1 / span 3")])
        i.rule(".c-fw__lists, .c-fw__foot", [("grid-column", "4 / -1")])
        S.media(d, i)
    pl = pillars(ctx)
    o.spec("rest", framework_html(ctx, pl[0] if pl else None), "rule → the framework's pillar colour · proper noun, no accent word", wide=True)


def fw_name(ctx, p):
    return offer(ctx, f"frameworks.{(p or {}).get('key')}.name") or (p or {}).get("framework") or ""


def framework_row_html(ctx):
    """Home: the four frameworks in one row of names + one line each, one link to Advisory."""
    lis = []
    for p in pillars(ctx):
        sm = offer(ctx, f"frameworks.{p['key']}.summary")
        body = f'<p class="c-pillar__body">{esc(sm)}</p>' if isinstance(sm, str) and sm else slot(fw_name(ctx, p), 12, cls="c-pillar__body", brief="framework one-line summary")
        lis.append(f'<li class="c-pillar" data-pillar="{p["key"]}"><p class="c-pillar__eyebrow">{esc(p["label"])}</p>'
                   f'<h3 class="c-pillar__title">{esc(fw_name(ctx, p))}</h3>{body}</li>')
    th, ta = ctx.tx("framework.terms", ((ctx.comp("framework_block") or {}).get("terms_line") or {}).get("content", ""))
    return (f'<ul class="c-pillars">{"".join(lis)}</ul><div class="c-fw__foot c-fw__foot--row"><p class="c-fw__terms"{ta}>{th}</p>'
            f'{btn(ctx, "tertiary", "Advisory", "nav.advisory", href=ctx.href("advisory"))}</div>')


def framework_html(ctx, p, compact=False):
    n = ctx.comp("framework_block") or {}
    L = n.get("lists") or {}
    eb = ctx.s("framework.eyebrow", "Advisory · {pillar}").format(pillar=p["label"] if p else "")
    fr = ctx.fr("framework.eyebrow") if ctx.lang == "en" else None
    ea = f' data-en="{esc(eb)}" data-fr="{esc(fr.format(pillar=p["label"]))}"' if fr and p else ""
    fw = offer(ctx, f"frameworks.{(p or {}).get('key')}") or {}
    sm = fw.get("summary") if isinstance(fw, dict) else None
    summary = f'<p class="c-fw__summary">{esc(sm)}</p>' if sm else ""
    if not compact:
        parts = []
        for k, key in (("covers", "framework.covers"), ("receives", "framework.receives")):
            spec = L.get(k) or {}
            hh, ha = ctx.tx(key, spec.get("head", k))
            vals = fw.get(k) if isinstance(fw, dict) else None
            if isinstance(vals, list) and vals:
                items = "".join(f'<li class="c-fw__item">{esc(x)}</li>' for x in vals[:spec.get("items_max", len(vals))])
            else:
                items = f'<li class="c-fw__item">{slot(hh, spec.get("words_per_item"), tag="span", brief="framework_block.lists." + k)}</li>'
            parts.append(f'<div><h4 class="c-fw__head"{ha}>{hh}</h4><ul>{items}</ul></div>')
        lists = f'<div class="c-fw__lists">{"".join(parts)}</div>'
    else:
        lists = f'<div class="c-fw__lists">{summary or slot(fw_name(ctx, p), 12)}</div>'
        summary = ""
    th, ta = ctx.tx("framework.terms", (n.get("terms_line") or {}).get("content", ""))
    lk = n.get("link") or {}
    pk = f' data-pillar="{p["key"]}"' if p else ""
    sid = f' id="fw-{p["key"]}"' if p else ""
    return (f'<article class="c-fw"{pk}{sid}><div class="c-fw__rail"><p class="c-fw__eyebrow"{ea}>{esc(eb)}</p>'
            f'<h3 class="c-fw__title">{esc(fw_name(ctx, p))}</h3>{summary}</div>{lists}'
            f'<div class="c-fw__foot"><p class="c-fw__terms"{ta}>{th}</p>'
            f'{btn(ctx, lk.get("variant", "tertiary"), lk.get("label", "Book a scoping call"), "cta.primary", href=ctx.href("contact"))}</div></article>')


@comp("stage_strip", "Content")
def c_stage_strip(ctx, n, o):
    S = o.css
    S.rule(".c-stages", [("display", "grid"), ("grid-template-columns", "minmax(0, 1fr)"), ("gap", "var(--space-sp-3)")])
    S.rule(".c-stage", [("display", "grid"), ("gap", "var(--space-sp-1)"), ("align-content", "start"),
                        ("padding-inline-start", "var(--space-sp-3)"), ("border-inline-start", ctx.border(n.get("rule")))])
    nm = n.get("number") or {}
    S.rule(".c-stage__num", ctx.type_decls(nm.get("type")) + [("color", ctx.color(nm.get("fg")))])
    S.rule(".c-stage__label", ctx.type_decls((n.get("label") or {}).get("type")))
    S.rule(".c-stage__line", ctx.type_decls((n.get("line") or {}).get("type")) + [("color", ctx.color((n.get("line") or {}).get("fg")))])
    t, d = ctx.mq("tablet"), ctx.mq("desktop")
    if t:
        i = Sheet()
        i.rule(".c-stages", [("grid-template-columns", "repeat(3, minmax(0, 1fr))"), ("column-gap", "var(--grid-tablet-gutter)"),
                             ("row-gap", "var(--space-sp-4)")])
        i.rule(".c-stage", [("border-inline-start", "0"), ("padding-inline-start", "0"), ("padding-block-start", "var(--space-sp-3)"),
                            ("border-block-start", ctx.border(n.get("rule")))])
        S.media(t, i)
    if d:
        i = Sheet()
        i.rule(".c-stages", [("grid-template-columns", "repeat(6, minmax(0, 1fr))"), ("column-gap", "var(--grid-desktop-gutter)")])
        S.media(d, i)
    o.spec("rest", stage_strip_html(ctx), f"{n.get('count')} stages · number {bind(nm)} · rule {n.get('rule_side')}", wide=True)


def stage_strip_html(ctx, with_lines=True):
    """The six stages: names from copy.<lang>.offer.stages when present (else
    the naming list), one line each from the same place."""
    n = ctx.comp("stage_strip") or {}
    names = stages(ctx)
    lines = offer(ctx, "stages")
    lis = []
    for k, s in enumerate(names):
        o = lines[k] if isinstance(lines, list) and k < len(lines) and isinstance(lines[k], dict) else {}
        nm = o.get("name") or s
        line = ""
        if with_lines:
            line = (f'<span class="c-stage__line">{esc(o["line"])}</span>' if o.get("line")
                    else slot(nm, (n.get("line") or {}).get("max_words"), cls="c-stage__line", brief="stage_strip.line"))
        lis.append(f'<li class="c-stage"><span class="c-stage__num">{k + 1:02d}</span><span class="c-stage__label">{esc(nm)}</span>{line}</li>')
    return f'<ol class="c-stages"{ctx.aria("stages.eyebrow", "Stages")}>{"".join(lis)}</ol>'


@comp("proof_line", "Content")
def c_proof(ctx, n, o):
    S = o.css
    S.rule(".c-proof", ctx.type_decls(n.get("type")) + [("color", ctx.color(n.get("fg"))), ("display", "flex"), ("flex-wrap", "wrap"),
                                                      ("column-gap", "var(--space-sp-2)"), ("font-variant-numeric", "tabular-nums")])
    S.rule(".c-proof__sep", [("display", "none")])
    S.rule(".c-proof li", [("flex-basis", "100%")])
    t = ctx.mq("tablet")
    if t:
        i = Sheet()
        i.rule(".c-proof__sep", [("display", "inline")])
        i.rule(".c-proof li", [("flex-basis", "auto")])
        S.media(t, i)
    o.spec("rest", proof_html(ctx), f"{str(n.get('type')).strip('{}')} · {n.get('numerals')}", wide=True)


def proof_html(ctx):
    n = ctx.comp("proof_line") or {}
    it = n.get("items") or []
    if ctx.lang != "en":
        loc = [x for x in (ctx.s("hero.proof", "") or "").split(" · ") if x.strip()]
        it = loc or it
    fr = (ctx.fr("hero.proof") or "").split(" · ") if ctx.lang == "en" else []
    parts = []
    for k, x in enumerate(it):
        if k:
            parts.append(f'<li class="c-proof__sep" aria-hidden="true">{esc(n.get("separator", "·"))}</li>')
        a = f' data-en="{esc(x)}" data-fr="{esc(fr[k])}"' if len(fr) == len(it) else ""
        parts.append(f"<li{a}>{esc(x)}</li>")
    return f'<ul class="c-proof">{"".join(parts)}</ul>'


@comp("logo_wall", "Content")
def c_logo_wall(ctx, n, o):
    o.spec("omitted", f'<p class="fx-note">{esc(n.get("$comment", "Omitted until supplied."))}</p>',
           f"caption {bind(n.get('caption'))} · logos {(n.get('logo') or {}).get('height_px')}px · filter none")
    o.notes.append("NOT RENDERED: no client logos are supplied; the component omits itself until they are")


@comp("conviction_band", "Content")
def c_conviction(ctx, n, o):
    S = o.css
    st = n.get("statement") or {}
    S.rule(".c-conv", [("padding-block", ctx.length(n.get("padding_block")))] + ctx.paint({"bg": n.get("bg"), "fg": n.get("fg")}, True))
    S.rule(".c-conv__grid", [("display", "grid"), ("gap", "var(--space-sp-3)")])
    S.rule(".c-conv__statement", ctx.type_decls(st.get("type")) + [("text-wrap", st.get("wrap", "balance"))])
    S.rule(".c-conv .c-accent", [("color", ctx.color(st.get("accent_fg"), True))])
    so = n.get("source") or {}
    S.rule(".c-conv__source", ctx.type_decls(so.get("type")) + [("color", ctx.color(so.get("fg"), True))])
    d = ctx.mq("desktop")
    if d:
        i = Sheet()
        i.rule(".c-conv__grid", [("grid-template-columns", "repeat(12, minmax(0, 1fr))"), ("column-gap", "var(--grid-desktop-gutter)")])
        i.rule(".c-conv__grid > *", [("grid-column", "4 / span 8")])
        S.media(d, i)
    o.spec("rest", conviction_html(ctx), f"bg {str(n.get('bg')).strip('{}')} · statement {str(st.get('type')).strip('{}')} · accent {str(st.get('accent_fg')).strip('{}')}", wide=True, frame="bare")


def conviction_html(ctx, k=0):
    """One conviction on Ink. The brand's own statement carries no source line:
    a house quoting itself is not a citation (p45 prints none)."""
    conv = ((ctx.cfg.get("identity") or {}).get("frameworks") or {}).get("convictions") or [""]
    t = conv[k % len(conv)]
    loc = ctx._lookup(ctx.lang, "identity.convictions") if ctx.lang != "en" else None
    if isinstance(loc, list) and len(loc) == len(conv):
        t, la = loc[k % len(loc)], ""
    else:
        la = ' lang="en"' if ctx.lang != "en" else ""
        if la:
            ctx.fallbacks.add("identity.convictions")
    return (f'<section class="c-conv" data-surface="ink" data-section="conviction_band"><div class="p-container c-conv__grid">'
            f'<blockquote{la}><p class="c-conv__statement">{accent_html(t)}</p></blockquote></div></section>')


@comp("cta_band", "Content")
def c_cta_band(ctx, n, o):
    S = o.css
    hd = n.get("heading") or {}
    S.rule(".c-cta", [("padding-block", "var(--space-sp-6)")] + ctx.paint({"bg": n.get("bg"), "fg": n.get("fg")}, True))
    S.rule(".c-cta__grid", [("display", "grid"), ("gap", "var(--space-sp-4)"), ("justify-items", "start")])
    S.rule(".c-cta__title", ctx.type_decls(hd.get("type")) + [("text-wrap", hd.get("wrap", "balance"))])
    S.rule(".c-cta .c-accent", [("color", ctx.color(hd.get("accent_fg"), True))])
    ln = n.get("line") or {}
    S.rule(".c-cta__line", ctx.type_decls(ln.get("type")) + [("color", ctx.color(ln.get("fg"), True)), ("max-inline-size", "44ch")])
    S.rule(".c-cta__ctas", [("display", "flex"), ("flex-wrap", "wrap"), ("gap", "var(--space-sp-3)")])
    d = ctx.mq("desktop")
    if d:
        i = Sheet()
        i.rule(".c-cta", [("padding-block", "var(--space-sp-7)")])
        i.rule(".c-cta__grid", [("grid-template-columns", "repeat(12, minmax(0, 1fr))"), ("column-gap", "var(--grid-desktop-gutter)")])
        i.rule(".c-cta__grid > *", [("grid-column", "1 / span 7")])
        S.media(d, i)
    o.spec("rest · secondary hover · primary focus", cta_band_html(ctx, force=True),
           f"bg {str(n.get('bg')).strip('{}')} · heading {str(hd.get('type')).strip('{}')} · primary + secondary_on_dark", wide=True, frame="bare")


def cta_band_html(ctx, force=False):
    n = ctx.comp("cta_band") or {}
    th, ta = ctx.tx("contact.title", "", accent=True)
    lh, la = ctx.tx("contact.line", "")
    p, s = n.get("primary") or {}, n.get("secondary") or {}
    return (f'<section class="c-cta" data-surface="ink" data-section="cta_band"><div class="p-container c-cta__grid">'
            f'<h2 class="c-cta__title"{ta}>{th}</h2><p class="c-cta__line"{la}>{lh}</p><div class="c-cta__ctas">'
            f'{btn(ctx, p.get("variant", "primary"), p.get("label", ""), "cta.primary", href=ctx.href("contact"), attrs=" data-force=\"focus\"" if force else "")}'
            f'{btn(ctx, s.get("variant", "secondary"), s.get("label", ""), "cta.catalogue", href=ctx.href("training"), attrs=" data-force=\"hover\"" if force else "")}'
            f'</div></div></section>')


@comp("article_list", "Content")
def c_article_list(ctx, n, o):
    S = o.css
    rw = n.get("row") or {}
    S.rule(".c-alist__row", [("display", "grid"), ("gap", "var(--space-sp-2)"), ("padding-block", ctx.length(rw.get("pad_block"))),
                             ("border-block-end", ctx.border(rw.get("rule")))])
    S.rule(".c-alist__eyebrow", ctx.type_decls((rw.get("eyebrow") or {}).get("type")) + [("color", ctx.color((rw.get("eyebrow") or {}).get("fg")))])
    t = rw.get("title") or {}
    S.rule(".c-alist__title", ctx.type_decls(t.get("type")) + [("color", ctx.color(t.get("fg")))])
    S.rule(".c-alist__title a", [("display", "inline-flex"), ("min-block-size", "var(--target-min)"), ("align-items", "center"),
                                 ("text-decoration-line", "none"), ("transition", ctx.transition("link"))])
    ctx.states(S, ".c-alist__title a", "hover", [("text-decoration-line", "underline")])
    sf = rw.get("standfirst") or {}
    S.rule(".c-alist__stand", ctx.type_decls(sf.get("type")) + [("display", "-webkit-box"), ("-webkit-box-orient", "vertical"),
                                                             ("-webkit-line-clamp", str(sf.get("line_clamp", 2))), ("overflow", "hidden")])
    S.rule(".c-alist .c-button", [("justify-self", "start")])
    S.rule(".c-alist__filter", [("margin-block-end", "var(--space-sp-4)")])
    o.spec("rest · title hover · focus", article_list_html(ctx, 3, force=True, filt=True),
           f"rows, not cards · filter = tabs rule · gate {n.get('gate_position')}", wide=True)


def article_list_html(ctx, count=3, force=False, filt=False, gate_after=None):
    """Rows, not cards. The config holds no articles: each row is the pillar it
    files under and a labelled frame for the title — never a stand-in title."""
    n = ctx.comp("article_list") or {}
    rw = n.get("row") or {}
    pl = pillars(ctx)
    rows = []
    for k in range(count):
        pill = pl[k % len(pl)]["label"] if pl else ""
        a = ' data-force="hover"' if force and k == 0 else (' data-force="focus"' if force and k == 1 else "")
        rows.append(f'<li class="c-alist__row"><p class="c-alist__eyebrow">{esc(pill)}</p>'
                    f'{slot(ctx.s("nav.insights", "Insights") if ctx else "", (rw.get("title") or {}).get("max_words"), cls="c-alist__title", brief="article_list.row: title + standfirst")}'
                    f'{btn(ctx, (rw.get("link") or {}).get("variant", "tertiary"), "Read", "cta.read", href=ctx.href("article"), attrs=a)}</li>')
        if gate_after and k + 1 == gate_after:
            rows.append(f'<li class="c-alist__gate">{library_gate_html(ctx)}</li>')
    f = f'<div class="c-alist__filter">{tabs_html(ctx, link=True)}</div>' if filt else ""
    return f'<div class="c-alist">{f}<ol>{"".join(rows)}</ol></div>'


@comp("article", "Content")
def c_article(ctx, n, o):
    S = o.css
    S.rule(".c-article", [("display", "grid"), ("gap", "var(--space-sp-5)")])
    S.rule(".c-article__rail", [("display", "grid"), ("gap", "var(--space-sp-2)"), ("align-content", "start")] +
           ctx.type_decls("{type.mono}") + [("color", ctx.color("{color.muted}"))])
    S.rule(".c-article__title", ctx.type_decls((n.get("title") or {}).get("type")) + [("text-wrap", "balance")])
    S.rule(".c-article__stand", ctx.type_decls((n.get("standfirst") or {}).get("type")))
    pr = n.get("prose") or {}
    S.rule(".c-prose", [("display", "grid"), ("gap", "var(--space-sp-4)"), ("max-inline-size", f"{pr.get('measure_ch', 75)}ch"),
                        ("text-wrap", pr.get("wrap", "pretty"))] + ctx.type_decls(pr.get("type")))
    S.rule(".c-prose h2", ctx.type_decls(pr.get("h2")) + [("margin-block-start", "var(--space-sp-4)")])
    S.rule(".c-prose h3", ctx.type_decls(pr.get("h3")))
    S.rule(".c-prose blockquote", ctx.type_decls(pr.get("pull_quote")) + [("padding-block", "var(--space-sp-4)"),
                                                                        ("border-block", ctx.border({"width": 1, "style": "solid", "color": "{color.border}"}))])
    S.rule(".c-prose figcaption, .c-caption", ctx.type_decls("{type.eyebrow}") + [("font-size", "var(--density-dense-label)"), ("letter-spacing", "0"),
                                                                                ("text-transform", "none"), ("color", ctx.color("{color.muted}")),
                                                                                ("margin-block-start", "var(--space-sp-2)")])
    S.rule(".c-prose code, .c-prose kbd, .c-prose samp", ctx.type_decls((n.get("code_or_data") or {}).get("type")))
    d = ctx.mq("desktop")
    if d:
        i = Sheet()
        i.rule(".c-article", [("grid-template-columns", "repeat(12, minmax(0, 1fr))"), ("column-gap", "var(--grid-desktop-gutter)")])
        i.rule(".c-article__rail", [("grid-column", "1 / span 3")])
        i.rule(".c-article__main", [("grid-column", "4 / span 8")])
        S.media(d, i)
    o.spec("rest", article_html(ctx), f"title {str((n.get('title') or {}).get('type')).strip('{}')} · prose {pr.get('measure_ch')}ch · {n.get('share')}", wide=True)


def article_html(ctx):
    """An article page with the brand's furniture and no invented text: the
    title, standfirst and body are labelled frames until the article exists."""
    n = ctx.comp("article") or {}
    idt = ctx.cfg.get("identity") or {}
    conv = (idt.get("frameworks") or {}).get("convictions") or []
    pl = pillars(ctx)
    ins = ctx.s("nav.insights", "Insights")
    crumbs = crumbs_html(ctx, [("not_found.links.home", "Home"), ("nav.insights", "Insights"), (None, ctx.factory("content"))]) if ctx.comp("breadcrumbs") else ""
    quote = ""
    if conv:
        loc = ctx._lookup(ctx.lang, "identity.convictions") if ctx.lang != "en" else None
        q, la = (loc[1 % len(loc)], "") if isinstance(loc, list) and loc else (conv[1 % len(conv)], ' lang="en"' if ctx.lang != "en" else "")
        quote = f'<blockquote{la}><p>{accent_html(q)}</p></blockquote>'
    return (f'<article class="c-article"><aside class="c-article__rail"><p>{esc(pl[0]["label"] if pl else "")}</p>'
            f'{crumbs}</aside>'
            f'<div class="c-article__main c-prose"><h1 class="c-article__title">{slot(ins, (n.get("title") or {}).get("max_words"), tag="span", brief="article.title")}</h1>'
            f'{slot("", None, brief="article.standfirst + body")}{quote}'
            f'<figure>{frame("", "4 / 3", brief="photograph, split_46_54, a real session")}</figure></div></article>')


@comp("library_gate", "Content")
def c_library_gate(ctx, n, o):
    S = o.css
    S.rule(".c-gate", ctx.elev_decls(n.get("elevation")) + [("padding", ctx.length(n.get("padding"))), ("display", "grid"), ("gap", "var(--space-sp-3)"),
                                                          ("background-color", ctx.color(n.get("bg")))])
    eb = n.get("eyebrow") or {}
    S.rule(".c-gate__eyebrow", ctx.type_decls(eb.get("type")) + [("color", ctx.color(eb.get("fg"))), ("display", "flex"), ("align-items", "center"),
                                                               ("gap", "var(--space-sp-2)")])
    S.rule(".c-gate__title", ctx.type_decls((n.get("title") or {}).get("type")))
    S.rule(".c-gate__line", ctx.type_decls((n.get("line") or {}).get("type")) + [("max-inline-size", "60ch")])
    S.rule(".c-form", [("display", "grid"), ("gap", "var(--space-sp-4)"), ("grid-template-columns", "minmax(0, 1fr)"), ("margin-block-start", "var(--space-sp-2)")])
    S.rule(".c-form .c-button", [("justify-self", "start")])
    # form states: one wrapper, data-state = rest | error | sending | success
    S.rule(".c-formstate [data-show]", [("display", "none")])
    S.rule('.c-formstate[data-state="error"] [data-show="error"]', [("display", "flex")])
    S.rule('.c-formstate[data-state="success"] [data-show="success"]', [("display", "flex")])
    S.rule('.c-formstate[data-state="success"] > form', [("display", "none")])
    S.rule(".c-hp", [("position", "absolute"), ("inline-size", "1px"), ("block-size", "1px"), ("overflow", "hidden"), ("clip-path", "inset(50%)")])
    t = ctx.mq("tablet")
    if t:
        i = Sheet()
        i.rule(".c-form--split", [("grid-template-columns", "repeat(2, minmax(0, 1fr))"), ("column-gap", "var(--space-sp-4)")])
        i.rule(".c-form--split .c-form__full", [("grid-column", "1 / -1")])
        S.media(t, i)
    o.spec("rest", library_gate_html(ctx), f"{str(n.get('elevation')).strip('{}')} · padding {str(n.get('padding')).strip('{}')} · lock icon by the eyebrow", wide=True)
    o.spec("error", library_gate_html(ctx, state="error"), "on submit focus the first error · inline message", wide=True)
    o.spec("loading · sending", library_gate_html(ctx, state="sending"), "disabled while the request runs · same width", wide=True)
    o.spec("success", library_gate_html(ctx, state="success"), "inline, replaces the form · aria-live polite", wide=True)


def ok_msg(ctx, title_key, line_key, demo=True):
    """The success message that replaces a form: what was sent and where."""
    line = ctx.s(line_key, "")
    shown = line.format(email="name@company.com") if demo else line
    fr = ctx.fr(line_key) if ctx.lang == "en" else None
    la = f' data-en="{esc(shown)}" data-fr="{esc(fr.format(email="name@company.com"))}"' if fr else ""
    return (f'<div class="c-msg c-msg--ok" role="status" aria-live="polite" data-show="success">{ctx.icon("check", 20)}<div>'
            f'{ctx.el("p", title_key, "", "c-msg__title")}<p class="c-msg__line" data-template="{esc(line)}"{la}>{esc(shown)}</p></div></div>')


def library_gate_html(ctx, state="rest", head=True):
    """The library sign-up. Fields in visual order (half-width pairs first,
    the full-width email after them), consent required, honeypot, and the
    rest / error / sending / success states as data-state on the wrapper."""
    n = ctx.comp("library_gate") or {}
    form = n.get("form") or {}
    ic = n.get("icon") or {}
    eh, ea = ctx.tx("library.eyebrow", (n.get("eyebrow") or {}).get("content", ""))
    hd = (f'<p class="c-gate__eyebrow">{ctx.icon(ic.get("name"), ic.get("px", 20))}<span{ea}>{eh}</span></p>'
          f'{ctx.el("h2", "library.title", "", "c-gate__title", accent=True)}{ctx.el("p", "library.line", "", "c-gate__line")}') if head else ""
    keymap = {"name": "library.name", "email": "library.email", "company": "library.company"}
    full = {"email"}
    fl = list(form.get("fields") or [])
    fl.sort(key=lambda f: f["name"] in full)
    fields = []
    for f in fl:
        st = "error" if state == "error" and f["name"] == "email" else ("disabled" if state == "sending" else "rest")
        h = field(ctx, keymap.get(f["name"]), f.get("label", f["name"]), f["name"], f.get("type", "text"), st,
                  "library.email_help" if f.get("help") else None, f.get("help"), optional=f.get("optional"),
                  width_ch=f.get("width_ch"), autocomplete=f.get("autocomplete"),
                  err_key="form_errors.email", err_default="", value="name@" if st == "error" else None,
                  required=not f.get("optional"), live_msg=True)
        fields.append(f'<div class="{"c-form__full" if f["name"] in full else ""}">{h}</div>')
    cons = ""
    if form.get("consent"):
        i = uid(ctx, "consent")
        ch, ca = ctx.tx("library.consent", "")
        req = " required" if (form.get("consent") or {}).get("required", True) else ""
        cons = (f'<div class="c-form__full"><label class="c-check" for="{i}"><input class="c-check__box" type="checkbox" id="{i}" name="consent"{req}>'
                f'{ctx.icon("check", 16, "c-check__mark")}<span class="c-check__text"{ca}>{ch}</span></label>'
                f'<p class="c-field__msg" id="{i}-e" hidden>{ctx.icon("circle-alert", 16)}<span></span></p></div>')
    hp = '<input class="c-hp" type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">' if form.get("honeypot") else ""
    sb = form.get("submit") or {}
    sub = submit_btn(ctx, sb.get("variant", "primary"), "library.submit", sb.get("label", ""), busy=(state == "sending"))
    err = (f'<div class="c-form__full c-msg c-msg--inline" role="alert" data-show="error">{ctx.icon("circle-alert", 20)}'
           f'{ctx.el("p", "form_errors.focus_first", "", "c-msg__line")}</div>')
    return (f'<section class="c-gate">{hd}<div class="c-formstate" data-state="{state}">'
            f'<form class="c-form c-form--split" data-form novalidate{form_messages(ctx, keymap)}>{err}{"".join(fields)}'
            f'{cons}{hp}<div class="c-form__full">{sub}</div></form>'
            f'{ok_msg(ctx, "library.success_title", "library.success_line")}</div></section>')


@comp("contact_form", "Content")
def c_contact(ctx, n, o):
    S = o.css
    S.rule(".c-contact", [("display", "grid"), ("gap", "var(--space-sp-5)")])
    S.rule(".c-contact__rail", [("display", "grid"), ("gap", "var(--space-sp-3)"), ("align-content", "start"),
                                ("padding-block-start", "var(--space-sp-3)"),
                                ("border-block-start", ctx.border({"width": 1, "style": "solid", "color": "{color.border}"}))])
    S.rule(".c-contact__rail p", ctx.type_decls("{type.body}"))
    S.rule(".c-contact__mail", [("display", "inline-flex"), ("gap", "var(--space-sp-2)"), ("align-items", "center"), ("min-block-size", "var(--target-min)")])
    S.rule(".c-contact__count", ctx.type_decls("{type.mono}") + [("color", ctx.color("{color.muted}")), ("justify-self", "end")])
    d = ctx.mq("desktop")
    if d:
        i = Sheet()
        i.rule(".c-contact", [("grid-template-columns", "repeat(12, minmax(0, 1fr))"), ("column-gap", "var(--grid-desktop-gutter)")])
        i.rule(".c-contact__form", [("grid-column", "1 / span 7")])
        i.rule(".c-contact__rail", [("grid-column", "9 / -1"), ("grid-row", "1")])
        S.media(d, i)
    o.spec("rest", contact_html(ctx), f"{n.get('density')} · {n.get('submit_behaviour', '')[:70]}", wide=True)
    o.spec("error", contact_html(ctx, state="error"), "on submit: the summary, the first invalid field focused, its message below it", wide=True)
    o.spec("loading · sending", contact_html(ctx, state="sending"), "fields and submit disabled, label 'Sending…' in the same width", wide=True)
    o.spec("success", contact_html(ctx, state="success"), "inline, replaces the form · polite", wide=True)


def contact_html(ctx, state="rest"):
    """The contact form and the faster route beside it. required on every
    field the config does not mark optional, maxlength and a live counter on
    the message, a placeholder option on the select, and the four states."""
    n = ctx.comp("contact_form") or {}
    keys = {"name": "contact.name", "email": "contact.email", "organisation": "contact.organisation", "topic": "contact.topic",
            "message": "contact.message"}
    rail = n.get("rail") or {}
    sc = rail.get("scoping") or {}
    mail = ctx.s("contact.email_address") or (ctx.cfg.get("identity") or {}).get("email")
    mail_h = (f'<a class="c-contact__mail c-link" href="mailto:{esc(mail)}">{ctx.icon("mail", 20)}<span>{esc(mail)}</span></a>' if mail
              else slot(ctx.s("contact.email", "Email"), None, brief="contact email: not in the config"))
    rail_h = (f'<aside class="c-contact__rail">{ctx.el("p", "contact.faster", "")}{mail_h}'
              f'{ctx.el("p", "contact.address", rail.get("address", ""))}'
              f'{btn(ctx, sc.get("variant", "tertiary"), sc.get("label", ""), "cta.primary", href="#")}</aside>')
    fs = []
    for f in n.get("fields") or []:
        ctl = f.get("control", "input")
        opts = ctx.node("contact.topics") if ctl == "select" else None
        st = "disabled" if state == "sending" else ("error" if state == "error" and f["name"] == "email" else "rest")
        h = field(ctx, keys.get(f["name"]), f.get("label"), f["name"], f.get("type", "text"), st,
                  "contact.message_help" if f.get("help") else None, f.get("help"),
                  width_ch=f.get("width_ch"), control=ctl, options=opts or f.get("options"), rows=f.get("rows"),
                  autocomplete=f.get("autocomplete"), required=not f.get("optional"), maxlength=f.get("max_chars"),
                  choose=choose_label(ctx, "contact", keys.get(f["name"])) if ctl == "select" else None,
                  err_key="form_errors.email", err_default="", value="name@" if st == "error" else None, live_msg=True)
        if ctl == "textarea" and f.get("max_chars"):
            fid = re.search(r'<textarea class="c-input" rows="\d+" id="([^"]+)"', h)
            cid = f' data-count-for="{fid.group(1)}"' if fid else ""
            h = h[:-6] + f'<p class="c-contact__count"{cid}>0 / {f["max_chars"]}</p></div>'
        fs.append(h)
    sb = n.get("submit") or {}
    sub = submit_btn(ctx, sb.get("variant", "primary"), "cta.send", sb.get("label", ""), busy=(state == "sending"))
    err = (f'<div class="c-msg c-msg--inline" role="alert" data-show="error">{ctx.icon("circle-alert", 20)}'
           f'{ctx.el("p", "form_errors.focus_first", "", "c-msg__line")}</div>')
    return (f'<div class="c-contact"><div class="c-contact__form c-formstate" data-state="{state}">'
            f'<form class="c-form" data-form novalidate{form_messages(ctx, keys)}>{err}{"".join(fs)}{sub}</form>'
            f'{ok_msg(ctx, "contact.success_title", "contact.success_line")}</div></div>').replace(
        '<div class="c-contact">', f'<div class="c-contact">{rail_h}', 1)


@comp("not_found", "Content")
def c_not_found(ctx, n, o):
    S = o.css
    S.rule(".c-404", [("display", "grid"), ("gap", "var(--space-sp-4)"), ("justify-items", "start")])
    S.rule(".c-404__title", ctx.type_decls((n.get("title") or {}).get("type")) + [("text-wrap", "balance")])
    S.rule(".c-404__line", ctx.type_decls((n.get("line") or {}).get("type")) + [("max-inline-size", "52ch")])
    S.rule(".c-404__links", [("display", "grid"), ("gap", "0")])
    d = ctx.mq("desktop")
    if d:
        i = Sheet()
        i.rule(".c-404", [("grid-template-columns", "repeat(12, minmax(0, 1fr))"), ("column-gap", "var(--grid-desktop-gutter)")])
        i.rule(".c-404 > *", [("grid-column", "4 / span 7")])
        S.media(d, i)
    o.spec("site", not_found_html(ctx, "site"), f"status {n.get('status')} · title {str((n.get('title') or {}).get('type')).strip('{}')} · three tertiary links", wide=True)
    o.spec("platform", not_found_html(ctx, "platform"), "platform variant", wide=True)


def not_found_html(ctx, which="site", level="h1"):
    n = ctx.comp("not_found") or {}
    base = "not_found" if which == "site" else "platform.not_found"
    links = (n.get("links") or {}).get(which) or []
    lk = list((ctx._lookup("en", f"{base}.links") or {}).keys())
    ls = []
    for k, lab in enumerate(links):
        key = f"{base}.links.{lk[k]}" if k < len(lk) else None
        href = ctx.href(lk[k]) if which == "site" and k < len(lk) else "#"
        ls.append(f"<li>{btn(ctx, 'tertiary', lab, key, href=href)}</li>")
    return (f'<div class="c-404">{ctx.el(level, f"{base}.title", "", "c-404__title", accent=(which == "site"))}'
            f'{ctx.el("p", f"{base}.line", "", "c-404__line")}<ul class="c-404__links">{"".join(ls)}</ul></div>')


@comp("accordion", "Content")
def c_accordion(ctx, n, o):
    S = o.css
    S.rule(".c-acc", [("border-block-start", ctx.border(n.get("row_rule")))])
    S.rule(".c-acc__item", [("border-block-end", ctx.border(n.get("row_rule")))])
    S.rule(".c-acc summary", [("display", "flex"), ("align-items", "center"), ("gap", "var(--space-sp-2)"), ("min-block-size", "var(--density-comfortable-row)"),
                              ("cursor", "pointer"), ("list-style", "none"), ("transition", ctx.transition("row"))] + ctx.type_decls("{type.heading_sm}"))
    S.rule(".c-acc summary::-webkit-details-marker", [("display", "none")])
    ctx.states(S, ".c-acc summary", "hover", [("background-color", ctx.color("{color.state.surface_hover}"))])
    ch = n.get("chevron") or {}
    S.rule(".c-acc__chev", [("transition", ctx.transition("accordion", "chevron"))])
    S.rule(".c-acc details[open] .c-acc__chev", [("transform", f"rotate({ch.get('rotate_deg', 90)}deg)")])
    S.rule('[dir="rtl"] .c-acc details:not([open]) .c-acc__chev', [("transform", "scaleX(-1)")])
    S.rule(".c-acc__panel", [("padding-block", "0 var(--space-sp-3)"), ("padding-inline-start", "calc(var(--space-sp-2) + 16px)"),
                             ("display", "grid"), ("gap", "var(--space-sp-1)")])
    o.spec("closed · open · hover · focus", accordion_html(ctx), f"row_rule {bind({'r': n.get('row_rule')})[2:]} · chevron {ch.get('rotate_deg')}° {str(ch.get('motion')).strip('{}')} · panel instant", wide=True)


def accordion_html(ctx):
    items = []
    dh, da = ctx.tx("pillars.delivery", "")
    for k, p in enumerate(pillars(ctx)):
        op = " open" if k == 1 else ""
        f = ' data-force="hover"' if k == 2 else (' data-force="focus"' if k == 3 else "")
        items.append(f'<div class="c-acc__item"><details{op}><summary{f}><span class="c-acc__chev">{ctx.icon("chevron-right", 16)}</span>'
                     f'<span>{esc(p["label"])}</span></summary><div class="c-acc__panel"><p>{esc(p.get("framework") or "")}</p>'
                     f'<p class="fx-small"{da}>{dh}</p></div></details></div>')
    return f'<div class="c-acc">{"".join(items)}</div>'


@comp("citation", "Content")
def c_citation(ctx, n, o):
    S = o.css
    S.rule(".c-cite", ctx.type_decls("{type.mono}") + [("display", "inline-flex"), ("align-items", "center"), ("justify-content", "center"),
                                                    ("min-inline-size", "var(--space-sp-4)"), ("padding-inline", "var(--space-sp-1)"),
                                                    ("border-radius", ctx.length(n.get("chip_radius"))), ("color", ctx.color(n.get("chip_fg"))),
                                                    ("font-size", "var(--density-dense-label)"), ("vertical-align", "baseline"),
                                                    ("background-color", ctx.color("{color.state.selected}")), ("transition", ctx.transition("link"))])
    ctx.states(S, ".c-cite", "hover", [("background-color", ctx.color("{color.state.selected_hover}"))])
    ug = n.get("ungrounded") or {}
    S.rule(".c-cite--ungrounded", ctx.paint(ug) + [("background-color", "transparent"), ("letter-spacing", "0.08em")])
    o.spec("chip · ungrounded", chat_answer(ctx), f"chip_fg {str(n.get('chip_fg')).strip('{}')} · ungrounded {bind(ug)} · panel = drawer", wide=True)


def chat_answer(ctx):
    ug = ctx.s("platform.errors.ungrounded", "UNGROUNDED")
    return (f'<p class="fx-prose">Two. Candidate screening sits in the EU AI Act high-risk tier for employment decisions '
            f'<button class="c-cite c-hit" type="button" aria-label="Source 1">1</button>, and Supplier risk scoring has no named owner '
            f'<button class="c-cite c-hit" type="button" data-force="hover" aria-label="Source 2">2</button>. A third, support triage, is likely '
            f'to fail on retention but your policy does not state a period <span class="c-cite c-cite--ungrounded">{esc(ug)}</span></p>')


@comp("chat", "Content")
def c_chat(ctx, n, o):
    S = o.css
    S.rule(".c-chat", [("display", "grid"), ("max-inline-size", "75ch")])
    S.rule(".c-chat__turn", [("display", "grid"), ("gap", "var(--space-sp-2)"), ("padding-block", "var(--space-sp-3)"),
                             ("border-block-end", ctx.border(n.get("turn_rule"))), ("text-align", "start")])
    for k in ("ai_label", "person_label"):
        L = n.get(k) or {}
        S.rule(f".c-chat__{k.split('_')[0]}", ctx.type_decls(L.get("type")) + [("font-size", px(L["size"])) if L.get("size") else None,
                                                                              ("color", ctx.color(L.get("fg")))])
    S.rule(".c-chat__input", [("display", "grid"), ("grid-template-columns", "minmax(0, 1fr) auto"), ("gap", "var(--space-sp-2)"),
                              ("align-items", "end"), ("margin-block-start", "var(--space-sp-3)")])
    S.rule(".c-chat__input textarea", [("max-block-size", f"calc({n.get('input_max_lines', 6)} * 1.55em + 2 * var(--density-comfortable-pad-y))")])
    person = (ctx.cfg.get("owner") or {}).get("name", "")
    ai = next((f["name"] for f in ((ctx.cfg.get("identity") or {}).get("frameworks") or {}).get("list", []) if f.get("pillar") == "none"), "AI")
    ai = re.sub(r"^the ", "", ai)
    i = uid(ctx, "chat")
    h = (f'<div class="c-chat"><div class="c-chat__turn"><p class="c-chat__person">{esc(person)}</p>'
         f'<p>Which of our mapped use cases would fail the governance check?</p></div>'
         f'<div class="c-chat__turn"><p class="c-chat__ai">{esc(ai)}</p>{chat_answer(ctx)}</div>'
         f'<div class="c-chat__input"><label class="c-sr" for="{i}">Message</label><textarea class="c-input" id="{i}" rows="1"></textarea>'
         f'<button class="c-button c-button--primary" type="button" aria-label="Send">{ctx.icon("send", 20)}</button></div>'
         f'<p class="fx-note">Example conversation from Brand Book 3.3 p93.</p></div>')
    o.spec("rest", h, f"no bubbles · align {n.get('align')} · turn_rule {bind({'r': n.get('turn_rule')})[2:]} · ai label accent, person muted", wide=True)


# ── Feedback ─────────────────────────────────────────────────────────────
def msg_css(ctx, S):
    if getattr(ctx, "_msg_done", False):
        return
    ctx._msg_done = True
    im = ctx.comp("inline_message") or {}
    S.rule(".c-msg", [("display", "flex"), ("gap", "var(--space-sp-2)"), ("align-items", "flex-start"),
                      ("padding", "var(--space-sp-3) var(--space-sp-4)")])
    S.rule(".c-msg--inline", ctx.elev_decls("{elevation.e1}") + [("border-inline-start", ctx.border(im.get("edge"))),
                                                               ("flex-wrap", "wrap"), ("transition", ctx.transition("inline_message", "enter"))])
    S.rule(".c-msg--ok", [("padding-inline", "0")])
    S.rule(".c-msg__title", ctx.type_decls("{type.heading_sm}"))
    S.rule(".c-msg__line", ctx.type_decls("{type.caption}") + [("flex", "1 1 24ch")])
    S.rule(".c-msg > div", [("display", "grid"), ("gap", "var(--space-sp-1)")])


@comp("inline_message", "Feedback")
def c_inline_msg(ctx, n, o):
    msg_css(ctx, o.css)
    tr = "platform.errors.transient"
    h = (f'<div class="c-msg c-msg--inline" role="alert"><div>{ctx.el("p", tr + ".title", "", "c-msg__title")}'
         f'{ctx.el("p", tr + ".line", "", "c-msg__line")}</div>'
         f'{btn(ctx, "secondary", "Try again", tr + ".retry", icon="refresh-cw")}</div>')
    o.spec("error", h, f"edge {bind({'e': n.get('edge')})[2:]} inline-start · e1 · role alert", wide=True)


@comp("toast", "Feedback")
def c_toast(ctx, n, o):
    S = o.css
    S.rule(".c-toast", ctx.elev_decls(n.get("elevation")) + [("display", "inline-flex"), ("align-items", "center"), ("gap", "var(--space-sp-2)"),
                                                           ("padding", "var(--space-sp-3) var(--space-sp-4)"), ("border-radius", "var(--radius-floating)"),
                                                           ("max-inline-size", "100%"),
                                                           ("transition", ctx.transition("toast", "enter"))])
    h = f'<div class="c-toast" role="status" aria-live="polite">{ctx.icon("check", 20)}{ctx.el("span", "platform.success.settings", "Saved.")}</div>'
    o.spec("rest", h, f"{str(n.get('elevation')).strip('{}')} · {n.get('position')} · {n.get('duration_s')}s · confirmation only")


@comp("banner", "Feedback")
def c_banner(ctx, n, o):
    S = o.css
    S.rule(".c-banner", ctx.paint(n) + [("display", "flex"), ("align-items", "center"), ("gap", "var(--space-sp-2)"),
                                       ("padding", "var(--space-sp-2) var(--space-sp-4)"), ("min-block-size", "var(--target-min)"),
                                       ("transition", ctx.transition("banner", "enter"))] + ctx.type_decls("{type.caption}"))
    h = f'<div class="c-banner" role="status">{ctx.icon("triangle-alert", 20)}{ctx.el("span", "platform.errors.offline", "")}</div>'
    o.spec("rest · offline", h, bind(n) + f" · max {n.get('max')} per screen", wide=True)


@comp("badge", "Feedback")
def c_badge(ctx, n, o):
    S = o.css
    lb = n.get("label") or {}
    S.rule(".c-badge", ctx.type_decls(lb.get("type")) + [("font-size", px(lb["size"])) if lb.get("size") else None,
                                                       ("letter-spacing", lb.get("tracking")), ("display", "inline-flex"), ("align-items", "center"),
                                                       ("gap", "var(--space-sp-1)"), ("padding", "var(--space-sp-1) var(--space-sp-2)"),
                                                       ("border-radius", ctx.length(n.get("radius"))), ("border", ctx.border({"width": 1, "style": "solid", "color": "transparent"})),
                                                       ("white-space", "nowrap")] + ctx.paint(n.get("default") or {}))
    fills = n.get("fills") or {}
    for k in live(fills):
        S.rule(f'.c-badge--{k}', ctx.paint(fills[k]) + ([("border-color", ctx.color(fills[k].get("bg")))] if fills[k].get("bg") not in (None, "none") else []))
    rows = []
    for mk, mp in ((k, (n.get("map") or {})[k]) for k in live(n.get("map") or {})):
        bs = "".join(f'<span class="c-badge c-badge--{f}">{esc(v)}</span>' for v, f in mp.items())
        rows.append(f'<div class="fx-badges"><p class="fx-eyebrow">{esc(mk.replace("_", " "))}</p><div class="fx-wrap">{bs}</div></div>')
    o.spec("map · fills", "".join(rows), " · ".join(f"{k}: {bind(fills[k])}" for k in live(fills)), wide=True)


@comp("skeleton", "Feedback")
def c_skeleton(ctx, n, o):
    S = o.css
    tm = (ctx.cfg.get("motion") or {}).get("skeleton_timing") or {}
    S.rule(".c-skel", [("display", "block"), ("background-color", ctx.color(n.get("bg"))), ("border-radius", ctx.length(n.get("radius"))),
                       ("animation", f"c-pulse {tm.get('pulse_period_ms', 800)}ms var(--ease-standard) infinite")])
    S.raw("@media (prefers-reduced-motion: reduce) { .c-skel { animation: none; } }")
    S.rule(".c-skel--row", [("block-size", "var(--density-compact-row)"), ("margin-block-end", "1px")])
    S.rule(".c-skel--num", [("inline-size", "4ch"), ("block-size", "var(--type-display-lg-size)")])
    S.rule(".c-skel--line", [("block-size", "var(--space-sp-3)"), ("margin-block-end", "var(--space-sp-2)")])
    S.rule(".c-skel-group", [("display", "grid"), ("gap", "var(--space-sp-2)")])
    h = (f'<div class="c-skel-group" aria-busy="true"{ctx.aria("platform.loading.skeleton", "Loading")}>'
         f'<span class="c-skel c-skel--num"></span><span class="c-skel c-skel--line" style="inline-size: 90%"></span>'
         f'<span class="c-skel c-skel--line" style="inline-size: 75%"></span><span class="c-skel c-skel--line" style="inline-size: 55%"></span>'
         f'<span class="c-skel c-skel--row"></span><span class="c-skel c-skel--row"></span></div>')
    o.spec("loading", h, f"bg {str(n.get('bg')).strip('{}')} · {n.get('shape', '')[:60]} · pulse {tm.get('pulse_period_ms')}ms, static under reduced motion")


@comp("empty_state", "Feedback")
def c_empty(ctx, n, o):
    S = o.css
    S.rule(".c-empty", [("display", "grid"), ("gap", "var(--space-sp-3)"), ("justify-items", "start"), ("max-inline-size", "48ch"), ("text-align", "start")])
    S.rule(".c-empty__title", ctx.type_decls((n.get("title") or {}).get("type")))
    S.rule(".c-empty__line", ctx.type_decls((n.get("line") or {}).get("type")) + [("color", ctx.color("{color.muted}"))])
    for k in ("use_cases", "search"):
        o.spec(f"empty · {k}", empty_html(ctx, k, query="governance"), f"title {str((n.get('title') or {}).get('type')).strip('{}')} · action {(n.get('action') or {}).get('variant')} · left-ranged, no illustration")


def empty_html(ctx, key, query="", n_hidden=3, level="h2"):
    n = ctx.comp("empty_state") or {}
    b = f"platform.empty.{key}"
    t = ctx.s(b + ".title", "")
    fr = ctx.fr(b + ".title")
    fmt = {"query": query, "n": n_hidden}
    ta = f' data-en="{esc(t.format(**fmt))}" data-fr="{esc(fr.format(**fmt))}"' if fr else ""
    ln = ctx.s(b + ".line", "")
    lfr = ctx.fr(b + ".line")
    la = f' data-en="{esc(ln.format(**fmt))}" data-fr="{esc(lfr.format(**fmt))}"' if lfr else ""
    act = n.get("action") or {}
    return (f'<div class="c-empty"><{level} class="c-empty__title"{ta}>{esc(t.format(**fmt))}</{level}><p class="c-empty__line"{la}>{esc(ln.format(**fmt))}</p>'
            f'{btn(ctx, act.get("variant", "primary"), "", b + ".action", icon="plus" if key in ("use_cases", "dashboard") else None)}</div>')


@comp("error_recovery", "Feedback")
def c_errors(ctx, n, o):
    msg_css(ctx, o.css)
    S = o.css
    S.rule(".c-perm", ctx.type_decls("{type.caption}") + [("color", ctx.color("{color.muted}"))])
    perm = ctx.s("platform.errors.permission", "").format(action="export a blueprint", owner="the organisation owner")
    o.spec("input", field(ctx, "library.email", "Work email", "email", "email", "error", err_key="form_errors.email", value="name@"),
           (n.get("input") or {}).get("message", ""))
    o.spec("permission", f'<p class="c-perm">{esc(perm)}</p>', (n.get("permission") or {}).get("form", ""))
    o.spec("transient", f'<div class="c-msg c-msg--inline" role="alert"><div>{ctx.el("p", "platform.errors.transient.title", "", "c-msg__title")}'
                        f'{ctx.el("p", "platform.errors.transient.line", "", "c-msg__line")}</div>'
                        f'{btn(ctx, "secondary", "Try again", "platform.errors.transient.retry", icon="refresh-cw")}</div>',
           (n.get("transient") or {}).get("message", ""), wide=True)
    o.spec("absent", not_found_html(ctx, "platform", level="h3").replace("c-404__title", "c-404__title fx-h3"), "component.not_found", wide=True)
    if ctx.comp("banner"):
        o.spec("offline", f'<div class="c-banner" role="status">{ctx.icon("triangle-alert", 20)}{ctx.el("span", "platform.errors.offline", "")}</div>',
               "component.banner · not dismissible", wide=True)
    o.spec("model", f'<p class="fx-prose">{esc(ctx.s("platform.errors.model_refusal", "").format(what_instead="Score it from the questionnaire instead."))} '
                    f'<span class="c-cite c-cite--ungrounded">{esc(ctx.s("platform.errors.ungrounded", ""))}</span></p>', (n.get("model") or {}).get("form", ""))
    o.notes.append("conflict: rendered under Overlays (modal) — see confirm/modal")


@comp("long_loading", "Feedback")
def c_long(ctx, n, o):
    S = o.css
    S.rule(".c-task", [("display", "grid"), ("gap", "var(--space-sp-1)"), ("padding-block", "var(--space-sp-2)"),
                       ("border-block-end", ctx.border({"width": 1, "style": "solid", "color": "{color.border}"}))])
    S.rule(".c-task__status", ctx.type_decls("{type.mono}") + [("color", ctx.color("{color.muted}"))])
    b = btn(ctx, "primary", "Scoring", "platform.loading.scoring", attrs=' aria-busy="true"')
    o.spec("1–10s · button", b, n.get("button", ""))
    s = ctx.s("platform.loading.scoring_on", "").format(total=24, name="Invoice extraction", i=4)
    o.spec("over 10s · named task", f'<div class="c-task"><p>{esc(s)}</p>{ctx.el("p", "platform.loading.leave", "", "c-task__status")}</div>', n.get("over_10s", "")[:80], wide=True)


@comp("optimistic", "Feedback")
def c_optimistic(ctx, n, o):
    S = o.css
    S.rule(".c-saving", ctx.type_decls("{type.mono}") + [("color", ctx.color("{color.muted}")), ("margin-inline-start", "auto")])
    h = (f'<div class="c-row c-row--static">{esc("Invoice extraction")}<span class="c-saving" role="status">'
         f'{esc(ctx.s("platform.loading.saving", "Saving…"))}</span></div>')
    o.spec("pending > 1s", h, n.get("pending", "")[:80], wide=True)
    o.notes.append("allowed: " + ", ".join(n.get("allowed") or []) + " · never: " + ", ".join(n.get("never") or []))


@comp("consent", "Feedback")
def c_consent(ctx, n, o):
    S = o.css
    w = n.get("width") or {}
    S.rule(".c-consent", ctx.elev_decls(n.get("elevation")) + [("display", "grid"), ("gap", "var(--space-sp-3)"),
                                                             ("padding", ctx.length(n.get("padding"))), ("inline-size", "100%"),
                                                             ("background-color", ctx.color(n.get("bg"))), ("transition", ctx.transition("consent", "enter"))])
    S.rule(".c-consent__text", ctx.type_decls((n.get("text") or {}).get("type")))
    S.rule(".c-consent__actions", [("display", "flex"), ("flex-wrap", "wrap"), ("gap", "var(--space-sp-2)")])
    t = ctx.mq("tablet")
    if t and isinstance(w.get("tablet"), (int, float)):
        i = Sheet()
        i.rule(".c-consent", [("inline-size", px(w["tablet"]))])
        S.media(t, i)
    o.spec("rest", consent_html(ctx), f"{str(n.get('elevation')).strip('{}')} · {n.get('position')} · refuse = same weight, same row · no X", wide=True)


def consent_html(ctx):
    n = ctx.comp("consent") or {}
    a = n.get("actions") or {}
    return (f'<section class="c-consent"{ctx.aria("cookie.region", "Cookie notice")}><p class="c-consent__text">'
            f'{ctx.el("span", "cookie.text", "")} <a class="c-link" href="#">{ctx.el("span", "cookie.policy", "")}</a></p>'
            f'<div class="c-consent__actions">{btn(ctx, (a.get("accept") or {}).get("variant", "primary"), "", "cookie.accept")}'
            f'{btn(ctx, (a.get("refuse") or {}).get("variant", "secondary"), "", "cookie.refuse")}</div></section>')


# ── Overlays ─────────────────────────────────────────────────────────────
def dialog_css(ctx, S):
    if getattr(ctx, "_dlg_done", False):
        return
    ctx._dlg_done = True
    m = ctx.comp("modal") or {}
    S.rule(".c-scrim", [("position", "absolute"), ("inset", "0"), ("background-color", ctx.scrim("{elevation.e3}")),
                        ("transition", ctx.transition("dialog", "scrim"))])
    S.rule(".c-dialog", ctx.elev_decls(m.get("elevation", "{elevation.e3}")) +
           [("position", "relative"), ("inline-size", "100%"), ("border-radius", "var(--radius-floating)"), ("padding", "var(--space-sp-4)"),
            ("display", "grid"), ("gap", "var(--space-sp-3)"), ("transition", ctx.transition("dialog", "panel"))])
    for w in m.get("widths") or []:
        S.rule(f".c-dialog--{w}", [("max-inline-size", px(w))])
    S.rule(".c-dialog__title", ctx.type_decls("{type.heading_sm}"))
    S.rule(".c-dialog__body", ctx.type_decls("{type.caption}"))
    S.rule(".c-dialog__actions", [("display", "flex"), ("flex-wrap", "wrap"), ("gap", "var(--space-sp-2)")])


@comp("modal", "Overlays")
def c_modal(ctx, n, o):
    dialog_css(ctx, o.css)
    b = "platform.errors.not_found"
    d = (f'<div class="c-dialog c-dialog--{(n.get("widths") or [480])[0]}" role="dialog" aria-modal="true" aria-labelledby="dlg-nf">'
         f'{ctx.el("h2", b + ".title", "", "c-dialog__title", attrs=" id=\"dlg-nf\"")}{ctx.el("p", b + ".line", "", "c-dialog__body")}'
         f'<div class="c-dialog__actions">{btn(ctx, "primary", "", b + ".action")}</div></div>')
    o.spec("open (static)", overlay_frame(ctx, d, scrim=True), f"{str(n.get('elevation')).strip('{}')} + scrim · widths {n.get('widths')} · focus trapped", wide=True)


@comp("confirm", "Overlays")
def c_confirm(ctx, n, o):
    dialog_css(ctx, o.css)
    a = n.get("actions") or {}
    t = ctx.s("platform.confirm.discard_line", "").format(n=8)
    fr = ctx.fr("platform.confirm.discard_line")
    la = f' data-en="{esc(t)}" data-fr="{esc(fr.format(n=8))}"' if fr else ""
    d = (f'<div class="c-dialog c-dialog--{n.get("width", 480)}" role="alertdialog" aria-modal="true" aria-labelledby="dlg-cf">'
         f'{ctx.el("h2", "platform.confirm.discard_title", "", "c-dialog__title", attrs=" id=\"dlg-cf\"")}<p class="c-dialog__body"{la}>{esc(t)}</p>'
         f'<div class="c-dialog__actions">{btn(ctx, (a.get("confirm") or {}).get("variant", "destructive"), ctx.s("platform.confirm.discard", "").format(n=8))}'
         f'{btn(ctx, (a.get("cancel") or {}).get("variant", "secondary"), "", "platform.confirm.keep", attrs=" data-force=\"focus\"")}</div></div>')
    o.spec("open · focus on cancel", overlay_frame(ctx, d, scrim=True), f"base modal {n.get('width')} · destructive names the consequence · {n.get('focus')}", wide=True)


@comp("drawer", "Overlays")
def c_drawer(ctx, n, o):
    S = o.css
    dialog_css(ctx, S)
    S.rule(".c-drawer", [("position", "relative"), ("inline-size", "100%"), ("max-inline-size", px(n.get("width", 420))),
                         ("margin-inline-start", "auto"), ("background-color", f"var(--elevation-{str(n.get('elevation', '{elevation.e3}')).strip('{}').split('.')[-1]}-surface)"),
                         ("border-inline-start", f"var(--elevation-{str(n.get('elevation', '{elevation.e3}')).strip('{}').split('.')[-1]}-border)"),
                         ("padding", "var(--space-sp-4)"), ("display", "grid"), ("align-content", "start"), ("gap", "var(--space-sp-3)"),
                         ("transition", ctx.transition("drawer", "enter"))])
    ctx.elev_decls(n.get("elevation"))
    S.rule(".c-drawer__head", [("display", "flex"), ("justify-content", "space-between"), ("align-items", "center"), ("gap", "var(--space-sp-2)")])
    o.spec("open (static)", overlay_frame(ctx, detail_panel(ctx, "c-drawer"), scrim=True, side="end", tall=True),
           f"{str(n.get('elevation')).strip('{}')} · {n.get('width')}px · side {n.get('side')}", wide=True)


def detail_panel(ctx, cls, title="Invoice extraction"):
    data, _ = examples(ctx)
    row = next((d for d in data if d[0] == title), data[0])
    k, lab = zone(ctx, row[1], row[2])
    zh, za = ctx.tx(f"platform.quadrant.zones.{k}", lab)
    return (f'<aside class="{cls}" role="dialog" aria-labelledby="dp-{cls}"><div class="c-drawer__head">'
            f'<h2 class="c-dialog__title" id="dp-{cls}">{esc(row[0])}</h2>'
            f'<button class="c-iconbtn" type="button"{ctx.aria(None, "Close")}>{ctx.icon("x", 20)}</button></div>'
            f'{score_meter(ctx, 4.2) if ctx.comp("score") else ""}<p class="c-kpi__sub"><span{za}>{zh}</span> · {row[3]}</p></aside>')


@comp("side_panel", "Overlays")
def c_side(ctx, n, o):
    S = o.css
    dialog_css(ctx, S)
    S.rule(".c-side", [("inline-size", "100%"), ("max-inline-size", px(n.get("width", 420))), ("background-color", ctx.color(n.get("bg"))),
                       (f"border-{n.get('side', 'inline-end').replace('inline-end', 'inline-start')}", ctx.border(n.get("edge"))),
                       ("padding", "var(--space-sp-4)"), ("display", "grid"), ("align-content", "start"), ("gap", "var(--space-sp-3)"),
                       ("margin-inline-start", "auto")])
    o.spec("open · no scrim", overlay_frame(ctx, detail_panel(ctx, "c-side"), side="end"), f"{n.get('width')}px · edge {bind({'e': n.get('edge')})[2:]} · scrim none · not trapped", wide=True)


@comp("menu", "Overlays")
def c_menu(ctx, n, o):
    S = o.css
    S.rule(".c-menu", ctx.elev_decls(n.get("elevation")) + [("min-inline-size", px(n.get("min_width", 240))), ("max-inline-size", "100%"),
                                                          ("border-radius", "var(--radius-floating)"), ("padding-block", "var(--space-sp-1)"),
                                                          ("transition", ctx.transition("menu", "enter"))])
    S.rule(".c-menu__item", [("display", "flex"), ("align-items", "center"), ("gap", "var(--space-sp-2)"), ("inline-size", "100%"),
                             ("min-block-size", "var(--target-min)"), ("padding-inline", "var(--space-sp-3)"), ("text-align", "start"),
                             ("transition", ctx.transition("row"))] + ctx.type_decls("{type.caption}"))
    ctx.states(S, ".c-menu__item", "hover", [("background-color", ctx.color("{color.state.surface_hover}"))])
    S.rule(".c-menu__item:focus-visible, .c-menu__item[data-force~=\"focus\"]", ctx.focus() + [("outline-offset", "-2px")])
    S.rule(".c-menu__sep", [("block-size", "1px"), ("background-color", ctx.color("{color.border}")), ("margin-block", "var(--space-sp-1)")])
    o.spec("open · hover · roving focus", menu_html(ctx), f"{str(n.get('elevation')).strip('{}')} · min {n.get('min_width')}px · roving focus")


def menu_html(ctx, head=""):
    items = [("platform.top_bar.settings", "settings"), ("platform.top_bar.shortcuts", "keyboard"), (None, None), ("platform.top_bar.sign_out", "log-out")]
    out = []
    for k, (key, ic) in enumerate(items):
        if key is None:
            out.append('<li class="c-menu__sep" role="separator"></li>')
            continue
        h, a = ctx.tx(key, "")
        f = ' data-force="hover"' if k == 0 else (' data-force="focus"' if k == 1 else "")
        out.append(f'<li role="none"><button class="c-menu__item" role="menuitem" type="button"{f}>{ctx.icon(ic, 16)}<span{a}>{h}</span></button></li>')
    return f'<div class="c-menu">{head}<ul role="menu">{"".join(out)}</ul></div>'


@comp("popover", "Overlays")
def c_popover(ctx, n, o):
    S = o.css
    S.rule(".c-pop", ctx.elev_decls(n.get("elevation")) + [("max-inline-size", px(n.get("max_width", 360))), ("inline-size", "100%"),
                                                         ("border-radius", "var(--radius-floating)"), ("padding", "var(--space-sp-3) var(--space-sp-4)"),
                                                         ("display", "grid"), ("gap", "var(--space-sp-2)"), ("transition", ctx.transition("popover", "enter"))])
    S.rule(".c-pop__title", ctx.type_decls("{type.eyebrow}") + [("color", ctx.color("{color.muted}"))])
    h = (f'<div class="c-pop" role="dialog" aria-label="{esc(ctx.s("platform.tasks.title", "Tasks"))}">{ctx.el("p", "platform.tasks.title", "", "c-pop__title")}'
         f'{ctx.el("p", "platform.tasks.none", "", "fx-small")}</div>')
    o.spec("open", h, f"{str(n.get('elevation')).strip('{}')} · max {n.get('max_width')}px")


@comp("tooltip", "Overlays")
def c_tooltip(ctx, n, o):
    S = o.css
    S.rule(".c-tip", ctx.elev_decls(n.get("elevation")) + ctx.type_decls("{type.caption}") +
           [("display", "inline-flex"), ("align-items", "center"), ("gap", "var(--space-sp-2)"), ("max-inline-size", px(n.get("max_width", 280))),
            ("padding", "var(--space-sp-1) var(--space-sp-2)"), ("border-radius", "var(--radius-floating)"),
            ("transition", ctx.transition("tooltip", "enter"))])
    h = (f'<span class="c-tip" role="tooltip">{ctx.el("span", "platform.nav.collapse", "")}'
         f'{kbd_html(ctx, "[")}</span>')
    o.spec("open", h, f"{str(n.get('elevation')).strip('{}')} · max {n.get('max_width')}px · delay {n.get('delay_ms')}ms, peers {n.get('delay_peers_ms')}ms · not interactive")


@comp("palette", "Overlays")
def c_palette(ctx, n, o):
    S = o.css
    dialog_css(ctx, S)
    S.rule(".c-palette", ctx.elev_decls(n.get("elevation")) + [("inline-size", "100%"), ("max-inline-size", px(n.get("width", 640))),
                                                             ("border-radius", "var(--radius-floating)"), ("position", "relative"),
                                                             ("margin-inline", "auto")])
    S.rule(".c-palette__search", [("display", "flex"), ("align-items", "center"), ("gap", "var(--space-sp-2)"), ("padding-inline", "var(--space-sp-3)"),
                                  ("border-block-end", ctx.border({"width": 1, "style": "solid", "color": "{color.border}"}))])
    S.rule(".c-palette__search input", [("flex", "1"), ("min-inline-size", "0"), ("min-block-size", "var(--density-comfortable-row)"), ("border", "0"),
                                        ("background-color", "transparent"), ("outline", "none")])
    S.rule(".c-palette__group", [("padding-block", "var(--space-sp-2)")])
    S.rule(".c-palette__head", ctx.type_decls("{type.eyebrow}") + [("color", ctx.color("{color.muted}")), ("padding-inline", "var(--space-sp-3)"),
                                                                 ("padding-block", "var(--space-sp-1)")])
    o.spec("open · selected", overlay_frame(ctx, palette_html(ctx), scrim=True, side="top", top=n.get("top", "20%")),
           f"{str(n.get('elevation')).strip('{}')} + scrim · {n.get('width')}px · top {n.get('top')} · {n.get('shortcut')} · motion instant", wide=True)


def palette_html(ctx):
    n = ctx.comp("palette") or {}
    secs = n.get("sections") or []
    data, _ = examples(ctx)
    pl = pillars(ctx)
    content = {"Actions": [ctx.s("platform.empty.use_cases.action", ""), ctx.s("platform.empty.governance.action", "")],
               "Use cases": [d[0] for d in data[:2]], "Programmes": [p["label"] for p in pl[:2]],
               "Recent": [ctx.s("platform.nav.scorecard", ""), ctx.s("platform.nav.roadmap", "")]}
    i = uid(ctx, "pal")
    groups = []
    first = True
    for s in secs:
        opts = []
        for x in content.get(s, []):
            sel = ' aria-selected="true"' if first else ' aria-selected="false"'
            first = False
            opts.append(f'<li class="c-option" role="option"{sel}><span>{esc(x)}</span>{ctx.icon("corner-down-left", 16)}</li>')
        groups.append(f'<div class="c-palette__group" role="group" aria-label="{esc(s)}"><p class="c-palette__head">{esc(s)}</p><ul>{"".join(opts)}</ul></div>')
    return (f'<div class="c-palette" role="dialog" aria-modal="true" aria-label="Command palette"><div class="c-palette__search">{ctx.icon("search", 20)}'
            f'<label class="c-sr" for="{i}">Search</label><input id="{i}" type="text" role="combobox" aria-expanded="true" autocomplete="off"'
            f'{ctx.aria("platform.empty.palette", "", attr="placeholder", short="ph")}>{kbd_html(ctx, "Esc")}</div>'
            f'<div role="listbox">{"".join(groups)}</div></div>')


@comp("shortcuts", "Overlays")
def c_shortcuts(ctx, n, o):
    dialog_css(ctx, o.css)
    en = ctx._lookup("en", "platform.shortcuts") or {}
    rev = {v: k for k, v in en.items() if isinstance(v, str)}
    rows = []
    for it in n.get("list") or []:
        key = rev.get(it.get("action"))
        h, a = ctx.tx(f"platform.shortcuts.{key}", it.get("action")) if key else (esc(it.get("action")), "")
        keys = " ".join(kbd_html(ctx, k.strip()) for k in re.split(r"\+", it.get("keys", "").replace("Mod", "Ctrl")) if k.strip())
        rows.append(f'<tr><td{a}>{h}</td><td class="c-table__num">{keys}</td></tr>')
    th1, ta1 = ctx.tx("platform.shortcuts.action", "Action")
    th2, ta2 = ctx.tx("platform.shortcuts.keys", "Keys")
    d = (f'<div class="c-dialog c-dialog--{n.get("width", 640)}" role="dialog" aria-modal="true" aria-labelledby="dlg-sc">'
         f'{ctx.el("h2", "platform.shortcuts.title", "", "c-dialog__title", attrs=" id=\"dlg-sc\"")}'
         f'<div class="c-table-wrap"><table class="c-table"><thead><tr><th scope="col"{ta1}>{th1}</th><th scope="col" class="c-table__num"{ta2}>{th2}</th></tr></thead>'
         f'<tbody>{"".join(rows)}</tbody></table></div></div>')
    o.spec("open", overlay_frame(ctx, d, scrim=True), f"base modal {n.get('width')} · table + kbd · motion {n.get('motion')}", wide=True)


# ── Data ─────────────────────────────────────────────────────────────────
@comp("row", "Data")
def c_row(ctx, n, o):
    S = o.css
    S.rule(".c-row", [("display", "flex"), ("align-items", "center"), ("gap", "var(--space-sp-3)"), ("inline-size", "100%"),
                      ("min-block-size", "var(--density-compact-row)"), ("padding-inline", "var(--density-compact-pad-x)"),
                      ("text-align", "start"), ("text-decoration-line", "none"), ("transition", ctx.transition("row")),
                      ("border-inline-start", ctx.border({**((n.get("selected") or {}).get("edge") or {"width": 2, "style": "solid"}), "color": "transparent"}))] +
           ctx.paint(n.get("rest") or {}))
    for st in ("hover", "active", "selected", "disabled"):
        ctx.states(S, ".c-row", st, ctx.paint(n.get(st) or {}, edge="inline-start"))
    f = n.get("focus") or {}
    S.rule('.c-row:focus-visible, .c-row[data-force~="focus"]', ctx.paint(f))
    S.rule(".c-row--static", [("cursor", "default")])
    for st, a in (("rest", ""), ("hover", ' data-force="hover"'), ("active", ' data-force="active"'), ("focus", ' data-force="focus"'),
                  ("selected", ' aria-current="true"'), ("disabled", ' aria-disabled="true"')):
        o.spec(st, f'<a class="c-row c-hit" href="#"{a}>Invoice extraction<span class="c-table__numcell">86</span></a>', bind(n.get(st)))
    o.notes.append(n.get("$note", ""))


@comp("table", "Data")
def c_table(ctx, n, o):
    S = o.css
    hd = n.get("header") or {}
    dens = n.get("density", "compact")
    S.rule(".c-table-wrap", [("overflow-x", "auto"), ("max-inline-size", "100%")])
    S.rule(".c-table", [("inline-size", "100%"), ("border-collapse", "collapse"), ("font-size", f"var(--density-{dens}-text)")])
    S.rule(".c-table th", ctx.type_decls(hd.get("type")) + [("font-size", px(hd["size"])) if hd.get("size") else None,
                                                         ("letter-spacing", hd.get("tracking")), ("color", ctx.color(hd.get("fg"))),
                                                         ("font-weight", "500"), ("text-align", "start"),
                                                         ("border-block-end", ctx.border(hd.get("rule"))),
                                                         ("padding-block", f"var(--density-{dens}-pad-y)"), ("padding-inline", f"0 var(--density-{dens}-pad-x)"),
                                                         ("position", "sticky"), ("inset-block-start", "0"), ("background-color", ctx.color("{color.bg}")),
                                                         ("white-space", "nowrap")])
    S.rule(".c-table td", [("vertical-align", "middle"), ("padding-block", f"var(--density-{dens}-pad-y)"), ("padding-inline", f"0 var(--density-{dens}-pad-x)"),
                           ("block-size", f"var(--density-{dens}-row)"), ("border-block-end", ctx.border(n.get("row_rule"))),
                           ("max-inline-size", f"{(n.get('truncation') or {}).get('max_width_ch', 40)}ch"),
                           ("overflow", "hidden"), ("text-overflow", "ellipsis"), ("white-space", "nowrap")])
    S.rule(".c-table--dense td", [("block-size", "var(--density-dense-row)"), ("padding-block", "var(--density-dense-pad-y)"), ("font-size", "var(--density-dense-text)")])
    nm = n.get("numerals") or {}
    S.rule(".c-table__num, .c-table__numcell", [("font-family", f"var(--font-{nm.get('family', 'mono')})"), ("font-variant-numeric", "tabular-nums"),
                                                ("text-align", nm.get("align", "end"))])
    S.rule(".c-table th.c-table__num", [("text-align", nm.get("align", "end"))])
    S.rule(".c-table__numcell", [("margin-inline-start", "auto")])
    S.rule(".c-table__zone", ctx.type_decls("{type.mono}") + [("font-size", "var(--density-compact-label)"), ("color", ctx.color("{color.muted}"))])
    row = ctx.comp("row") or {}
    S.rule(".c-table tbody tr", [("transition", ctx.transition("row"))])
    S.rule(".c-table tbody td:first-child", [("border-inline-start", ctx.border({**((row.get("selected") or {}).get("edge") or {"width": 2, "style": "solid"}), "color": "transparent"}))])
    ctx.states(S, ".c-table tbody tr", "hover", ctx.paint({"bg": (row.get("hover") or {}).get("bg")}))
    ctx.states(S, ".c-table tbody tr", "selected", ctx.paint({"bg": (row.get("selected") or {}).get("bg")}))
    S.rule('.c-table tbody tr[aria-selected="true"] td:first-child, .c-table tbody tr[data-force~="selected"] td:first-child',
           [("border-inline-start-color", ctx.color(((row.get("selected") or {}).get("edge") or {}).get("color")))])
    S.rule(".c-table__sort", [("display", "inline-flex"), ("align-items", "center"), ("gap", "var(--space-sp-1)"), ("color", "inherit"),
                              ("letter-spacing", "inherit"), ("text-transform", "inherit"), ("font-weight", "inherit")])
    ctx.states(S, ".c-table__sort", "hover", [("color", ctx.color("{color.fg}"))])
    S.rule(".c-table__name", [("display", "block"), ("max-inline-size", "100%"), ("text-decoration-line", "none"),
                              ("overflow", "hidden"), ("text-overflow", "ellipsis"), ("white-space", "nowrap")])
    ctx.states(S, ".c-table__name", "hover", [("text-decoration-line", "underline")])
    S.rule(".c-table .c-check", [("min-block-size", "auto"), ("min-inline-size", "auto")])
    S.rule(".c-table .c-check::after", [("content", '""'), ("position", "absolute"), ("inset", "min(0px, calc(50% - var(--target-min) / 2))")])
    sb = n.get("selection_bar") or {}
    S.rule(".c-selbar", ctx.paint({k: sb[k] for k in ("bg", "fg") if k in sb}) +
           [("display", "flex"), ("flex-wrap", "wrap"), ("align-items", "center"), ("gap", "var(--space-sp-3)"),
            ("min-block-size", "var(--density-compact-row)"), ("padding-inline", "var(--density-compact-pad-x)")])
    S.rule(".c-selbar__n", ctx.type_decls("{type.mono}"))
    # phone: the table becomes rows (p104)
    S.rule(".c-table--stack thead", [("display", "none")])
    S.rule(".c-table--stack tr", [("display", "grid"), ("grid-template-columns", "auto minmax(0, 1fr) auto"), ("align-items", "center"),
                                  ("column-gap", "var(--space-sp-2)"), ("border-block-end", ctx.border(n.get("row_rule")))])
    S.rule(".c-table--stack td", [("border-block-end", "0"), ("block-size", "auto"), ("padding-block", "var(--space-sp-1)")])
    S.rule(".c-table--stack td:first-child", [("grid-column", "1"), ("grid-row", "1 / span 2")])
    S.rule(".c-table--stack td:nth-child(2)", [("grid-column", "2"), ("grid-row", "1")])
    S.rule(".c-table--stack td.c-table__num", [("grid-column", "3"), ("grid-row", "1")])
    S.rule(".c-table--stack td.c-table__zone", [("grid-column", "2 / -1"), ("grid-row", "2"), ("padding-block-start", "0")])
    t = ctx.mq("tablet")
    if t:
        i = Sheet()
        i.rule(".c-table--stack thead", [("display", "table-header-group")])
        i.rule(".c-table--stack tr", [("display", "table-row")])
        i.rule(".c-table--stack td", [("border-block-end", ctx.border(n.get("row_rule"))), ("block-size", f"var(--density-{dens}-row)"),
                                      ("padding-block", f"var(--density-{dens}-pad-y)")])
        S.media(t, i)
    o.spec("rest · hover · selected · focus · sort", table_html(ctx, force=True), f"header {bind(hd, ('fg', 'rule'))} · row_rule · {dens} · numerals mono end · zebra {n.get('zebra')}", wide=True)
    o.spec("selection bar", selbar_html(ctx, 2), bind(sb, ("bg", "fg")), wide=True)
    o.spec("dense (≥25 rows)", table_html(ctx, dense=True), f"dense from {n.get('dense_from_rows')} rows · data tables only", wide=True)
    o.spec("loading", f'<div class="c-skel-group" aria-busy="true">{"".join("<span class=c-skel c-skel--row></span>".replace("class=c-skel c-skel--row", "class=\"c-skel c-skel--row\"") for _ in range(4))}</div>',
           "skeleton rows at the row's own height", wide=True)
    o.spec("empty cell", f'<p class="fx-prose">{esc(n.get("empty_cell", "–"))} <span class="fx-small">— an en dash, never a blank, never N/A</span></p>', "empty_cell")


def selbar_html(ctx, k):
    t = ctx.s("platform.table.selected", "{n} selected").format(n=k)
    return (f'<div class="c-selbar" role="region" aria-label="Selection"><span class="c-selbar__n">{esc(t)}</span>'
            f'{btn(ctx, "secondary", "Export", None, icon="download")}{btn(ctx, "tertiary", "Clear", "platform.table.clear_selection").replace("c-button__arrow", "c-sr")}</div>')


def table_html(ctx, force=False, dense=False, selectable=True, sel=None):
    n = ctx.comp("table") or {}
    so = n.get("sort") or {}
    data, _ = examples(ctx)
    rows = []
    for k, (name, r, i, sc) in enumerate(sorted(data, key=lambda d: -d[3])):
        zk, lab = zone(ctx, r, i)
        zh, za = ctx.tx(f"platform.quadrant.zones.{zk}", lab)
        a = ""
        if force and k == 1:
            a = ' data-force="hover"'
        if (force and k == 2) or sel == name:
            a = ' aria-selected="true"'
        cb = ""
        if selectable:
            cid = uid(ctx, "row")
            chk = " checked" if 'aria-selected' in a else ""
            cb = (f'<td><label class="c-check" for="{cid}"><input class="c-check__box" type="checkbox" id="{cid}"{chk}>'
                  f'{ctx.icon("check", 16, "c-check__mark")}<span class="c-sr">{esc(name)}</span></label></td>')
        nf = ' data-force="focus"' if force and k == 3 else ""
        rows.append(f'<tr{a}>{cb}<td><a class="c-table__name c-hit" href="#"{nf} title="{esc(name)}">{esc(name)}</a></td>'
                    f'<td class="c-table__zone"{za}>{zh}</td><td class="c-table__num">{sc}</td></tr>')
    icon = lambda s: ctx.icon(so.get({"none": "unsorted_icon", "ascending": "asc_icon", "descending": "desc_icon"}[s]), so.get("icon_px", 16))  # noqa: E731
    col = lambda lab, s, cls="": (f'<th scope="col" aria-sort="{s}"{" class=" + chr(34) + cls + chr(34) if cls else ""}>'  # noqa: E731
                                  f'<button class="c-table__sort c-hit" type="button">{esc(lab)}{icon(s)}</button></th>')
    head = ("<th scope=\"col\"><span class=\"c-sr\">Select</span></th>" if selectable else "") + \
        col("Use case", "none") + col("Zone", "none") + col("Score", "descending", "c-table__num")
    d = " c-table--dense" if dense else ""
    return (f'<div class="c-table-wrap"><table class="c-table c-table--stack{d}"><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


@comp("score", "Data")
def c_score(ctx, n, o):
    S = o.css
    S.rule(".c-score", [("display", "grid"), ("gap", "var(--space-sp-2)"), ("max-inline-size", "32ch")])
    S.rule(".c-score__top", [("display", "flex"), ("align-items", "baseline"), ("gap", "var(--space-sp-2)")])
    S.rule(".c-score__num", ctx.type_decls("{type.heading_lg}") + [("font-family", f"var(--font-{(n.get('numeral') or {}).get('family', 'display')})"),
                                                                 ("font-variant-numeric", "tabular-nums"), ("color", ctx.color(n.get("fg")))])
    S.rule(".c-score__band", ctx.type_decls("{type.eyebrow}") + [("color", ctx.color(n.get("fg")))])
    S.rule(".c-score__track", [("position", "relative"), ("block-size", "var(--space-sp-2)"), ("background-color", ctx.color(n.get("track"))),
                               ("direction", "ltr")])
    S.rule(".c-score__fill", [("position", "absolute"), ("inset", "0"), ("background-color", ctx.color(n.get("fill"))),
                              ("transform-origin", "left"), ("transition", ctx.transition("score_meter_fill"))])
    for v in (1.2, 2.8, 4.2):
        o.spec(f"rest · {band(n, v)}", score_meter(ctx, v), f"track {str(n.get('track')).strip('{}')} · fill {str(n.get('fill')).strip('{}')} · band a word, never a colour")


def band(n, v):
    for k, (a, b) in (n.get("bands") or {}).items():
        if a <= v <= b + 0.05:
            return k
    return ""


def score_meter(ctx, v):
    n = ctx.comp("score") or {}
    return (f'<div class="c-score"><div class="c-score__top"><span class="c-score__num">{v:.1f}</span>'
            f'<span class="c-score__band">{esc(band(n, v))}</span></div><div class="c-score__track" role="meter" aria-valuemin="0" '
            f'aria-valuemax="5" aria-valuenow="{v}" aria-label="Score"><span class="c-score__fill" style="transform: scaleX({v / 5:.2f})"></span></div></div>')


@comp("kpi", "Data")
def c_kpi(ctx, n, o):
    S = o.css
    nm = n.get("numeral") or {}
    S.rule(".c-kpi", [("display", "flex"), ("flex-wrap", "wrap"), ("align-items", "flex-end"), ("justify-content", "space-between"), ("gap", "var(--space-sp-4)")])
    S.rule(".c-kpi__fig", [("display", "grid"), ("gap", "var(--space-sp-1)")])
    S.rule(".c-kpi__num", ctx.type_decls(nm.get("type")) + [("font-family", f"var(--font-{nm.get('family', 'display')})"),
                                                          ("font-variant-numeric", "tabular-nums"), ("color", ctx.color(nm.get("fg")))])
    lb = n.get("label") or {}
    S.rule(".c-kpi__label", ctx.type_decls(lb.get("type")) + [("color", ctx.color(lb.get("fg")))])
    sc = n.get("secondary") or {}
    S.rule(".c-kpi__sub", ctx.type_decls(sc.get("type")) + [("color", ctx.color(sc.get("fg"))), ("font-variant-numeric", "tabular-nums")])
    o.spec("rest", kpi_html(ctx, 24), f"numeral {str(nm.get('type')).strip('{}')} tabular · one per screen · no bg, no border", wide=True)
    o.spec("loading", kpi_html(ctx, None, loading=True), n.get("loading", ""), wide=True)
    o.spec("empty", kpi_html(ctx, 0), n.get("empty", ""), wide=True)


def kpi_html(ctx, value, loading=False, label_key="platform.kpi.scored", sub=True, action=True):
    n = ctx.comp("kpi") or {}
    num = '<span class="c-skel c-skel--num" aria-hidden="true"></span>' if loading else f'<span class="c-kpi__num">{value}</span>'
    s = ""
    if sub and value:
        a = ctx.s("platform.kpi.in_build", "{n}").format(n=7)
        b = ctx.s("platform.kpi.live", "{n}").format(n=3)
        s = f'<p class="c-kpi__sub">{esc(a)} · {esc(b)}</p>'
    ac = btn(ctx, (n.get("action") or {}).get("variant", "primary"), "Add use case", "platform.kpi.add", icon="plus") if action else ""
    busy = ' aria-busy="true"' if loading else ""
    return (f'<div class="c-kpi" aria-live="polite"{busy}><div class="c-kpi__fig">{num}{ctx.el("p", label_key, "", "c-kpi__label")}{s}</div>{ac}</div>')


@comp("quadrant", "Data")
def c_quadrant(ctx, n, o):
    S = o.css
    ax = n.get("axes") or {}
    pa = n.get("partition") or {}
    dot = n.get("dot") or {}
    lab = n.get("label") or {}
    zn = n.get("zones") or {}
    S.rule(".c-quad", [("display", "grid"), ("grid-template-columns", "auto minmax(0, 1fr)"), ("grid-template-rows", "minmax(0, 1fr) auto auto"),
                       ("gap", "var(--space-sp-2)"), ("inline-size", "100%"), ("max-inline-size", "calc(var(--space-sp-8) * 6)")])
    S.rule(".c-quad__plot", [("position", "relative"), ("grid-column", "2"), ("grid-row", "1"), ("aspect-ratio", "4 / 3"), ("min-block-size", "0")])
    S.rule(".c-quad__svg", [("position", "absolute"), ("inset", "0"), ("inline-size", "100%"), ("block-size", "100%"), ("overflow", "visible")])
    S.rule(".c-quad__axis", [("stroke", ctx.color(ax.get("rule", {}).get("color"))), ("stroke-width", px(ax.get("rule", {}).get("width", 1))),
                             ("fill", "none")])
    S.rule(".c-quad__cut", [("stroke", ctx.color((pa.get("rule") or {}).get("color"))), ("stroke-width", px((pa.get("rule") or {}).get("width", 1))),
                            ("fill", "none")])
    zl = zn.get("label") or {}
    S.rule(".c-quad__zone", ctx.type_decls(zl.get("type")) + [("position", "absolute"), ("color", ctx.color(zl.get("fg"))),
                                                            ("font-size", "var(--density-dense-label)"), ("letter-spacing", "0.08em"),
                                                            ("padding", "var(--space-sp-1) var(--space-sp-2)"), ("pointer-events", "none")])
    S.rule(".c-quad__zone--start-top", [("inset-inline-start", "0"), ("inset-block-start", "0")])
    q = ((ctx.cfg.get("patterns") or {}).get("quadrant") or {}).get("cuts") or {}
    S.rule(".c-quad__zone--mid-top", [("inset-inline-start", f"{q.get('readiness_foundations', 50)}%"), ("inset-block-start", "0"),
                                      ("max-inline-size", f"{q.get('readiness_start', 65) - q.get('readiness_foundations', 50)}%")])
    S.rule(".c-quad__zone--end-top", [("inset-inline-end", "0"), ("inset-block-start", "0"), ("text-align", "end")])
    S.rule(".c-quad__zone--end-bottom", [("inset-inline-end", "0"), ("inset-block-end", "0"), ("text-align", "end")])
    S.rule(".c-quad__axis-title", ctx.type_decls((ax.get("title") or {}).get("type")) + [("color", ctx.color((ax.get("title") or {}).get("fg"))),
                                                                                       ("font-size", "var(--density-dense-label)")])
    S.rule(".c-quad__axis-title--x", [("grid-column", "2"), ("grid-row", "2"), ("justify-self", "end")])
    S.rule(".c-quad__axis-title--y", [("grid-column", "1"), ("grid-row", "1"), ("writing-mode", "vertical-rl"), ("transform", "rotate(180deg)"),
                                      ("align-self", "start")])
    S.rule(".c-quad__note", [("grid-column", "1 / -1"), ("grid-row", "3")] + ctx.type_decls("{type.eyebrow}") +
           [("font-size", "var(--density-dense-label)"), ("letter-spacing", "0"), ("text-transform", "none"), ("color", ctx.color("{color.muted}"))])
    ds = px(dot.get("size", 8))
    S.rule(".c-quad__dot", [("position", "absolute"), ("display", "inline-flex"), ("align-items", "center"), ("gap", "var(--space-sp-1)"),
                            ("min-block-size", "var(--target-min)"), ("min-inline-size", "var(--target-min)"),
                            ("translate", f"calc(-1 * var(--space-sp-1) - {ds} / 2) 50%"),
                            ("padding-inline-start", "calc(var(--space-sp-1) + var(--space-sp-1))"), ("padding-inline-end", "var(--space-sp-1)"),
                            ("white-space", "nowrap"), ("border-radius", "var(--radius-control)"),
                            ("transition", ctx.transition("quadrant_platform", "move"))] + ctx.type_decls(lab.get("type")) +
           [("font-size", "var(--density-dense-label)"), ("color", ctx.color(lab.get("fg")))])
    S.rule(".c-quad__dot::before", [("content", '""'), ("flex", "none"), ("inline-size", ds), ("block-size", ds), ("margin-inline-start", f"calc(-1 * {ds} / 2)"),
                                    ("border-radius", "var(--radius-floating)"), ("background-color", ctx.color(dot.get("fill"))),
                                    ("transition", ctx.transition("quadrant_platform", "arrival"))])
    S.rule(".c-quad__dot--end", [("flex-direction", "row-reverse"), ("padding-inline", "var(--space-sp-1) calc(var(--space-sp-1) + var(--space-sp-1))"),
                                 ("translate", "calc(-100% + var(--space-sp-1) + var(--space-sp-1)) 50%")])
    S.rule(".c-quad__dot--end::before", [("margin-inline-start", "0"), ("margin-inline-end", f"calc(-1 * {ds} / 2)")])
    hv = (dot.get("hover") or {}).get("size")
    if hv:
        S.rule('.c-quad__dot[data-force~="hover"]::before', [("inline-size", px(hv)), ("block-size", px(hv))])
        inner = Sheet()
        inner.rule(".c-quad__dot:hover::before", [("inline-size", px(hv)), ("block-size", px(hv))])
        S.media(ctx.hover_q, inner)
    S.rule('.c-quad__dot[aria-pressed="true"]::before', ctx.outline((dot.get("selected") or {}).get("outline")))
    # A label crossing a partition line is unreadable: knock the line out
    # behind the text with the ground colour (a fill, not a box — no border,
    # no radius). Found on the 1280 render of the portfolio screen.
    S.rule(".c-quad__label", [("background-color", ctx.color("{color.bg}")), ("padding-inline", "var(--space-sp-1)")])
    S.rule(".c-quad__dot--blocked::before", [("background-color", ctx.color((dot.get("blocked") or {}).get("fill")))])
    S.rule(".c-quad__score", [("color", ctx.color("{color.muted}")), ("font-variant-numeric", "tabular-nums")])
    S.rule(".c-quad__empty", [("position", "absolute"), ("inset-inline-end", "0"), ("inset-block-start", "var(--space-sp-5)"),
                              ("inline-size", f"{100 - q.get('readiness_start', 65)}%"), ("display", "grid"), ("gap", "var(--space-sp-2)"),
                              ("padding", "var(--space-sp-2)"), ("justify-items", "start")])
    S.rule(".c-quad__empty-title", ctx.type_decls("{type.caption}"))
    S.rule(".c-quad[aria-busy] .c-quad__zone", [("visibility", "hidden")])
    # the list form: phone (p104) and the linked list beside the chart
    S.rule(".c-scorelist__row", [("display", "grid"), ("grid-template-columns", "minmax(0, 1fr) auto auto"), ("align-items", "center"),
                                 ("column-gap", "var(--space-sp-3)"), ("min-block-size", "var(--density-compact-row)"),
                                 ("border-block-end", ctx.border({"width": 1, "style": "solid", "color": "{color.border}"}))])
    # overflow: clip (not hidden) with a clip margin, so the .c-hit area that
    # extends the link to the target size is not cut off by the truncation
    S.rule(".c-scorelist__name", [("display", "block"), ("min-inline-size", "0"), ("text-decoration-line", "none"), ("overflow", "clip"),
                                  ("overflow-clip-margin", "var(--space-sp-2)"), ("text-overflow", "ellipsis"), ("white-space", "nowrap")])
    ctx.states(S, ".c-scorelist__name", "hover", [("text-decoration-line", "underline")])
    S.rule(".c-scorelist__zone", ctx.type_decls("{type.mono}") + [("font-size", "var(--density-compact-label)"), ("color", ctx.color("{color.muted}"))])
    S.rule(".c-scorelist__score", ctx.type_decls("{type.mono}") + [("font-variant-numeric", "tabular-nums"), ("text-align", "end")])
    lay = n.get("layout") or {}
    o.spec("rest · selected", quadrant_html(ctx, selected="Tender triage"), f"axes {bind({'r': ax.get('rule')})[2:]} · cuts {bind({'r': pa.get('rule')})[2:]} · dot {dot.get('size')}px {str(dot.get('fill')).strip('{}')} · zones unfilled · never mirrors", wide=True)
    o.spec("blocked · hover · focus", quadrant_html(ctx, blocked="HR onboarding assistant").replace('data-d="1"', 'data-d="1" data-force="hover"').replace('data-d="2"', 'data-d="2" data-force="focus"'),
           f"blocked {bind(dot.get('blocked'), ('fill',))} · hover {px((dot.get('hover') or {}).get('size', 10))} · focus ring", wide=True)
    o.spec("loading", quadrant_html(ctx, loading=True), (n.get("states") or {}).get("loading", ""), wide=True)
    o.spec("empty", quadrant_html(ctx, empty=True), (n.get("states") or {}).get("empty", ""), wide=True)
    o.spec("phone · the list", score_list(ctx), lay.get("phone", ""))


@comp("stepper", "Data")
def c_stepper(ctx, n, o):
    S = o.css
    st = n.get("states") or {}
    S.rule(".c-stepper", [("display", "grid"), ("gap", "var(--space-sp-2)"), ("grid-template-columns", "minmax(0, 1fr)")])
    S.rule(".c-step", [("display", "grid"), ("gap", "var(--space-sp-1)"), ("padding-inline-start", "var(--space-sp-3)"),
                       ("padding-block", "var(--space-sp-1)")] + ctx.paint(st.get("todo") or {}, rule="inline-start"))
    S.rule(".c-step__num", ctx.type_decls("{type.eyebrow}") + [("font-size", "var(--density-dense-label)")])
    S.rule(".c-step__label", ctx.type_decls("{type.caption}"))
    S.rule('.c-step[data-state="done"]', ctx.paint(st.get("done") or {}, rule="inline-start"))
    S.rule('.c-step[aria-current="step"]', ctx.paint(st.get("current") or {}, rule="inline-start"))
    S.rule('.c-step[aria-current="step"] .c-step__num', [("color", ctx.color(((st.get("current") or {}).get("rule") or {}).get("color")))])
    t = ctx.mq("tablet")
    if t:
        i = Sheet()
        i.rule(".c-stepper", [("grid-template-columns", "repeat(6, minmax(0, 1fr))"), ("column-gap", "var(--space-sp-3)")])
        i.rule(".c-step", [("padding-inline-start", "0"), ("padding-block", "var(--space-sp-2) 0"), ("border-inline-start", "0")])
        for k in ("todo", "done", "current"):
            r = (st.get(k) or {}).get("rule")
            sel = {"todo": ".c-step", "done": '.c-step[data-state="done"]', "current": '.c-step[aria-current="step"]'}[k]
            i.rule(sel, [("border-block-start", ctx.border(r)), ("border-inline-start", "0")])
        S.media(t, i)
    o.spec("done · current · todo", stepper_html(ctx, 2), " · ".join(f"{k}: {bind(st.get(k))}" for k in ("done", "current", "todo")) + " · never a percentage", wide=True)


def stepper_html(ctx, current):
    lis = []
    for k, s in enumerate(stages(ctx)):
        a = ' data-state="done"' if k < current else (' aria-current="step"' if k == current else "")
        lis.append(f'<li class="c-step"{a}><span class="c-step__num">{k + 1:02d}</span><span class="c-step__label">{esc(s)}</span></li>')
    return f'<ol class="c-stepper">{"".join(lis)}</ol>'


@comp("filter_bar", "Data")
def c_filter(ctx, n, o):
    S = o.css
    se = n.get("search") or {}
    S.rule(".c-filter", [("display", "flex"), ("flex-wrap", "wrap"), ("align-items", "center"), ("gap", ctx.length(n.get("gap")))])
    S.rule(".c-filter__search", [("position", "relative"), ("display", "block"), ("padding-block", "var(--space-sp-1)"),
                                 ("inline-size", f"min(100%, {se.get('width_ch', 24) + 6}ch)")])
    S.rule(".c-filter__search .c-icon", [("position", "absolute"), ("inset-inline-start", "var(--density-compact-pad-x)"), ("inset-block-start", "50%"),
                                         ("translate", "0 -50%"), ("color", ctx.color("{color.muted}")), ("pointer-events", "none")])
    S.rule(".c-filter__search .c-input", [("padding-inline-start", "calc(var(--density-compact-pad-x) + var(--space-sp-4))")])
    S.rule(".c-filter__search .c-kbd", [("position", "absolute"), ("inset-inline-end", "var(--space-sp-2)"), ("inset-block-start", "50%"),
                                        ("translate", "0 -50%")])
    S.rule(".c-input--compact", [("min-block-size", "var(--density-compact-row)"), ("padding-inline", "var(--density-compact-pad-x)"),
                                 ("font-size", "var(--density-compact-text)")])
    S.rule(".c-filter .c-select", [("padding-block", "var(--space-sp-1)")])
    S.rule(".c-filter .c-select .c-input", [("padding-inline-end", "var(--space-sp-5)")])
    S.rule(".c-filter .c-button", [("min-block-size", "var(--density-compact-row)")])
    ac = n.get("active_count") or {}
    S.rule(".c-filter__count", ctx.type_decls(ac.get("type")) + [("color", ctx.color(ac.get("fg")))])
    S.rule(".c-filter__more", [("display", "inline-flex")])
    S.rule(".c-filter__sel", [("display", "none")])
    # the "/" hint is a keyboard affordance: hidden where there is no keyboard
    # to speak of — a touch pointer, or a phone-width screen
    S.rule(".c-filter__search .c-kbd", [("display", "none")])
    S.rule(".c-filter__search .c-input", [("padding-inline-end", "var(--density-compact-pad-x)")])
    t = ctx.mq("tablet")
    if t:
        i = Sheet()
        i.rule(".c-filter__more", [("display", "none")])
        i.rule(".c-filter__sel", [("display", "contents")])
        S.media(t, i)
        k = Sheet()
        k.rule(".c-filter__search .c-kbd", [("display", "inline-flex")])
        k.rule(".c-filter__search .c-input", [("padding-inline-end", "var(--space-sp-5)")])
        S.media(f"{t} and {ctx.hover_q}", k)
    o.spec("rest", filter_html(ctx, active=0), f"{n.get('density')} · search {se.get('width_ch')}ch · '{se.get('shortcut')}' focuses it · state in the URL", wide=True)
    o.spec("active · focus", filter_html(ctx, active=2, focus=True), f"active count {bind(ac)} · Clear only when active", wide=True)


def filter_html(ctx, active=0, focus=False):
    n = ctx.comp("filter_bar") or {}
    se = n.get("search") or {}
    i = uid(ctx, "flt")
    f = ' data-force="focus"' if focus else ""
    search = (f'<label class="c-filter__search" for="{i}"><span class="c-sr">{esc(ctx.s("platform.top_bar.search", "Search"))}</span>'
              f'{ctx.icon(se.get("icon", "search"), se.get("icon_px", 16))}'
              f'<input class="c-input c-input--compact" id="{i}" type="search" autocomplete="{esc(se.get("autocomplete", "off"))}"{f}'
              f'{ctx.aria("platform.filter.search_placeholder", se.get("placeholder", ""), attr="placeholder", short="ph")}>{kbd_html(ctx, se.get("shortcut", "/"))}</label>')
    sels = []
    all_ = ctx.s("platform.filter.all", "All")
    for k, key in enumerate(("function", "flag", "stage")):
        j = uid(ctx, "fs")
        lab = ctx.s(f"platform.filter.{key}", key.capitalize())
        val = all_ if k >= active else ("Finance" if key == "function" else "Review")
        sels.append(f'<label class="c-select" for="{j}"><span class="c-sr">{esc(lab)}</span><select class="c-input c-input--compact" id="{j}">'
                    f'<option>{esc(lab)}: {esc(val)}</option></select>{ctx.icon("chevron-down", 16, "c-select__icon")}</label>')
    cnt = ""
    clear = ""
    if active:
        ct = ctx.s("platform.filter.active", "{n} active").format(n=active)
        cnt = f'<span class="c-filter__count">{esc(ct)}</span>'
        clear = btn(ctx, "tertiary", "Clear filters", "platform.filter.clear", cls="c-hit").replace('<span class="c-button__arrow">', '<span class="c-sr">')
    fl = ctx.s("platform.filter.filters", "Filters")
    more = btn(ctx, "secondary", f"{fl} ({active})" if active else fl, None, icon="list-filter", cls="c-filter__more c-hit")
    return f'<div class="c-filter" role="search">{search}{more}<span class="c-filter__sel">{"".join(sels)}</span>{cnt}{clear}</div>'


@comp("format", "Data")
def c_format(ctx, n, o):
    S = o.css
    S.rule(".c-spec", [("display", "grid"), ("grid-template-columns", "minmax(0, 12ch) minmax(0, 1fr)"), ("gap", "var(--space-sp-1) var(--space-sp-3)")])
    S.rule(".c-spec dt", ctx.type_decls("{type.eyebrow}") + [("font-size", "var(--density-dense-label)"), ("color", ctx.color("{color.muted}"))])
    S.rule(".c-spec dd", ctx.type_decls("{type.mono}") + [("font-variant-numeric", "tabular-nums"), ("overflow-wrap", "anywhere")])
    nb = " "
    rows = [("date", "11/10/2026"), ("export", "2026-10-11"), ("time", "14:32"), ("week", n.get("week", "W41")),
            ("thousands", f"1{nb}248"), ("score", n.get("score", "")), ("percent", f"{(n.get('percent') or {}).get('en', '')} · {(n.get('percent') or {}).get('fr', '')}"),
            ("currency", f"{(n.get('currency') or {}).get('en', '')} · {(n.get('currency') or {}).get('fr', '')}"), ("units", "20" + nb + "MB")]
    h = "<dl class=\"c-spec\">" + "".join(f"<dt>{esc(a)}</dt><dd>{esc(b)}</dd>" for a, b in rows) + "</dl>"
    o.spec("examples", h, n.get("implementation", "")[:90], wide=True)


@comp("truncation", "Data")
def c_trunc(ctx, n, o):
    S = o.css
    S.rule(".c-trunc", [("display", "block"), ("overflow", "hidden"), ("text-overflow", "ellipsis"), ("white-space", "nowrap"), ("max-inline-size", "28ch"),
                        ("padding-block", "calc((var(--target-min) - 1lh) / 2)")])
    S.rule(".c-tags", [("display", "flex"), ("gap", "var(--space-sp-1)"), ("flex-wrap", "wrap")])
    long = "Support deflection for the customer service centre in three regions"
    fn = "Use-Case-Portfolio-export-2026-10-11.xlsx"
    mid = fn[:14] + "…" + fn[-11:]
    h = (f'<dl class="c-spec"><dt>single line</dt><dd><span class="c-trunc" title="{esc(long)}" tabindex="0">{esc(long)}</span></dd>'
         f'<dt>file</dt><dd title="{esc(fn)}">{esc(mid)}</dd><dt>email</dt><dd>{esc("name@company.com")}</dd>'
         f'<dt>tags</dt><dd><span class="c-tags"><span class="c-badge">Finance</span><span class="c-badge">Legal</span><span class="c-badge">People</span>'
         f'<span class="c-badge">+8</span></span></dd></dl>')
    o.spec("examples", h, f"{n.get('single_line', '')[:60]} · files middle · tags {n.get('tags')}", wide=True)


# ── Platform ─────────────────────────────────────────────────────────────
@comp("focus", "Platform")
def c_focus(ctx, n, o):
    S = o.css
    S.rule(':focus-visible, [data-force~="focus"]', ctx.focus("ring"))
    S.rule('[data-surface="ink"] :focus-visible, [data-surface="ink"] [data-force~="focus"]', ctx.focus("on_dark"))
    S.rule('.c-on-accent :focus-visible, .c-on-accent [data-force~="focus"]', ctx.focus("on_accent"))
    S.rule(":focus:not(:focus-visible)", [("outline", "none")])
    S.rule("html", [("scroll-padding-block-start", px(((ctx.comp("header") or {}).get("height") or {}).get("desktop", 64)) if ctx.comp("header") else None)])
    S.rule(".c-on-accent", [("background-color", ctx.color("{color.accent}")), ("color", ctx.color("{color.accent_on}")), ("padding", "var(--space-sp-3)")])
    o.spec("ring", btn(ctx, "secondary", "See the catalogue", "cta.catalogue", attrs=' data-force="focus"'), bind({"ring": n.get("ring")}))
    o.spec("on dark", btn(ctx, "secondary_on_dark", "See the catalogue", "cta.catalogue", attrs=' data-force="focus"'), bind({"on_dark": n.get("on_dark")}), ink=True)
    o.spec("on accent", f'<div class="c-on-accent"><a class="c-link c-link--standalone" style="color: inherit" href="#" data-force="focus">{esc(ctx.s("cta.primary", ""))}</a></div>',
           bind({"on_accent": n.get("on_accent")}))
    o.spec("inset (rows)", f'<a class="c-row c-hit" href="#" data-force="focus">Invoice extraction</a>', f"inset_offset {n.get('inset_offset')}px")


@comp("kbd", "Platform")
def c_kbd(ctx, n, o):
    S = o.css
    S.rule(".c-kbd", ctx.type_decls(n.get("type")) + [("font-size", px(n["size"])) if n.get("size") else None,
                                                    ("display", "inline-flex"), ("align-items", "center"), ("justify-content", "center"),
                                                    ("min-inline-size", "2.2ch"), ("padding-inline", px(n.get("pad_x", 6))),
                                                    ("border-radius", ctx.length(n.get("radius"))), ("line-height", "1.6")] +
           ctx.paint({k: n[k] for k in ("bg", "fg", "border") if k in n}))
    S.rule('[data-surface="ink"] .c-kbd', ctx.paint(n.get("on_dark") or {}, True))
    S.rule(".c-keys", [("display", "inline-flex"), ("gap", "var(--space-sp-1)")])
    o.spec("rest", f'<span class="c-keys">{kbd_html(ctx, "⌘")}{kbd_html(ctx, "K")}</span> <span class="c-keys">{kbd_html(ctx, "Ctrl")}{kbd_html(ctx, "K")}</span>',
           bind(n, ("bg", "fg", "border")) + f" · {n.get('platform_symbols', '')[:40]}")
    o.spec("on dark", f'<span class="c-keys">{kbd_html(ctx, "Ctrl")}{kbd_html(ctx, "K")}</span>', bind(n.get("on_dark")), ink=True)


def kbd_html(ctx, k):
    return f'<kbd class="c-kbd">{esc(k)}</kbd>' if ctx.comp("kbd") else f"<kbd>{esc(k)}</kbd>"


@comp("top_bar", "Platform")
def c_topbar(ctx, n, o):
    S = o.css
    S.rule(".c-topbar", [("display", "flex"), ("align-items", "center"), ("gap", "var(--space-sp-2)"), ("min-block-size", px(n.get("height", 56))),
                         ("padding-inline", "var(--space-sp-3)")] + ctx.paint({"bg": n.get("bg"), "fg": n.get("fg")}, True))
    S.rule(".c-topbar__title", ctx.type_decls("{type.heading_sm}") + [("overflow", "hidden"), ("text-overflow", "ellipsis"), ("white-space", "nowrap"),
                                                                    ("min-inline-size", "0")])
    S.rule(".c-topbar__spacer", [("flex", "1")])
    S.rule(".c-topbar .c-crumbs, .c-topbar__toggle, .c-topbar__search", [("display", "none")])
    S.rule(".c-topbar__search .c-button__label", [("margin-inline-end", "var(--space-sp-3)")])
    S.rule(".c-topbar .c-button", [("min-block-size", "var(--target-min)"), ("padding-inline", "var(--space-sp-3)")])
    S.rule(".c-count", ctx.type_decls(((ctx.comp("task_tray") or {}).get("trigger") or {}).get("count", {}).get("type")) +
           ctx.paint({k: v for k, v in (((ctx.comp("task_tray") or {}).get("trigger") or {}).get("count") or {}).items() if k in ("bg", "fg", "radius")}, True) +
           [("font-size", "var(--density-dense-label)"), ("letter-spacing", "0"), ("padding-inline", "var(--space-sp-1)"),
            ("min-inline-size", "var(--space-sp-3)"), ("text-align", "center"), ("margin-inline-start", "calc(-1 * var(--space-sp-2))"),
            ("align-self", "flex-start"), ("margin-block-start", "var(--space-sp-1)")])
    S.rule(".c-topbar .c-iconbtn", [("color", "inherit")])
    S.rule(".c-topbar__phone", [("display", "contents")])
    t, d = ctx.mq("tablet"), ctx.mq("desktop")
    if t:
        i = Sheet()
        i.rule(".c-topbar .c-crumbs, .c-topbar__search", [("display", "block")])
        i.rule(".c-topbar__search", [("display", "inline-flex")])
        i.rule(".c-topbar__phone", [("display", "none")])
        S.media(t, i)
    if d:
        i = Sheet()
        i.rule(".c-topbar__toggle", [("display", "inline-flex")])
        S.media(d, i)
    o.spec("rest · search hover", topbar_html(ctx, force_search="hover"), f"Ink {n.get('height')}px · {n.get('layout', '')[:70]}", wide=True, frame="bare")
    o.notes.append(n.get("phone", ""))


def topbar_html(ctx, crumbs=None, title="Use cases", force_search=None):
    n = ctx.comp("top_bar") or {}
    st = n.get("search_trigger") or {}
    sh, sa = ctx.tx("platform.top_bar.search", "Search")
    f = f' data-force="{force_search}"' if force_search else ""
    search = (f'<button class="c-button c-button--secondary_on_dark c-topbar__search" type="button"{f}>{ctx.icon("search", 16)}'
              f'<span class="c-button__label"{sa}>{sh}</span><span class="c-keys">{kbd_html(ctx, "Ctrl")}{kbd_html(ctx, "K")}</span></button>')
    crumbs = crumbs or [("platform.nav.dashboard", "Dashboard"), ("platform.nav.use_cases", "Use cases")]
    tasks = (f'<button class="c-iconbtn" type="button"{ctx.aria("platform.top_bar.tasks", "Tasks")}>{ctx.icon("bell", 20)}</button>'
             f'<span class="c-count" aria-hidden="true">1</span>') if ctx.comp("task_tray") else ""
    return (f'<header class="c-topbar" data-surface="ink"><button class="c-iconbtn c-topbar__toggle" type="button"'
            f'{ctx.aria("platform.nav.collapse", "Collapse sidebar")}>{ctx.icon("panel-left", 20)}</button>'
            f'<span class="c-topbar__phone">{mark_svg(ctx, 32)}<span class="c-topbar__title">{esc(title)}</span></span>'
            f'{crumbs_html(ctx, crumbs) if ctx.comp("breadcrumbs") else ""}<span class="c-topbar__spacer"></span>'
            f'{search}{tasks}{avatar_html(ctx)}</header>')


def user_name(ctx):
    """The signed-in person the platform screens show: patterns.dashboard.user
    when the config names one, else the brand owner."""
    u = (((ctx.cfg.get("patterns") or {}).get("dashboard") or {}).get("user") or {})
    return (u.get("name") if isinstance(u, dict) else None) or (ctx.cfg.get("owner") or {}).get("name", "")


def avatar_html(ctx, force=None):
    n = ctx.comp("user_menu") or {}
    if not n:
        return ""
    name = user_name(ctx)
    parts = name.split()
    # first letter of the first and last name; one if one name (user_menu.avatar.initials)
    ini = (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper() if parts else ""
    f = f' data-force="{force}"' if force else ""
    return (f'<button class="c-user" type="button" aria-haspopup="menu"{f}{ctx.aria("platform.top_bar.account", "Account menu")}>'
            f'<span class="c-avatar" aria-hidden="true">{esc(ini)}</span></button>')


@comp("user_menu", "Platform")
def c_user(ctx, n, o):
    S = o.css
    av = n.get("avatar") or {}
    S.rule(".c-user", [("display", "inline-flex"), ("align-items", "center"), ("justify-content", "center"),
                       ("min-inline-size", px((n.get("trigger") or {}).get("target", 44))), ("min-block-size", px((n.get("trigger") or {}).get("target", 44))),
                       ("border-radius", "var(--radius-control)")])
    S.rule(".c-avatar", ctx.type_decls(av.get("type")) + [("display", "inline-flex"), ("align-items", "center"), ("justify-content", "center"),
                                                        ("inline-size", px(av.get("size", 32))), ("block-size", px(av.get("size", 32))),
                                                        ("letter-spacing", "0.04em"), ("border-radius", ctx.length(av.get("radius")))] +
           ctx.paint({k: av[k] for k in ("bg", "fg") if k in av}, True))
    S.rule(".c-menu__head", [("display", "grid"), ("gap", "var(--space-sp-1)"), ("padding", "var(--space-sp-2) var(--space-sp-3)"),
                             ("border-block-end", ctx.border({"width": 1, "style": "solid", "color": "{color.border}"}))])
    S.rule(".c-menu__email", ctx.type_decls("{type.mono}") + [("color", ctx.color("{color.muted}")), ("font-size", "var(--density-compact-label)")])
    name = user_name(ctx)
    head = f'<div class="c-menu__head"><p>{esc(name)}</p><p class="c-menu__email">name@company.com</p></div>'
    o.spec("trigger · focus", avatar_html(ctx, "focus"), f"avatar {av.get('size')}px square · {bind(av, ('bg', 'fg'))}", ink=True)
    o.spec("open", menu_html(ctx, head) if ctx.comp("menu") else "", "base component.menu · email middle-truncated at 28ch")


@comp("task_tray", "Platform")
def c_tasks(ctx, n, o):
    S = o.css
    rw = n.get("row") or {}
    S.rule(".c-task__done", [("display", "flex"), ("align-items", "center"), ("gap", "var(--space-sp-1)")])
    st = (rw.get("status") or {})
    s = st.get("format", "")
    h = (f'<div class="c-pop" role="dialog" aria-label="{esc(ctx.s("platform.tasks.title", "Tasks"))}">{ctx.el("p", "platform.tasks.title", "", "c-pop__title")}'
         f'<div class="c-task"><p>{esc(ctx.s("platform.loading.scoring", "Scoring…"))}</p><p class="c-task__status">{esc(s)}</p></div>'
         f'<div class="c-task"><p class="c-task__done">{ctx.icon("check", 16)}{ctx.el("span", "platform.tasks.done", "")}</p>'
         f'<a class="c-link c-link--standalone" href="#">{ctx.el("span", "platform.tasks.open_result", "")}</a></div></div>')
    o.spec("open · running · done", h, f"panel = popover · count {bind((n.get('trigger') or {}).get('count'))} · {rw.get('progress', '')}")


@comp("bottom_bar", "Platform")
def c_bottom(ctx, n, o):
    S = o.css
    it = n.get("item") or {}
    S.rule(".c-bottombar", [("display", "flex"), ("min-block-size", px(n.get("height", 56))), ("padding-block-end", "env(safe-area-inset-bottom)")] +
           ctx.paint({"bg": n.get("bg")}, True))
    S.rule(".c-bottombar__item", [("flex", "1"), ("display", "flex"), ("flex-direction", "column"), ("align-items", "center"), ("justify-content", "center"),
                                  ("gap", "var(--space-sp-1)"), ("min-block-size", px(it.get("target", 44))), ("min-inline-size", px(it.get("target", 44))),
                                  ("text-decoration-line", "none"), ("color", ctx.color(it.get("rest"), True)),
                                  (f"border-{it.get('edge_side', 'block-start')}", ctx.border({**((it.get("current") or {}).get("edge") or {"width": 2, "style": "solid"}), "color": "transparent"}))] +
           ctx.type_decls((it.get("label") or {}).get("type")) + [("font-size", px((it.get("label") or {}).get("size", 11))), ("letter-spacing", "0.04em")])
    S.rule('.c-bottombar__item[aria-current="page"]', ctx.paint(it.get("current") or {}, True, edge=it.get("edge_side", "block-start")))
    S.rule('.c-bottombar__item:focus-visible, .c-bottombar__item[data-force~="focus"]', [("outline-offset", "-2px")])
    items = []
    for k, (key, ic) in enumerate(SCREENS[:n.get("items_max", 5) - 1] + [("more", "ellipsis")]):
        h, a = ctx.tx(f"platform.nav.{key}", key)
        cur = ' aria-current="page"' if k == 1 else ""
        items.append(f'<a class="c-bottombar__item" href="#"{cur}>{ctx.icon(ic, it.get("icon_px", 20))}<span{a}>{h}</span></a>')
    o.spec("rest · current", f'<nav class="c-bottombar" data-surface="ink"{ctx.aria("nav.main_nav", "Main")}>{"".join(items)}</nav>',
           f"<600px · {n.get('items_max')} items · rest {bind({'r': it.get('rest')})[2:]} · current {bind(it.get('current'))}", wide=True, frame="bare")


@comp("shadcn", "Platform")
def c_shadcn(ctx, n, o):
    S = o.css
    S.rule(".c-swatch", [("display", "inline-block"), ("inline-size", "var(--space-sp-4)"), ("block-size", "var(--space-sp-4)"),
                         ("border", ctx.border({"width": 1, "style": "solid", "color": "{color.border}"})), ("vertical-align", "middle"),
                         ("margin-inline-end", "var(--space-sp-2)")])
    mp = n.get("map") or {}
    rows = []
    for k, v in mp.items():
        if k.startswith("$"):
            continue
        val = ctx.color(v) if str(v).startswith("{color") else None
        sw = f'<span class="c-swatch" style="background-color: {val}"></span>' if val else ""
        rows.append(f"<dt>--{esc(k)}</dt><dd>{sw}{esc(str(v).strip('{}'))}</dd>")
    o.spec("map", f'<dl class="c-spec c-spec--wide">{"".join(rows)}</dl>', "shadcn 'accent' = color.state.selected, never the brand accent", wide=True)


@comp("focus_route", "Platform")
def c_focus_route(ctx, n, o):
    tp = n.get("title_pattern") or {}
    rows = [("navigate", n.get("on_navigate", "")), ("back", n.get("on_back", "")),
            ("title · site", tp.get("site", "")), ("title · platform", tp.get("platform", ""))]
    h = '<dl class="c-spec">' + "".join(f"<dt>{esc(a)}</dt><dd>{esc(b)}</dd>" for a, b in rows) + "</dl>"
    o.spec("rule", h, "behaviour, no visual: rendered as its rule", wide=True)


# ── fixture ──────────────────────────────────────────────────────────────
def fixture_css(ctx):
    S = Sheet()
    S.rule(".fx-top", [("border-block-end", ctx.border({"width": 1.6, "style": "solid", "color": "{color.fg}"})), ("padding-block", "var(--space-sp-5) var(--space-sp-4)")])
    S.rule(".fx-top h1", ctx.type_decls("{type.display_lg}"))
    S.rule(".fx-top p", ctx.type_decls("{type.body}") + [("max-inline-size", "75ch"), ("margin-block-start", "var(--space-sp-3)")])
    S.rule(".fx-tools", [("display", "flex"), ("flex-wrap", "wrap"), ("gap", "var(--space-sp-2)"), ("margin-block-start", "var(--space-sp-4)")])
    S.rule(".fx-tools button", [("min-block-size", "var(--target-min)"), ("min-inline-size", "var(--target-min)"), ("padding-inline", "var(--space-sp-3)"),
                                ("border", ctx.border({"width": 1, "style": "solid", "color": "{color.fg}"})), ("border-radius", "var(--radius-control)")]
           + ctx.type_decls("{type.eyebrow}"))
    S.rule('.fx-tools button[aria-pressed="true"]', [("background-color", ctx.color("{color.fg}")), ("color", ctx.color("{color.bg}"))])
    S.rule(".fx-toc", [("display", "flex"), ("flex-wrap", "wrap"), ("column-gap", "var(--space-sp-3)"), ("margin-block-start", "var(--space-sp-3)")])
    S.rule(".fx-toc a", ctx.type_decls("{type.eyebrow}") + [("display", "inline-flex"), ("align-items", "center"), ("min-block-size", "var(--target-min)"),
                                                         ("min-inline-size", "var(--target-min)"),
                                                         ("color", ctx.color("{color.accent}"))])
    S.rule(".fx-group", [("padding-block", "var(--space-sp-6) 0")])
    S.rule(".fx-group__title", ctx.type_decls("{type.display_md}") + [("padding-block-start", "var(--space-sp-3)"),
                                                                     ("border-block-start", ctx.border({"width": 1.6, "style": "solid", "color": "{color.fg}"}))])
    S.rule(".fx-comp", [("padding-block", "var(--space-sp-5) var(--space-sp-3)"), ("border-block-end", ctx.border({"width": 1, "style": "solid", "color": "{color.border}"}))])
    S.rule(".fx-comp__head", [("display", "grid"), ("gap", "var(--space-sp-1)"), ("margin-block-end", "var(--space-sp-4)")])
    S.rule(".fx-comp__name", ctx.type_decls("{type.heading_md}"))
    S.rule(".fx-meta, .fx-eyebrow, .fx-cap", ctx.type_decls("{type.eyebrow}") + [("font-size", "var(--density-dense-label)"), ("letter-spacing", "0.06em"),
                                                                               ("text-transform", "none"), ("color", ctx.color("{color.muted}"))])
    S.rule(".fx-eyebrow", [("text-transform", "uppercase"), ("letter-spacing", "0.14em"), ("margin-block-end", "var(--space-sp-2)")])
    S.rule(".fx-note", ctx.type_decls("{type.caption}") + [("color", ctx.color("{color.muted}")), ("max-inline-size", "75ch")])
    S.rule(".fx-grid", [("display", "grid"), ("gap", "var(--space-sp-4) var(--space-sp-4)"), ("grid-template-columns", "minmax(0, 1fr)")])
    S.rule(".fx-spec", [("display", "grid"), ("gap", "var(--space-sp-2)"), ("align-content", "start"), ("min-inline-size", "0")])
    S.rule(".fx-stage", [("padding", "var(--space-sp-3)"), ("border", ctx.border({"width": 1, "style": "dashed", "color": "{color.border}"})),
                         ("min-inline-size", "0"), ("overflow-x", "auto")])
    S.rule(".fx-stage--bare", [("padding", "0"), ("border-style", "solid")])
    S.rule(".fx-cap", [("display", "grid"), ("gap", "var(--space-sp-1)")])
    S.rule(".fx-state", [("color", ctx.color("{color.fg}")), ("text-transform", "uppercase"), ("letter-spacing", "0.14em")])
    S.rule(".fx-prose, .fx-small", ctx.type_decls("{type.body}"))
    S.rule(".fx-small", ctx.type_decls("{type.caption}"))
    S.rule(".fx-h3", ctx.type_decls("{type.heading_md}"))
    S.rule(".fx-wrap", [("display", "flex"), ("flex-wrap", "wrap"), ("gap", "var(--space-sp-2)")])
    S.rule(".fx-badges + .fx-badges", [("margin-block-start", "var(--space-sp-3)")])
    S.rule(".fx-skipstage", [("position", "relative"), ("min-block-size", "calc(var(--target-min) + 2 * var(--space-sp-3))")])
    S.rule(".fx-oframe", [("position", "relative"), ("display", "flex"), ("justify-content", "center"), ("align-items", "center"),
                          ("min-block-size", "calc(var(--space-sp-8) * 2.5)"), ("padding", "var(--space-sp-4)"), ("overflow", "hidden")])
    S.rule(".fx-oframe > :not(.c-scrim)", [("position", "relative"), ("z-index", "1")])
    S.rule(".fx-oframe--end", [("justify-content", "flex-end"), ("align-items", "stretch"), ("padding", "0")])
    S.rule(".fx-oframe--tall", [("min-block-size", "calc(var(--space-sp-8) * 4)")])
    S.rule(".fx-oframe--top", [("align-items", "flex-start")])
    S.rule(".c-spec--wide", [("grid-template-columns", "minmax(0, 22ch) minmax(0, 1fr)")])
    S.rule(".fx-gaps", [("display", "grid"), ("gap", "var(--space-sp-1)")])
    t, d = ctx.mq("tablet"), ctx.mq("desktop")
    if t:
        i = Sheet()
        i.rule(".fx-grid", [("grid-template-columns", "repeat(2, minmax(0, 1fr))")])
        i.rule(".fx-spec--wide", [("grid-column", "1 / -1")])
        S.media(t, i)
    if d:
        i = Sheet()
        i.rule(".fx-grid", [("grid-template-columns", "repeat(3, minmax(0, 1fr))")])
        S.media(d, i)
    return S


def section_html(ctx, name, group, o, src, pid):
    specs = []
    for state, html_, b, wide, ink, frm in o.specs:
        sur = ' data-surface="ink"' if ink else ""
        cls = "fx-stage" + (" fx-stage--bare" if frm == "bare" else "")
        w = " fx-spec--wide" if wide else ""
        specs.append(f'<figure class="fx-spec{w}"><div class="{cls}"{sur}>{html_}</div>'
                     f'<figcaption class="fx-cap"><span class="fx-state">{esc(state)}</span>'
                     f'{"<span>" + esc(b) + "</span>" if b else ""}</figcaption></figure>')
    notes = "".join(f'<p class="fx-note">{esc(x)}</p>' for x in o.notes if x)
    meta = f"{group} · $src {src or '–'}" + (f" · {', '.join(pid)}" if pid else "")
    return (f'<section class="fx-comp" id="c-{name}" data-component="{name}"><header class="fx-comp__head">'
            f'<h3 class="fx-comp__name">{esc(name)}</h3><p class="fx-meta">{esc(meta)}</p>{notes}</header>'
            f'<div class="fx-grid">{"".join(specs)}</div></section>')


def config_refs(ctx, node, depth=0):
    """Every token a config node references, following {component.x} once."""
    out = set()
    if isinstance(node, dict):
        for k, v in node.items():
            if not k.startswith("$"):
                out |= config_refs(ctx, v, depth)
    elif isinstance(node, list):
        for v in node:
            out |= config_refs(ctx, v, depth)
    elif isinstance(node, str):
        m = REF.match(node.strip())
        if m:
            name = m.group(1)
            if name.startswith("component.") and depth == 0:
                out |= config_refs(ctx, ctx.comp(name.split(".", 1)[1]), 1)
            elif name in ctx.tokens:
                out.add(name)
    return out


# ── 3.4 proposal linkage ─────────────────────────────────────────────────
REPOS = [("vercel", "vercel"), ("emil", "emil"), ("refero", "refero"), ("impeccable", "impeccable"),
         ("lucide", "lucide"), ("motion-primitives", "mp"), ("ibelick", "mp")]


def _refs(s):
    out = set()
    for part in str(s).split(";"):
        repo = next((v for k, v in REPOS if k in part), None)
        for m in re.finditer(r"([\w.-]+\.(?:md|tsx|svg)):([\d,\-]+)", part):
            for seg in m.group(2).split(","):
                if not seg:
                    continue
                a, _, b = seg.partition("-")
                for k in range(int(a), int(b or a) + 1):
                    out.add((repo, m.group(1), k))
        for m in re.finditer(r"\bp(\d+)(?:-(\d+))?((?:,p?\d+)*)", part):
            nums = list(range(int(m.group(1)), int(m.group(2) or m.group(1)) + 1))
            nums += [int(x.lstrip("p")) for x in m.group(3).split(",") if x]
            out |= {("S2", n) for n in nums}
        out |= {("S1", m.group(1)) for m in re.finditer(r"S1:([\w.]+)", part)}
    return out


def _texts(node, acc):
    if isinstance(node, dict):
        for k, v in node.items():
            if k.startswith("$src") and isinstance(v, str):
                acc.append(v)
            elif k in ("$comment", "$note") and isinstance(v, str):
                acc.append(v)
            elif not k.startswith("$"):
                _texts(v, acc)
    elif isinstance(node, list):
        for v in node:
            _texts(v, acc)
    return acc


_DOC = {}


def doc_links(cfg):
    """component → [P-id] from the proposals document the config names
    (proposals_3_4.doc), when it sits beside the config or in source/.
    Each row reads `| P-XXX-NN | **Title**: …`; the title is split on + , and /
    and each part names one component (the best word match, earliest first);
    'a `kbd` component' in the text names one too."""
    pp = cfg.get("proposals_3_4") or {}
    doc = pp.get("doc")
    key = (doc, tuple(sorted(cfg.get("components") or {})))
    if key in _DOC:
        return _DOC[key]
    out = {}
    path = next((b / doc for b in (ROOT, ROOT / "source") if doc and (b / doc).is_file()), None)
    if path:
        ids = set(pp.get("ids") or {})
        names = [k for k in (cfg.get("components") or {}) if not k.startswith("$")]
        words = lambda s: re.findall(r"[a-z0-9]+", s.lower())  # noqa: E731
        hit = lambda cw, ws: all(any(w == x or (len(x) >= 4 and w.startswith(x)) for w in ws) for x in cw)  # noqa: E731
        for pid, desc in re.findall(r"^\|\s*(P-[A-Z]{3}-\d{2})\s*\|\s*(.*?)\s*\|", path.read_text(encoding="utf-8"), re.M):
            if pid not in ids:
                continue
            m = re.match(r"\*\*(.+?)\*\*", desc)
            found = set()
            if m:
                title = m.group(1)
                for seg in re.split(r"\s*(?:\+|,|/|\band\b)\s*", title):
                    ws = words(seg)
                    c = []
                    for n in names:
                        cw = n.split("_")
                        if ws and hit(cw, ws):
                            pos = min(k for k, w in enumerate(ws) for x in cw if w == x or (len(x) >= 4 and w.startswith(x)))
                            c.append((len(cw), -pos, n))
                    if c:
                        found.add(max(c)[2])
                tw = words(title)
                found |= {n for n in names if "_" in n and hit(n.split("_"), tw)}
            found |= {x for x in re.findall(r"\ba `(\w+)` component", desc) if x in names}
            for n in found:
                out.setdefault(n, []).append(pid)
    _DOC[key] = out
    return out


def proposal_ids(cfg, name, node):
    """The 3.4 proposal a component came from. An explicit `$pid` on the
    node wins. Otherwise the component's own citations ($src*, and page or
    file:line references in $comment/$note) are matched against
    proposals_3_4.ids; a UNIQUE best match is taken, a tie is reported as
    candidates. Only a component the 3.4 round touched (a NEW/AMENDMENT
    comment, or an S6 citation) is matched at all."""
    ids = ((cfg.get("proposals_3_4") or {}).get("ids")) or {}
    if not ids or not isinstance(node, dict):
        return [], [], "none"
    if node.get("$pid"):
        v = node["$pid"]
        v = v if isinstance(v, list) else [v]
        return [x for x in v if x in ids], [], "explicit $pid"
    linked = doc_links(cfg).get(name)
    if linked:
        return sorted(set(linked)), [], f"proposals doc ({(cfg.get('proposals_3_4') or {}).get('doc')})"
    texts = _texts(node, [])
    touched = any(re.match(r"\s*(NEW|AMENDMENT)", t) for t in texts if not t.startswith("S")) or \
        any("S6" in t for t in texts)
    if not touched:
        return [], [], "3.3 (not from the 3.4 round)"
    refs = set().union(*[_refs(t) for t in texts]) if texts else set()
    score = {k: len(refs & _refs(v)) for k, v in ids.items()}
    best = max(score.values()) if score else 0
    top = sorted(k for k, v in score.items() if v == best and best)
    if len(top) == 1:
        return top, [], "citation match"
    return [], top, ("ambiguous citation match" if top else "unlinked — add $pid")


# ── main ─────────────────────────────────────────────────────────────────
def build(ctx):
    _LANG["ctx"] = ctx
    S = Sheet()
    S.extend(base_css(ctx))
    groups = {g: [] for g in GROUPS}
    manifest = []
    unrendered = []
    names = [k for k in ctx.comps]
    # render order: by group, then config order
    for g in GROUPS:
        for name in names:
            grp, fn = R.get(name, ("Platform", None))
            if grp != g:
                continue
            node = ctx.comps[name]
            o = Out(ctx, name)
            ctx.used = set()
            before = len(ctx.problems)
            if fn is None:
                o.spec("slots", f'<p class="fx-note">No renderer for this component. Its slots: {esc(bind(node) or "none")}</p>', "")
                unrendered.append({"component": name, "why": "no renderer in components.py for this component"})
            elif not isinstance(node, dict):
                o.spec("value", f'<p class="fx-note">{esc(str(node))}</p>', "")
                unrendered.append({"component": name, "why": "the config node is not an object"})
            else:
                fn(ctx, node, o)
            probs = ctx.problems[before:]
            S.raw(f"/* ── {name} ({g}) */")
            S.extend(o.css)
            src = (node.get("$src") if isinstance(node, dict) else None) or (ctx.cfg.get("components") or {}).get("$src")
            pid, cand, basis = proposal_ids(ctx.cfg, name, node)
            classes = sorted(set(re.findall(r"\.(c-[a-z0-9_-]+)", o.css.css())))
            ctx.used |= config_refs(ctx, node)
            states = list(dict.fromkeys(s for s in o.states))
            if any("NOT RENDERED" in x for x in o.notes):
                unrendered.append({"component": name, "why": next(x for x in o.notes if "NOT RENDERED" in x)})
            for p in probs:
                unrendered.append({"component": name, "why": f"slot did not resolve: {p}"})
            manifest.append({"name": name, "group": g, "states": [s for s in STATE_ORDER if s in states] +
                             [s for s in states if s not in STATE_ORDER],
                             "classes": classes, "tokens": sorted(ctx.used), "source": src,
                             "p_ids": pid, "p_id_candidates": cand, "p_id_basis": basis,
                             "pointer": f"/components/{name}",
                             **({"gaps": [x for x in o.notes if str(x).startswith("GAP")]} if any(str(x).startswith("GAP") for x in o.notes) else {})})
            groups[g].append(section_html(ctx, name, g, o, src, pid))
    if ctx.icon_missing:
        unrendered.append({"component": "(icons)", "why": "icon not found: " + ", ".join(sorted(ctx.icon_missing))})
    return S, groups, manifest, unrendered


def main():
    try:
        ctx = Ctx.load()
    except ConfigError as e:
        sys.exit(f"config gate failed:\n  {e}")
    if not (OUT / "tokens" / "tokens.css").exists():
        sys.exit("out/tokens/tokens.css is missing — run build/tokens_css.py first")
    S, groups, manifest, unrendered = build(ctx)
    css = (f"/* {ctx.cfg.get('brand')} {ctx.cfg.get('version')} — components.css. Generated by build/components.py from\n"
           f"   brand.config.json. Every value is a token from tokens/tokens.css. Do not edit. */\n\n" + S.css())
    write(OUT / "components.css", css)
    # copy the logo files the components reference
    files = ((ctx.cfg.get("logo") or {}).get("files") or {})
    for k in live(files):
        p = (files[k] or {}).get("path") if isinstance(files[k], dict) else None
        if p and (ROOT / p).is_file():
            dst = OUT / "assets" / "logos" / pathlib_name(p)
            dst.parent.mkdir(parents=True, exist_ok=True)
            data = (ROOT / p).read_bytes()
            if not dst.exists() or dst.read_bytes() != data:
                dst.write_bytes(data)
    fx = fixture_css(ctx)
    toc = "".join(f'<a href="#g-{g.lower()}">{g}</a>' for g in GROUPS if groups[g])
    body_groups = "".join(f'<section class="fx-group" id="g-{g.lower()}"><h2 class="fx-group__title">{g}</h2>{"".join(groups[g])}</section>'
                          for g in GROUPS if groups[g])
    if not manifest:
        body_groups = '<p class="fx-note" style="margin-block: var(--space-sp-5)">This config has no components block: nothing to render.</p>'
    locs = [l for l in ((ctx.cfg.get("locales") or {}).get("list") or []) if l in ctx.copy]
    tools = "".join(f'<button type="button" data-lang-btn="{l}" aria-pressed="{str(k == 0).lower()}">{l.upper()}</button>' for k, l in enumerate(locs))
    tools += '<button type="button" data-dir-btn aria-pressed="false">RTL</button>'
    req = ((ctx.cfg.get("logo") or {}).get("required_css") or {}).get("value", "")
    head = f"<style>\n{fx.css()}{req}\n</style>\n"
    body = (f'{mark_symbol(ctx)}<main id="main" class="p-container"><header class="fx-top"><p class="fx-eyebrow">{esc(ctx.cfg.get("brand", ""))} {esc(ctx.cfg.get("version", ""))} · interface</p>'
            f'<h1>{accent_html("Every component, every state")}</h1>'
            f'<p>Generated from brand.config.json by build/components.py. Forced states use data-force and the same rules as the real '
            f'pseudo-classes. Each caption names the state and the tokens it binds. Copy slots and image frames mark what the config does not hold.</p>'
            f'<div class="fx-tools">{tools}</div><nav class="fx-toc" aria-label="Groups">{toc}</nav></header>{body_groups}</main>')
    htmlp = OUT / "components.html"
    doc = page(f"{ctx.cfg.get('brand', '')} — components", body,
               ["fonts-embedded.css", "tokens/tokens.css", "components.css"], extra_head=head, script=TOGGLE_JS)
    doc = doc.replace("{ASSETS}", "assets/")
    write(htmlp, doc)
    man = {"brand": ctx.cfg.get("brand"), "version": ctx.cfg.get("version"), "generator": "build/components.py",
           "count": len(manifest), "groups": GROUPS, "components": manifest, "not_rendered": unrendered,
           "unresolved": sorted(set(ctx.problems))}
    write(OUT / "components.manifest.json", json.dumps(man, indent=1, ensure_ascii=False) + "\n")
    print(f"  {len(manifest)} components · {sum(len(m['states']) for m in manifest)} states · "
          f"{len(set(c for m in manifest for c in m['classes']))} classes · {len(unrendered)} not fully rendered")

    # gates
    outs = [OUT / "components.css", htmlp]
    fails = []
    lit = literal_gate(outs)
    print(f"  literal gate · {len(lit)} literal value(s)")
    fails += lit
    vg = vars_gate(outs)
    print(f"  var gate · {len(vg)} undefined var()")
    fails += vg
    bad, out = check_gate(outs)
    print("  check.py · " + ("FAILED" if bad else "clean"))
    if bad:
        fails.append("check.py:\n" + out)
    if not fails:
        ok, rout = render_gate([(htmlp.resolve(), "components")], ctx.cfg)
        print("  " + rout.replace("\n", "\n  "))
        if not ok:
            fails.append("render gate failed")
    if fails:
        print("FAILED\n  " + "\n  ".join(fails[:40]))
        sys.exit(1)
    print(f"out/components.css + components.html + components.manifest.json written · gates clean")


if __name__ == "__main__":
    main()
