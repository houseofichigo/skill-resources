# The full decision tree

SKILL.md carries the compressed version. This file has the branches worth
consulting when the short tree does not settle it.

Work top to bottom. Stop as soon as a step decides the answer. Earlier steps
outrank later ones: a hard tool requirement beats any amount of model quality.

---

## 1. Freshness

**Does the answer depend on information that can change?**

| Signal | Requirement |
|---|---|
| News, prices, availability, who holds a role, "current", "latest", "this year" | Live web search is mandatory |
| Someone will fact-check the claims, or it goes to a client / regulator / publication | Citations are mandatory too |
| Stable knowledge: how something works, history, definitions, writing craft | No search needed |

A model without search will answer a current-events question confidently and
wrongly. This step outranks every later one.

**Deep research vs ordinary search.** If the task needs many sources
cross-checked and synthesised into something long, that is a dedicated research
mode, not a chat turn with search switched on. Those modes take minutes and
produce cited reports; use them when the work would otherwise be an afternoon
of manual searching.

---

## 2. Environment

**Where does the work physically have to happen?**

| Environment | Route to |
|---|---|
| Google Drive, Gmail, Docs, Sheets | Whatever is natively connected to that workspace, or a product with a working connector |
| Microsoft 365, SharePoint, Outlook, Office files | A product with tested Office file handling or an M365 integration |
| A code repository | A coding agent that can read the repo, run tests and edit files — not a chat window |
| The person's own computer / local files | A product that can reach the desktop |
| A database or internal system | An integration or API pipeline; a chat window cannot reach it |
| Nowhere in particular | Continue down the tree |

This step decides the answer more often than people expect. Integration usually
outweighs a modest model-quality difference.

---

## 3. Files and volume

**Are there files, and how many?**

| Volume | Approach |
|---|---|
| 1–5 ordinary documents | Attach them directly; any capable assistant handles this |
| 1 very long document (hundreds of pages) | Needs strong long-document handling; ask what they want *from* it before choosing |
| 10–100 documents | File search / retrieval. Do not paste |
| 1,000+ documents | Indexing, batch processing, aggregation. This is a project, not a chat. Say so |

**Separate size from count.** One 300-page report and ten thousand 20-page
reports are different problems, even if a model advertises a window large
enough for either. The second needs an index, a retrieval step and a way to
aggregate results — plus a cheaper model, because it runs thousands of times.

**Then ask what they want from the file**, because the same PDF routes
differently:

| Goal | Needs |
|---|---|
| Summary | Ordinary summarisation, cheap tier |
| One exact fact | Retrieval accuracy and a citation to the page |
| A table extracted | Structured extraction with a fixed schema, then validation |
| Charts or scans read | Genuine vision capability, not just text extraction |
| Comparison across documents | Multi-document synthesis, usually with retrieval |
| Judgement or interpretation | The reasoning tier — this is the only branch that justifies the flagship |

---

## 4. Modalities

**What is in the input besides text?**

Images, charts, diagrams, scanned pages, audio, video. Each narrows the pool to
products and models that accept that input at all. Check this before comparing
intelligence — a smarter model that cannot see the chart is useless here.

Raw audio usually needs a transcription step first, then a text model. Treat
those as two jobs.

Image *generation* and image *editing* are specialist models, not a general
assistant decision. Route them separately.

---

## 5. Reasoning depth

**How hard is the thinking, honestly?**

| Level | Examples | Tier |
|---|---|---|
| Routine | Rewriting, tone changes, short summaries, classification, extraction, simple Q&A | Fast / light |
| Professional | Drafting real documents, normal analysis, everyday coding, document work | Balanced |
| Hard | Strategy, system architecture, complex maths or science, long autonomous runs, anything where being wrong is expensive | Frontier / deep thinking |

The most common mistake in both directions:

- Using the flagship for routine work — slow and expensive for no gain.
- Using the cheap tier for work that gets sent to a client — the savings vanish
  the first time someone has to fix it.

---

## 6. The binding constraint

**Which one actually binds: quality, speed, or cost?**

Usually one dominates. Name it, optimise for it, and tell the person what they
traded away.

- **Quality binds** when the output is client-facing, regulated, or expensive to
  get wrong. Pay for the top tier and verify the output.
- **Speed binds** in anything interactive — a live chat, a voice interface, a
  UI that waits for the answer.
- **Cost binds** at volume. At one run a day, cost is irrelevant. At a hundred
  thousand, it is the whole decision.

The measure that matters is **cost per successful task**, not price per million
tokens. A cheap model that retries, produces more tokens, or creates review
work is often more expensive overall.

---

## 7. Governance

**Is the data sensitive or regulated?**

A hard gate, not a preference. Consumer plans, enterprise agreements and
self-hosted deployments differ on data retention, training use and residency.

If the person is at all unsure: tell them to check their organisation's policy
before uploading, and route them to whatever their employer already approved —
even if it is not the best tool for the job. Getting this wrong is worse than
using a slightly weaker model.

---

## 8. Repetition

**Once, or continuously?**

| Frequency | Shape |
|---|---|
| One-off | A chat window. Ease of use beats economics |
| Weekly / recurring by hand | A saved prompt, a project, or a skill — something that keeps the instructions stable |
| Automated and frequent | A pipeline with a pinned model, a fixed output format and validation |

For anything repeated, consistency matters more than peak quality. Pin the
setup, fix the output format, and validate the results — an occasional
brilliant answer is worth less than a reliably adequate one.

---

## Escalation pattern

When cost matters but quality sometimes does, do not choose once. Start on the
cheap tier and escalate only what fails: run the light model, check the output
against a rule or a validator, and send only the failures to the stronger
model. This is how large-scale pipelines are actually built, and it beats
picking a single tier for everything.
