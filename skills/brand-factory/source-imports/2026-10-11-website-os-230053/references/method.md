# The method

Why this is built the way it is. Read once; the SOP assumes it.

---

## The problem this solves

A brand book is a PDF full of pictures. An AI cannot read pictures of
rules, so when someone asks a model to "make a deck in our brand", it
approximates — and the approximation is close enough that nobody catches
it until forty decks later, when the brand has quietly drifted.

The fix is not a better PDF. It is to make the brand **machine-readable
and self-checking**, so that:

- every value lives in one file
- the book, the stylesheet, the rules and the AI skill are all *generated*
  from that file and cannot disagree with it
- the build **fails** on the things nobody catches by reading

That last point is the whole design. Everything else follows.

---

## Principle 1 · One source, everything generated

```
brand.config.json          you edit this
        │
        ▼
    tokens.json            measured, derived, checked
        │
        ├──► tokens.css    the website and product
        ├──► BRAND.md      what an AI reads
        ├──► brand book    what people read
        └──► the skill     what an agent installs
```

Nothing downstream is hand-edited. The moment you fix a hex "just in the
CSS", you have two sources of truth and one of them is wrong.

**Test for it:** run the build twice and compare hashes. A generator that
appends rather than replaces looks fine on the first run and grows on the
second. `build/all.py` does this automatically and fails on drift. It
caught a one-byte-per-run leak in a real build.

---

## Principle 2 · Measure, never assert

A brand book that says "AA compliant" and a brand book that says
"**8.62:1**, measured" are different documents. The second one can be
checked, argued with, and trusted.

Everything measurable is measured:

| Claim | How it is established |
|---|---|
| Contrast | computed to WCAG 2.1 relative luminance, checked against floors |
| "This palette is ours" | RGB distance against palettes you named |
| "A dense row is 28px" | derived: `2 × padding + one line box`, and verified |
| "This typeface fits" | rendered and measured, not chosen from a specimen |
| "The page fits on A4" | rendered in a browser and measured |

Anything not measurable — whether the margin is right, whether the voice
sounds like you — is a judgement, and the book says so rather than
dressing it as a rule.

---

## Principle 3 · The failures that matter are silent

This is the part most systems miss. Ranked by how long they survive
undetected:

**A fallback font.** You link a font service; the page renders in whatever
the browser has. It looks correct to the person who made it, because their
machine has the font installed. Everyone else sees something else. In the
build this originated from, the font CDN was unreachable from the build
container, `document.fonts.check()` returned `true` anyway, and four
typeface candidates were compared in a specimen where all four rendered
identically. **Self-host, and probe for it.**

**A clipped page.** `.page` is `overflow:hidden`, so a page whose content
exceeds the sheet loses the bottom of it. Nothing errors. The PDF just
omits a row. Two pages in a real 100-page book had been clipped for three
versions.

**A synthesised italic.** Many geometric sans faces have no italic. Ask
for one and the browser slants the roman. It ships. Six of these survived
a full typeface migration, on a page two spreads from the rule
prohibiting them.

**A one-hex-two-meanings collision.** A success green identical to a
brand pillar's green. Both are "correct"; together they are meaningless.

**A metric that does not hold.** A "28px" row that renders at 34px,
because padding fell outside `min-height` and the row never set its own
font size. The number in the book was true and the number on screen was
not.

Every one of these is now a build gate. The gate is worth more than the
document.

---

## Principle 4 · Fewer colours, checked against the obvious ones

Two brands look alike when their **chromatic** colours are close. RGB
distance under about 40 reads as the same colour to someone who is not
holding a swatch.

The reason so many recent brands look generated is not imitation. It is
that everyone reaches for the same obvious values — the defaults of the
CSS framework they use, or of the AI product their market lives in. You
do not need to have copied anything to land 15 units from Tailwind's
cyan.

So `avoid_palettes` takes your competitors' hexes and your market's
default tooling, and the build **fails** under the threshold.

One metric does not serve every part of a palette, so the check runs three
regimes — each one learned by getting it wrong against a real palette:

- **Near-black is never compared.** Everyone's ink reads as black, tinted
  or not. A navy-black 23 units from a neutral near-black is not a borrowed
  colour, and flagging it is how a check earns a reputation for crying wolf.
