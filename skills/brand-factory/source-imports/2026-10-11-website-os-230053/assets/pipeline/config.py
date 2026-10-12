#!/usr/bin/env python3
"""brand.config.json v2 — load, check provenance, and hand the v1 scripts
the shape they expect.

    python3 build/config.py                 # report + out/provenance.json + out/CONFIRM.md
    python3 build/config.py path/to/brand.config.json

Every generator imports `load()` instead of reading the JSON itself, so
there is one place that knows the schema.

What this gate fails on:
  · the config does not match assets/schema/brand.config.v2.schema.json
  · a $src names a source that is not in `sources`
  · a component references a token that does not exist, or holds a
    literal hex (fixtures must resolve through tokens)
  · reproduce mode, a value whose $conf is "guess" with no reconcile item
    covering it — a guess is a question, not a value

What it reports, never fails on:
  · how many values are high / medium / derived / default / gap
  · every default and gap, grouped, so the owner sees what is not theirs

Provenance rules (JSON Schema cannot express inheritance, so they live
here, not in the schema):
  · `$src` and `$conf` on any object apply to everything beneath it.
  · `$src_<x>` / `$conf_<x>` / `$gap_<x>` on an object apply to the
    descendant whose path relative to that object (keys joined by "_",
    list indices dropped) is EXACTLY x. An explicit `$src` further down
    wins; the override stops there.
  · a `$src` without a `$conf` means "high", unless the source is WO
    (the website-os default), which means "default".
  · `$gap` marks the node and everything under it as a gap.
  · null is never a value. It is a gap, or — under a node with a policy,
    rule or $note — an empty slot explained in place. Absent-by-design is
    the string "none", which IS a value.

Standard library only. jsonschema is used when installed and skipped
with a warning when it is not.
"""
import collections, json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
# Two homes, as with check.py: build/ inside a project, assets/pipeline/
# inside the skill.
ROOT = HERE.parent
SCHEMA_CANDIDATES = [ROOT / "schema" / "brand.config.v2.schema.json",
                     HERE.parent / "schema" / "brand.config.v2.schema.json",
                     HERE.parent.parent / "assets" / "schema" / "brand.config.v2.schema.json"]

CONF = ("high", "medium", "derived", "guess", "default", "gap")
META = re.compile(r"^\$")
SKIP_TOP = {"sources", "reconcile", "$schema", "$comment", "$src", "$conf"}


class ConfigError(Exception):
    pass


# ── loading ─────────────────────────────────────────────────────────────
def path_default():
    return ROOT / "brand.config.json"


def read(path=None):
    p = pathlib.Path(path) if path else path_default()
    return json.loads(p.read_text(encoding="utf-8")), p


def schema_errors(cfg):
    schema_path = next((p for p in SCHEMA_CANDIDATES if p.exists()), None)
    if schema_path is None:
        return ["schema file not found — looked beside build/ and in assets/schema/"], None
    try:
        import jsonschema
    except ImportError:
        return [], "jsonschema not installed — structure not checked (pip install jsonschema)"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    v = jsonschema.Draft202012Validator(schema)
    out = []
    for e in sorted(v.iter_errors(cfg), key=lambda e: list(e.path)):
        where = "/".join(str(x) for x in e.path) or "(root)"
        out.append(f"schema: {where}: {e.message[:160]}")
    return out, None


# ── provenance ──────────────────────────────────────────────────────────
def _sid(src):
    return str(src).split(":")[0] if src else None


def _conf_for(src, explicit, inherited=None, inherited_src=None):
    """$conf given → that. WO → default. Otherwise keep what was inherited,
    unless what was inherited came from WO (a default does not stay a
    default once a real source is named) — then high."""
    if explicit:
        return explicit
    if _sid(src) == "WO":
        return "default"
    if inherited and _sid(inherited_src) != "WO" and inherited != "gap":
        return inherited
    return "high"


