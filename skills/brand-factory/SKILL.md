---
name: brand-factory
description: Build a machine-readable, self-checking brand system for a company, and generate the installable brand Skill that keeps an AI on-brand afterwards. Use when someone asks to create, rebuild, document, audit or version a brand book, brand guidelines, design tokens, a visual identity or a brand Skill — including "turn our brand book into something an AI can follow", "our decks keep drifting off-brand", "generate tokens from our brand", "does our palette look generated" or "build a brand book from these files". One config file generates the book, the stylesheet, the tokens, the written rules and a per-brand Skill, with gates that fail on what a reader cannot see — a font that fell back, a clipped page, a synthesised italic, a colour indistinguishable from a competitor's or a framework default. Also audits an existing identity on measured contrast, typeface fit and originality. Not for logo design.
license: MIT
metadata:
  version: "1.0"
  requires: "python>=3.9, node>=18, playwright, npm registry access"
---

# Brand Factory

A brand book is a PDF full of pictures. An AI cannot read pictures of rules,
so when someone asks a model for "a deck in our brand" it approximates, and
the approximation is close enough that nobody notices until the brand has
drifted across forty decks.

This builds the brand as **one config file that generates everything else**,
with gates that fail the build on the failures a reader cannot see.

Use it to create a brand system, rebuild an existing one, or audit an
identity against measurements.

## Start here

```bash
python3 scripts/init.py <project-dir>
cd <project-dir>
npm install playwright && npx playwright install chromium
python3 build/all.py
```

`init.py` scaffolds a project and never overwrites anything. `build/all.py`
produces a nine-page book for a fictional company, renders it in Chromium,
measures every page, and ends with `verify ok` and `selftest ok`. Confirm
that before changing a single value: it proves the toolchain works, so any
later failure is about the brand and not the setup.

Playwright is not optional. It is how the build catches a clipped page and a
font that silently fell back. Without it you have a generator, not a system.

## How the work runs

1. **Collect.** Everything the company already has goes in `source/` — an
   old brand book as PDF or HTML, decks, documents, a stylesheet, a Figma
   token export, font files, the logo. `references/intake.md` has the full
   list of 13 and why each matters. What is missing is itself a finding.
2. **Onboard.** One command inventories, samples and drafts:

   ```bash
   python3 build/onboard.py --url <their-site>
   ```

   It reports what they sent against the checklist and what is missing,
   samples every hex and typeface out of the material, writes
   `brand.config.draft.json` with the sampled values placed in the slots
   they most likely belong to — **every guess labelled** — and prints the
   questions the files cannot answer as one batch. Against a real 100-page
   brand book it recovered the ground, the ink, the brand colour, three
   accents and all four typefaces unprompted.

   Never skip to asking. The brand as practised and the brand as documented
   always differ, and the practised one is what people defend.
3. **Confirm every guess, then fill in `brand.config.json`** — the only file
   anyone edits by hand. Frequency is not meaning: the most-used colour in a
   document is usually the body-text grey, not the brand colour.
4. **Build and read the failures** — `python3 build/all.py`. Expect to fail
   two or three times. That is the tool working.
5. **Write the content** — `references/contents.md` is the page-by-page
   inventory of a finished 100-page book, which third of it generates
   itself, and the `BRAND.md` outline. Gather material before writing a
   page; a page written first becomes a good layout with thin copy in it.
6. **Generate and test the brand Skill** —
   `python3 build/skill.py && python3 build/skill_lint.py`, then run its
   checker on work it has not seen. The skill ships eight working surfaces
   (below) plus `BRAND.md`, the tokens and its own checker.
7. **Package** — `python3 build/package.py` writes `dist/`.

`references/sop.md` is the full twelve-step procedure, each step with what
you do, what you check, and what goes wrong.

## The pipeline

| Step | Script | Fails when |
|---|---|---|
| 1 | `build/fonts.py` | a named font file is not in the npm package |
| 2 | `build/tokens.py` | contrast below floor · a colour too near an avoided palette · density that does not add up |
| 3 | `build/css.py` | — |
| 4 | `build/brandmd.py` | — |
| 5 | `build/book.py` | a folio placeholder survives |
| 6 | `build/verify.js` | a clipped page · a fallback font · a shadow · a fake italic |
| 7 | `build/selftest.py` | a gate stops firing on a bad file, or fires on a good one |
| 8 | `build/divergence.py` | more than 25% of the starter's own prose survives, once `book.status` is `final` |
| 9 | `build/skill.py` | — |
| 10 | `build/skill_lint.py` | description over 1024 chars · bad name · unfilled placeholder |
| 11 | `build/package.py` | — |