- **Near-white is compared only when both sides are deliberately warm.**
  Every near-white sits within ~20 units of every other, so plain distance
  flags all of them and says nothing. Cool is the default — every
  framework's lightest grey is cool. A *warm* ground is a choice, so two
  warm papers 19 apart are the same paper. This is a real collision the
  check was blind to until the near-black false positive sent me back to it.
- **Everything else needs chroma on one side.** A hairline grey matching
  someone's hairline grey is not a finding.
- **Semantic fills are exempt entirely.** A danger red *should* look like a
  danger red. Warning yellows occupy a narrow band every system shares.
  Flagging those is the metric being naive.

All of that is pinned to nine cases in `build/selftest.py`, which runs on
every build. A metric with no fixture drifts, and a drifting metric is worse
than no metric because people still quote it.

What actually prevents a generated look: few colours, small areas of
them, a true ground, and no indigo-to-violet gradient anywhere.

---

## Principle 5 · Say what is prohibited, and why

"Use Cobalt for primary actions" is guidance. "**Never** white on the
warning colour — 1.60:1" is a rule, and an agent can enforce it.

Every prohibition in a generated system carries its reason, because a
rule whose reason is missing gets overridden by the first person with a
deadline. Compare:

> Don't use box-shadow.

> No `box-shadow`, at any elevation. Separation comes from surface,
> border weight and a scrim. An Ink hairline is 19:1 against white — it
> separates harder than a soft shadow, and unlike a shadow it survives
> print, a 1x display and a dark ground.

The second one wins the argument without you in the room.

---

## Principle 6 · Some things are editorial, and the build should say so

Not everything is fixable by tooling, and pretending otherwise produces
worse work.

In the book this came from, 23 of 100 pages fill 70% or less. Those pages
carry 150–250 words on A4 landscape. Enlarging the type would contradict
the type scale the book itself defines. Merging pages would break its own
conventions. **The honest fix is writing more**, and the right move was to
measure it, report it, and leave it alone.

A build that quietly papers over a content problem produces a document
that looks finished and is not.

---

## Principle 7 · The values diverge; the book does not, unless you write it

This is the system's real limit and it was measured, not guessed. Two brands
were configured with nothing in common — warm paper ground against white,
forest-black against navy-black, terracotta against cobalt, a serif display
against a geometric sans, 18px radius against 0, line-height 1.6 against
1.4, A4 portrait against landscape, 700ms motion against 400ms. Both built
clean. Then the two books were compared:

| | shared between the two brands |
|---|---|
| Book markup skeleton | **99.0%** |
| Book prose | **94.1%** |
| `tokens.css` lines | 66% |
| `BRAND.md` lines | 62% |

Read that honestly. **Every value diverged and almost nothing else did.**
The palettes are unrecognisable as relatives; the books are twins.

Two of those numbers are fine. `tokens.css` and `BRAND.md` share their
*structure* — class definitions, section headings — which is what makes them
machine-readable, and their values are entirely different. The 99% markup
figure is also expected: the starter is a chassis, nine pages proving the
pipeline works, and a chassis is supposed to be the same chassis.

**94% shared prose is not fine.** The chassis ships sentences, and those
sentences will appear verbatim in every book anyone generates from it unless
they are replaced. A client who has seen one book built this way will
recognise the next one.

So the same rule applies as everywhere else here: make it measurable and
make it fail. `build/divergence.py` counts how many of the chassis's own
sentences survive in your book, reading them out of the generator so it
cannot drift. `book.status` in the config decides what happens:

| `book.status` | Behaviour |
|---|---|
| `starter` | reports only — the shipped default |
| `draft` | warns above 25% |
| `final` | **fails the build** above 25% |

Set it to `final` before handover. What the build then refuses to do is call
a recoloured chassis a finished brand book.

What it still cannot judge: whether your replacement prose is any good, and
whether the layouts are yours. A book that clears the threshold can still be
nine pages in someone else's composition. That is what
[`05-contents.md`](05-contents.md) is for — the hundred-page inventory, and
the reminder that a third of it generates itself and the rest is writing.

---

## What this is not

- **Not a design system.** It produces the *rules and the book*. Your
  components still need building.
- **Not a replacement for a designer.** It removes the arguing about
  hexes so the judgement can go somewhere useful.
- **Not automatic taste.** Configure it with three bad colours and it
  will measure them precisely and generate a consistent book full of
  them.

---

Next: [`01-sop.md`](01-sop.md) — install and run.
