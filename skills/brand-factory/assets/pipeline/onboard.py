#!/usr/bin/env python3
"""The front door. Turn a pile of uploads into a config you can build from.

    python3 build/onboard.py                       # everything in source/
    python3 build/onboard.py --url https://x.com   # sample the live site too
    python3 build/onboard.py --apply               # write brand.config.json

Three things happen, in this order, and the order is the point:

  1. INVENTORY. What did they actually send, against the intake checklist?
     What is missing is itself information — a company with no written voice
     guide has no voice guide, and that is a finding, not an obstacle.

  2. SAMPLE. Every hex and typeface in the real material, ranked by how
     often it appears. Never ask a client what colours they use. The brand
     as practised and the brand as documented always differ, and the
     practised one is the one they will defend.

  3. DRAFT. A brand.config.json with the sampled values placed in the slots
     they most likely belong to, every guess marked, and the questions that
     the material cannot answer printed as a single batch to take to the
     client.

The draft is a starting point, not an answer. Step 3 guesses; it says so on
every line it guessed. Read docs/02-intake.md before the conversation.

Writes brand.config.draft.json. `--apply` also copies it over
brand.config.json, backing up any existing one first.

Standard library only, plus whatever extract.py needs for PDFs.
"""
import argparse, collections, json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "source"

# ── what we hoped they would send ───────────────────────────────────────
# (label, extensions, essential, why it matters)
WANTED = [
    ("logo, as vector", (".svg", ".ai", ".eps"), True,
     "raster logos cannot be recoloured, resized or checked for clear "
     "space. If all they have is a PNG, that is the first deliverable."),
    ("existing brand book or guidelines", (".pdf", ".indd", ".html", ".htm"), True,
     "even four bad slides tell you what they think their brand is. The "
     "gap between that and reality is most of your value."),
    ("real recent deliverables", (".pptx", ".docx", ".pdf", ".key"), True,
     "the brand as practised. You want three."),
    ("design tokens, CSS or Figma export", (".css", ".json", ".scss", ".sass"), False,
     "what engineering already believes, which often contradicts the "
     "brand book."),
    ("font files", (".woff2", ".woff", ".otf", ".ttf"), False,
     "decides whether you can ship the typeface at all."),
    ("photography or icons", (".jpg", ".jpeg", ".png", ".webp"), False,
     "decides whether imagery needs a rule or a rebuild."),
    ("spreadsheets, data", (".xlsx", ".csv"), False, "rarely brand-bearing."),
]

# ── the questions no file can answer ────────────────────────────────────
# Grouped so they can be asked in one batch. Full versions, with what you
# are really asking and what a bad answer sounds like, in docs/02-intake.md.
QUESTIONS = [
    ("Position", [
        "In one sentence: what do you do, for whom?",
        "What do you refuse to do, that a competitor would say yes to?",
        "Name the three competitors you actually lose deals to — and, if "
        "you can, their brand colours.",
    ]),
    ("What exists", [
        "What in the current identity is untouchable?",
        "What in the current identity embarrasses you?",
        "What gets made most often, and by whom?",
    ]),
    ("Colour", [
        "Does any colour carry legal or contractual weight?",
        "Where does the brand appear at its smallest, and at its largest?",
        "Do you print? Offset, digital, or neither?",
        "Is there a dark mode, or will there be?",
        "Open the tool your team uses most — the AI assistant, the CSS "
        "framework, the slide tool. What colours does it use by default? "
        "(Ask this LAST.)",
    ]),
    ("Type", [
        "Do you own a licence for the typeface you use now?",
        "What is the smallest text you ship, and where?",
        "Do you publish in more than one language? Which scripts?",
        "Does anything need an italic?",
    ]),
    ("Product", [
        "Desktop tool, mobile-first, or both?",
        "What is the densest screen? Show me.",
        "Does anything make a decision on the user's behalf?",
        "What accessibility level do you claim, and has anyone tested it?",
    ]),
    ("Governance", [
        "Who says no?",
        "What happens when someone needs something the system does not have?",
        "Where will this live, and who will run the build?",
    ]),
]

GENERIC_FONTS = {"arial", "helvetica", "helvetica neue", "calibri", "times",
                 "times new roman", "verdana", "tahoma", "segoe ui", "roboto",
                 "courier", "courier new", "georgia", "cambria", "wingdings",
                 "symbol", "arial black", "arial narrow", "aptos", "aptos display"}


# ── colour maths, enough to sort a palette ──────────────────────────────
def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lum(h):
    def f(c):
        c /= 255
        return c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4
    r, g, b = rgb(h)
    return .2126 * f(r) + .7152 * f(g) + .0722 * f(b)


def chroma(h):
    r, g, b = rgb(h)
    return max(r, g, b) - min(r, g, b)


