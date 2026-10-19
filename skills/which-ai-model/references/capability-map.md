# Task → capability → tooling map

What a task actually *requires*, before any model is named. Use this to
translate a plain-language request into requirements, then let the decision
tree pick the tier.

The third column is the one people skip. It is usually what decides the answer.

---

## Writing and language

| Task | Capability needed | Tooling / product requirement | Tier |
|---|---|---|---|
| Everyday questions | General reasoning | None | Fast |
| Brainstorming | Ideation, language quality | None; interactive speed helps | Fast–balanced |
| Professional writing | Writing, instruction following | None, unless house style must be loaded | Balanced |
| Rewriting / tone change | Editing, constraint adherence | None | Fast |
| Short summary | Summarisation | None | Fast |
| Meeting transcript summary | Summarisation over long input | Transcription first if audio | Fast–balanced |
| Translation | Language pair quality | None | Fast–balanced |

Writing quality is subjective. Recommend a side-by-side test on the person's
own house style rather than a benchmark.

---

## Documents

| Task | Capability needed | Tooling / product requirement | Tier |
|---|---|---|---|
| Read one long PDF | Long-document comprehension | File upload | Balanced |
| Find an exact fact in a PDF | Retrieval precision, citation to location | File search | Fast–balanced |
| Extract a table | Structured extraction, schema adherence | Fixed output format + validation | Fast |
| Read charts or scans | Genuine vision | Multimodal input | Balanced |
| Compare contracts | Long-document reasoning, precision | Both documents accessible at once | Balanced–frontier |
| Search across hundreds of documents | Retrieval, synthesis | File search / RAG | Balanced |
| Process thousands of documents | Indexing, batch, aggregation | Pipeline, not a chat window | Fast + retrieval |

Advertised context window is not a proxy for document-analysis quality.
Retrieving accurately from deep inside a long document is a distinct skill from
accepting it as input.

---

## Research

| Task | Capability needed | Tooling / product requirement | Tier |
|---|---|---|---|
| Quick current fact | Live search | Web search enabled | Fast |
| Current web research | Search, freshness, citations | Web search enabled | Balanced |
| Deep multi-source research | Browsing, synthesis, citation discipline | A dedicated research mode | Frontier |
| Competitive / market scan | Search, structured synthesis | Search + a place to put the output | Balanced–frontier |

Tool availability is the hard gate here, not model rank. Verify search is
actually switched on for the plan the person has.

---

## Code

| Task | Capability needed | Tooling / product requirement | Tier |
|---|---|---|---|
| Write one function | Coding | None | Fast–balanced |
| Debug | Diagnosis, code reasoning | Ability to run the code and see errors | Balanced |
| Review a pull request | Code understanding | Access to the diff | Balanced |
| Work across a repository | Repo search, file editing, test execution, long-horizon focus | A coding agent, not a chat window | Balanced–frontier |
| Design an architecture | Hard reasoning, planning | None; quality over speed | Frontier |
| Port or refactor at scale | Long autonomous work, consistency | Coding agent + tests as a safety net | Frontier |

Repository-scale work changes the question from "which coding model" to "which
coding agent, with what execution environment". Tests matter as much as the
model.

---

## Data and structure

| Task | Capability needed | Tooling / product requirement | Tier |
|---|---|---|---|
| Analyse a CSV | Data reasoning, arithmetic | Code execution — do not let a model do arithmetic in prose | Balanced |
| Analyse a spreadsheet | Spreadsheet semantics, formulas | A product that can actually open and write the file | Balanced |
| Build a financial model | Reasoning + auditability | Spreadsheet tooling + verification of every formula | Frontier |
| Extract fields from invoices | OCR, structured extraction | Document handling + fixed schema + validation | Fast |
| Classify at scale | Classification | Batch pipeline, cheapest tier that passes a test | Fast |
| Produce reliable JSON | Schema adherence | Structured output *and* a parser that validates it | Fast |

"The model usually returns valid JSON" is not a specification. Constrain the
output and validate it downstream.

---

## Deliverables

| Task | Capability needed | Tooling / product requirement | Tier |
|---|---|---|---|
| Presentation | Structure, writing, file generation | A product that produces a real .pptx, not a description of one | Balanced |
| Formatted report | Writing, document generation | Document file output | Balanced |
| Spreadsheet deliverable | Structure + file generation | Spreadsheet file output | Balanced |
| Image | Image generation | A dedicated image model | Specialist |
| Edited image | Image-to-image editing | An editing-capable image model | Specialist |

If the person needs a *file*, the product's ability to produce that file
outranks model intelligence. This is the clearest case of product capability
beating model capability.

---

## Agents and automation

| Task | Capability needed | Tooling / product requirement | Tier |
|---|---|---|---|
| Call an API or SaaS tool | Function calling | Tool integration + an approval step for anything destructive | Balanced |
| Multi-step workflow | Planning, state, error recovery | Agent framework with observability | Balanced–frontier |
| Control a computer or browser | Visual perception, action planning | Computer-use capability + human approval on risky steps | Frontier |
| High-volume background job | Throughput, cost | Batch processing, pinned model | Fast |

For agents, reliability and error recovery dominate raw intelligence. A model
that fails predictably is more useful than one that fails creatively.

---

## Governance overlay

Applies on top of everything above.

| Situation | Effect on the choice |
|---|---|
| Personal or client confidential data | Check the plan's retention and training terms before uploading anything |
| Regulated industry | The employer's approved tool wins, even if weaker |
| Data residency requirement | Narrows to deployments in the right region; may rule out consumer plans entirely |
| Auditability required | Pin the model version, log inputs and outputs, keep the prompt stable |

This overlay can override the entire rest of the analysis, and it should.
