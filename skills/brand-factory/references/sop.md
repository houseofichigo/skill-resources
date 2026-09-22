# SOP — from an empty folder to a delivered brand system

Twelve steps. The first eleven take about two days with a cooperative
client; step 12 never really ends.

Every step says **what you do**, **what you check**, and **what goes
wrong**.

---

## Prerequisites

```bash
python3 --version     # 3.9 or later
node --version        # 18 or later
npm --version
```

Then, once, in the repo:

```bash
npm install playwright
npx playwright install chromium
```

Playwright is not optional. It is how the build renders the book and
catches the failures nobody sees by reading source. Without it you have a
generator, not a system.

---

## Step 1 · Clone and prove it runs

```bash
git clone <this-repo> my-brand && cd my-brand
python3 build/all.py
```

**Check:** it ends with `verify ok`. You now have a nine-page book for a
fictional company in `out/`. Open it.

**Goes wrong:** `npm install failed` — you are offline, or behind a proxy
that blocks the npm registry. The fonts come from npm; nothing else needs
the network.

---

## Step 2 · Collect the material

Work through [`02-intake.md`](02-intake.md), Part 1. Put everything in
`source/`.

**Check:** you have a vector logo and three real recent deliverables. If
the logo is a PNG, that is now the first deliverable and the timeline
moves.

**Goes wrong:** you accept a beautiful template without checking whether
its typeface is embedded and licensed. Run the `unzip` check in the intake
doc *now*, not in week six.

---

## Step 3 · Onboard: inventory, sample, draft

One command does all three, and it is the front door for a client who is
doing this themselves rather than a consultant working through the list:

```bash
python3 build/onboard.py --url https://client.com
```

It reports what they sent against the intake checklist and what is
conspicuously missing, samples every hex and typeface out of the real
material, writes `brand.config.draft.json` with the sampled values placed in
the slots they most likely belong to — **every guess labelled as a guess** —
and prints the questions the files cannot answer as one batch to take to the
client.

Run it on an existing brand book (PDF *or* HTML), a deck, a stylesheet or a
Figma token export. Against a real 100-page brand book it recovered the
ground, the ink, the brand colour, three accents and all four typefaces
without being told any of them.

`--apply` copies the draft over `brand.config.json`, backing up what was
there. `build/extract.py` is still available on its own if you only want the
sampling.

**Check:** the top five colours against what the brand book says. The gap
between them is your opening slide with the client. Then read every
`$guessed` line in the draft — each one is a decision you have not made yet.
Frequency is not meaning: the most-used colour in a document is often the
body-text grey.

**Goes wrong:** you trust the brand book. The brand as practised and the
brand as documented always differ, and the practised one is the one
clients will defend.

---

## Step 4 · Ask the questions

[`02-intake.md`](02-intake.md), Part 2. Twenty-three questions, six
groups, in order.

**Check:** you have three real competitor names with hexes, one sentence
of positioning, and a name for who says no.

**Goes wrong:** you ask before looking at the material, and get
aspirations instead of answers. Step 3 comes first for a reason.

---

## Step 5 · Fill in the config

Edit `brand.config.json`. Nothing else, ever.

Three fields decide more than the rest combined:

- `color.retired` — **every hex the old identity used.** This is what
  stops old material leaking into new work; the checker fails on them.
- `avoid_palettes.sets` — competitors, plus whichever framework or AI tool
  your market's tooling defaults to.
- `type.display.has_italic` — get this wrong and you will ship fake
  italics for a year.

**Check:** `python3 build/tokens.py`. Read every line. It will tell you
what fails and refuse to write anything downstream.

**Goes wrong:** the originality check fires. **This is the build
working.** Do not raise the threshold. Move the colour.

---

## Step 6 · Choose the typefaces on measurement

```bash
python3 build/measure_fonts.py Manrope Outfit "Plus Jakarta Sans"
```

Renders each candidate against your display face and reports line box, ink
height and whether a real italic exists.

For a second script — Arabic, Hebrew, CJK — this step is not optional. A
face whose line box is 50% taller than your Latin one breaks every row
height in your density scale the moment the locale switches.

**Check:** the chosen face is within ~10% of your display face's line box,
and you know whether it has an italic.

**Goes wrong:** you choose from a specimen page. Specimens are set large
and loose. Your product is set in 28px table rows.

---

## Step 7 · Build, and read the failures

```bash
python3 build/all.py
```

It runs everything twice, compares hashes, then renders the book and
checks it. Expect to fail here two or three times. That is the point.

**Check:** `idempotent`, then `verify ok`, then `selftest ok`.

**Goes wrong, in order of likelihood:**

