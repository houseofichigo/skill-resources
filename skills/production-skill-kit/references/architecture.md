# The architecture: eight patterns behind a production skill

These are extracted from skills that survived real client use. Each has a *why*, a *how to instantiate*, and the *failure* it prevents. Instantiate all eight; skipping one is where the skill later breaks.

---

## 1. Thin brain, deep library

**Why.** The model reads the whole SKILL.md every time the skill fires, but needs any given reference file only at one step. A fat SKILL.md spends attention on step-9 detail while doing step 2.

**How.** SKILL.md = non-negotiables + workflow + quality floor + traps. Nothing else. Each workflow step links the one reference file it needs (`See [references/x.md]`). Reference files are 40–120 lines, one topic each.

**Failure prevented.** The 3,000-word skill that "covers everything" and follows none of it because the model can't hold it all at the decision point.

---

## 2. The contract: what bends / what never bends  {#the-contract}

**Why.** "On-brand" and "good" pull in opposite directions. Without a written split, the model either bolts the brand on rigidly (correct, lifeless) or takes creative licence with the logo (alive, off-brand).

**How.** One table at the top of the new SKILL.md:

| | Never bends (the look) | Bends (the craft) |
|---|---|---|
| Deck | palette, logo, fonts, approved claims, correctness of every number | layout density, build order, emphasis, section pacing |
| Proposal | brand tokens, legal limits, pricing given by owner | structure, framing of pain, ordering of use cases |
| Film | palette, logo files, voice, claims | pace, light, depth, transitions |

For any organization, "never bends" points to its user-owned brand source of truth; do not copy private tokens into the public skill. "Bends" is the deliverable-specific craft you are about to write in the craft file.

**Failure prevented.** Endless "is this on-brand?" loops, and the opposite — a beautiful deliverable that fails brand review.

---

## 3. Discovery and memory: four inputs, one profile  {#discovery-and-memory}

**Why.** Users arrive with wildly different material. If each input path builds the output differently, you maintain four skills. If they all fill one profile, you maintain one.

**How.** Define, in `references/discovery.md`, how each path writes `PROFILE.md`:

- **A brand folder / tokens / a design skill** → read it, it is law.
- **A codebase** → parallel read-only sweeps (rules files, tokens, components, features), return paths and values, not opinions.
- **A URL only** → capture it, then read the capture like a brand folder; a blocked capture is a hard stop, not a guess.
- **Nothing** → the brand round of the interview, "You choose for me" on every question.

All four converge on the same `PROFILE.md`. The build step never knows which path was taken.

The profile's four load-bearing sections:
- **Owner choices** — standing decisions reused every run (format, tone, language, audience).
- **Chosen by assistant** — defaults the skill picked, dated, so the owner can overrule.
- **Assumed, not asked** — what it decided when told "just go".
- **A log** of past outputs (name, date, what the owner changed) — notes on one output ("less text") become standing choices for the next.

**Failure prevented.** A skill that only works when the user has a perfect brand book, and a "memory" that is written but never read.

---

## 4. The interview: ask little, remember everything

**Why.** Every question is friction and a chance to ask something a file already answered.

**How.** Read PROFILE.md first (step 1). Then the host question tool, ≤4 questions per call, 2–4 options each, options *named after what discovery found* (their products, their colours, their tagline), `multiSelect` where several fit. Every question has "You choose for me"; when there's a clear best answer, put it first and mark "(Recommended)". Write down explicitly, in `references/interview.md`, the list of things you will **never** ask because discovery answers them.

Show, don't ask, for taste: produce 2–3 sample frames/sections and let the user react. People answer pictures faster than questions.

**Failure prevented.** The 12-question intake form that makes the skill feel like paperwork.

---

## 5. The craft file: the opinionated core

**Why.** This is the file that makes the skill *yours* and not a generic generator. It is the source skill's `showreel.md`: the shape of a good output, the recipe, the pacing, and a section titled **"why a first pass comes out flat, and how the good ones differ"** — the hard-won taste, ranked by impact.

**How.** Write it as a default register with a bias, not a menu. "Fast is the default. Never ask calm or fast." State the shape (the bars/sections/pages), the recipe (the concrete moves that create quality), and the anti-patterns. If two outputs from the same inputs can look years apart, this file explains why and forces the good version.

**Failure prevented.** A skill that produces technically-correct, on-brand, forgettable output — because nobody wrote down what "good" looks like.

---

## 6. Templates: stamp, don't describe

**Why.** A template the skill fills is reproducible; prose telling the model to "produce a well-structured X" is not.

**How.** `assets/templates/` holds fill-in files with `<placeholders>` and inline `<!-- guidance -->`. The skill copies and fills them. The per-run **brief** template captures the one job (this output's variant, facts, assets, decisions); the **profile** template is the memory. Keep guidance *inside* the template as comments so it travels with the file.

**Failure prevented.** Output whose structure drifts every run because it was described, not stamped.

---

## 7. Verification: inspect the artifact, not the intent

**Why.** The model will confidently report success it did not achieve. The only defence is checking the real thing.

**How.** The last workflow step opens the produced file and checks it against the contract: decode the deck's theme and read the hex values; re-open the PDF and count the pages; parse the proposal and confirm the price matches the owner's figure. For high-stakes output, a second pass that has not seen the build does the check. Name the exact checks in `references/review.md`.

**Failure prevented.** "Done!" on a deck with the wrong accent colour, shipped to a client unattended.

---

## 8. Traps that grow

**Why.** The expensive failures are specific and non-obvious, and they recur. Written down, each one is paid for once.

**How.** A "Traps that cost real time" section in the new SKILL.md, each line prefixed with proof it happened, phrased as *the rule*, not the story ("Measure only after every font has loaded" — not "once I forgot to load fonts"). Seed it from the two dry runs; add to it every time the skill burns a real deliverable.

**Failure prevented.** The same 45-minute debugging session, three times, in three different client projects.

---

## The shape of the folder you produce

```
<new-skill>/
├── SKILL.md              # patterns 1, 2, 7, 8 live here (thin)
├── references/
│   ├── discovery.md      # pattern 3
│   ├── interview.md      # pattern 4
│   ├── <craft>.md        # pattern 5 — the core, named for the deliverable
│   ├── <variants>.md     # the 3–8 shapes of the deliverable
│   └── review.md         # pattern 7
├── assets/templates/     # pattern 6
│   ├── PROFILE.md        # the memory
│   └── brief.md          # the per-run job
└── scripts/              # only if the output needs deterministic tooling
```

Scripts are optional. Add them only when the deliverable needs code that must run the same way every time (rendering, parsing, measuring). A proposal skill may need none; a film skill needs many.