def walk(cfg):
    """[(pointer, value, src, conf, gap)] for every leaf.

    Precedence, innermost wins:
      1. the node's own $src / $conf / $gap
      2. the nearest ancestor's $src_<x> / $conf_<x> / $gap_<x> whose x is
         EXACTLY this node's path relative to that ancestor (keys joined by
         "_", list indices dropped). An explicit $src further down beats
         an override further up — the override never reaches past it.
      3. inherited context.
    Lists of dicts are walked; a list of scalars is one leaf. A null is
    never a value: it is a gap (with its reason) or, under a node that
    states a policy, rule or note, an empty slot explained in place.
    """
    out = []

    def apply(ctx, stack):
        src, conf, gap = ctx
        for rel, ov in reversed(stack):          # nearest ancestor first
            key = "_".join(rel)
            hit = False
            if key in ov["src"]:
                conf = _conf_for(ov["src"][key], None, conf, src)
                src, hit = ov["src"][key], True
            if key in ov["conf"]:
                conf, hit = ov["conf"][key], True
            if key in ov["gap"]:
                gap, conf, hit = ov["gap"][key], "gap", True
            if hit:
                break
        return src, conf, gap

    def overrides(node):
        o = {"src": {}, "conf": {}, "gap": {}}
        for k, v in node.items():
            m = re.match(r"^\$(src|conf|gap)_(.+)$", k)
            if m:
                o[m.group(1)][m.group(2)] = v
        return o

    def rec(node, ptr, ctx, stack, why_null):
        src, conf, gap = apply(ctx, stack)
        if isinstance(node, dict):
            if "$src" in node:
                # A fresh citation on the node is judged on its own: high,
                # or default for WO. Only an override inherits confidence.
                conf = _conf_for(node["$src"], node.get("$conf"))
                src, gap = node["$src"], None      # a named source ends an inherited gap
                stack = []                         # explicit source: overrides stop here
            elif "$conf" in node:
                conf = node["$conf"]
            if "$gap" in node:
                gap, conf = node["$gap"], "gap"
            stack = [(rel, o) for rel, o in stack]
            here = overrides(node)
            explains = any(k in node for k in ("$note", "$gap", "policy", "rule"))
            for k, v in node.items():
                if META.match(k):
                    continue
                child_stack = [(rel + [k], o) for rel, o in stack] + [([k], here)]
                rec(v, f"{ptr}/{k}", (src, conf, gap), child_stack, explains)
        elif isinstance(node, list) and any(isinstance(x, dict) for x in node):
            for i, v in enumerate(node):
                if isinstance(v, dict):
                    rec(v, f"{ptr}/{i}", (src, conf, gap), stack, why_null)   # index not in rel
                else:
                    out.append((f"{ptr}/{i}", v, src, conf, gap))
        elif node is None:
            if gap:
                out.append((ptr, None, src, "gap", gap))
            elif why_null:
                out.append((ptr, None, src, "empty", "explained in place"))
            else:
                out.append((ptr, None, src, "empty", None))
        else:
            out.append((ptr, node, src, conf, gap))

    root_src = cfg.get("$src")
    root = (root_src, _conf_for(root_src, cfg.get("$conf")) if root_src else None, None)
    for k, v in cfg.items():
        if k in SKIP_TOP or META.match(k):
            continue
        rec(v, f"/{k}", root, [], False)
    return out


def _dotted(ptr):
    """/type/scale/roles/3/px/phone → type.scale.roles.px.phone"""
    return ".".join(x for x in ptr.strip("/").split("/") if not x.isdigit())


def _covers(item_path, ptr_dotted):
    for p in re.split(r"\s*,\s*", item_path):
        p = re.sub(r"\[\*\]|\.\*|\|.*$", "", p.split(" ")[0]).strip(".")
        if p and (ptr_dotted == p or ptr_dotted.startswith(p + ".")):
            return True
    return False


def _verify_sources(cfg, base):
    errs = []
    for sid, s in cfg.get("sources", {}).items():
        if not isinstance(s, dict) or not s.get("path"):
            continue
        f = (base / s["path"]) if base else None
        if f is None or not f.exists():
            errs.append(f"source {sid}: {s['path']} does not exist")
            continue
        if s.get("sha256") and f.is_file():
            import hashlib
            h = hashlib.sha256(f.read_bytes()).hexdigest()
            if not h.startswith(s["sha256"].lower()):
                errs.append(f"source {sid}: sha256 {h[:12]} ≠ recorded {s['sha256']} — "
                            f"the evidence changed; re-run reconcile")
    return errs