| Message | Meaning |
|---|---|
| `contrast: … is 3.9:1, floor 4.5:1` | change the colour, not the floor |
| `originality: … is 15.1 from …` | your colour is someone else's |
| `density.dense: stated 28px, computes to 34px` | the numbers never agreed |
| `NOT IDEMPOTENT` | a generator appends where it should replace |
| `CLIPPED PAGES: p3:+53px` | a page overflows and is losing its bottom |
| `fonts not distinct` | a face did not load and you are seeing a fallback |
| `SILENT  BOX-SHADOW` | a gate stopped working. Fix the gate before the brand. |

---

## Step 8 · Write the book's content

The starter book is a chassis, not a book: nine pages against the hundred a
finished one runs to. **[`05-contents.md`](05-contents.md) is the
inventory** — what the ten sections contain, page by page, which pages
generate themselves, and what order to build in. Read it before writing
anything.

Add sections by writing a function in `build/book.py` that returns
`page(...)` and appending it to `PAGES`. Folios and the contents adjust
themselves.

**Order matters.** Gather the material first, then write the page. A page
written before its content exists becomes a beautiful layout with thin
copy in it, every time.

**Check:** `python3 build/all.py` after each section. The gate catches a
clipped page the moment you create one, not forty pages later.

**Goes wrong:** you hand-edit the generated HTML. The next build discards
it. If you need a fix to persist, it belongs in a generator.

---

## Step 9 · Build the skill

```bash
python3 build/skill.py
```

Produces `out/<slug>-brand/` from the templates in `skill-template/`:

```
<slug>-brand/
├── SKILL.md                  name, and the description that decides
│                             when an agent reaches for it
├── BRAND.md                  the rules, generated
├── references/
│   ├── tokens.json           machine-readable
│   ├── tokens.css            the stylesheet
│   ├── fonts-embedded.css    base64, for offline
│   └── fonts/                the woff2 files
├── templates/                eight ready-to-fill surfaces:
│                             deck · web · document · proposal
│                             brief · onepager · card · social
└── scripts/check.py          the checker, shipped with it
```

`BRAND.md` is the file that actually governs an agent's output, and the
generator only writes a ~700-word skeleton. A working one runs 6,000–7,000
words of rules-with-reasons; [`05-contents.md`](05-contents.md), Part 2, has
the outline and the standard a line has to meet.

**Check:** `python3 build/skill_lint.py`. The `description` field has a
**1024-character limit** that lives in the installer, not the file — a
real skill grew past it over six revisions and simply would not install.
The lint is there because of that.

**Goes wrong:** the folder name does not match the `name` in `SKILL.md`.
Some installers care.

---

## Step 10 · Test the skill on work you have not done

Install it, then ask an agent for something real — a deck, a proposal — and
run the checker on what comes back.

```bash
python3 scripts/check.py out/generated-deck.html
```

**Check:** it passes. If it does not, the skill is missing a rule, not the
agent being careless.

**Goes wrong:** you test on an example already in the skill. Test on
something new, in the awkward format the client actually uses.

---

## Step 11 · Package and hand over

```bash
python3 build/package.py
```

Produces, in `dist/`:

| File | For |
|---|---|
| `<slug>-brand-skill.zip` | an AI — unzip into a skills folder |
| `<slug>-brand-book.html` | people — self-contained, fonts embedded |
| `<slug>-brand-book.pdf` | sending |
| `BRAND.md` | pasting into a tool that takes no skills |
| `tokens.json` / `tokens.css` | engineering |
| `fonts.zip` | whoever builds the site |
| `README.md` | which file is for whom |

**Check:** unzip the skill into a clean folder and run its own checker
from there. A package that only works in the folder it was built in is not
a package. This has caught a stylesheet referencing four font files that
were not in the zip.

---

## Step 12 · Keep it alive

A brand system decays when the first person needs something it does not
have and improvises.

- **The rule:** if the thing you need is not in the system, it gets
  *added to the system* — not improvised once in one file and forgotten.
- **Every new rule gets a check, and every check gets an entry in
  `build/selftest.py`** that makes it fire. A gate nobody has watched fail
  is a gate that may have stopped working months ago.
- Run `build/all.py` in CI — `.github/workflows/build.yml` does it,
  including the clean-unzip test from step 11. A pull request that breaks contrast or clips a
  page should not merge.
- Version deliberately. `3.1 → 3.2` should name what changed and what was
  retired, and old hexes go into `color.retired` so old material starts
  failing.

---

## The whole thing, once you know it

```bash
git clone <repo> my-brand && cd my-brand
npm install playwright && npx playwright install chromium
python3 build/extract.py source/*            # what is actually there
$EDITOR brand.config.json                    # the only file you edit
python3 build/all.py                         # build, twice, then verify
python3 build/skill.py && python3 build/skill_lint.py
python3 build/package.py                     # dist/
```
