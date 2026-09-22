---
name: which-ai-model
description: Help a non-technical person decide which AI product, mode and model to use for a specific task — ChatGPT vs Claude vs Gemini, which tier inside each, and whether a chat window, a research mode, a coding agent or an API pipeline is the right place to do the work. Use when someone asks "which model should I use for this", "is ChatGPT or Claude better for X", "which Gemini should I pick", "am I overpaying for the expensive model", "why is my AI bad at this task", or asks to compare AI assistants for a job. Also use when someone is choosing an AI subscription or standardising model choice for a team. Not for routing API traffic programmatically — that is a job for a router library, not this skill.
---

# Which AI Model Should I Use?

Help someone pick the right AI setup for one specific task, in plain language,
without assuming they know what a token, a context window or an API is.

## The one rule that matters

**Never name a model from memory. Always search first.**

Model lineups, tier names, prices and product modes change every few weeks.
Anything you "know" about the current lineup is probably a version or two
behind. `references/snapshot.md` is a dated fallback, not a source of truth.

Before naming any specific model or price:

1. Search the web for the current lineup of whichever providers are in play.
   Useful queries: `OpenAI models current lineup`, `Anthropic Claude models
   overview`, `Gemini models list`, `<provider> pricing per million tokens`.
2. Prefer the provider's own docs and help centre over blog round-ups.
3. State the date of what you found, and say plainly if you could not verify
   something.

If no search tool is available, say so, use `references/snapshot.md`, and warn
the person that the specifics may be out of date — then give them the reasoning
(which is durable) rather than the names (which are not).

## The core insight

Most people ask "which model is best?" That is the wrong first question,
because the strongest model is often the wrong choice.

Route through four layers, in order, and pick the model **last**:

```
Task  →  Capability needed  →  Product / tool needed  →  Model tier
```

> Product capability ≠ model capability ≠ tool availability.

A weaker model inside the right product beats a stronger model in the wrong
one. A spreadsheet task can be better served by an assistant that can actually
build and verify a spreadsheet file than by a cleverer model that can only
describe one. A task about the person's own documents is decided by which
product can reach those documents, not by benchmark rank.

## How to run the conversation

Ask at most 2–3 short questions before answering. Never interrogate. If the
person has already said enough, skip straight to the recommendation.

The questions worth asking, roughly in order of how much they change the answer:

1. **What is the actual task?** Push past "write something" to what the output
   is and who reads it.
2. **Does it need current information?** Anything about now — prices, news, who
   holds a role, what a company is doing — needs live search, which rules out
   any offline setup regardless of model quality.
3. **Where do the files or data live?** Their computer, Google Drive,
   SharePoint, a code repository, a database, nowhere. This usually decides the
   product on its own.
4. **What does a wrong answer cost?** A first draft they will edit anyway is a
   different problem from a client deliverable or a legal review.
5. **How often?** Once is a chat window. A thousand times a day is a pipeline,
   and cost per run starts to dominate.

## The decision tree

Walk this in order. Stop as soon as a step decides the answer.

**1. Does the task need information that can change?**
Yes → it needs live web search, and citations if anyone will check the claims.
That requirement outranks model quality: a brilliant model with no search will
confidently invent the answer.

**2. Is the work tied to a particular environment?**
- Google Drive / Gmail / Docs → favour whatever is natively connected to that
  workspace.
- Office files or SharePoint → favour a product with tested Office file
  handling, or a connector into that environment.
- A code repository → this is a coding agent's job, not a chat window's.
- None of the above → continue.

**3. Are there files, and how many?**
- One or a few normal documents → any capable assistant can read them directly.
- One very long document → needs strong long-document handling. Note that a big
  advertised context window does not guarantee good retrieval from deep inside
  it.
- Dozens to hundreds → needs file search / retrieval, not pasting.
- Thousands → this is an indexing and batch-processing project, not a chat.
  Say so plainly; do not let someone try to paste 10,000 PDFs into a chat
  window.

**4. What is in the input besides text?**
Images, charts, scanned documents, audio, video — each narrows the pool to
products and models that genuinely accept that input. Check this before
comparing intelligence.

