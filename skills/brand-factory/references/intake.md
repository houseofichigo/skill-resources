# Intake — what to collect, and what to ask

Two halves. **Collect** is what the client uploads before you start.
**Ask** is the conversation you have once you have looked at it.

Do them in that order. Questions asked before you have seen the material
get answered aspirationally; questions asked after get answered against
something on the screen.

---

## Part 1 · What to upload

Ask for everything in this list. Expect about half of it. What is missing
is itself information — a company with no written voice guide has no voice
guide, and that is a finding, not an obstacle.

### Essential — you cannot start without these

| # | Item | Why it is essential | Accept |
|---|---|---|---|
| 1 | **The logo, as vector** | Raster logos cannot be recoloured, resized or checked for clear space. If they only have a PNG, that is the first deliverable. | `.svg` `.ai` `.eps` `.pdf` |
| 2 | **The existing brand book or guidelines**, however bad | Even a 4-slide PDF tells you what they think their brand is. The gap between that and reality is most of your value. | `.pdf` `.pptx` `.indd` export |
| 3 | **Three real, recent deliverables** — a deck, a proposal, a document | The brand as practised, not as documented. These two always differ. | anything |
| 4 | **The website**, as a URL | The only surface with live colours you can sample rather than guess. | URL |

### Strongly wanted

| # | Item | Why |
|---|---|---|
| 5 | Any existing design tokens, CSS, Figma export or Tailwind config | Tells you what engineering already believes. Often contradicts the brand book. |
| 6 | The product, if there is one — screenshots or access | Sections 08 and 09 are unwritable without it. |
| 7 | The master presentation template | Reveals the real type scale, and whether fonts are licensed or embedded. |
| 8 | Font files or licences | Decides whether you can ship the typeface at all. See the trap below. |
| 9 | Photography and icon sets | Decides whether imagery needs a rule or a rebuild. |
| 10 | A customer-facing document in each language they sell in | A brand that ships in Arabic and has never set Arabic has a gap it does not know about. |

### Useful, rarely supplied

11. Competitor names — you need three, and they need to be the ones the
    client loses deals to, not the ones they admire.
12. Anything they have said publicly about positioning: a pitch deck, an
    About page, a funding announcement.
13. Whoever owns the brand internally. A system with no owner is a system
    that decays in a quarter.

### The font trap, which catches nearly everyone

If they hand you a template with a beautiful custom typeface, **check
whether it is actually embedded and licensed before you build on it.**

```bash
unzip -o template.pptx -d /tmp/t
ls /tmp/t/ppt/fonts/                       # empty = nothing embedded
grep -o 'embedTrueTypeFonts[^/]*' /tmp/t/ppt/presentation.xml
```

An empty `ppt/fonts/` and no `embedTrueTypeFonts` flag means the face is
installed on their designer's machine and nowhere else. Every deck you
build will silently substitute for everyone who opens it. Say so early —
it is an awkward conversation at week one and a catastrophic one at week
six.

---

## Part 2 · What to ask

Twenty-three questions in six groups. Work through them in order; later
answers depend on earlier ones.

For each: **what you are really asking**, and **what a bad answer sounds
like**. A bad answer is not a reason to move on. It is the signal to ask
the same thing a different way.

### Group A · Position — before any colour is discussed

**A1. In one sentence: what do you do, for whom?**
*Really asking:* can they say it without a list? If it takes three
sentences the brand will take thirty pages.
*Bad answer:* "We're an end-to-end platform for digital transformation."
That is a category, not a company.

**A2. What do you refuse to do, that a competitor would say yes to?**
*Really asking:* for the edge of the brand. A brand with no refusal has no
shape, and this single answer usually writes the positioning line.
*Bad answer:* "Nothing, we're flexible." Push: "What was the last project
you turned down?"

**A3. Name the three competitors you actually lose deals to.**
*Really asking:* whose palette and voice yours must not resemble. These
go straight into `avoid_palettes` and the build measures against them.
*Bad answer:* naming aspirational peers. Ask who the client compared them
to in the last lost deal.

**A4. Which of your clients would you want on the cover, and why that one?**
*Really asking:* who they think they are for. The answer often contradicts
the answer to A1.

### Group B · What already exists

**B1. What in the current identity is untouchable?**
*Really asking:* for the fixed point. Usually a mark, sometimes a founder's
decision. Establish it now, because it constrains everything.