`build/all.py` runs 1–5 **twice**, compares hashes, then runs 6, 7 and 8. Three
tools are run by hand: `build/onboard.py` first of all, `build/extract.py` if
you want the sampling without a draft, and `build/measure_fonts.py` when
choosing a typeface.

## What the brand Skill can build

The generated skill carries eight surfaces, each a working file that already
passes its own checker — an agent starts from the closest one and deletes
what it does not need.

| Template | Surface | Geometry |
|---|---|---|
| `deck.html` | slides, any presentation | 254 × 143mm, 16:9 |
| `web.html` | website, landing page | responsive |
| `document.html` | report, advisory paper, memo | A4 portrait |
| `proposal.html` | proposal, quote, SOW | A4, 5 pages in decision order |
| `brief.html` | creative or project brief | A4, one page |
| `onepager.html` | leave-behind, sell sheet | A4, one side |
| `card.html` | business card | 85 × 55mm, bleed and safety guides |
| `social.html` | social posts | 1200² · 1200 × 628 · 1080 × 1350 |

Print and screen are separate type scales and neither is a fallback for the
other. A surface that is not here gets **added** to `skill-template/`, not
improvised once in one file — and `build/selftest.py` fails the build if any
shipped template stops passing the checker.

## Rules

- **Never hand-edit anything in `out/`.** The next build discards it. A fix
  that must persist belongs in a generator.
- **Never raise a threshold to make a check quiet.** Move the colour.
- **Never let a model state a number a script can measure.** Contrast,
  colour distance, line box, row height come from the build. A model that
  reports a contrast ratio is guessing, and it will be close enough to be
  believed and wrong enough to fail an audit.
- **A new rule needs a check**, and the check needs an entry in
  `build/selftest.py` that makes it fire. A gate nobody has watched fail may
  have stopped working months ago.
- **Some things are editorial.** 250–400 words per A4 landscape page; under
  150 the page is visibly empty and no gate can see it. Say so rather than
  enlarging the type.
- **The starter is a chassis, not a book.** Measured: two brands with nothing
  in common — opposite palette temperature, serif against geometric sans, 0
  against 18px radius, portrait against landscape — come out of it 99%
  identical in markup and 94% identical in wording. Only the values diverge.
  Set `book.status` to `final` before handover and `build/divergence.py`
  fails the build while more than 25% of the chassis's own sentences survive.
  Replacing them is the work; `references/contents.md` is the inventory to
  write against.

## Choosing a typeface

```bash
python3 build/measure_fonts.py Manrope Outfit "Plus Jakarta Sans"
```

Reports line box, set width and whether a real italic file exists. **Line
box is the number that breaks things**: a face more than ~10% off your
display face disagrees with every row height in the density scale. For a
second script this is not optional — an Arabic face 36% taller than the
Latin one turns every 28px row into a clipped row the moment the locale
switches.

## References

Read the one the task needs; they are independent.

| File | For |
|---|---|
| `references/method.md` | why it is built this way. Six principles. |
| `references/sop.md` | the twelve steps, start to handover. |
| `references/intake.md` | what to collect, and the 23 questions. |
| `references/anatomy.md` | what each file does and when it runs. |
| `references/failures.md` | thirteen real silent failures and the gates they caused. |
| `references/contents.md` | what actually goes in the book and `BRAND.md`. |
| `references/prompts.md` | six paste-in prompts: discovery, audit, palette, type, sections, adversarial review. |

## Environment

Python 3.9+ and Node 18+. The typefaces come from `@fontsource` npm
packages, so the npm registry must be reachable once; nothing else needs the
network. If Chromium cannot launch, `build/verify.js` says so and points at
`npx playwright install chromium` or `CHROMIUM_PATH=…` — do not skip the
step, because it is the only one that renders and measures.

Where a host has no shell, the pipeline cannot run. Use `references/` as
guidance and `references/prompts.md` for the judgement steps, and say which
numbers are unmeasured rather than estimating them.
