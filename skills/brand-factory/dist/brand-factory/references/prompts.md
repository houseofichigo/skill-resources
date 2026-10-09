# Prompts

Six paste-in prompts for the steps a script cannot do. Each is written to be
pasted whole into a fresh conversation with the bracketed parts filled in.


---

# Prompt 0 · Discovery

Use after you have read the supplied material, not before. Attach
everything from `source/`.

The point of running this through a model rather than off a printed list is
follow-ups: a model that has read the deck can notice that the answer to
A1 contradicts the cover slide, and ask about it in the room.

---

```
You are helping me run a brand discovery session with a client. I have
attached everything they sent: [list what you attached].

Read all of it first. Then work through the interview below with me, one
question at a time. Do not send me the whole list — ask the question, wait
for the answer I bring back from the client, and then decide what to ask
next.

For each question you ask, tell me in one line what we are really trying
to establish, so I can steer if the client goes sideways.

After each answer:
- If the answer contradicts something in the attached material, say so and
  quote the contradiction. This is the most useful thing you can do.
- If the answer is a category rather than a company ("end-to-end platform
  for digital transformation"), tell me it is unusable and give me one
  concrete rephrasing to ask instead.
- If the answer is complete, move on. Do not summarise or affirm it.

The questions, in order:

GROUP A — POSITION
A1  In one sentence: what do you do, for whom?
A2  What do you refuse to do, that a competitor would say yes to?
A3  Name the three competitors you actually lose deals to.
A4  Which of your clients would you want on the cover, and why that one?

GROUP B — WHAT ALREADY EXISTS
B1  What in the current identity is untouchable?
B2  What in the current identity embarrasses you?
B3  Who made the current one, and when?
B4  Show me the last thing you made that felt right.
B5  What gets made most often, and by whom?

GROUP C — COLOUR
C1  Does any colour carry legal or contractual weight?
C2  Where does the brand appear at its smallest, and at its largest?
C3  Do you print? Offset, digital, or neither?
C4  Is there a dark mode, or will there be?
C5  Open the tool your team uses most — the AI assistant, the CSS
    framework, the slide tool. What colours does it use by default?
    (Ask this LAST in the group, after they have described what they like.)

GROUP D — TYPE
D1  Do you own a licence for the typeface you use now?
D2  What is the smallest text you ship, and where?
D3  Do you publish in more than one language? Which scripts?
D4  Does anything need an italic?

GROUP E — PRODUCT (skip the group if there is no product)
E1  Desktop tool, mobile-first, or both?
E2  What is the densest screen? Show me.
E3  Does anything in the product make a decision on the user's behalf?
E4  What accessibility level do you claim, and has anyone tested it?

GROUP F — GOVERNANCE
F1  Who says no?
F2  What happens when someone needs something the system does not have?
F3  Where will this live, and who will run the build?

When all groups are done, produce two things and nothing else:

1. A one-page brief: the positioning sentence in their words, the fixed
   points, the change list, and the three competitors with their hexes if
   we have them.

2. A list of every unresolved item, each marked as either BLOCKING (we
   cannot fill brand.config.json without it) or OPEN (we can proceed and
   decide later).

Do not propose colours, typefaces or taglines. That is not this step.
```

---

## What good output looks like

The brief is short, and the contradictions are the valuable part. If the
model comes back with no contradictions between what the client said and
what they sent, either the client is unusually self-aware or the model did
not read the attachments — check by asking it to quote the smallest text
size in the deck.


---

# Prompt 1 · Audit what is actually there

Run `build/extract.py` first. It samples every hex, font name and image out
of the supplied files and the live site, and it does not guess:

```bash
python3 build/extract.py source/*.pdf source/*.pptx --url https://client.com
```

Then paste its output into this prompt along with the client's existing
brand book. The script tells you what is used; this step tells you what
that means.

---

```
Below is the output of a tool that extracted every colour, typeface and
image reference from a client's real, recent material and their live
website. I have also attached their official brand guidelines.

[paste extract.py output]

Compare the two. Produce exactly four things:

1. THE GAP. A table: what the guidelines specify, what the material
   actually uses, and how far apart they are. Order it by how often the
   divergent value appears, not by how large the divergence is — a slightly
   wrong grey on every page matters more than a badly wrong accent on one.

2. THE UNDOCUMENTED PALETTE. Colours that appear repeatedly in real work
   and are in no guideline. These are usually the honest brand. Say where
   each one appears and guess why it was introduced (a chart library
   default, a stock template, one designer's preference).

3. THE DEAD VALUES. Colours and faces in the guidelines that appear
   nowhere in the material. These are candidates for retirement, and every
   one of them belongs in `color.retired` in the config.

4. THE ONE SLIDE. The single most uncomfortable finding, stated in one
   sentence a client will accept. Not "your brand is inconsistent" —
   something like "the grey in your body copy is a different grey on every
   surface, and none of them is the one in your guidelines."

Rules:
- Do not compute contrast ratios or colour distances. The build measures
  those; anything you state I have to verify anyway.
- Do not propose a new palette. You are describing what exists.
- If the extracted data is too thin to support a claim, say the data is
  thin. A confident reading of four PDFs is worse than an honest "not
  enough material".
```

