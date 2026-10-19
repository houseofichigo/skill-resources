# Prompt-context template

For context payloads, standing instructions, brand files, terminology files, design-system files, tool guidance files, or any file attached to a session that constrains future outputs.

## When to use this template

- The asset is a file (Markdown, text, JSON) attached to a session as standing context, not a string sent as a turn.
- The asset constrains downstream output but does not produce output by itself.
- The asset is paired with prompts in actual use (the prompts and the file have separate library entries).

If the asset is a runnable prompt, use one of the `templates-<level>.md` files instead.

Use this template for a context file reused across one or more AI tools.

## YAML frontmatter

Note the two-version model: `prompt_version` is the version of the file being documented, `doc_version` is the version of this documentation about the file. They evolve on different cadences.

```yaml
---
type: prompt-context
book: prompts
status: living | draft
source_id: "[file-version-id, e.g., brand-context-v5.1]"
source_kind: "internal-context-document"
source_date: YYYY-MM-DD
review_due: YYYY-MM-DD
sources:
  - "raw/prompts/[context-file].md"
  - "raw/[upstream-source].html"
related: []
last_reviewed: YYYY-MM-DD
owner: ""
maintainer: ""
reviewer: ""
tags: []
unresolved_claims: []
draft_reason: ""
prompt_version: "[file version, e.g., 5.1]"
doc_version: "[documentation version, e.g., 1.0]"
linked_patterns: []
linked_agents: []
linked_automations: []
canonical_location: "raw/prompts/[context-file].md"
model_tested: []
superseded_by: ""
retired_reason: ""
---
```

## Body sections (in order)

