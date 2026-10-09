#!/usr/bin/env python3
"""A starter brand book, generated from out/tokens.json.

Eight pages. Not a finished book — a working chassis that demonstrates the
four things worth copying:

  1. every page is generated, so the book cannot disagree with the tokens
  2. folios renumber themselves, so inserting a page never desynchronises
  3. the contents is generated from the folios, so it cannot drift
  4. `.page` is overflow:hidden, so a too-tall page loses its bottom in
     SILENCE — which is why build/verify.js renders and measures

Add sections by writing a function that returns page() and appending it to
PAGES. Everything downstream adjusts.
"""
import json, pathlib, re, html

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = json.loads((ROOT / "out" / "tokens.json").read_text(encoding="utf-8"))
CSS = (ROOT / "out" / "tokens.css").read_text(encoding="utf-8")
FONTS = (ROOT / "out" / "fonts-embedded.css").read_text(encoding="utf-8")
C, M, D, TY = T["color"], T["measured_contrast"], T["density"], T["type"]
PG = T["book"]["page"]
W, H = PG["width_mm"], PG["height_mm"]
MT, MR, MB, ML = PG["margin_mm"]

PAGE_CSS = f"""
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#4A505E}}
.page{{width:{W}mm;height:{H}mm;background:var(--ground);margin:0 auto 6mm;
  position:relative;overflow:hidden;padding:{MT}mm {MR}mm {MB}mm {ML}mm;
  display:flex;flex-direction:column}}
.page.dark{{background:var(--ink);color:var(--ground)}}
.folio{{position:absolute;left:{ML}mm;right:{MR}mm;bottom:8mm;display:flex;
  justify-content:space-between;font-family:var(--mono);font-size:6.2pt;
  letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}}
.page.dark .folio{{color:rgba(255,255,255,.45)}}
.eb{{font-family:var(--mono);font-size:6.6pt;letter-spacing:.2em;
  text-transform:uppercase;color:var(--brand)}}
h1{{font-size:46pt;line-height:.96;letter-spacing:var(--track-xl)}}
h2{{font-size:27pt;line-height:1.04;letter-spacing:var(--track-lg)}}
h4{{font-family:var(--mono);font-size:6.4pt;font-weight:500;letter-spacing:.18em;
  text-transform:uppercase;color:var(--muted);margin-bottom:2.2mm}}
.lede{{font-size:10.4pt;line-height:1.42;margin-top:4mm}}
.sm{{font-size:9.2pt;line-height:1.5}}
.xs{{font-size:7.4pt;line-height:1.5;color:var(--muted)}}
.hr{{border-top:1px solid var(--line);margin:4mm 0}}
.hr-ink{{border-top:1.6px solid var(--ink);margin:4mm 0}}
.rail{{display:grid;grid-template-columns:3fr 9fr;gap:10mm;flex:1;min-height:0}}
.rail>.side,.rail>.main{{display:flex;flex-direction:column;min-height:0}}
.cols3{{display:grid;grid-template-columns:repeat(3,1fr);gap:9mm}}
.cols3>div{{display:flex;flex-direction:column}}
table{{width:100%;border-collapse:collapse;font-size:7.4pt}}
td,th{{padding:1.8mm 2.4mm 1.8mm 0;border-bottom:1px solid var(--line);
  text-align:left}}
th{{font-family:var(--mono);font-size:6pt;letter-spacing:.14em;
  text-transform:uppercase;color:var(--muted);border-bottom:1.2px solid var(--ink)}}
td.n{{font-family:var(--mono);font-size:6.9pt;text-align:right}}
.note{{border-left:1.6px solid var(--brand);padding-left:5mm;margin-top:auto}}
.divnum{{font-family:var(--display);font-size:150pt;font-weight:200;
  line-height:.76;letter-spacing:-.04em;color:rgba(255,255,255,.13)}}
.sw{{height:17mm;display:flex;align-items:flex-end;padding:2mm;
  font-family:var(--mono);font-size:5.8pt}}
.page.has-foot::after{{content:'';display:block;margin-top:auto;
  border-top:1px solid var(--line);height:0}}
@media print{{.page{{margin:0;page-break-after:always}}body{{background:#fff}}}}
"""

FOOT = ('<div class="folio"><span>{brand} · Brand Book {ver}</span>'
        '<span>{sec}</span><span>__N__</span></div></section>')


def page(body, sec, dark=False, foot=True):
    cls = "page dark" if dark else ("page has-foot" if foot else "page")
    return (f'<section class="{cls}">{body}'
            + FOOT.format(brand=html.escape(T["brand"]),
                          ver=T["version"], sec=html.escape(sec)))