---

## What to do with it

- Every dead value → `color.retired` in `brand.config.json`. That is what
  makes old material start failing the checker.
- Every undocumented colour that is *load-bearing* → either adopt it
  deliberately or retire it deliberately. Leaving it undecided is how it
  survives the rebrand.
- "The one slide" opens your presentation. It buys you the rest of the
  engagement.


---

# Prompt 2 · Palette

This is the prompt most likely to be misused. A model cannot tell you
whether a colour is good, and it cannot compute a contrast ratio you should
trust. What it is genuinely useful for is the *shape* of a palette — how
few colours, what each one is allowed to do, and what to cut.

So the loop is: model proposes, build measures, model revises.

```
model proposes hexes  →  python3 build/tokens.py  →  read the failures
        ▲                                                    │
        └────────────────────────────────────────────────────┘
```

Never skip the middle step, and never raise the threshold to make the
middle step quiet.

---

```
I am building a brand palette that has to survive an automated check. Help
me choose the colours; a script will measure them.

CONTEXT
Positioning: [one sentence]
Where the brand appears smallest: [e.g. 11px table labels, 8pt print footer]
Where it appears largest: [e.g. 88px web hero, exhibition banner]
Dark mode: [yes / no / later]
Print: [offset / digital / no]
Colours that cannot change: [hexes, and why]
Retired: [every hex from the old identity]

MUST NOT RESEMBLE — these are measured by RGB distance, threshold 40:
[competitor 1 name]: [hexes]
[competitor 2 name]: [hexes]
[competitor 3 name]: [hexes]
The default palette of the tooling our market uses: [hexes — Tailwind
defaults, the AI product they live in, whatever it is]

THE SHAPE I NEED
- ground        the page. Everything sits on it.
- ink           all body text, and the dark surface
- brand         ONE colour. Every CTA, link and focus ring.
- brand_on_dark the brand colour where it must sit on ink
- muted         secondary text, light surfaces only
- surface       hover, disabled, quiet fills
- line          hairlines
- accents       wayfinding only, never a button, never body copy.
                [n] of them, for: [what they distinguish]
- semantic      fills that mean a human must act. As few as I can defend.

GIVE ME
For each slot: a hex, and one sentence on what it is allowed to do and
what it is not.

Then, separately:
- Which slot you are least confident about, and what would resolve it.
- Any colour in my list above that is doing two jobs, and which job it
  should lose.
- Whether I need a success colour at all, given the accents I listed. Argue
  the case for dropping it.

CONSTRAINTS
- Do not state contrast ratios or colour distances. I measure those. If you
  think a pairing is marginal, say "this may fail the 4.5:1 floor" and let
  the build decide.
- Neutrals do not need to be original. Everyone's near-black is near
  everyone else's. Spend the originality on the chromatic colours.
- No indigo-to-violet gradient, and no palette whose brand colour is a
  mid-blue at around #3B82F6. Both read as machine-generated in 2026,
  whatever their provenance.
- Fewer is the goal. If you can do it with one accent, do it with one.
```

---

## Then run it

```bash
$EDITOR brand.config.json     # paste the hexes in
python3 build/tokens.py       # read every line
```

## Reading the failures

| Failure | What to do |
|---|---|
| `contrast: … is 3.9:1, floor 4.5:1` | darken the foreground, or use an existing token that already passes. **Adding a colour to fix a contrast problem is usually wrong.** |
| `originality: … is 15.1 from tailwind_default/#0891B2` | move the colour. Not the threshold. |
| `collision: #008558 means accents.two and semantic.success` | one of the two meanings has to go. Usually the semantic one. |

Feed the failures back to the model verbatim and ask for a revision of only
the failing slots. Changing the whole palette to fix one hex loses the work
you already validated.

## The one that will annoy you

The originality check fires on colours nobody copied. A teal at 15 units
from Tailwind's `cyan-600` was arrived at independently — and it is still a
teal your market's eye has been trained on by every dashboard it has ever
seen. The check is doing its job. Move it.


---

# Prompt 3 · Typefaces

A model is good at producing a shortlist with reasons. It is not good at
knowing whether a face has a real italic, what its line box measures, or
whether it is on npm — it will state all three confidently and be wrong
about at least one.

So use it for the shortlist, then measure:

```bash
python3 build/measure_fonts.py Manrope Outfit "Plus Jakarta Sans" Figtree
```

That renders each candidate in a real browser and reports line box, set
width and whether an italic file actually exists in the package.

