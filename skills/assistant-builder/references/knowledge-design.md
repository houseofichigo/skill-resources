# Knowledge design

"It ignores its files" is almost never a retrieval bug. It's a design bug. Retrieval finds *chunks* that look like the question — so a document that buries the answer inside a 90-page PDF with no headings, or spreads it across three files that all half-answer it, will lose to the model's own prior knowledge every time.

Design the knowledge base to be found, not to be complete.

## Instructions vs knowledge

| Put it in **instructions** | Put it in **knowledge** |
|---|---|
| Behavior, rules, workflow, tone | Facts to look up |
| Small and stable | Large or changing |
| Read every turn | Retrieved on demand |
| "Quote the clause, then explain it" | The clauses |

If you're pasting a table into the instruction box, you're in the wrong lever.

## What a good knowledge file looks like

- **One topic per file, named for its topic.** `refund-policy-2026.md` beats `docs_final_v3.pdf`. The filename is itself a retrieval signal and a citation.
- **Headed and chunk-friendly.** Descriptive headings every few hundred words; a self-contained answer under each heading. A chunk that only makes sense if you've read the previous ten pages will be retrieved and misunderstood.
- **Text, not pictures of text.** Scanned PDFs, slides that are images, screenshots of tables — all read as noise or as nothing. Convert to clean text/markdown first.
- **Deduplicated.** Two versions of the same policy is worse than one, because the assistant will confidently cite the wrong one. Delete the old one; don't "keep it just in case".
- **Dated.** Put the effective date and version in the file, near the top. Then instruct the assistant to state the version it used.
- **Small and few.** Fewer, sharper files retrieve better than a document dump — and every file you add is one more thing to review when it changes.

## The index file

Add one short file — `00-index.md` — that lists each document, what it's authoritative for, and when to use it. Then reference it in the instructions: "Consult the index first to decide which document answers the question."

This is the cheapest quality win available in any of the three platforms. It gives the assistant a routing map instead of a pile.

```
# Knowledge index
- 01-refund-policy-2026.md — refunds, returns, exchanges. Authoritative. Effective 2026-01-01.
- 02-shipping-zones.md — delivery times and costs by zone.
- 03-faq-support.md — common customer questions and approved answers.
Use 01 for anything touching money back. Use 03 for tone; use 01/02 for facts.
```

## What not to upload

- Anything you'd be unhappy to see published. **Assume knowledge files can be extracted** by a determined user — asking the assistant nicely for its sources works more often than people expect. This is the design assumption on every platform.
- Credentials, keys, tokens, internal URLs with secrets in them.
- Personal data (customer records, HR files, health information) — unless the platform, the tier, and your legal basis all genuinely permit it, and the sharing scope matches. Default to redacting or aggregating.
- Raw exports, whole drives, "everything we have". Volume is not context; volume is noise.

## The retrieval rules that go in the instructions

Without these, good files still fail:

```
- The uploaded files are authoritative for [scope]. Where they conflict with your general
  knowledge, the files win, and you say that they do.
- Consult 00-index.md to route the question to the right document.
- Cite the document (and section) you used.
- If the answer is not in the files, say so plainly. Do not fill the gap from general
  knowledge; offer what the files do say, and name what's missing.
```

That last rule is the difference between a knowledge assistant and a plausible liar.