def inventory():
    """What is here, and what is conspicuously not."""
    if not SRC.exists():
        SRC.mkdir(parents=True)
    files = [p for p in SRC.rglob("*") if p.is_file()
             and not p.name.startswith(".")]
    by_ext = collections.Counter(p.suffix.lower() for p in files)

    print(f"inventory · {len(files)} file(s) in source/\n")
    missing_essential = []
    for label, exts, essential, why in WANTED:
        hits = [p for p in files if p.suffix.lower() in exts]
        mark = "have" if hits else ("MISSING" if essential else "none")
        print(f"  {mark:8} {label}")
        if hits:
            for p in hits[:4]:
                print(f"           · {p.name}")
            if len(hits) > 4:
                print(f"           · … and {len(hits) - 4} more")
        else:
            print(f"           {why}")
        if essential and not hits:
            missing_essential.append(label)

    unclaimed = sorted(set(by_ext) - {e for _, exts, _, _ in WANTED
                                      for e in exts})
    if unclaimed:
        print(f"\n  unclassified: {', '.join(x or '(no extension)' for x in unclaimed)}")
    return files, missing_essential


def sample(files, url):
    """Run extract.py and parse what it found."""
    args = [sys.executable, str(ROOT / "build" / "extract.py")]
    args += [str(p) for p in files
             if p.suffix.lower() in (".pdf", ".pptx", ".docx", ".xlsx",
                                     ".css", ".scss", ".json", ".svg",
                                     ".html")]
    if url:
        args += ["--url", url]
    if len(args) == 2:
        print("\nsample · nothing extractable in source/ — skipping")
        return [], []

    print()
    r = subprocess.run(args, capture_output=True, text=True, cwd=ROOT)
    sys.stdout.write(r.stdout)
    if r.returncode:
        print(r.stderr.strip()[:400])
        return [], []

    colours, fonts, mode = [], [], None
    for ln in r.stdout.splitlines():
        if ln.startswith("colours"):
            mode = "c"; continue
        if ln.startswith("typefaces"):
            mode = "f"; continue
        if not ln.startswith("  ") or not ln.strip():
            continue
        m = re.match(r"\s+(#[0-9A-F]{6})\s+(\d+)", ln)
        if mode == "c" and m:
            colours.append((m.group(1), int(m.group(2))))
        elif mode == "f":
            m2 = re.match(r"\s+(.+?)\s{2,}(\d+)\s*$", ln)
            if m2:
                fonts.append((m2.group(1).strip(), int(m2.group(2))))
    return colours, fonts


