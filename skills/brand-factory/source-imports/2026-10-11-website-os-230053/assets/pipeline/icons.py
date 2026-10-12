#!/usr/bin/env python3
"""Lucide icons for the brand's icon set → out/assets/icons/.

    python3 build/icons.py

Reads config `icons`: `set.map` (brand name → Lucide name) and
`ui_set.list` ([{name, use, mirror}], the Lucide name is the brand name).
Writes, per icon, <brand-name>.svg normalised to the config:

  · viewBox 0 0 24 24, fill="none", stroke="currentColor",
    stroke-width = icons.stroke, linecap / linejoin as Lucide ships them
    (never faked), aria-hidden="true", no width, height, class.
  · stroke scaling follows icons.library.stroke_scaling. "proportional"
    (HOI): the stroke stays 1.6 in the 24 box and scaling the SVG scales the
    stroke with it (1.07 at 16px). "absolute": vector-effect=non-scaling-stroke
    on every shape, so the stroke holds at its pixel width.

plus sprite.svg (<symbol id="i-<name>">), icons.manifest.json and
LICENSE-lucide.txt. A config with no `icons` block writes nothing.

Lucide is looked for in $LUCIDE_DIR, <project>/vendor/lucide/icons,
/home/claude/refs/lucide-icons_lucide/icons. Standard library only.

Gate (exit 1): every configured icon exists in Lucide (all missing ones
listed); every output parses as XML and has no fill other than none.
"""
import json, os, pathlib, re, shutil, sys
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from config import load, ConfigError  # noqa: E402

ROOT = HERE.parent
OUT = ROOT / "out" / "assets" / "icons"
SVG = "http://www.w3.org/2000/svg"
SHAPES = {"path", "circle", "rect", "line", "polyline", "polygon", "ellipse"}
FALLBACK = "/home/claude/refs/lucide-icons_lucide/icons"


def find_lucide(root=ROOT):
    tried = []
    cands = [os.environ.get("LUCIDE_DIR"), str(root / "vendor" / "lucide" / "icons"), FALLBACK]
    for c in cands:
        if not c:
            continue
        p = pathlib.Path(c)
        tried.append(str(p))
        if (p / "icons").is_dir():      # the repo root was given
            p = p / "icons"
        if p.is_dir() and any(p.glob("*.svg")):
            return p
    raise FileNotFoundError(
        "Lucide icons not found. Looked in: " + ", ".join(tried) +
        ". Set LUCIDE_DIR to the icons/ folder of a Lucide checkout or copy it "
        "to <project>/vendor/lucide/icons.")


def wanted(cfg):
    """[(brand name, lucide name, use, mirror, group)] from the config."""
    ic = cfg.get("icons") or {}
    out, seen = [], {}
    for brand, lucide in ((ic.get("set") or {}).get("map") or {}).items():
        if brand.startswith("$"):
            continue
        out.append((brand, lucide, None, False, "brand"))
        seen[brand] = lucide
    for it in ((ic.get("ui_set") or {}).get("list") or []):
        n = it["name"]
        if n in seen and seen[n] != n:
            raise ValueError(f"icon name '{n}' is in the brand set (→ {seen[n]}) and the UI set (→ {n})")
        if n in seen:
            continue
        out.append((n, n, it.get("use"), bool(it.get("mirror")), "ui"))
        seen[n] = n
    return out


def children_xml(src, nonscaling, stroke):
    root = ET.fromstring(src)
    parts = []
    for el in root:
        tag = el.tag.split("}")[-1]
        if tag not in SHAPES:
            raise ValueError(f"unexpected element <{tag}>")
        attrs = [(k, v) for k, v in el.attrib.items()]
        if tag == "circle" and el.attrib.get("fill") not in (None, "none") \
                and float(el.attrib.get("r", 99)) <= stroke / 2:
            # A dot whose radius is within half a stroke is already covered by
            # its own stroke: dropping the fill changes no pixel, and the set
            # stays outline-only (icons.never: filled).
            attrs = [(k, v) for k, v in attrs if k != "fill"]
        if nonscaling:
            attrs.append(("vector-effect", "non-scaling-stroke"))
        a = "".join(f' {k}="{escape(v)}"' for k, v in attrs)
        parts.append(f"<{tag}{a}/>")
    return root, parts


