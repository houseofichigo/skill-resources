# The failure catalogue

Every one of these happened in a real 100-page build. They are here
because none of them announce themselves — each looked correct to the
person who made it. The build gates exist because of this list, not the
other way round.

Ordered by how long each survived undetected.

---

## 1 · The fallback font · survived a whole typeface migration

**What happened.** A specimen page compared four typeface candidates. The
build container could not reach the font CDN, so all four rendered in the
same fallback face. `document.fonts.check()` returned `true` anyway — it
reports whether text can be rendered, not whether *your* font arrived.

**Why nobody caught it.** The page looked fine. The four candidates looked
similar because they *were* the same font.

**The fix.** Self-host every face. Probe by measuring the rendered width
of a string in each family and asserting they differ:

```js
d.style.fontFamily = `'${family}'`;
widths[family] = d.getBoundingClientRect().width;
// all equal  ⇒  a fallback is in use
```

**The variant that came back.** Three batches later, an Arabic face was
added to the config, documented in the book, and **absent from the page** —
the `@font-face` block had been baked into a build base and was never
re-synced. Latin glyphs would have fallen back silently, so the probe
needs its own Arabic string. Now it has one.

---

## 2 · Clipped pages · survived three versions

**What happened.** `.page` is `overflow:hidden`. Two pages exceeded the
sheet and simply lost their bottoms. The PDF omitted a row of content.

**Why nobody caught it.** Nothing errors. The page looks complete because
what is missing is not there to be missed.

**The fix.**

```js
document.querySelectorAll('section').forEach((s, i) => {
  if (s.scrollHeight > s.clientHeight) fail(`p${i} clipped`);
});
```

**It kept firing, which is the point.** It caught the contents page 419px
over after entries were added, then 4px over after seven more, then a
starter book on its very first build.

---

## 3 · The synthesised italic · survived, two pages from the rule banning it

**What happened.** The display face has no italic. Six accent words were
written as inline `font-style:italic`. The browser slanted the roman and
shipped it — on pages two spreads from the rule prohibiting exactly that.

**The fix.** `font-synthesis-weight:none; font-synthesis-style:none` on
`body`, and a gate that fails on any element whose computed style is
italic while resolving to a face with no italic.

---

## 4 · One hex, two meanings

**What happened.** `--success` was `#008558`. So was the Build pillar. On
any screen showing both, one green meant "Build owns this" and "this
passed".

**The fix.** Walk the colour tree and fail on any hex appearing under two
paths. Then decide which meaning survives — here, neither: a success
colour was unnecessary, because nothing needs to shout that it is fine.

---

## 5 · A metric that did not hold

**What happened.** The density scale specified a 28px dense row. It
rendered at 34px: padding fell outside `min-height`, and the row never set
its own font size, so it inherited 16px body text.

**Why it matters.** The book stated a number that was true in the document
and false on the screen. A contract that does not hold is not a contract.

**The fix.** Derive padding from the row height and line box rather than
stating both, and fail when they disagree:

```
pad_y = (row − text × line_height) / 2
assert |2 × pad_y + line − row| ≤ 1
```

---

## 6 · The non-idempotent generator

**What happened.** A generator spliced content between two markers. The
strip removed the marker but left the newline the next insert added, so
the file grew one byte per build.

**Why it matters.** Not the byte. It means the generator is *appending*,
and one day it will append something visible.

**The fix.** Run the whole build twice and compare hashes. `build/all.py`
does this and refuses to continue on drift.

---

## 7 · The skill that would not install

**What happened.** `SKILL.md`'s `description` grew by a clause per
revision. At 1,646 characters it exceeded the installer's 1,024 limit. The
build knew nothing, because the limit lives in the installer.

**The fix.** `build/skill_lint.py`. Validate the frontmatter, the name
format, the folder name and the required files before packaging.

---

## 8 · The package that only worked where it was built

**What happened.** The skill shipped a `fonts-linked.css` referencing four
font files that were not in the zip — the folder had been populated by
hand and went stale when a face was added. Separately, the checker
hardcoded a path that only exists in the repo.

**The fix.** Generated assets are copied by the build, never by hand. And
the last step of packaging is: unzip into a clean folder and run the thing
from there. Both bugs were found that way, one of them twice.

---

## 9 · The regex that was blind to most of its input

**What happened.** The font checker used `font-family\s*:\s*([^;}"']+)`.
Stopping at the first quote makes every *quoted* family name invisible —
which is most of them. `font-family:'Comic Sans MS'` passed.

**Why it matters.** A check that silently passes is worse than no check,
because it buys confidence.

**The fix.** `[^;}]+`, then split and strip quotes. And test every checker
against deliberately broken input:

