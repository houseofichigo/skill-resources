#!/usr/bin/env python3
"""What is actually in the client's material — not what they say is.

    python3 build/extract.py source/*.pdf source/*.pptx --url https://x.com

Pulls every hex and font name out of supplied files and a live page, and
ranks them by how often they appear. The brand as practised and the brand
as documented always differ; this is how you find out by how much.
"""
import collections, json, pathlib, re, subprocess, sys, warnings, zipfile
warnings.filterwarnings("ignore")

HEX = re.compile(r"#([0-9A-Fa-f]{6})\b")
SRGB = re.compile(r"srgbClr val=\"([0-9A-Fa-f]{6})\"")
TYPEFACE = re.compile(r"typeface=\"([^\"+][^\"]*)\"")


def from_ooxml(p):
    """pptx / docx / xlsx are zips of XML."""
    hexes, fonts = collections.Counter(), collections.Counter()
    try:
        with zipfile.ZipFile(p) as z:
            for n in z.namelist():
                if not n.endswith(".xml"):
                    continue
                x = z.read(n).decode("utf-8", "ignore")
                hexes.update("#" + m.upper() for m in SRGB.findall(x))
                fonts.update(TYPEFACE.findall(x))
    except Exception as e:
        print(f"  ! {p.name}: {e}")
    return hexes, fonts


FAMILY = re.compile(r"font-family\s*:\s*([^;}\n]+)", re.I)
GENERIC = {"sans-serif", "serif", "monospace", "system-ui", "ui-sans-serif",
           "ui-monospace", "cursive", "fantasy", "inherit", "initial", "unset",
           "-apple-system", "blinkmacsystemfont"}


def from_text(p):
    """html, css, scss, svg, json — read as text.

    A brand book handed over as HTML, or a stylesheet, or a Figma token
    export, is the most direct evidence there is: the values are literal
    rather than compressed into a stream. Treating these as zips (which an
    earlier version did) threw the richest source away with `File is not a
    zip file`."""
    hexes, fonts = collections.Counter(), collections.Counter()
    try:
        t = p.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"  ! {p.name}: {e}")
        return hexes, fonts
    hexes.update("#" + m.upper() for m in HEX.findall(t))
    # #abc shorthand expands; plenty of stylesheets use it
    for m in re.finditer(r"#([0-9A-Fa-f]{3})\b", t):
        a, b, c = m.group(1).upper()
        hexes["#" + a + a + b + b + c + c] += 1
    for m in FAMILY.finditer(t):
        for fam in m.group(1).split(","):
            fam = fam.strip().strip("'\"")
            if (fam and not fam.startswith("var(")
                    and fam.lower() not in GENERIC):
                fonts[fam] += 1
    return hexes, fonts


def from_pdf(p):
    hexes, fonts = collections.Counter(), collections.Counter()
    try:
        import pypdf
        r = pypdf.PdfReader(str(p))
        for page in r.pages:
            res = page.get("/Resources", {})
            f = res.get("/Font", {})
            if hasattr(f, "items"):
                for _, v in f.items():
                    bf = v.get_object().get("/BaseFont")
                    if bf:
                        fonts[str(bf).lstrip("/").split("+")[-1]] += 1
    except Exception as e:
        print(f"  ! {p.name}: pypdf — {e}")
    # colours: pdftotext will not give them; sample the raw stream
    try:
        import zlib
        blob = p.read_bytes()
        raw = blob.decode("latin-1", "ignore")
        # colour operators usually sit inside Flate streams
        for m in re.finditer(rb"stream\r?\n(.*?)endstream", blob, re.S):
            try:
                raw += zlib.decompress(m.group(1)).decode("latin-1", "ignore")
            except Exception:
                pass
        for m in re.finditer(r"([\d.]+) ([\d.]+) ([\d.]+) (?:rg|RG)", raw):
            vals = [float(x) for x in m.groups()]
            if all(0 <= v <= 1 for v in vals):
                hexes["#" + "".join(f"{round(v*255):02X}" for v in vals)] += 1
    except Exception:
        pass
    return hexes, fonts


def from_url(url):
    hexes, fonts = collections.Counter(), collections.Counter()
    js = """
    const {chromium}=require('playwright');(async()=>{
      const b=await chromium.launch();const p=await b.newPage();
      await p.goto(process.argv[1],{waitUntil:'networkidle',timeout:45000});
      const r=await p.evaluate(()=>{const c={},f={};
        for(const e of document.querySelectorAll('*')){
          const s=getComputedStyle(e);
          const area=e.getBoundingClientRect().width*e.getBoundingClientRect().height;
          for(const prop of ['color','backgroundColor','borderTopColor']){
            const v=s[prop]; if(!v||v==='rgba(0, 0, 0, 0)')continue;
            const m=v.match(/\\d+/g); if(!m||m.length<3)continue;
            const hex='#'+m.slice(0,3).map(x=>(+x).toString(16).padStart(2,'0')).join('').toUpperCase();
            c[hex]=(c[hex]||0)+(prop==='backgroundColor'?Math.max(1,area/1000):1);}
          const fam=s.fontFamily.split(',')[0].replace(/["']/g,'').trim();
          if(fam)f[fam]=(f[fam]||0)+1;}
        return {c,f};});
      console.log(JSON.stringify(r)); await b.close();})();
    """
    tmp = pathlib.Path("/tmp/_extract.js")
    tmp.write_text(js)
    r = subprocess.run(["node", str(tmp), url], capture_output=True, text=True)
    if r.returncode:
        print(f"  ! {url}: {r.stderr.strip()[:200]}")
        return hexes, fonts
    d = json.loads(r.stdout)
    hexes.update({k: round(v) for k, v in d["c"].items()})
    fonts.update(d["f"])
    return hexes, fonts


def main(argv):
    url = None
    if "--url" in argv:
        i = argv.index("--url")
        url = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]

    H, F = collections.Counter(), collections.Counter()
    for a in argv:
        p = pathlib.Path(a)
        if not p.exists():
            continue
        print(f"reading {p.name}")
        ext = p.suffix.lower()
        if ext == ".pdf":
            h, f = from_pdf(p)
        elif ext in (".html", ".htm", ".css", ".scss", ".sass", ".svg",
                     ".json", ".txt", ".md", ".xml"):
            h, f = from_text(p)
        else:
            h, f = from_ooxml(p)
        H.update(h)
        F.update(f)
    if url:
        print(f"reading {url}")
        h, f = from_url(url)
        H.update(h)
        F.update(f)

    print("\ncolours, by weight — compare this against what the guidelines say")
    for hexv, n in H.most_common(18):
        print(f"  {hexv}  {n}")
    print("\ntypefaces, by frequency")
    for fam, n in F.most_common(12):
        print(f"  {fam:32} {n}")
    print("\nNote: a PDF exported from a browser embeds subset Type 3 fonts, "
          "so family\nnames there are unreliable. The --url pass is the "
          "trustworthy one for type.")
    print("\nPaste the ones that matter into brand.config.json. Every hex "
          "the OLD identity used\ngoes into color.retired — that is what "
          "stops old material leaking into new work.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