def cover():
    return page(
        '<div style="display:flex;flex-direction:column;height:100%;'
        'justify-content:space-between">'
        f'<div class="eb" style="color:var(--brand-on-dark)">'
        f'Corporate identity · Version {T["version"]}</div>'
        f'<div><h1>Brand <span class="accent">Book</span>.</h1>'
        f'<div style="height:2px;width:32mm;background:var(--brand);'
        f'margin:9mm 0 6mm"></div>'
        f'<p class="lede" style="max-width:140mm;margin:0">'
        f'{html.escape(T["positioning"])}</p></div>'
        f'<div class="eb" style="color:rgba(255,255,255,.45);'
        f'letter-spacing:.16em">{html.escape(T["date"])} · supersedes '
        f'{html.escape(T["supersedes"])}</div></div>',
        "Cover", dark=True)


def contents_stub():
    return page('<div class="eb">Contents</div>'
                '<h2 style="margin:3mm 0 5mm">What is in this book</h2>'
                '<div class="hr-ink"></div>'
                '<div class="toc" style="flex:1"></div>',
                "Contents", foot=False)


def divider(num, name, items):
    return page(
        '<div class="rail" style="align-items:center">'
        f'<div class="side"><div class="divnum">{num}</div></div>'
        '<div class="main" style="justify-content:center">'
        f'<h1><span class="accent">{html.escape(name)}</span></h1>'
        '<div class="hr" style="margin:7mm 0 5mm;max-width:132mm"></div>'
        '<ul style="columns:2;column-gap:12mm;max-width:132mm;'
        'font-size:9.2pt">'
        + "".join(f"<li>{html.escape(i)}</li>" for i in items)
        + '</ul></div></div>', f"{num} · {name}", dark=True)


def palette():
    def sw(name, hexv, fg):
        return (f'<div><div class="sw" style="background:{hexv};color:{fg}">'
                f'{hexv}</div><h4 style="margin-top:2mm">{name}</h4></div>')
    cells = []
    for k, v in C.items():
        if isinstance(v, dict) and "hex" in v:
            fg = C["ground"]["hex"] if k in ("ink", "brand") else C["ink"]["hex"]
            cells.append(sw(k, v["hex"], fg))
    for k, v in C.get("accents", {}).items():
        if isinstance(v, dict):
            cells.append(sw(v.get("label", k), v["hex"], C["ground"]["hex"]))
    rows = "".join(
        f'<tr><td>{k}</td><td class="n">{v["ratio"]}:1</td>'
        f'<td class="n" style="color:var(--muted)">{v["floor"]}</td></tr>'
        for k, v in list(M.items())[:8])
    return page(
        '<div class="eb">02 · Colour</div>'
        '<h2 style="margin-top:3mm">The <span class="accent">palette</span></h2>'
        '<div class="hr-ink" style="margin-top:5mm"></div>'
        '<div style="display:grid;grid-template-columns:repeat(5,1fr);'
        f'gap:4mm;margin-top:5mm">{"".join(cells)}</div>'
        '<h4 style="margin-top:6mm">Measured</h4>'
        f'<table><tbody>{rows}</tbody></table>'
        '<div class="note"><p class="sm" style="margin:0">Every ratio here '
        'was computed, not estimated, and the build fails below the floor. '
        'A brand book that states a ratio nobody measured is a brand book '
        'nobody can rely on.</p></div>',
        "02 · Colour")


def typography():
    cards = ""
    for k in ("display", "text", "mono"):
        t = TY[k]
        fam = {"display": "var(--display)", "text": "var(--text-face)",
               "mono": "var(--mono)"}[k]
        cards += (
            f'<div><div style="font-family:{fam};font-size:46pt;'
            f'line-height:1;letter-spacing:var(--track-lg)">Rag</div>'
            f'<h4 style="margin-top:4mm">{html.escape(t["family"])}</h4>'
            f'<p class="sm">{html.escape(t.get("use",""))} '
            f'Weights {t.get("weights","")}.</p>'
            + ("" if t.get("has_italic", True) else
               '<p class="xs" style="margin-top:auto">No italic exists. '
               'Never synthesise one.</p>')
            + '</div>')
    return page(
        '<div class="eb">03 · Typography</div>'
        '<h2 style="margin-top:3mm">The <span class="accent">stack</span></h2>'
        '<div class="hr-ink" style="margin-top:5mm"></div>'
        f'<div class="cols3" style="flex:1;margin-top:5mm">{cards}</div>'
        '<div class="note"><p class="sm" style="margin:0"><strong>No fourth '
        'font.</strong> Not for a campaign, not for a client sector, not for '
        'one deck.</p></div>',
        "03 · Typography")


