#!/usr/bin/env python3
"""Tailwind v4 CSS-first theme → out/tokens/tailwind-v4.css, bound to tokens.css.

    python3 build/tailwind.py

The site imports tokens.css first, then this file. Nothing here is a literal
value except what Tailwind cannot read from a variable: the base spacing unit
and the breakpoints (media queries cannot use var()).

The naming problem, and how it is solved
----------------------------------------
tokens.css names a colour --color-accent. Tailwind's theme namespace for
colours is also --color-*, so `--color-accent: var(--color-accent)` would be
circular, and Tailwind writes a used theme variable into :root, replacing the
real one with a loop. Binding to --palette-* would avoid that but would also
freeze the roles: tokens.css remaps --color-bg / --color-fg on a dark surface
([data-surface=ink]) and --font-text under :lang(ar), and a utility bound to
the palette would ignore the remap.

So the theme binds to a thin alias layer defined here:

    :root, [data-surface], [data-theme], :lang(ar), [dir=rtl] {
      --bind-color-accent: var(--color-accent);   /* re-resolved in every scope */
    }
    @theme inline { --color-accent: var(--bind-color-accent); }

`inline` makes a utility read `var(--bind-color-accent)` instead of a copy of
the value, and the alias is re-declared in each scope that remaps, so
`bg-bg` inside [data-surface=ink] is Ink. Names that already differ
(--font-sans ← --font-text, --text-h1 ← --type-h1-size, --spacing-sp-1 ←
--space-sp-1) bind directly.

Import tokens.css unlayered (plain @import): Tailwind re-emits a theme variable
that any var() in the compiled CSS mentions, and the unlayered tokens.css
definition is what beats that re-emission.

Gate (exit 1): no `--x: var(--x)` and no longer cycle; every var() resolves
in this file or in tokens.css; no colour literal; every --color-* in the
theme is a var() or `initial`.
Standard library only.
"""
import pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from config import load, ConfigError  # noqa: E402
from tree import REF  # noqa: E402
from tokens_css import css_var  # noqa: E402

ROOT = HERE.parent
OUT = ROOT / "out" / "tokens"

# Scopes tokens.css remaps roles in. The alias layer is re-declared in each so
# that a utility follows the remap.
SCOPES = ":root, [data-surface], [data-theme], :lang(ar), [dir=rtl]"
DECL = re.compile(r"(--[\w-]+)\s*:\s*([^;{}]+);")


