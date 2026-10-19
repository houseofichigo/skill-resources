# Operating system template (Level 3)

For strategic, long-form, high-value, or multi-step prompts and context files. Brand systems, client-facing deliverables, AI agents, reusable internal workflows. About 400–700 lines of documentation total.

## When to use this level

- Strategic prompts that shape major deliverables
- Multi-phase intake (e.g., the brand-book-generator)
- Production prompts where failure has business consequences
- Prompts paired with operational workflow (review steps, regeneration policy)
- Prompts with versioning history worth preserving
- Prompts with multiple model targets and observed model differences

Use this template when the asset is high-value, multi-step, or operationally significant.

## YAML frontmatter

Same as Standard, with all fields populated.

```yaml
---
type: prompt
book: prompts
status: living | draft
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

## Body sections (in order)

```md
# [Prompt name]

## Purpose

[Two paragraphs. What the prompt does, what it produces, who it is for, why it exists. End with a sentence on reusability.]

## Quick start

Use this prompt when [specific situation].

**Minimum required before use:**

1. [Requirement]
2. [Requirement]
3. [Requirement]
4. [Requirement]

**Do not use this for:** [short list, point to "When not to use" for full]

**How to navigate this doc:** [Explain section-by-section what to read for what.]

## When to use

- [Concrete use case 1]
- [Concrete use case 2]
- [Concrete use case 3]
- [Concrete use case 4]

## When not to use

- [Wrong use case 1] — use [alternative] instead.
- [Wrong use case 2] — use [alternative] instead.
- [Wrong use case 3] — use [alternative] instead.

## Input readiness

| Level | What the user has | Recommended action |
|---|---|---|
| **Low** | [Thin or incomplete setup] | [Action — usually "stop, run prerequisite workflow first"] |
| **Medium** | [Partially ready] | [Action — usually "use the prompt with extra time for clarification"] |
| **High** | [Strong setup] | [Action — usually "use the prompt directly"] |

If unsure which level applies, ask:

1. [Question]
2. [Question]
3. [Question]

## Expected effort

- Intake: [time]
- Generation: [time]
- Review: [time]
- Regeneration rounds: [typical count]
- Total wall-clock: [estimate]

## Required inputs

A flat list for scannability:

- [Input 1]
- [Input 2]
- [Input 3]
- [Input 4]
- [Input 5]

## Prompt variables

The surface area an adapter can rewire if turning the prompt into a templated form, automation input, or Project structure.

```text
[VARIABLE_1]              <- explanation
[VARIABLE_2]              <- explanation
[VARIABLE_3]              <- explanation
```

## Output shape

A verifiable checklist of what the output must contain.

- [ ] [Expected output feature 1]
- [ ] [Expected output feature 2]
- [ ] [Expected output feature 3]
- [ ] [Expected output feature 4]
- [ ] [Expected output feature 5]

Failure modes to guard against:

- [Failure mode 1]
- [Failure mode 2]
- [Failure mode 3]

## Quality checklist

Run this against any output before accepting it. A v1.0 output should pass at least 8 of 10.

1. **[Test name]** — [Specific test, with concrete pass/fail criteria.]
2. **[Test name]** — [Specific test.]
3. **[Test name]** — [Specific test.]
4. **[Test name]** — [Specific test.]
5. **[Test name]** — [Specific test.]
6. **[Test name]** — [Specific test.]
7. **[Test name]** — [Specific test.]
8. **[Test name]** — [Specific test.]
9. **[Test name]** — [Specific test.]
10. **[Test name]** — [Specific test.]

## Review workflow

The end-to-end operating procedure. Each step is sequential.

1. **Confirm input readiness.** Use the readiness table. If Low, stop.
2. **Run intake.** [Specifics for this prompt.]
3. **Generate the pre-output summary.** [If applicable.]
4. **Confirm or revise the summary** with the user.
5. **Generate the output.**
6. **Run the quality checklist.** Score [N]/[M] minimum before accepting.
7. **Regenerate weak sections only.** Do not regenerate the whole output.
8. **Test downstream usability.** [If applicable.]
9. **Save and add changelog entry.**
10. **Hand off** with [next steps].

## V0 mode (optional — only if applicable)

Use only when the user explicitly accepts the limitations of generating from thin inputs.

A v0 must:

- Mark assumptions clearly.
- Label weak sections.
- Include omitted inputs.
- Avoid invented evidence.
- End with a list of questions needed to upgrade v0 to v1.

V0 mode is opt-in only. The default behavior is to refuse generation on thin inputs and continue intake.

## Prompt body

Reproduced in full because this is the canonical retrieval surface for the prompt. Designed to paste into a fresh session with no system prompt customization.

---

````
[PASTE FULL PROMPT HERE]
````

## Patterns used

- [[pattern-name]] — explanation of how this prompt instantiates the pattern.
- [[pattern-name]] — explanation.

## Linked agents and automations

- [[agent-name]] — relationship.
- [[automation-name]] — relationship.
- *Candidate, not built:* [automation idea].

## Model and parameters

- **Models tested:** [list, honestly]
- **Recommended temperature:** [value, by intake/generation]
- **Max tokens:** [requirement]
- **Known behavior differences:**
  - [Model A] — [behavior]
  - [Model B] — [behavior]

## Example invocation

**Correct behavior**

> User: "[input]"
>
> Model: "[response — should follow the prompt's structure]"

**Incorrect behavior — what the prompt is designed to prevent**

> Model: "[response — typically generating before intake, or accepting thin answers]"

## Example input (synthetic)

[Full worked example of intake answers across all phases. Use a generic synthetic business unless the user specifically wants a named anchor.]

## Example output (synthetic)

[One worked section of generated output, at the right fidelity. Note size scale extrapolated to full output.]

## Adaptation notes

How to modify this prompt for adjacent use cases. **Critical for reusability** — this is where a future user learns to swap the original anchor business for theirs.

**For [adjacent use case 1]:**
- Change [X].
- Remove [Y].
- Add [Z].

**For [adjacent use case 2]:**
- Change [X].

**To change the model:**
- For [smaller model]: [adjustment].
- For [non-Claude model]: [adjustment].

**To change the output format:**
- For Markdown-only: [instruction].
- For JSON: [instruction].
- For PDF: [instruction].

**To swap the anchor business:**
- Replace [anchor reference] with [your business].
- Update [domain-specific terminology].
- Verify the prompt body's examples still apply.

## Failures observed

This prompt is v[N] and has been [tested / not tested] in production. [Anticipated / observed] failure modes:

- **[Failure mode 1].** [What happens.] **Fix:** [What to do.]
- **[Failure mode 2].** [What happens.] **Fix:** [What to do.]
- **[Failure mode 3].** [What happens.] **Fix:** [What to do.]

## Version history

- **v1.0** (YYYY-MM-DD) — initial version. [Source.]
- **v1.1** (YYYY-MM-DD) — [what changed and why].
- **v2.0** (YYYY-MM-DD) — [major restructure, what and why].

## Changelog

- YYYY-MM-DD — [doc-level change]. Source: [why].
- YYYY-MM-DD — [doc-level change]. Source: [why].

## Open questions

Real next steps. Not throat-clearing.

- [Question that future work could answer.]
- [Question about validation.]
- [Question about scope or scaling.]

## Related

- [[other-entry]] — relationship.
- [[other-entry]] — relationship.
- [[concept-page]] — concept this prompt depends on.
```