---

```
Help me shortlist typefaces. I will measure the candidates myself, so give
me reasons rather than measurements.

WHAT IT HAS TO DO
Display: [e.g. 88px web heroes, deck titles, and the whole interface]
Body: [e.g. 15-16px long-form, proposals and reports]
Smallest text shipped: [e.g. 11px table labels]
Densest screen: [e.g. 41-row data table at 28px rows]
Scripts: [Latin only / Latin + Arabic / + CJK …]
Italic needed: [yes / no — and where]
Numerals: [do they need to be tabular? charts, tables, prices?]
Character: [three adjectives, and the one adjective it must NOT be]
Licence: must be self-hostable, open licence, and available on npm as a
@fontsource or @fontsource-variable package.

GIVE ME
Six candidates for the display role, as a table:
| face | npm package | why it fits | what I will dislike about it | italic? |

Then, for the top three, one paragraph each on how it behaves at 11px —
not at 88px. Specimens are set large and loose; my constraint is a table
row.

Then:
- Which one you would pair with which body face, and why the pairing is
  not just "they're both geometric sans".
- Whether a separate body face is warranted at all, or whether one family
  across both roles is the better call here. Argue it.
- For each non-Latin script I listed: two candidates, and a warning about
  which one has the taller line box.

CONSTRAINTS
- Do not tell me x-height, cap height, line box or set width numbers. I
  measure those. State relative expectations ("this runs noticeably taller
  than Inter") and let the tool confirm.
- Do not claim a face has an italic unless you are certain; mark it
  "verify" instead. Fake italics are the single most common silent failure
  in a type migration.
- Variable fonts preferred, one file per script.
- No face whose primary association is a well-known product's brand.
```

---

## Then measure

```bash
python3 build/measure_fonts.py "Candidate One" "Candidate Two"
```

Output looks like:

```
face                          line box   set width   italic
Manrope (reference)              137        1284      no
Outfit                           140        1301      no
Plus Jakarta Sans                136        1268      yes
```

## Reading it

- **Line box** is the number that breaks things. A body face more than
  ~10% off your display face's line box will disagree with every row
  height in your density scale.
- **Italic** is a file on disk or it does not exist. If it says no and you
  need italics, either change the face or change the rule — the build
  bans synthesised italics and will fail the book if one appears.
- **Set width** tells you whether copy fitted to one face will still fit
  when you swap. A 5% wider face reflows every deck you have.

For a second script, the comparison is against your Latin display face:

```
IBM Plex Sans Arabic            151       (+10% vs Manrope)
Cairo                           187       (+36%)
Noto Sans Arabic                211       (+54%)
```

+36% means every 28px row in your product becomes a clipped row the moment
someone switches locale. That is why this is a measurement and not a
preference.


---

# Prompt 4 · Write a section of the book

Two prompts, used in order. The order is the point.

**Write the content first, then generate the page.** A page written before
its content exists becomes a beautiful layout with 90 words in it, and no
build gate catches that — it is the one failure mode in this whole system
that only a person can see. In the book this repo came from, 23 of 100
pages fill 70% or less of the sheet, every one of them for this reason.

---

## 4a · The content

```
I am writing section [NN · Name] of a brand book. Write the content only —
no HTML, no layout, no page breaks.

WHAT THIS SECTION HAS TO SETTLE
[e.g. "how the logo behaves at small sizes and on photography", or "what
the product does when a model is uncertain"]

WHO OVERRIDES IT
Someone with a deadline, three hours before a client meeting. Every rule
has to survive that person.

WHAT I HAVE
[attach out/tokens.json]
[attach out/BRAND.md]
Positioning: [sentence]
Decisions already made: [the ones this section must not contradict]

WRITE
For each rule in this section:
- the rule, in one sentence, in the imperative
- the reason, in one sentence, with a measured number where one exists in
  tokens.json
- what it prohibits, stated as a prohibition, not as a preference

Then a short list of the decisions in this section that are JUDGEMENT, not
rules — the things where a designer has to look at it. Mark them as such.
The book should say which is which; a system that dresses taste as a rule
loses credibility on the first exception.

HOW TO WRITE IT
- Sentences a busy person reads once. No "leverage", "seamless",
  "empower", "journey", "unlock" — or anything else in voice.banned in the
  attached tokens.
- Never "ensure consistency" or "maintain brand integrity". Say the
  specific thing.
- Prohibitions carry their reason IN the prohibition: not "don't use
  box-shadow" but "no box-shadow at any elevation — separation comes from
  surface, border weight and a scrim; an ink hairline is 19:1 against white
  and survives print, a 1x display and a dark ground, which a soft shadow
  does not."
- Use the numbers in tokens.json. Do not invent one. If you need a number
  that is not there, say which number you need.

LENGTH
Tell me how many pages this wants to be at roughly 250–400 words per A4
landscape page, and if the answer is fewer pages than I asked for, say so.
I would rather have four full pages than seven thin ones.
```