def density_page():
    cols = ""
    for k, v in D.items():
        rows = "".join(
            f'<div style="height:{v["row"]*0.265:.1f}mm;border-bottom:1px '
            f'solid var(--line);display:flex;align-items:center;'
            f'padding:0 2mm;font-size:{v["text"]*0.58:.1f}pt">Row {i}</div>'
            for i in range(1, 7))
        cols += (f'<div><h4>{k}</h4><p class="xs" style="margin-bottom:2mm">'
                 f'{v["row"]}px row · {v["text"]}px text · pad {v["pad_y"]}px'
                 f'</p><div style="border-top:1px solid var(--line)">{rows}'
                 f'</div><p class="xs" style="margin-top:3mm">'
                 f'{html.escape(v.get("use",""))}</p></div>')
    return page(
        '<div class="eb">08 · Interface</div>'
        '<h2 style="margin-top:3mm">The density <span class="accent">'
        'contract</span></h2>'
        '<div class="hr-ink" style="margin-top:5mm"></div>'
        f'<div class="cols3" style="margin-top:5mm">{cols}</div>'
        '<div class="note"><p class="sm" style="margin:0">A row is exactly '
        '<strong>2 × padding + one line box</strong>. The padding is derived '
        'from the row height and the type size, and the build fails if they '
        'stop agreeing — which is how a "28px" row quietly becomes 34px.</p>'
        '</div>',
        "08 · Interface")


def quickref():
    rows = "".join(
        f'<tr><td>{k}</td><td class="n">{v["ratio"]}:1</td></tr>'
        for k, v in M.items())
    return page(
        '<div class="eb">Quick reference</div>'
        '<h2 style="margin-top:3mm">Every value, one page</h2>'
        '<div class="hr-ink" style="margin-top:5mm"></div>'
        '<div class="rail" style="margin-top:4mm">'
        f'<div class="side"><h4>Measured contrast</h4>'
        f'<table><tbody>{rows}</tbody></table></div>'
        '<div class="main"><h4>Shape</h4><p class="sm">'
        f'{T["shape"]["surface"]} holds content · {T["shape"]["control"]}px '
        f'you press · {T["shape"]["floating"]}px floats.</p>'
        '<div class="hr"></div><h4>Never</h4>'
        '<ul class="sm" style="padding-left:4mm">'
        '<li>a retired colour</li><li>a linked font service</li>'
        '<li>opacity as a hover state</li><li>box-shadow at any elevation</li>'
        '<li>a bare @media (max-width)</li>'
        '<li>a logo image without the align-self guard</li></ul></div></div>',
        "Quick reference")


PAGES = [cover(), contents_stub(),
         divider("02", "Colour", ["The palette", "Measured contrast"]),
         palette(),
         divider("03", "Typography", ["The stack", "Scale", "Setting rules"]),
         typography(),
         divider("08", "Interface", ["Density", "States", "Elevation"]),
         density_page(),
         quickref()]


def renumber(doc):
    secs = list(re.finditer(r"<section.*?</section>", doc, re.S))
    out, last = [], 0
    for i, m in enumerate(secs):
        s = m.group(0)
        # the cover carries no number, but it still has a placeholder to clear
        n = "" if i == 0 else str(i + 1)
        s = re.sub(r'(<div class="folio"><span>[^<]*</span>'
                   r'<span>[^<]*</span><span>)[^<]*(</span>)',
                   lambda mm, v=n: mm.group(1) + v + mm.group(2), s)
        out.append(doc[last:m.start()] + s)
        last = m.end()
    return "".join(out) + doc[last:]


def fill_contents(doc):
    """Built from the folios themselves, so it cannot drift."""
    entries = []
    for m in re.finditer(r"<section.*?</section>", doc, re.S):
        s = m.group(0)
        if "divnum" in s:
            continue
        fo = re.search(r'<div class="folio"><span>[^<]*</span>'
                       r'<span>([^<]*)</span><span>([^<]*)</span>', s)
        h = re.search(r"<h2[^>]*>(.*?)</h2>", s, re.S)
        if not fo or not h or fo.group(1) in ("Cover", "Contents"):
            continue
        title = re.sub(r"<[^>]+>", "", h.group(1)).strip()
        entries.append((fo.group(1), title, fo.group(2)))
    rows = "".join(
        f'<tr><td style="font-family:var(--mono);font-size:6pt;'
        f'color:var(--muted)">{html.escape(sec)}</td>'
        f'<td>{html.escape(t)}</td><td class="n">{p}</td></tr>'
        for sec, t, p in entries)
    return doc.replace('<div class="toc" style="flex:1"></div>',
                       f'<div class="toc" style="flex:1">'
                       f'<table><tbody>{rows}</tbody></table></div>', 1)


def main():
    doc = ("<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">"
           f"<title>{html.escape(T['brand'])} — Brand Book "
           f"{T['version']}</title><style>"
           + FONTS + "\n"
           + CSS.replace("@import url('fonts-embedded.css');", "")
           + PAGE_CSS + "</style></head><body>"
           + "".join(PAGES) + "</body></html>")
    doc = renumber(doc)
    doc = fill_contents(doc)
    assert "__N__" not in doc, "a placeholder folio survived renumbering"
    out = ROOT / "out" / f"{T['slug']}-brand-book-{T['version']}.html"
    out.write_text(doc, encoding="utf-8")
    n = len(re.findall(r"<section", doc))
    print(f"{out.name} · {n} pages · {len(doc)} bytes")


if __name__ == "__main__":
    main()