# ── the report ──────────────────────────────────────────────────────────
def analyse(cfg, base=None):
    errs, warns = [], []
    s_errs, s_warn = schema_errors(cfg)
    errs += s_errs
    if s_warn:
        warns.append(s_warn)
    errs += _verify_sources(cfg, base)

    sources = cfg.get("sources", {})
    pages = {sid: s.get("pages") for sid, s in sources.items()
             if isinstance(s, dict) and s.get("locator") == "page"}
    leaves = walk(cfg)
    by_conf = collections.Counter()
    by_src = collections.Counter()
    defaults, gaps, guesses = [], [], []
    prov = {}
    for ptr, val, src, conf, gap in leaves:
        sid = _sid(src)
        if src is None:
            errs.append(f"no source for {ptr}")
        elif sid not in sources:
            errs.append(f"{ptr}: $src '{src}' names no source in `sources`")
        else:
            for m in re.finditer(r"\bp(\d+)", str(src).split(":", 1)[-1] if ":" in str(src) else ""):
                n = pages.get(sid)
                if n and int(m.group(1)) > n:
                    errs.append(f"{ptr}: {src} — {sid} has {n} pages")
        if conf not in CONF + ("empty",):
            errs.append(f"{ptr}: $conf '{conf}' is not one of {', '.join(CONF)}")
        prov[ptr] = {"src": src, "conf": conf, **({"gap": gap} if gap else {})}
        if conf == "empty":
            if not gap:
                warns.append(f"{ptr} is null with no $gap, policy, rule or note — "
                             f"say why it is empty, or use \"none\" for absent-by-design")
            continue                                  # never counted as a value
        by_conf[conf] += 1
        by_src[sid] += 1
        if conf == "default":
            defaults.append(ptr)
        elif conf == "gap":
            gaps.append((ptr, gap))
        elif conf == "guess":
            guesses.append(ptr)

    items = cfg.get("reconcile", {}).get("items", [])
    if cfg.get("mode") == "reproduce":
        for ptr in guesses:
            if not any(_covers(i.get("path", ""), _dotted(ptr)) for i in items):
                errs.append(f"reproduce mode: {ptr} is a guess with no reconcile item")
    for i in items:
        if i.get("status") == "confirm" and not i.get("affects"):
            warns.append(f"reconcile {i['id']}: no `affects` — CONFIRM.md cannot say "
                         f"which values the answer rewrites")

    errs += check_components(cfg)
    counted = sum(by_conf.values())
    return {"errors": errs, "warnings": warns, "by_conf": by_conf, "by_src": by_src,
            "defaults": defaults, "gaps": gaps, "provenance": prov,
            "reconcile": items, "leaves": counted}


# ── references inside components ────────────────────────────────────────
REF = re.compile(r"\{([a-zA-Z0-9_.-]+)\}")
HEX = re.compile(r"#[0-9A-Fa-f]{3,8}\b|\brgba?\(|\bhsla?\(|\boklch\(")
# The only bare words a style slot may hold. Border styles (solid, dashed)
# live in a composite's `style` key, which is not a colour slot.
KEYWORDS = {"none", "transparent", "currentColor", "inherit", "underline"}
# A key is a style slot if it is named for paint: bg, fg, color, fill,
# border, outline, edge, track, ring, scrim — alone or as a suffix
# (row_rule, chip_fg, on_bg). Any composite under a slot is checked too.
# "rule" counts only as a suffix (row_rule): a bare `rule` key is prose.
SLOT_RE = re.compile(r"(?:^|_)(?:bg|fg|color|fill|border|outline|edge|track|"
                     r"ring|scrim|surface)$|_rule$|^on_(?:dark|accent)$")