def draft(colours, fonts):
    """Place sampled values in the slots they most likely belong to.

    Every placement here is a GUESS and is labelled as one in the output
    file. Luminance sorts grounds from inks; chroma separates a brand
    colour from a hairline. Nothing about frequency tells you what a
    colour MEANS, which is what the questions are for."""
    cfg = json.loads((ROOT / "brand.config.json").read_text(encoding="utf-8"))
    guessed = []

    # Two bars, because they answer different questions. 25 is enough to
    # say "this is not a neutral"; a BRAND colour has to be saturated, and
    # at 25 a desaturated grey-blue body-text colour wins the slot on
    # frequency alone — which is exactly what happened the first time this
    # ran against real material.
    chromatic = [(h, n) for h, n in colours if chroma(h) >= 25]
    saturated = [(h, n) for h, n in colours if chroma(h) >= 60]
    lights = [(h, n) for h, n in colours if lum(h) > .75]
    darks = [(h, n) for h, n in colours if lum(h) < .10]

    def put(path, value, note):
        node = cfg
        *head, last = path
        for k in head:
            node = node[k]
        if isinstance(node.get(last), dict):
            node[last]["hex"] = value
        else:
            node[last] = value
        guessed.append(f"{'.'.join(path)} = {value} — {note}")

    if lights:
        put(["color", "ground"], lights[0][0],
            f"lightest frequent colour ({lights[0][1]} hits)")
    if darks:
        put(["color", "ink"], darks[0][0],
            f"darkest frequent colour ({darks[0][1]} hits)")
    pool = saturated or chromatic
    if pool:
        note = (f"most frequent saturated colour ({pool[0][1]} hits)"
                if saturated else
                f"most frequent chromatic colour ({pool[0][1]} hits) — "
                f"NOTHING in the material is strongly saturated, so this may "
                f"be a neutral doing a brand colour's job")
        # Frequency is a weak signal and sometimes an actively wrong one: in
        # a brand book, an accent gets repeated once per page of the section
        # that explains it, and can outrank the real brand colour. When the
        # top candidates are close, say the slot is AMBIGUOUS rather than
        # picking confidently — the same material sampled with and without a
        # companion PDF picked two different winners.
        rivals = [(h, n) for h, n in pool[1:] if n >= pool[0][1] * .5]
        if rivals:
            note += (" — AMBIGUOUS: " + ", ".join(
                f"{h} ({n})" for h, n in [pool[0]] + rivals[:3])
                + " are all plausible on frequency alone. Frequency counts "
                  "mentions, not area, and a brand book repeats an accent "
                  "once per page of the section explaining it. Ask, or "
                  "re-run with --url so colours are weighted by area on the "
                  "live site")
        put(["color", "brand"], pool[0][0],
            note + " — frequency is not meaning, confirm this is the brand "
                   "colour")
        # Accents must be saturated too, and must not repeat a slot that is
        # already filled — the first version offered the body-text grey and
        # the ink colour as "pillars".
        taken = {pool[0][0].upper(), cfg["color"]["ground"]["hex"].upper(),
                 cfg["color"]["ink"]["hex"].upper()}
        extra = [c for c in (saturated or chromatic)
                 if c[0].upper() not in taken][:3]
        if extra:
            cfg["color"]["accents"] = {
                "$comment": cfg["color"]["accents"]["$comment"],
                **{k: {"hex": h, "label": f"PILLAR {i + 1} — NAME IT"}
                   for i, (k, (h, _)) in enumerate(
                       zip(("one", "two", "three"), extra))}}
            guessed.append("color.accents = "
                           + ", ".join(h for h, _ in extra)
                           + " — next chromatic colours by frequency. Accents "
                             "are wayfinding only; delete any that are not.")

    # Everything the old identity used is a retirement candidate. This is
    # the single most valuable field in the file: it is what makes old
    # material start failing the checker.
    keep = {cfg["color"][k]["hex"].upper() for k in
            ("ground", "ink", "brand", "muted", "surface", "line",
             "brand_on_dark")}
    keep |= {v["hex"].upper() for v in cfg["color"].get("accents", {}).values()
             if isinstance(v, dict) and "hex" in v}
    retire = {f"sampled_{i + 1}": h for i, (h, n) in enumerate(colours[:14])
              if h.upper() not in keep and chroma(h) >= 25}
    if retire:
        cfg["color"]["retired"] = {
            "$comment": "EVERY hex the old identity used. The checker fails "
                        "on these. Sampled from the supplied material — keep "
                        "the ones you are retiring, delete the ones you are "
                        "keeping, and add any the material did not contain.",
            **retire}
        guessed.append(f"color.retired = {len(retire)} sampled colours — "
                       f"review every one")

    real = [(f, n) for f, n in fonts if f.lower() not in GENERIC_FONTS]
    if real:
        cfg["type"]["$sampled_typefaces"] = [f for f, _ in real[:6]]
        guessed.append(
            "type.$sampled_typefaces = " + ", ".join(f for f, _ in real[:4])
            + " — NOT placed in the stack. A typeface goes in only after "
              "`build/measure_fonts.py` and a licence check; these names are "
              "what the material uses, which is a different question.")
    if any(f.lower() in GENERIC_FONTS for f, _ in fonts):
        guessed.append("generic system fonts appear in the material, which "
                       "usually means a face was never embedded and every "
                       "reader saw a substitute. Worth raising early.")

    cfg["$draft"] = {
        "warning": "Generated by build/onboard.py from sampled material. "
                   "Every value below marked in $guessed is a GUESS placed "
                   "by frequency and luminance, not by meaning. Confirm each "
                   "one before building, and answer the questions onboard.py "
                   "printed.",
        "$guessed": guessed,
    }
    return cfg, guessed


def main():
    ap = argparse.ArgumentParser(
        description="Inventory uploads, sample what they use, draft a config.")
    ap.add_argument("--url", help="the client's live site, sampled too")
    ap.add_argument("--apply", action="store_true",
                    help="also copy the draft over brand.config.json "
                         "(the existing one is backed up)")
    a = ap.parse_args()

    files, missing = inventory()
    colours, fonts = sample(files, a.url)
    cfg, guessed = draft(colours, fonts)

    out = ROOT / "brand.config.draft.json"
    out.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")

    print(f"\ndraft · {out.name}")
    if guessed:
        for g in guessed:
            print(f"  guess  {g}")
    else:
        print("  nothing could be placed — the material yielded no values")

    if a.apply:
        live = ROOT / "brand.config.json"
        if live.exists():
            bak = ROOT / "brand.config.backup.json"
            bak.write_text(live.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"\n  previous config backed up to {bak.name}")
        live.write_text(out.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"  applied to brand.config.json")

    print("\nask the client · one batch, in this order")
    for group, qs in QUESTIONS:
        print(f"\n  {group}")
        for q in qs:
            print(f"    · {q}")
    print("\n  Full versions — what you are really asking, and what a bad "
          "answer sounds like — in docs/02-intake.md.")

    if missing:
        print(f"\nblocking · cannot finish without: {', '.join(missing)}")
    print("\nnext")
    print("  1. answer the questions above with the client")
    print("  2. edit brand.config.draft.json — every $guessed line is a "
          "decision you have not made yet")
    print("  3. copy it to brand.config.json, then: python3 build/all.py")
    print("\nThe build will fail on contrast below the floor and on any "
          "colour too close\nto a palette you listed in avoid_palettes. "
          "That is it working. Move the\ncolour rather than the threshold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