```md
# [Context file name]

> **Type note.** This entry uses `type: prompt-context` rather than `type: prompt`.
> A prompt is a string sent to a model as a turn. A context file is attached to a session and constrains everything the model produces afterward. Keep the categories distinct.
>
> **Two version numbers.** `prompt_version` is the version of the context file itself. `doc_version` is the version of this documentation about the file. The file and the docs evolve on different cadences.

## Purpose

[What the context file constrains, where it is used, and why it exists. Two paragraphs.]

## Quick start

Use this file when [specific situation — typically when an AI tool needs to produce on-brand or on-spec output].

**Minimum required before invoking:**

1. [Context file attached or pinned]
2. [Supporting asset attached, e.g., logo file]
3. [Specific brief defined: what to make, for whom, what format]
4. [Tool can hold the file's context size]

**Do not use this for:** [short list]

**How to navigate this doc:** [Sections explain when, why, how. The Section map is a navigable index of what's INSIDE the file. The Quality checklist evaluates the file; the two Review workflows cover per-session use and file maintenance.]

## When to use

- [Use case 1 — name the AI tool and the deliverable type]
- [Use case 2]
- [Use case 3]
- [Use case 4 — vibe coding / Lovable / Cursor / v0 if applicable]

## When not to use

- **As a prompt by itself.** This file is context, not an instruction. It must be paired with a request.
- [Use case where the file's prescriptions don't apply]
- [Use case for tools that can't hold this much context]
- [Use case where the file is being mistaken for the upstream source document]

## Session readiness

| Level | What the session has | Recommended action |
|---|---|---|
| **Low** | [File not attached, or no supporting asset, or no specific brief] | Stop. Set up the session first. The file does not rescue thin briefs. |
| **Medium** | [File attached, supporting asset attached, but the brief is freeform] | Use the most fitting prompt template. Fill in placeholders. Iterate. |
| **High** | [File pinned as project knowledge, all assets on hand, brief fully specified] | Generate with confidence. The first output should pass most of the checklist. |

If unsure: ask three questions: *(1) is the file attached? (2) are the supporting assets on hand? (3) is the brief specific?* Anything missing means Low or Medium.

## Per-session effort

How much time to budget when using the file in a single working session.

- **Attach the file:** [time]
- **Attach supporting assets:** [time]
- **Fill in the prompt template:** [time]
- **First generation:** [time]
- **Consistency-checklist review:** [time]
- **Re-prompt for failed checklist items:** [time per round]
- **Total per session:** [estimate]

For repeat use in the same project, set up a Claude Project (or Custom GPT, or pinned Gemini Gem) once with the file as standing knowledge. After that, the per-session attach time drops to zero.

## File maintenance effort

How much time to budget for keeping the file itself current.

- **Quarterly review (mandatory):** [time]
- **Upstream source version bumps:** [time per bump]
- **New tool added to the stack:** [time]
- **Failure mode caught in the wild:** [time]
- **Annual major version bump:** [time]

The maintainer (see YAML) owns this. The reviewer signs off on quarterly reviews and major version bumps.

## Required inputs / What to attach

The file does not work alone. Every session needs:

- The **context file itself**, attached or pasted at the top of the session.
- [Other assets — logo files, supporting documents]
- **A specific brief** — what to make, for whom, what tier, what family.
- *Optional:* [reference materials]

For [specific tool, e.g., vibe-coding sessions], also attach:

- [Tool-specific addition]
- [Tool-specific addition]

## Variables / Template placeholders

The file itself is static — no runtime variables. But it contains prompt templates with placeholders. When using a template, fill these in:

```text
[PLACEHOLDER_1] <- explanation
[PLACEHOLDER_2] <- explanation
[PLACEHOLDER_3] <- explanation
```

## Output shape

This file does not produce output directly. It constrains the output of *whatever the paired prompt asks for*. Verify outputs against the file's own consistency checklist:

- [ ] [Output rule 1]
- [ ] [Output rule 2]
- [ ] [Output rule 3]
- [ ] [Output rule 4]
- [ ] [Output rule 5]
- [ ] [Output rule 6]
- [ ] [Output rule 7]
- [ ] [Output rule 8]
- [ ] [Output rule 9]
- [ ] [Output rule 10]

If the output fails any of these, the fix is usually to re-prompt with the failed rule named explicitly. Do not edit the file to relax a rule unless the upstream source has changed.

## Quality checklist (for the file itself)

Run this on the file itself, not on its outputs. A healthy file should pass at least 9 of 11.

1. **Source parity** — every rule in this file traces to a section in the canonical upstream source. Drift is a bug.
2. **Tool coverage** — every AI tool the team actively uses is named with at least one specific guidance line.
3. **Failure mode coverage** — every recurring AI mistake observed in the last quarter is listed with a documented fix.
4. **Terminology completeness** — every term that AI tools have miscapitalized, hyphenated, or substituted appears in the controlled-terminology section.
5. **Token-completeness** — every CSS variable / design token in the system appears in the file. No hex codes appear elsewhere without a token.
6. **Versioning hygiene** — the version line at the top of the file matches the version in the file's footer, and both match the upstream source's version.
7. **Self-containment** — a fresh AI tool, given only this file and its supporting assets, can produce a passable output without further context.
8. **[Domain-specific check 1]**
9. **[Domain-specific check 2]**
10. **Starter prompt freshness** — the starter prompt produces usable output across at least three of the named tools. If it's been six months since this was tested, retest.
11. **No flattery in the file itself** — the document describes operationally, not promotionally.

## Per-session review workflow

What to do every time you use the file to produce a deliverable.

1. **Confirm session readiness.** Use the table above. If Low, stop.
2. **Attach the file** (or confirm it is pinned as project knowledge).
3. **Attach supporting assets.**
4. **Pick the right prompt template** for the deliverable type.
5. **Generate.** First pass; do not iterate yet.
6. **Run the consistency checklist.** Score [N]/[M] minimum.
7. **Re-prompt failed items by name.** Do not regenerate the whole deliverable; ask the model to fix specific failures. Most failures resolve in 1–2 reprompts.
8. **Hand off** with the deliverable and a one-line note on which checklist items were checked.

## File maintenance review workflow

What to do when the file itself needs review or update.

1. **Trigger.** Either: (a) the quarterly review window opens, (b) the upstream source has been updated, (c) a new tool was added to the stack, or (d) a failure mode has been caught in the wild.
2. **Open the file's quality checklist.** Score it.
3. **Identify the deltas.** What needs adding, what needs updating, what needs removing.
4. **Make the edits in the file.** Don't reorganize without a major version bump.
5. **Update the file's version number** in the preamble and footer.
6. **Add a changelog entry** to this documentation noting what changed and why.
7. **Test the updated file** against at least three tool / use-case combinations.
8. **Update related agents and automations** if the changes affect them.
9. **Notify users** if the changes affect existing workflows.
10. **Set the next `review_due`** in YAML to ~3 months out.

## Slim mode (optional — only if applicable)

A trimmed extract of the file for tools that cap context below the file's full size.

**What to include:**
- [Section]
- [Section]
- [Section]

**What to omit:**
- [Section]
- [Section]

**Total size:** [target]

**When to use:**
- [Tool category 1]
- [Tool category 2]

**When NOT to use:**
- [Use case 1] — full file is needed.
- [Use case 2] — full file is needed.

Slim mode is a temporary workaround, not the default.

## Section map (of the file itself)

The context file is the canonical text. This documentation only describes it. Do not reproduce the full file here.

| § | Section | What it constrains |
|---|---|---|
| 00 | [Section name] | [What this section in the file constrains] |
| 01 | [Section name] | [Constraint] |
| 02 | [Section name] | [Constraint] |
| 03 | [Section name] | [Constraint] |
| ... | ... | ... |

## Patterns used

- [[context-payload-as-instruction]] — explanation.
- [[controlled-terminology-block]] — explanation.
- [[explicit-failure-mode-table]] — explanation.
- [[tool-specific-guidance-blocks]] — explanation.

## Linked agents and automations

- [[sibling-prompt]] — relationship.
- *Candidate, not built:* [Project / Custom GPT / Workspace template that pins this file].
- *Candidate, not built:* [CI check that validates outputs against the file's rules].

## Model and parameters

- **Tested with:** [list of tools, honestly]
- **No temperature recommendation** for the file itself (it's not a prompt). For paired prompts, use [recommendation].
- **Context-window note:** the file is ~[size]. Fits in [tools]. Use Slim mode for [tools].

**Known behavior differences by tool:**

- **[Tool 1]** — [behavior]
- **[Tool 2]** — [behavior]
- **[Tool 3]** — [behavior]

## Example invocation

**Pattern 1 — [Use case]**

> User attaches: [files]
> User prompt: "[brief]"
> [Tool] produces: [outcome]

**Pattern 2 — [Use case]**

> User attaches: [files]
> User prompt: "[brief]"
> [Tool] produces: [outcome]

**Pattern 3 — Wrong way (what to avoid)**

> User attaches: [missing something]
> User prompt: "[thin brief]"
> Result: [what goes wrong]

The file does not rescue thin briefs. It enforces standards, but the brief still has to specify [the things specific to the deliverable].

## Failures observed

The file's own [Common failures section] catalogs operational failure modes. The list below is *meta* failure modes about how the file itself is used, not about the outputs.

- **File not attached.** [Symptoms.] **Fix:** [How to prevent.]
- **Wrong [supporting asset] attached.** [Symptoms.] **Fix:** [How to prevent.]
- **File loaded into a tool that truncates context.** [Symptoms.] **Fix:** Use Slim mode or switch tools.
- **Drift from the upstream source.** [Symptoms.] **Fix:** [Quarterly review + diff check.]
- **Section bloat over time.** [Symptoms.] **Fix:** [Major version bump with split.]
- **Stale tool-specific guidance.** [Symptoms.] **Fix:** Quarterly review.
- **Used as a [upstream source] for humans.** [Symptoms.] **Fix:** Add preamble pointing humans to the upstream source.

## Version history

### File version history (`[context-file].md`)

- **v[N]** (YYYY-MM-DD) — [what changed in the file]
- **v[N-1]** (YYYY-MM-DD) — [what changed]

### Documentation version history (this entry)

- **doc v1.x** (YYYY-MM-DD) — [what changed in this doc]
- **doc v1.0** (YYYY-MM-DD) — initial library entry for [file v[N]]

## Changelog

- YYYY-MM-DD — doc v1.x. [What changed in this documentation.]
- YYYY-MM-DD — file bumped to v[N] (see file version history above).

## Open questions

- [Real next step]
- [Real next step]
- [Reviewer field assignment if empty]

## Related

- [[sibling-prompt]] — sibling prompt this file pairs with.
- [[upstream-source]] — canonical reference document.
- [[concept-page]] — concept this entry depends on.
```