def ref_targets(cfg):
    """Every name a {reference} may resolve to — the token tree the DTCG
    and Tailwind generators will emit, named the way they will name it."""
    C = cfg["color"]
    live = lambda d: [k for k, v in (d or {}).items() if not k.startswith("$")]
    def has_value(v):
        return isinstance(v, dict) and (v.get("hex") or v.get("value") not in (None, ""))
    t = {f"color.{k}" for k, v in (C.get("roles") or {}).items()
         if not k.startswith("$") and has_value(v)}
    t |= {f"color.state.{k}" for k in live(C.get("states"))}
    t |= {f"color.semantic.{k}" for k, v in (C.get("semantic") or {}).items()
          if not k.startswith("$") and isinstance(v, dict) and v.get("hex")}
    t |= {f"color.pillar.{k}" for k in live(C.get("accents"))}
    t |= {f"color.dataviz.chart.{k}" for k in live((C.get("dataviz") or {}).get("chart"))}
    t |= {f"radius.{k}" for k in ("surface", "control", "floating")}
    t |= {f"space.{k}" for k in live(cfg["layout"]["spacing"].get("steps"))}
    t |= {f"type.{r['role']}" for r in cfg["type"]["scale"]["roles"]}
    t |= {f"motion.{k}" for k in live(cfg["motion"].get("durations_ms"))}
    t |= {f"ease.{k}" for k in live(cfg["motion"].get("easing"))}
    t |= {f"elevation.{k}" for k in live(cfg.get("elevation", {}).get("levels"))}
    t |= {f"component.{k}" for k in live(cfg.get("components"))}
    return t


def check_components(cfg):
    """A style slot holds a reference, a keyword, a number, or a composite
    whose colour is a reference. Anything else is a literal that would
    reach a fixture — the 'no literal values' gate, one step early."""
    errs = []
    targets = ref_targets(cfg)

    def check_ref(v, ptr):
        for m in REF.finditer(v):
            if m.group(1) not in targets:
                errs.append(f"unresolved {{{m.group(1)}}} at {ptr}")

    def rec(n, ptr, slot):
        if isinstance(n, dict):
            for k, v in n.items():
                if k.startswith("$"):
                    continue
                rec(v, f"{ptr}/{k}", bool(SLOT_RE.search(k)) or (slot and k == "color"))
        elif isinstance(n, list):
            for i, v in enumerate(n):
                rec(v, f"{ptr}/{i}", slot)
        elif isinstance(n, str):
            check_ref(n, ptr)
            if HEX.search(n):
                errs.append(f"literal colour at {ptr}: '{n[:40]}' — reference a token")
            elif slot and not REF.fullmatch(n) and n not in KEYWORDS:
                errs.append(f"style slot {ptr} holds '{n[:40]}' — a reference, a "
                            f"keyword or a composite, not prose")
    rec(cfg.get("components", {}), "/components", False)
    # The same grammar holds wherever the config binds paint to a token.
    rec(cfg.get("elevation", {}).get("levels", {}), "/elevation/levels", False)
    rec(cfg.get("layout", {}).get("rules", {}), "/layout/rules", False)
    rec((cfg["color"].get("dataviz") or {}).get("score", {}), "/color/dataviz/score", False)
    for k, v in (cfg["motion"].get("assign") or {}).items():
        if isinstance(v, list):
            for x in v:
                if isinstance(x, str) and not REF.fullmatch(x) and x not in ("loop",):
                    errs.append(f"motion.assign.{k}: '{x}' — use {{motion.x}} / {{ease.x}}")
                elif isinstance(x, str):
                    check_ref(x, f"/motion/assign/{k}")
    return errs


def _group(ptrs, depth=3):
    g = collections.OrderedDict()
    for p in ptrs:
        key = "/".join(p.split("/")[:depth + 1])
        g.setdefault(key, []).append(p)
    return g