def decls(css):
    """[(name, value)] for every custom-property declaration, comments removed."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return [(m.group(1), m.group(2).strip()) for m in DECL.finditer(css)]


def num(v):
    """A config scalar that may be {value: n}."""
    return v.get("value") if isinstance(v, dict) else v


def root_decls(css):
    """Declarations of the top-level :root blocks (not inside @media, not a
    scope): the light-surface values a utility should start from."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"@media[^{]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", "", css)
    out = []
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        if m.group(1).strip() == ":root":
            out += [(d.group(1), d.group(2).strip()) for d in DECL.finditer(m.group(2))]
    return out


# shadcn names a component library reads that a brand map often omits. Each is
# derived from the brand's own roles, in this order of preference; the build
# lists what it derived so the config can state it (components.shadcn.map).
SHADCN_DERIVED = [
    ("card", ["{color.bg}"]),
    ("card-foreground", ["{color.fg}"]),
    ("popover", ["{color.bg}"]),
    ("popover-foreground", ["{color.fg}"]),
    ("destructive-foreground", ["@semantic.danger.on", "{color.bg}"]),
    ("sidebar", ["@nav.sidebar.bg", "{color.fg}"]),
    ("sidebar-foreground", ["@nav.sidebar.item_rest", "{color.bg}"]),
    ("sidebar-primary", ["{color.accent}"]),
    ("sidebar-primary-foreground", ["{color.accent_on}", "{color.bg}"]),
    ("sidebar-accent", ["{color.state.fg_hover}", "{color.fg}"]),
    ("sidebar-accent-foreground", ["@nav.sidebar.item_current.fg", "{color.bg}"]),
    ("sidebar-border", ["{color.state.fg_active}", "{color.border_strong}", "{color.fg}"]),
    ("sidebar-ring", ["{color.accent_on_dark}", "{color.accent}"]),
]


def derive_shadcn(cfg, sh, defined):
    """→ [(name, ref, absolute)] for the shadcn names the map lacks. Sidebar
    values are absolute (the palette layer): the sidebar is always Ink, even
    inside a scope that remaps the roles."""
    out = []
    for name, prefs in SHADCN_DERIVED:
        if name in sh:
            continue
        for p in prefs:
            ref = p
            if p.startswith("@"):
                node = cfg
                path = p[1:].split(".")
                node = (cfg.get("color") or {}) if path[0] == "semantic" else ((cfg.get("components") or {}))
                for part in path:
                    node = node.get(part) if isinstance(node, dict) else None
                if isinstance(node, str) and node in ("bg", "fg"):
                    node = "{color.%s}" % node
                ref = node if isinstance(node, str) and REF.match(node) else None
            if ref and f"var({css_var(REF.match(ref).group(1))})" and css_var(REF.match(ref).group(1)) in defined:
                out.append((name, ref, name.startswith("sidebar")))
                break
    return out


def build(cfg, tokens_css):
    defined = {}
    for n, v in root_decls(tokens_css):
        defined.setdefault(n, v)
    for n, v in decls(tokens_css):
        defined.setdefault(n, v)
    names = sorted(defined)
    policy = (cfg.get("effects") or {}).get("policy") or {}

    theme = ["  /* Reset Tailwind's defaults where the brand has its own set, so an",
             "     off-brand utility (bg-blue-500, rounded-xl) does not exist. */",
             "  --color-*: initial;",
             "  --font-*: initial;",
             "  --text-*: initial;",
             "  --radius-*: initial;",
             "  --ease-*: initial;",
             "  --animate-*: initial;",
             "  --breakpoint-*: initial;"]
    if policy.get("shadow") == "none":
        theme += ["  /* effects.policy.shadow = none */",
                  "  --shadow-*: initial;", "  --inset-shadow-*: initial;",
                  "  --drop-shadow-*: initial;", "  --text-shadow-*: initial;"]
    if policy.get("blur") == "none":
        theme += ["  /* effects.policy.blur = none */", "  --blur-*: initial;",
                  "  --backdrop-blur-*: initial;"]

    aliases = []  # (alias, source var)

    def alias(kind, name):
        a = f"--bind-{kind}-{name}"
        aliases.append((a, f"--{kind}-{name}"))
        return f"var({a})"

    # colour. A colour tokens.css defines as a var() of another name
    # (--color-bg: var(--palette-bg)) is mirrored verbatim in a plain @theme:
    # utilities then read var(--color-bg), so a remap in a scope is followed,
    # and the declaration Tailwind may emit into :root repeats tokens.css's own.
    # A colour tokens.css defines as a literal has no second name to bind to,
    # so it goes through the alias layer.
    colors = [n for n in names if n.startswith("--color-")]
    mirror = []
    theme.append("  /* colour: literal tokens.css colours, through the alias layer */")
    for n in colors:
        v = defined[n]
        m = re.fullmatch(r"var\((--[\w-]+)\)", v)
        if m and m.group(1) != n:
            mirror.append(f"  {n}: {v};")
        else:
            theme.append(f"  {n}: {alias('color', n[len('--color-'):])};")

    # shadcn colour names. Skipped where the brand already owns the name:
    # shadcn's `accent` (a hover tint) and `muted` (a surface) are not the
    # brand's, and `border` is the same colour either way.
    sh = dict(((cfg.get("components") or {}).get("shadcn") or {}).get("map") or {})
    derived = derive_shadcn(cfg, sh, defined) if sh else []
    for k, ref, _ in derived:
        sh[k] = ref
    skipped = []
    if sh:
        theme.append("  /* shadcn names, bound to the :root bridge below */")
    for k, v in sh.items():
        if k.startswith("$") or k == "radius":
            continue
        if f"--color-{k}" in defined:
            skipped.append(k)
            theme.append(f"  /* --color-{k}: not emitted, the brand's own --color-{k} owns the utility */")
            continue
        theme.append(f"  --color-{k}: var(--{k});")

    # fonts
    theme.append("  /* fonts */")
    for n in names:
        if not n.startswith("--font-"):
            continue
        key = n[len("--font-"):]
        if key == "text":
            theme.append(f"  --font-sans: var({n});")
        else:
            theme.append(f"  {n}: {alias('font', key)};")

    # type roles
    theme.append("  /* type roles: --text-<role> with Tailwind's companion properties */")
    for n in names:
        m = re.fullmatch(r"--type-([\w-]+)-size", n)
        if not m:
            continue
        role = m.group(1)
        if f"--type-{role}-lh" not in defined:
            continue
        theme.append(f"  --text-{role}: var({n});")
        theme.append(f"  --text-{role}--line-height: var(--type-{role}-lh);")
        if f"--type-{role}-weight" in defined:
            theme.append(f"  --text-{role}--font-weight: var(--type-{role}-weight);")
        if f"--type-{role}-tracking" in defined:
            theme.append(f"  --text-{role}--letter-spacing: var(--type-{role}-tracking);")

    # radius
    theme.append("  /* radius */")
    for n in names:
        if n.startswith("--radius-"):
            theme.append(f"  {n}: {alias('radius', n[len('--radius-'):])};")

    # spacing
    theme.append("  /* spacing: Tailwind's unit, then the brand's named steps (p-sp-3) */")
    sp = (cfg.get("layout") or {}).get("spacing") or {}
    base = num(sp.get("base_px"))
    if base:
        theme.append(f"  --spacing: {base:g}px;")
    for n in names:
        if n.startswith("--space-"):
            theme.append(f"  --spacing-{n[len('--space-'):]}: var({n});")

    # breakpoints
    theme.append("  /* breakpoints: literal px, media queries cannot read a variable */")
    bp = (cfg.get("layout") or {}).get("breakpoints") or {}
    mins = bp.get("min") or {}
    for tw, brand in (bp.get("tailwind") or {}).items():
        if tw.startswith("$"):
            continue
        if brand is None:
            theme.append(f"  --breakpoint-{tw}: initial;")
        elif brand in mins:
            theme.append(f"  --breakpoint-{tw}: {mins[brand]}px;")

    # motion
    theme.append("  /* easing */")
    for n in names:
        if n.startswith("--ease-"):
            theme.append(f"  {n}: {alias('ease', n[len('--ease-'):])};")
    anims = (cfg.get("motion") or {}).get("animations")
    if isinstance(anims, dict):
        theme.append("  /* named animations */")
        for k, v in anims.items():
            if k.startswith("$"):
                continue
            val = v.get("value") if isinstance(v, dict) else v
            if val:
                theme.append(f"  --animate-{k}: {val};")

    bpn = (cfg.get("layout") or {}).get("breakpoints") or {}
    nulls = [k for k, v in (bpn.get("tailwind") or {}).items() if not k.startswith("$") and v is None]
    out = [f"/* {cfg['brand']} {cfg['version']} — tailwind-v4.css. Generated by build/tailwind.py.",
           "   Do not edit: change the config and rebuild.",
           "",
           "   Import order (index.css):",
           '     @import "./tokens.css";          ← plain, UNLAYERED, first',
           '     @import "tailwindcss";',
           '     @import "./tailwind-v4.css";',
           "   tokens.css must stay unlayered: its definitions are what beat the theme",
           "   variables Tailwind re-emits. Never @import it with layer(...).",
           ""]
    if nulls:
        out += [f"   Breakpoints {', '.join(n + ':' for n in nulls)} are `initial` by brand decision",
                "   (layout.breakpoints.tailwind): those prefixes are NO-OPS here. A template or",
                "   shadcn block that uses them (md:grid-cols-2 …) silently stays at its base",
                "   layout — rewrite them to " + ", ".join(f"{k}:" for k, v in (bpn.get("tailwind") or {}).items()
                                                        if not k.startswith("$") and v) + ".", ""]
    if derived:
        out += ["   shadcn names not in components.shadcn.map, derived from the brand's roles",
                "   (state them in the config to own them): " + ", ".join(f"{k} = {r.strip('{}')}" for k, r, _ in derived) + ".", ""]
    out[-1] = out[-1] + " */" if out[-1] else "*/"
    out += ["",
           "/* alias layer: re-declared in every scope tokens.css remaps, so utilities",
           "   follow a dark surface or the Arabic face. See the module docstring. */",
           f"{SCOPES} {{"]
    out += [f"  {a}: var({src});" for a, src in aliases]
    out += ["}", "", "@theme inline {"] + theme + ["}", ""]
    out += ["/* colours tokens.css defines as a var(): mirrored, not inlined, so the utility",
            "   reads the live custom property and follows [data-surface] / [data-theme]. */",
            "@theme {"] + mirror + ["}", ""]

    if sh:
        out += ["/* shadcn bridge: components.shadcn.map. The only place shadcn's names and",
                "   the brand's meet. */", ":root, [data-surface], [data-theme] {"]
        absolute = {k for k, _, a in derived if a}
        for k, v in sh.items():
            if k.startswith("$"):
                continue
            m = REF.match(v) if isinstance(v, str) else None
            if not m:
                continue
            cv = css_var(m.group(1))
            if k in absolute and cv.replace("--color-", "--palette-") in defined and m.group(1).count(".") == 1:
                cv = cv.replace("--color-", "--palette-")
            out.append(f"  --{k}: var({cv});")
        out += ["}", ""]
    return "\n".join(out), skipped, len(colors), derived


def gate(css, tokens_css):
    """Return a list of failure strings; empty is a pass."""
    errs = []
    body = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    D = decls(css)
    # 1. self-reference and longer cycles
    # (@theme inline entries are compile-time inputs: Tailwind substitutes
    # their value into the utility and does not declare them, so they are
    # checked for self-reference but are not edges of the runtime graph.)
    runtime = re.sub(r"@theme[^{]*\{.*?\n\}", "", body, flags=re.S)
    live = set(decls(runtime))
    edges = {}
    for n, v in D:
        refs = re.findall(r"var\((--[\w-]+)", v)
        if (n, v) in live:
            edges.setdefault(n, set()).update(refs)
        if n in refs:
            errs.append(f"self-reference: {n}: {v}")
    for start in sorted(edges):
        seen, stack = set(), list(edges[start] - {start})
        while stack:
            cur = stack.pop()
            if cur == start:
                errs.append(f"cycle through {start}")
                break
            if cur not in seen:
                seen.add(cur)
                stack.extend(edges.get(cur, ()))
    # 2. every var() resolves here or in tokens.css
    have = {n for n, _ in D} | {n for n, _ in decls(tokens_css)}
    used = set(re.findall(r"var\((--[\w-]+)", body))
    for u in sorted(used - have):
        errs.append(f"unresolved var({u})")
    # 3. no literal colours; colour theme entries are var() or initial
    for m in re.finditer(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?|oklch|oklab|lab|lch)\(", body):
        errs.append(f"colour literal: {m.group(0)}")
    for n, v in D:
        if n.startswith("--color-") and not (v == "initial" or v.startswith("var(")) \
                and not n.endswith("*"):
            errs.append(f"{n} is not a var(): {v}")
    # 4. literal lengths only where Tailwind demands them
    for n, v in D:
        if re.search(r"\d(px|rem|em)\b", v) and not (n == "--spacing" or n.startswith("--breakpoint-")):
            errs.append(f"literal value outside spacing/breakpoints: {n}: {v}")
    return sorted(set(errs))


def main():
    try:
        cfg, _, a = load()
    except ConfigError as e:
        sys.exit(f"config gate failed:\n  {e}")
    tp = OUT / "tokens.css"
    if not tp.exists():
        sys.exit("FAILED · out/tokens/tokens.css missing: run build/tokens_css.py first")
    tokens_css = tp.read_text(encoding="utf-8")
    css, skipped, ncolors, derived = build(cfg, tokens_css)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "tailwind-v4.css").write_text(css, encoding="utf-8")
    errs = gate(css, tokens_css)
    if errs:
        print("FAILED · tailwind-v4.css:\n  " + "\n  ".join(errs))
        sys.exit(1)
    msg = f"out/tokens/tailwind-v4.css written · {ncolors} colours, no self-reference, every var() resolves"
    if skipped:
        msg += f" · shadcn {', '.join(skipped)} not emitted as utilities (brand owns the name)"
    if derived:
        msg += f" · shadcn derived (add to components.shadcn.map): {', '.join(k for k, _, _ in derived)}"
    print(msg)


if __name__ == "__main__":
    main()
