# What actually goes in it

The rest of this documentation tells you how to run the machine. This tells
you what to put through it.

It exists because of a measurable gap. What the repo builds out of the box,
against the real 100-page system it was extracted from:

| | starter | the real one | |
|---|---|---|---|
| Book pages | 9 | **100** | the chassis demonstrates three sections; a book needs ten |
| `BRAND.md` | 728 words | **6,951** | what an agent reads is where the leverage is |
| Sections with content | 3 | 10 | |

(Templates were the third gap on this list and are now closed: eight ship
with the repo. See Part 3.)

Nothing in that gap is machinery. It is all content, and content is the
part no build gate can supply. So: the inventory below, taken page by page
off a finished book, is the shape you are aiming at.

---

## Part 1 · The book, page by page

Ten sections, two front-matter spreads, one back. Each section opens with a
**dark divider** carrying its number at 150pt and a two-column list of what
is inside — that page is generated, costs nothing, and is what makes a book
feel like a book rather than a slide dump.

| § | Pages | What the pages are |
|---|---|---|
| — | 1 | **Cover.** |
| — | 2 | **Contents**, generated from the folios. Two pages, balanced by a minimax split so neither runs short. |
| 00 | 4 | **Foundation.** What changed and why (the version diff — put it first, it answers the only question anyone has). The house. The offer in one page. How to read this book. |
| 01 | 8 | **Logo.** The mark · the lockup · one artwork on two grounds · clear space · minimum sizes · the container shape · misuse · partner lockups. |
| 02 | 7 | **Colour.** The palette · the one brand colour, alone on a page · the accent system · tints and surfaces · proportion (how much of each, by area) · **measured contrast** · what is retired. |
| 03 | 7 | **Typography.** The stack · one page per face · the scale · the accent treatment · setting rules · what not to do. |
| 04 | 5 | **Voice.** Principles · the word family · banned language · tone by audience · naming conventions. |
| 05 | 8 | **Composition.** The signature layout · signature moves · rules not boxes · dark-page rhythm · grid · imagery · what breaks it. |
| 06 | 15 | **Applications.** One page per surface you actually ship — website, deck anatomy, deck layouts, documents, proposals, stationery, social, merchandise, signage. **The biggest section, and the one clients use.** |
| 07 | 4 | **Governance.** Do and don't · tokens and assets · the machine-readable spec · migrating from the old version. |
| 08 | 20 | **Interface.** States · the interaction ramp · elevation without shadow · the density contract · focus · motion · components · overlays · conversation · time. Skip the whole section if there is no product. |
| 09 | 8 | **Experience.** Principles · the journey · the error taxonomy · working with a model (provenance, uncertainty, human checkpoints) · accessibility · locale and RTL. |
| — | 2 | **Quick reference.** Every value on one page, and the rules that break most often. The two pages people actually print. |

Ten dividers on top of that, one per section.

### How to read that table

- **Sections 08 and 09 are optional and huge.** 28 of 100 pages. If the
  client has no product, a complete book is ~70 pages and you should not
  pad it to 100.
- **Section 06 scales with the client, not the brand.** Ask question B5 in
  the intake — what gets made most often — and give each answer a page.
  Fifteen is what one consultancy needed; a hardware company needs
  different fifteen.
- **The front three pages and the back two carry the most weight per page.**
  "What changed and why" and the quick reference are the pages people open
  a second time.

### Which pages generate themselves

Roughly a third, and they are free once the generator exists:

| Generated from tokens | Written by a person |
|---|---|
| the palette page and every swatch | why this colour |
| the measured contrast table | proportion and where it fails |
| the type scale | the setting rules |
| the density table | what density is for |
| the interaction ramp | the state semantics |
| every divider, folio and the contents | everything in 00, 04, 06, 07 |

Write the generated ones first. They fill 30 pages in an afternoon and give
you a book to react to, which is a much better place to write from than an
empty file.

### The one rule about page count

**250–400 words per A4 landscape page at this type scale.** Under 150 and
the page is visibly empty; the build cannot see this and will happily ship
it. In the source book, 23 of 100 pages fall below that line. Count words
before you write the layout, not after.

---

## Part 2 · `BRAND.md` — what the agent reads

