# Standard template (Level 2)

For prompts reused across projects. Team-shared prompts. Prompts with non-trivial intake. About 200–350 lines of documentation total.

## When to use this level

- Prompts shared across teams or projects
- Prompts with named inputs and structured outputs
- Prompts that have failure modes worth documenting
- Prompts that benefit from a quality checklist
- Prompts in active iteration where version history matters

If the prompt also has multi-phase intake, strategic output, or significant operational complexity, escalate to Operating system.

## YAML frontmatter

```yaml
---
type: prompt
book: prompts
status: draft
source_id: ""
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
unresolved_claims: []
draft_reason: ""
prompt_version: "1.0"
doc_version: "1.0"
linked_patterns: []
linked_agents: []
linked_automations: []
canonical_location: "raw/prompts/[prompt-name].md"
model_tested: []
superseded_by: ""
retired_reason: ""
---
```

## Body sections

```md
# [Prompt name]

## Purpose

[What the prompt does, what it produces, who it is for, and why it exists.]

## Quick start

Use this prompt when [specific situation].

**Minimum required before use:**

1. [Requirement]
2. [Requirement]
3. [Requirement]

**Do not use this for:**

- [Out-of-scope use case]
- [Out-of-scope use case]

**How to navigate this doc:** [Explain how to use this documentation.]

## When to use

- [Concrete use case]
- [Concrete use case]
- [Concrete use case]

## When not to use

- [Wrong use case]
- [Wrong use case]
- [Wrong use case]

## Required inputs

- [Input]
- [Input]
- [Input]

## Variables

```text
[VARIABLE] <- explanation
[VARIABLE] <- explanation
```

## Output shape

- [ ] [Expected output feature]
- [ ] [Expected output feature]
- [ ] [Expected output feature]

Failure modes to guard against:

- [Failure]
- [Failure]

## Quality checklist

Run this before accepting the output. A strong output should pass at least 8 of 10.

1. **[Test name]** — [What to check.]
2. **[Test name]** — [What to check.]
3. **[Test name]** — [What to check.]

## Review workflow

1. Confirm input readiness.
2. Collect required inputs.
3. Run the prompt.
4. Generate final output.
5. Run the quality checklist.
6. Regenerate weak sections only.
7. Save final output.
8. Add changelog entry.

## Prompt body

Reproduced in full because this is the canonical retrieval surface for the prompt.

---

````
[PASTE FULL PROMPT HERE]
````

## Example invocation

**Correct use**

> [User input]

**Expected behavior**

> [Model behavior]

**Incorrect use**

> [Bad user input or bad model behavior]

**Why this is wrong**

[Explanation.]

## Failures observed

- **[Failure].** [What happens.] **Fix:** [Fix.]

## Version history

- v1.0 (YYYY-MM-DD) — initial version.

## Changelog

- YYYY-MM-DD — created.

## Open questions

- [Question]

## Related

- [[related-entry]] — relationship.
```