```bash
python3 build/check.py tests/deliberately-awful.html   # must exit 1
```

---

## 10 · The metric that was too naive to be useful

**What happened.** The originality check compared every colour against
every avoided colour, and fired on near-blacks, hairline greys and pure
white. Everyone's near-black is near everyone else's.

**The fix.** Two exemptions, both learned by getting it wrong:

- **Neutrals.** Only chromatic colours, and a *tinted* ground, discriminate.
- **Semantic fills.** A danger red *should* look like a danger red.

A check nobody trusts gets switched off, so a false positive costs more
than a missed one.

---

## 11 · The check that only looked at rule blocks

Found by writing a deliberately bad file to prove the checker worked.

**What happened.** The synthesised-italic check scanned every `{...}` rule
block for `font-style:italic` on the display face. A test file carrying
`<h1 style="font-family:var(--display);font-style:italic">` passed clean.
An inline style attribute is not a rule block, and an agent asked to write
HTML reaches for `style="..."` far more often than for a stylesheet.

**The fix.** Scan rule blocks *and* `style="..."` attributes.

**The lesson.** A check you have never seen fail is not a check. Every gate
in this repo has a file that makes it fire; write that file when you write
the gate, not when you are wondering why nothing has failed in a month.

---

## 12 · The false positive that would have trained people to ignore it

**What happened.** The same checker warned `no font-synthesis:none` on both
shipped templates. Both link `tokens.css`, which sets
`font-synthesis-weight:none` and `font-synthesis-style:none` on `body`. The
guard was present; the checker could not see into the linked file.

**The fix.** A file that links `tokens.css` inherits the guard.

**The lesson.** This is the mirror of every other entry here. A checker that
cries wolf on its own shipped templates is a checker whose output people
learn to skim — and then the real failure scrolls past with the noise. A
false positive costs more than a missed one.

---

## 13 · The metric that flagged a black for being black

Found by running the finished check against a real 12-colour palette rather
than the placeholder.

**What happened.** The originality check exempted neutrals by measuring
distance from pure white and pure black. A navy near-black — `#0A0E27`,
chroma 29 — is 42 units from pure black, so it was not exempt, and it landed
23 units from another brand's neutral near-black. Flagged. Both colours read
as black to everyone who is not holding a swatch.

Worse, the same rule made the check **blind in the other direction**: it
required chroma ≥ 25 before comparing anything, and a warm paper ground has
a chroma of about 10. So a warm off-white sitting 18 units from another
brand's warm off-white — a genuine collision, and the exact one that forced
a real palette's previous version to be retired — was never compared at all.

**The fix.** Judge comparability by luminance and temperature, not by
distance from the extremes. Near-black: never compared. Near-white: compared
only when both sides are deliberately warm. Everything else: chroma on one
side.

**The lesson.** Two of them, and the second is the one worth keeping. The
first is that a metric validated only on the placeholder data is not
validated. The second is that a false positive and a false negative are
usually the *same* bug seen from two sides — the rule that wrongly included
the near-black was the rule that wrongly excluded the warm paper. Fixing the
noise found the blind spot. Nine cases are now pinned in
`build/selftest.py`, seven of them from real palettes.

---

## 14 · The book that was the same book

Found by being asked a direct question — "can you confirm this won't build
exactly the same brand book for everyone?" — and measuring instead of
answering.

**What happened.** Two configs were written to have nothing in common: warm
paper against white, terracotta against cobalt, a serif display against a
geometric sans, 18px radius against 0, portrait against landscape. Both
built clean. The two books were **99.0% identical in markup and 94.1%
identical in wording.**

Every gate in the repo passed both. Contrast is measurable, a clipped page
is measurable, a fallback font is measurable — "this is the same document
with different colours in it" is not, so nothing saw it.

**The fix.** `build/divergence.py`, which counts how many of the chassis's
own sentences are still in the generated book, and `book.status` in the
config: `starter` reports, `draft` warns, `final` fails above 25%. The
sentences are read out of `book.py` itself rather than kept in a second
list, so rewriting one stops it being counted — which is correct, because a
rewritten sentence is no longer the chassis's.

**The lesson.** Every other entry here is a failure of correctness. This one
is a failure of *identity*, and it is the more dangerous kind, because a
correct document that is indistinguishable from someone else's still passes
every check and still fails the client. A build that measures only
correctness will let you ship a perfect copy of the starter.

---

## The pattern

Every failure here is **silent**. None of them throw. All of them look
correct to whoever made them.

So the rule is: **if a thing can be measured, measure it in a gate, and
make the gate fail the build.** A warning is a thing people scroll past.