**5. How hard is the thinking?**
- Routine (rewrite, summarise, classify, answer a simple question) → the cheap
  fast tier is correct. Using the flagship here wastes money and time.
- Everyday professional work (drafting, analysis, normal coding) → the middle
  tier. This is where most work belongs.
- Genuinely hard (strategy, architecture, complex maths, long autonomous runs)
  → the top tier, or the product's deepest thinking mode.

**6. What is the constraint that actually binds?**
Quality, speed, or cost — usually one dominates. Say which one you optimised
for, and what the person gives up.

**7. Sensitive or regulated data?**
This is a hard gate, not a preference. Consumer chat plans, enterprise
agreements and self-hosted deployments differ on retention and residency. If in
doubt, tell the person to check their organisation's rules before uploading
anything, and route to whatever their employer has already approved.

## Tier translation

Most provider lineups can be understood as the same three-step ladder under
different names. Teach the ladder, not the names — the names change, while the
decision pattern is durable.

| Rung | What it is for | Cost tendency |
|---|---|---|
| **Fast / light** | High volume, simple, repetitive: classification, extraction, short summaries, quick answers | Lowest |
| **Balanced / everyday** | Most real work: drafting, analysis, normal coding, document work | Higher |
| **Frontier / deep thinking** | Hard reasoning, architecture, long autonomous tasks, work where being wrong is expensive | Highest |

In consumer chat apps this same ladder appears as a "how hard should it think"
control rather than a model name. People understand *fast / think harder /
maximum* far better than family names — use that framing with non-technical
users.

Look up the current names and prices for each rung before stating them. Do not
apply a universal multiplier: price gaps vary materially by provider. See
`references/snapshot.md` for the shape of the ladder and a dated example.

## Rules of thumb worth repeating

- **Don't route by sticker price.** What matters is cost per *successful* task.
  A cheap model that needs three attempts and a human fix is more expensive
  than one good run.
- **Don't route "analyse this PDF" straight to a model.** Ask what they want
  from it: a summary, one exact fact, a table, a chart reading, a comparison
  across documents, or a judgement. Those go to completely different setups.
- **Don't route "write code" straight to a model.** One function, a bug hunt, a
  repo-wide refactor and an architecture review are four different jobs.
- **Don't treat a big context window as a document-analysis guarantee.** Fitting
  the text in is not the same as reasoning well over all of it.
- **Don't switch providers for a few benchmark points.** Ecosystem fit,
  connectors and the person's existing subscription usually matter more.
- **Benchmarks shortlist; they don't decide.** Recommend a 10-minute side-by-side
  test on the person's own real task over any leaderboard.

## Shape of the answer

Keep it short and concrete. A good answer contains:

1. **The recommendation** — product, mode, and tier, in one or two sentences.
2. **Why** — the one constraint that drove it (usually a tool or environment
   requirement, not intelligence).
3. **The cheaper fallback** — what to use instead if cost matters more than the
   last few percent of quality.
4. **What would change the answer** — the condition under which they should
   pick differently.
5. **A date stamp** — "as of <date>", plus a note that lineups change monthly.

Do not produce a giant comparison table unless asked. One clear recommendation
beats a matrix the person has to interpret.

## Worked example

> *"I need to summarise 40 client call transcripts every week and pull out who
> asked for what."*

Walk the tree: no current-information need (1); the transcripts are files
somewhere — ask where (2); 40 files repeated weekly is retrieval plus batch, not
pasting (3); text only unless raw audio, in which case transcription comes first
(4); summarising and extracting named requests is routine, not hard reasoning
(5); at 40×weekly, cost and consistency bind harder than peak quality (6).

**Answer:** the fast/light tier with a fixed extraction format, run as a
repeatable job rather than by hand in a chat window — plus a spot-check of a
few outputs each week. Escalate one rung only if the transcripts are technical
or legally sensitive. Name the specific current model only after searching.

## References

- `references/decision-tree.md` — the full tree with the branches this file
  compresses
- `references/capability-map.md` — common tasks mapped to the capability and
  tooling they actually require
- `references/snapshot.md` — dated snapshot of the lineup; **treat as stale**,
  verify by search
- `references/sources.md` — where to look up current lineups and prices