def confirm_md(cfg, a):
    L = [f"# CONFIRM — {cfg['brand']} {cfg['version']}", "",
         f"Generated by build/config.py from brand.config.json (mode: {cfg['mode']}). "
         "Do not edit this file. To answer: in brand.config.json, write your answer "
         "in the item's `answer`, set `status` to `confirmed`, and change the values "
         "listed under *changes* to match — then rebuild.", ""]
    open_items = [i for i in a["reconcile"] if i.get("status") == "confirm"]
    L += [f"## Questions for the brand owner ({len(open_items)})", ""]
    for i in open_items:
        L.append(f"### {i['id']} · `{i['path']}`")
        L.append("")
        L.append(f"**{i['question']}**")
        L.append("")
        for c in i.get("candidates", []):
            L.append(f"- candidate: `{json.dumps(c.get('value'), ensure_ascii=False)}` — {c.get('src', '')}")
        L.append(f"- using until answered: `{json.dumps(i.get('chosen'), ensure_ascii=False)}`")
        if i.get("affects"):
            L.append(f"- changes: {', '.join('`' + a + '`' for a in i['affects'])}")
        L.append(f"- why: {i['why']}")
        L.append("")
    done = [i for i in a["reconcile"] if i.get("status") != "confirm"]
    L += [f"## Resolved without you ({len(done)})", "",
          "Contradictions inside the sources, decided with a reason. Read them; overturn any by editing `reconcile`.", ""]
    for i in done:
        L.append(f"- **{i['id']}** `{i['path']}` → `{json.dumps(i.get('chosen'), ensure_ascii=False)}`. {i['why']}")
    L += ["", f"## Values that are not the brand's ({len(a['defaults'])} leaves)", "",
          "website-os defaults, used so the build can run. Each is yours to accept or replace.", ""]
    for k, ps in _group(a["defaults"]).items():
        L.append(f"- `{k}` ({len(ps)})")
    L += ["", f"## Gaps ({len(a['gaps'])} leaves)", "",
          "Not in any source. Left empty; the generators omit them and DESIGN.md lists them under Known Gaps.", ""]
    seen = set()
    for ptr, why in a["gaps"]:
        key = "/".join(ptr.split("/")[:4])
        if key in seen:
            continue
        seen.add(key)
        L.append(f"- `{key}` — {why}")
    return "\n".join(L) + "\n"


# ── the v1 view ─────────────────────────────────────────────────────────
def _w(v):
    """v1 wants "200 800" for a variable face and a list for static ones."""
    if isinstance(v, dict):
        if "axis" in v:
            return " ".join(str(x) for x in v["axis"])
        return v.get("static")
    return " ".join(str(x) for x in v) if isinstance(v, list) else v


def v1_view(cfg):
    """The v1 shape tokens.py, fonts.py, css.py, book.py and brandmd.py read.
    Built from v2, never stored. v2-only blocks ride along under their own
    keys so downstream generators can start reading them one at a time."""
    C = cfg["color"]
    R = C["roles"]
    idn = cfg.get("identity", {}).get("positioning", {})
    pos = " ".join(x for x in (idn.get("architecture"), idn.get("boundary")) if x) \
        or cfg.get("positioning", "")
    accents = {k: {"hex": v["hex"], "label": v.get("label", k)}
               for k, v in C.get("accents", {}).items()
               if isinstance(v, dict) and v.get("hex") and not v.get("alias_of")}
    # v1's chassis names semantic fills attention/blocking (var(--blocking)
    # in its CSS and templates). A brand that calls them Warning/Danger
    # keeps its names in v2 and maps here through component_name.
    semantic = {}
    for k, v in C.get("semantic", {}).items():
        if isinstance(v, dict) and v.get("hex"):
            on = v.get("on", "fg")
            semantic[v.get("component_name", k)] = {
                "hex": v["hex"], "text": {"fg": "ink", "bg": "ground"}.get(on, on),
                "use": v.get("use", "")}
    retired = {}
    for k, v in C.get("retired", {}).items():
        if k.startswith("$"):
            continue
        if isinstance(v, str):
            retired[k] = v
        elif isinstance(v, dict) and v.get("hex") and not v.get("retired_role_only"):
            retired[k] = v["hex"]
    av = cfg.get("avoid_palettes", {})
    sets = {k: (v.get("value", []) if isinstance(v, dict) else v)
            for k, v in av.get("sets", {}).items() if not k.startswith("$")}
    F = cfg["type"]["families"]

    def fam(k, extra=()):
        f = F[k]
        d = {x: f[x] for x in ("family", "npm", "file", "italic_file", "base_weight",
                               "accent_weight", "has_italic", "ceiling_px", "use",
                               "file_pattern", "scale", "line_height_bump") + tuple(extra)
             if x in f}
        if "weights" in f:
            d["weights"] = _w(f["weights"])
        return d

    bands = [b for b in cfg["type"].get("tracking", {}).get("bands", [])
             if b.get("family", "display") == "display"]
    trk = {}
    for name, lo in (("xl", 64), ("lg", 43), ("md", 24), ("sm", 0)):
        b = next((b for b in bands if b["min_px"] == lo), None)
        if b:
            trk[name] = b["value"]
    type_v1 = {"display": fam("display"), "text": fam("text"), "mono": fam("mono"),
               "tracking": trk}
    if "arabic" in F:
        type_v1["arabic"] = fam("arabic")

    def role(k, alt=None):
        r = R.get(k) or {}
        return {"hex": r.get("hex"), "role": r.get("role", alt or k)}

    color = {"ground": role("bg"), "ink": role("fg"), "brand": role("accent"),
             "brand_on_dark": role("accent_on_dark"), "muted": role("muted"),
             "surface": role("surface"), "line": role("border")}
    if accents:
        color["accents"] = accents
    color["semantic"] = semantic
    color["retired"] = retired

    dens = cfg["density"]
    return {
        "brand": cfg["brand"], "slug": cfg["slug"], "version": cfg["version"],
        "date": cfg.get("date", ""), "supersedes": cfg.get("supersedes", "nothing"),
        "positioning": pos,
        "locales": cfg["locales"]["list"],
        "color": color,
        "avoid_palettes": {"threshold": av.get("threshold", 40), "sets": sets,
                           "accepted": av.get("accepted", [])},
        "type": type_v1,
        "shape": {k: cfg["shape"][k] for k in ("surface", "control", "floating")},
        "density": {"line_height": dens["line_height"],
                    "scales": {k: {x: v[x] for x in ("row", "text", "label", "pad_x", "use") if x in v}
                               for k, v in dens["scales"].items()}},
        "motion": {"durations_ms": cfg["motion"]["durations_ms"],
                   "easing": cfg["motion"]["easing"]},
        "a11y": {k: cfg["a11y"][k] for k in ("target", "target_min_px", "floors") if k in cfg["a11y"]},
        "voice": {"banned": cfg["voice"]["banned"]["list"]},
        "book": cfg.get("book", {}),
        # v2 blocks, carried for the generators and the checker
        "mode": cfg["mode"],
        "effects": cfg["effects"],
        "states": {k: v for k, v in C.get("states", {}).items() if not k.startswith("$")},
    }