---

## 4b · The page

Once the content exists, generate the page. Sections are Python functions
in `build/book.py`:

```
I need a page function for build/book.py. Here is the existing file:

[attach build/book.py]

And here is the content for the page:

[paste the content from 4a]

Write one function that returns page(body, "NN · Name"). Rules, all of
them load-bearing:

- Use ONLY the classes already defined in PAGE_CSS: .eb .lede .sm .xs .hr
  .hr-ink .rail .cols3 .note .sw .divnum h1 h2 h4 table td.n. If you need
  a class that does not exist, add it to PAGE_CSS rather than inlining a
  style twice.
- Read every value from T / C / M / D / TY — the tokens dict at the top of
  the file. Do not hardcode a hex, a font name, a row height or a contrast
  ratio. A hardcoded value is how the book starts disagreeing with the
  tokens.
- Units are mm for layout and pt for type. This is a print document.
- No box-shadow anywhere.
- No font-style:italic on the display face. It has no italic and the
  browser will fake one. Use font-weight for emphasis instead.
- Anything inside .rail needs .side / .main; both are flex columns, so
  margin-top:auto works inside them.
- Escape every string that came from config with html.escape.

Then tell me where in PAGES to insert the call.
```

Then:

```bash
python3 build/all.py
```

## What it will tell you

```
CLIPPED PAGES: p7:+53px
```

The page overflows the sheet and `overflow:hidden` is silently eating the
bottom of it. Fix it by cutting content or reducing a repeated element's
height — not by raising the page height, and not by removing
`overflow:hidden`, which converts a caught failure into an uncaught one.

Build after **every** section. The gate finds a clipped page the moment you
create it; if you write ten sections first, you are debugging ten pages at
once.


---

# Prompt 5 · Argue against your own system

Run this before handover, in a **fresh conversation** with no memory of the
build. A model that helped you make the decisions will defend them.

Two passes. The first is mechanical and you should run it as a script; the
second is the one that finds things.

---

## Pass 1 · The checker, on work you have not seen

Install the skill, ask an agent for something real in the client's most
awkward format, and check what comes back:

```bash
python3 scripts/check.py out/whatever-it-made.html
```

Test on something **new**. Testing on an example that ships inside the
skill proves only that the example is consistent with itself.

If the output fails, the skill is missing a rule. Add the rule; do not
blame the agent.

---

## Pass 2 · The adversarial read

```
You are reviewing a brand system that someone else built, before it is
handed to a client. Your job is to find what is wrong with it. You did not
build it and you owe it nothing.

ATTACHED
- the brand book (HTML)
- BRAND.md
- tokens.json
- brand.config.json
- the skill's SKILL.md

Produce findings in these five categories, most damaging first within each.
If a category is genuinely clean, say so in one line — do not pad it.

1. CONTRADICTIONS. Any place the book, BRAND.md, the tokens and the skill
   disagree with each other. Quote both sides. A system whose documents
   disagree is worse than no system, because the disagreement gets
   discovered by whoever is under the most time pressure.

2. UNENFORCEABLE RULES. Rules stated as rules that no script can check and
   no reader can apply. For each, say whether it should become a
   measurable rule, be demoted to a stated judgement, or be cut.

3. MISSING SURFACES. What will someone need next month that this does not
   cover? Look at what the positioning implies they sell and check whether
   there is a template for it. Rank by how soon it will be needed.

4. THIN PAGES. Pages carrying too little content for their size. Quote the
   opening line of each. This is the one thing in the system no automated
   check catches.

5. THE GENERATED LOOK. Be specific and be harsh. Does this read as
   designed or as generated? Name the exact elements: the palette's
   proximity to defaults, gradient use, icon style, whether the type scale
   has any point of interest, whether anything at all is surprising.

Then two verdicts, each one paragraph:
- If a competent designer at the client reviewed this, what is the first
  thing they would push back on?
- What is the single change with the highest ratio of improvement to
  effort?

Do not summarise what the system does. Do not praise it. If you find
nothing in a category, the sentence is "nothing found in this category",
not three paragraphs of reassurance.
```

---

## What to do with the findings

| Finding | Action |
|---|---|
| A contradiction | fix the generator, never the generated file |
| An unenforceable rule | add a check, or move it to the judgement list |
| A missing surface | a template in `skill-template/templates/` |
| A thin page | write more, or merge. Not larger type. |
| The generated look | this is the finding to take seriously, and the one you will most want to dismiss |

And the finding you will not like: if pass 2 says the palette reads as
generated, re-run `build/tokens.py` with your market's actual default
tooling added to `avoid_palettes.sets`. Most of the time the model is
seeing something the threshold would have caught, against a palette you
never listed.
