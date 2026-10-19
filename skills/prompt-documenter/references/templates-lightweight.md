# Lightweight template (Level 1)

For simple reusable prompts. Single-purpose, one-shot tasks, utility prompts under 30 lines. About 60–120 lines of documentation total. Do not over-document.

## When to use this level

- Simple utility prompts (reformat this, extract that, summarize the other thing)
- One-shot tasks the user runs in chat without setup
- Prompts under 30 lines that don't have intake or multi-step structure
- Prompts where the user explicitly wants minimum documentation overhead

If the prompt has any of the following, use Standard or Operating system instead:
- Multi-phase intake
- Significant business logic
- Production deployment
- Multiple model targets with different behavior
- Strategic or client-facing output

## YAML frontmatter

```yaml
---
type: prompt
book: prompts
status: draft
source_kind: "internal-prompt"
source_date: YYYY-MM-DD
review_due: YYYY-MM-DD
sources:
  - "raw/prompts/[source-file].md"
related: []
last_reviewed: YYYY-MM-DD
owner: ""
maintainer: ""
reviewer: ""
tags: []
prompt_version: "1.0"
doc_version: "1.0"
linked_patterns: []
canonical_location: "raw/prompts/[prompt-name].md"
model_tested: []
---
```

## Body sections

```md
# [Prompt name]

## Purpose

[What this prompt does, in one sentence.]

## Quick start

Use this prompt when [specific situation].

Minimum required:

1. [Input]
2. [Input]

Do not use this for [out-of-scope case].

## Required inputs

- [Input 1]
- [Input 2]
- [Input 3]

## Variables

```text
[VARIABLE] <- explanation
[VARIABLE] <- explanation
```

## Output shape

- [ ] [Expected output feature]
- [ ] [Expected output feature]
- [ ] No placeholders, invented claims, or generic filler.

## Quality checklist

1. **Specificity** — [Check.]
2. **Completeness** — [Check.]
3. **Format** — [Check.]
4. **Usefulness** — [Check.]

## Prompt body

````
[PASTE PROMPT HERE]
````

## Example invocation

**Input**

> [Example user request]

**Expected behavior**

> [Expected model response]

## Failures observed

- **[Failure].** Fix: [Fix.]

## Version history

- v1.0 (YYYY-MM-DD) — initial version.

## Changelog

- YYYY-MM-DD — created.

## Open questions

- [Question]

## Related

- [[related-entry]]
```