def escape(s):
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def svg_attrs(root, stroke):
    return (f'fill="none" stroke="currentColor" stroke-width="{stroke:g}" '
            f'stroke-linecap="{root.get("stroke-linecap", "round")}" '
            f'stroke-linejoin="{root.get("stroke-linejoin", "round")}"')


def render(src, stroke, nonscaling):
    root, parts = children_xml(src, nonscaling, stroke)
    body = "".join(parts)
    attrs = svg_attrs(root, stroke)
    svg = (f'<svg xmlns="{SVG}" viewBox="0 0 24 24" {attrs} aria-hidden="true">'
           f'{body}</svg>\n')
    sym = f'<symbol id="i-{{id}}" viewBox="0 0 24 24" {attrs}>{body}</symbol>'
    return svg, sym


def gate_svg(name, text):
    errs = []
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        return [f"{name}: not XML ({e})"]
    for el in root.iter():
        f = el.attrib.get("fill")
        if f is not None and f != "none":
            tag = el.tag.split("}")[-1]
            errs.append(f'{name}: fill="{f}" on <{tag}>')
        if re.search(r"fill\s*:\s*(?!none)", el.attrib.get("style", "")):
            errs.append(f"{name}: fill in style")
    return errs


def main():
    try:
        cfg, _, a = load()
    except ConfigError as e:
        sys.exit(f"config gate failed:\n  {e}")
    ic = cfg.get("icons")
    items = wanted(cfg) if ic else []
    if not items:
        print("no icons block in the config · nothing written")
        return
    try:
        lucide = find_lucide()
    except FileNotFoundError as e:
        print(f"FAILED · {e}")
        sys.exit(1)

    missing = sorted({f"{b} → {l}" for b, l, *_ in items if not (lucide / f"{l}.svg").exists()})
    if missing:
        print("FAILED · not in Lucide (" + str(lucide) + "):\n  " + "\n  ".join(missing))
        sys.exit(1)

    stroke = float(num(ic.get("stroke") or (ic.get("library") or {}).get("stroke") or 2))
    scaling = str((ic.get("library") or {}).get("stroke_scaling") or "proportional")
    nonscaling = scaling == "absolute"
    sizes = num(ic.get("sizes")) or []

    if OUT.exists():
        for f in OUT.glob("*.svg"):
            f.unlink()
    OUT.mkdir(parents=True, exist_ok=True)

    errs, symbols, manifest = [], [], []
    for brand, lucide_name, use, mirror, group in sorted(items):
        src = (lucide / f"{lucide_name}.svg").read_text(encoding="utf-8")
        svg, sym = render(src, stroke, nonscaling)
        errs += gate_svg(f"{brand}.svg", svg)
        (OUT / f"{brand}.svg").write_text(svg, encoding="utf-8")
        symbols.append(sym.replace("{id}", brand))
        manifest.append({"name": brand, "lucide": lucide_name, "group": group, "use": use,
                         "mirror_rtl": mirror, "sizes": sizes, "licence": "ISC",
                         "source": f"lucide/icons/{lucide_name}.svg"})
    sprite = (f'<svg xmlns="{SVG}" aria-hidden="true" style="display:none">\n  '
              + "\n  ".join(symbols) + "\n</svg>\n")
    errs += gate_svg("sprite.svg", sprite)
    (OUT / "sprite.svg").write_text(sprite, encoding="utf-8")
    (OUT / "icons.manifest.json").write_text(json.dumps({
        "library": "lucide", "licence": "ISC", "stroke": stroke, "stroke_scaling": scaling,
        "grid": num(ic.get("grid")) or 24, "sizes": sizes, "icons": manifest},
        indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lic = next((p for p in (lucide.parent / "LICENSE", lucide / "LICENSE") if p.exists()), None)
    if lic:
        shutil.copyfile(lic, OUT / "LICENSE-lucide.txt")
    else:
        errs.append("Lucide LICENSE not found next to the icons folder")
    if errs:
        print("FAILED · icons:\n  " + "\n  ".join(errs))
        sys.exit(1)
    print(f"out/assets/icons/ written · {len(items)} icons + sprite + manifest + licence · "
          f"stroke {stroke:g} ({scaling}) · all resolve in Lucide, all parse, no fill")


def num(v):
    return v.get("value") if isinstance(v, dict) else v


if __name__ == "__main__":
    main()