def load(path=None, strict=True):
    """Return (v2 config, v1 view). Raises ConfigError on any gate failure
    when strict; the caller decides whether to print and exit."""
    cfg, p = read(path)
    if cfg.get("config_version") != 2:
        raise ConfigError(f"{p} is not a v2 config (config_version missing or "
                          f"not 2). See references/config-v2.md.")
    a = analyse(cfg, p.parent)
    if strict and a["errors"]:
        raise ConfigError("\n".join(a["errors"]))
    return cfg, v1_view(cfg), a


def load_v1(path=None):
    """For the v1 scripts: the v1 view, or exit with the gate's errors."""
    try:
        return load(path)[1]
    except ConfigError as e:
        sys.exit(f"brand.config.json failed the config gate:\n  " +
                 str(e).replace("\n", "\n  ") + "\nRun build/config.py for the full report.")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else None
    cfg, p = read(path)
    if cfg.get("config_version") != 2:
        sys.exit(f"{p}: not a v2 config")
    a = analyse(cfg, p.parent)
    out = (p.parent / "out")
    out.mkdir(exist_ok=True)
    (out / "provenance.json").write_text(json.dumps(a["provenance"], indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "CONFIRM.md").write_text(confirm_md(cfg, a), encoding="utf-8")

    print(f"{cfg['brand']} {cfg['version']} — config v2, mode {cfg['mode']}\n")
    print(f"provenance · {a['leaves']} values")
    for c in CONF:
        if a["by_conf"][c]:
            print(f"  {c:8} {a['by_conf'][c]:>4}")
    print("  by source  " + "  ".join(f"{k}:{v}" for k, v in sorted(a["by_src"].items(), key=lambda x: str(x[0]))))
    open_n = sum(1 for i in a["reconcile"] if i.get("status") == "confirm")
    print(f"\nreconcile · {len(a['reconcile'])} items, {open_n} for the owner → out/CONFIRM.md")
    for w in a["warnings"]:
        print("  warning ·", w)
    if a["errors"]:
        print("\nFAILED")
        for e in a["errors"]:
            print("  ·", e)
        sys.exit(1)
    print("\nconfig ok · out/provenance.json · out/CONFIRM.md")


if __name__ == "__main__":
    main()