This is the highest-leverage file in the system and the one most likely to
be under-built. The book persuades people; `BRAND.md` is what actually
governs output, because it is what a model has in context when it makes
your next deck.

The generator produces a skeleton of about 700 words. A working one runs
**6,000–7,000**. The difference is entirely rules-with-reasons.

Structure, in this order — the order matters, because a model reading top
to bottom should be unable to make a wrong choice early:

```
# <Brand> — brand rules
    one paragraph: what this file is, and that it overrides habit

## The company            positioning, what it refuses, the vocabulary
## Colour                 every hex with its ROLE, then the ramp,
                          then measured contrast, then what is retired
### Rules                 prohibitions, each with its number
## Typography             the stack, the scale, the rules
## Logo                   clear space, minimums, misuse, both grounds
## Layout                 the signature structure and its proportions
## Images                 what a photograph may and may not be
## Icons                  stroke, corner, size, and what is not an icon
## Slides                 the layouts by name, and when each applies
## Voice                  principles, word family, banned list, tone
## The frameworks, named  your own IP, spelled exactly right
## Before you present     the checklist a human runs
## Interface …            three sections, only if there is a product
## Experience …           only if a model makes decisions for a user
```

### What makes a line in this file work

Every rule carries its reason **and a number**, because a rule whose reason
is missing loses to the first person with a deadline:

> **Weak.** Don't use box-shadow.
>
> **Works.** No `box-shadow`, at any elevation. Separation comes from
> surface, border weight and a scrim. An ink hairline is 19:1 against
> white — it separates harder than a soft shadow, and unlike a shadow it
> survives print, a 1× display and a dark ground.

The numbers come from `out/tokens.json`. Never type one from memory into
this file; if you need a value that is not in the tokens, that is a signal
the tokens are incomplete.

### The description field

`SKILL.md`'s `description` decides whether an agent reaches for the skill at
all, and it has a **hard 1024-character limit** enforced by the installer,
not by the file. A real skill grew past it over six revisions and simply
would not install. It must name: the brand, its aliases and domain, the
surfaces it covers, and — critically — **what is retired**, so an agent
holding old material knows this file supersedes it.

---

## Part 3 · The templates

Eight ship with the repo, covering the surfaces almost every company
produces:

| Template | Surface |
|---|---|
| `deck.html` | slides, 16:9, exports at PowerPoint proportions |
| `web.html` | website, landing page |
| `document.html` | report, advisory paper, memo |
| `proposal.html` | proposal, quote, SOW |
| `brief.html` | creative or project brief |
| `onepager.html` | leave-behind, sell sheet |
| `card.html` | business card, with bleed and safety guides |
| `social.html` | three feed sizes |

Every one is a working file that passes the checker, and `build/selftest.py`
fails the build if any of them stops passing.

That covers the generic surfaces. **What it cannot cover is the two or three
artefacts specific to how the company works**, and those come from intake
question **B5, what gets made most often, and by whom.** One consultancy's
eight looked like this:

| Template | Why it existed |
|---|---|
| `web.html` | the site |
| `document.html` | reports and advisory papers |
| `deck.html` | the surface produced most often |
| `brochure.html` | the thing that gets printed |
| `catalogue.html` | the product list, updated quarterly |
| `collateral.html` | one-pagers and leave-behinds |
| `use-case-blueprint.html` | a repeated internal artefact |
| `validation-dossier.html` | a repeated client artefact |

The last two are the point. **Five of the eight are generic; three are
specific to how that company works.** Those three are what stop people
improvising, and you can only learn them by asking B5 and looking at what
comes back.

Each template is a real, fillable surface that passes `scripts/check.py` —
not a swatch page. If it does not pass its own checker, it is teaching the
agent the wrong thing.

---

## The order to build in

1. Generated pages — 02, 03, 08 structure. An afternoon, ~30 pages.
2. `BRAND.md` to full length. This is what governs output; do it before
   the book is pretty.
3. Section 06, driven by B5. The section clients actually use.
4. Templates, one per surface in 06.
5. 00, 04, 07 — the written sections. Last, because by now you know what
   the system actually is.
6. Quick reference. Only possible once everything else exists.

Sections 01 and 05 sit wherever the logo work lands, which is usually
outside this repo's control.