**B2. What in the current identity embarrasses you?**
*Really asking:* the real brief. People will describe this more honestly
than they will describe what they want.

**B3. Who made the current one, and when?**
*Really asking:* whether there is a relationship to manage, and whether the
palette predates the product.

**B4. Show me the last thing you made that felt right.**
*Really asking:* for evidence over adjectives. "Clean and modern" means
nothing; the artefact means something.

**B5. What gets made most often, and by whom?**
*Really asking:* where to spend the effort. If they produce forty decks a
month and two documents a year, the deck template is the deliverable and
the document template is a courtesy.

### Group C · Colour, with the trap named

**C1. Does any colour carry legal or contractual weight?**
A partner brand, a certification mark, a regulated safety colour. Find out
before you retire anything.

**C2. Where does the brand appear at its smallest, and at its largest?**
*Really asking:* the contrast range you must survive. A colour that works
on a website and fails on a 12pt printed footer is not a brand colour.

**C3. Do you print? Offset, digital, or neither?**
*Really asking:* whether CMYK matters. If nobody has printed anything in
two years, say the CMYK values are indicative and move on rather than
faking a colour build.

**C4. Is there a dark mode, or will there be?**
*Really asking:* whether every colour needs a second measured value. Decide
now; retrofitting dark mode doubles the palette work.

> **The trap.** Ask this last, after they have described the colours they
> like: *"Open the tool your team uses most — the AI assistant, the CSS
> framework, the slide tool. What colours does it use by default?"*
>
> Half of all recent brands are within measuring distance of Tailwind's
> defaults or of whichever AI product their market lives in. They did not
> copy; they reached for the same obvious colours. This is what
> `avoid_palettes` exists to catch, and it is the single most valuable
> thing in the build. Run it before you present anything.

### Group D · Type

**D1. Do you own a licence for the typeface you use now?**
*Really asking:* whether you can ship it. See the font trap above. A "yes"
needs a document, not a memory.

**D2. What is the smallest text you ship, and where?**
*Really asking:* the real constraint. A face that sings at 88px and falls
apart in a 13px table row is the wrong face for a product company.

**D3. Do you publish in more than one language? Which scripts?**
*Really asking:* whether you need a second face, and whether the density
system survives it. Arabic, Hebrew, Thai and CJK all change line heights,
and a face with a line box 50% taller than your Latin one breaks every row
height you set.

**D4. Does anything need an italic?**
*Really asking:* an unglamorous question that eliminates candidates. Many
geometric sans faces ship no italic at all. If they publish in French,
italic is not optional — it is required for titles and foreign terms.

### Group E · Product, if there is one

**E1. Desktop tool, mobile-first, or both?**
Different defaults, not different breakpoints. Decide which is primary.

**E2. What is the densest screen? Show me.**
*Really asking:* for the row count that sets the density scale. "A table"
is not an answer; forty-one rows is.

**E3. Does anything in the product make a decision on the user's behalf?**
*Really asking:* whether you need provenance, uncertainty and human
checkpoints in the system. Any product with a model in it does.

**E4. What accessibility level do you claim, and has anyone tested it?**
*Really asking:* whether AA is a commitment or a hope. European public
buyers ask in writing. Claiming untested conformance is worse than
claiming less.

### Group F · Governance, which decides whether any of this survives

**F1. Who says no?**
*Really asking:* for a name. A brand system with no arbiter is a
suggestion.

**F2. What happens when someone needs something the system does not have?**
*Really asking:* whether there is a route to extend it. Without one, people
improvise once, in one file, and it is never seen again.

**F3. Where will this live, and who will run the build?**
*Really asking:* whether the toolchain will be used or admired. If nobody
will run a command, generate once and hand over files.

---

## Part 3 · Turning answers into config

| Answer | Goes into |
|---|---|
| A1, A2 | `positioning` |
| A3 | `avoid_palettes.sets` — add their hexes |
| B1 | whatever you must not change |
| B2 | the change list, and the "what changed and why" page |
| C1–C4 | `color`, and whether you need a dark variant |
| D1–D4 | `type`, and `locales` |
| E1–E3 | density scales, and whether Sections 08 / 09 apply |
| E4 | `a11y.target` |
| Old palette | `color.retired` — every hex, so old material fails the check |
| Banned words | `voice.banned` |

Then: `python3 build/all.py`. Read what it tells you. If the originality
check fails, you have found the most useful thing in the engagement before
you have designed anything.
