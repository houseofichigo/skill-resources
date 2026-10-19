# Type taxonomy — six types of LLM library entry

The library has six entry types. Picking the right type is the most important decision in documenting an LLM asset, because it determines section names, what YAML fields apply, and what the canonical location field means.

## The six types

### `type: prompt`

A string sent to a model as a turn or system prompt. Has a prompt body. Has runtime variables (or elicits them through dialogue). Produces output when invoked.

**Examples:** brand book generator, transcript summarizer, code review prompt, Custom GPT system prompt that's reused across instances.

**Key sections:** Prompt body, Variables, Output shape, Example invocation, Example input, Example output.

### `type: prompt-context`

A file attached to a session that constrains everything the model produces afterward. Has no prompt body — paired with prompts. Provides standing instructions, reference data (color tokens, terminology, schemas), or both.

**Examples:** brand-context.md for AI design tools, style guide pinned in a Project, API schema attached to a code-gen session, "company knowledge" file uploaded to a Custom GPT.

**Key sections:** Section map (instead of Prompt body), Per-session effort + File maintenance effort (split), Per-session review workflow + File maintenance review workflow (split), Slim mode (instead of V0 mode), `doc_version` in YAML alongside `prompt_version`.

### `type: prompt-pattern`

A reusable technique, not a concrete prompt. Describes a method that can be applied across many prompts. Has no prompt body — has a description of the technique, when to apply it, and worked examples of prompts that use it.

**Examples:** step-back prompting, ReAct, structured-intake-before-generation, push-back-on-generic-answers, chain-of-density summarization.

**Key sections:** "The pattern" (technique description) instead of Prompt body, "When this pattern pays for itself" instead of Expected effort, "Example prompts using this pattern" instead of Example output.

### `type: source-summary`

A summary of an external prompt source — someone else's published prompt, a paper's prompt template, an open-source repo's system prompt — captured for reference but not as a canonical asset.

**Examples:** summary of OpenAI's published GPT-4 system prompt, summary of a prompt from an Anthropic blog post, distilled version of a third-party agent's instruction set.

**Key sections:** Source attribution prominent, Differences from our practice, What we keep / what we discard. No prompt body unless the original is short and freely usable.

### `type: automation-prompt`

A prompt embedded in an automation, pipeline, or scheduled job. Different from `prompt` because it runs without a human in the loop and the failure modes are different (no human can correct the input).

**Examples:** weekly summarization job that runs over Slack archives, CI prompt that reviews PRs, scheduled report generator.

**Key sections:** Trigger conditions, Input pipeline, Failure handling (more detailed than `prompt`), Monitoring, Rollback procedure.

### `type: agent-instruction`

An instruction set for a multi-step agent that uses tools, makes decisions, and maintains state across steps. Different from `prompt` because it's not a single turn — it's a behavioral specification.

**Examples:** ReAct agent instructions, instructions for a customer-support agent that uses three tools, instructions for an autonomous research agent.

**Key sections:** Tool catalog, State model, Decision tree / control flow, Stopping criteria, Failure recovery, Loop guards.

## Decision tree

When in doubt, walk this tree top to bottom:

1. **Is this a description of a reusable technique that can be applied across many prompts?**
   - Yes → `type: prompt-pattern`. Stop.
   - No → continue.

2. **Is this a summary of someone else's prompt source, captured for reference?**
   - Yes → `type: source-summary`. Stop.
   - No → continue.

3. **Is this a file that gets attached to a session as standing instructions or reference data?**
   - Yes → `type: prompt-context`. Stop.
   - No → continue.

4. **Is this an instruction set for a multi-step agent (uses tools, makes decisions, maintains state)?**
   - Yes → `type: agent-instruction`. Stop.
   - No → continue.

5. **Is this a prompt embedded in an automation that runs without a human in the loop?**
   - Yes → `type: automation-prompt`. Stop.
   - No → continue.

6. **Is this a prompt sent to a model as a single instruction (or system prompt that's reused across instances)?**
   - Yes → `type: prompt`. Stop.
   - No → ask the user what they want to document. Library may need a new type.

## Mixed cases (worth disambiguating explicitly)

### A long prompt with embedded reference data (like brand-context.md)

If the asset is *primarily* attached as standing context (read once per session, constrains output), it's a `prompt-context` even if it ends with a copy-paste prompt template inside it. The brand-context.md is the canonical example: it ships with prompt templates in Sections 15 and 16, but it's still a `prompt-context` because users attach it once and pair it with the templates.

### A pattern with a worked-example prompt inline

If the asset is *primarily* explaining a technique (with the prompt as illustration), it's a `prompt-pattern`. If it's primarily a runnable prompt (with a brief mention of the underlying technique), it's a `prompt`.

### A system prompt for a Custom GPT or Claude Project

If the system prompt is meant to be reused across instances or copied into other projects, document it as `type: prompt`. If it's a one-off for a specific project that won't be reused, it doesn't belong in the library at all.

### An agent that's mostly one big system prompt with one tool

Boundary case between `prompt` and `agent-instruction`. Use `agent-instruction` if there's any control flow, state, or tool use. Use `prompt` only if it's a single-turn instruction with no decision-making structure.

### A `brand-context.md` actively edited turn-by-turn during a session

That's not a context payload anymore — it's a working document. Don't document it as either; it's not a reusable asset.

### A scheduled CI check that calls Claude

`type: automation-prompt`. Even if the prompt itself is short, the automation framing matters because the failure modes (no human to correct input, must self-recover) are different from interactive use.

## Section name mapping by type

Some sections take different names depending on type. Use this mapping when drafting:

| Section concept | `prompt` | `prompt-context` | `prompt-pattern` | `automation-prompt` | `agent-instruction` |
|---|---|---|---|---|---|
| Readiness routing | "Input readiness" | "Session readiness" | "Applicability check" | "Trigger conditions" | "Activation conditions" |
| Effort | "Expected effort" | "Per-session effort" + "File maintenance effort" | "When this pattern pays for itself" | "Per-run cost" + "Maintenance" | "Per-task effort" |
| Workflow | "Review workflow" | "Per-session review workflow" + "File maintenance review workflow" | "How to apply" | "Operations runbook" + "Incident response" | "Operations runbook" |
| Thin-input mode | "V0 mode" | "Slim mode" | n/a | "Degraded mode" | "Fallback behavior" |
| Body | "Prompt body" | "Section map" | "The pattern" | "Prompt body" + "Pipeline integration" | "Instruction body" + "Tool catalog" |
| Examples | "Example invocation" + "Example input" + "Example output" | "Example invocation" only (3 patterns: correct + incorrect) | "Example prompts using this pattern" | "Example run + log" | "Example trajectory" |

## Sections that don't apply per type

- `prompt-context` entries do not have "Example input" or "Example output" — they don't produce output.
- `prompt-pattern` entries do not have a prompt body, runtime variables, or output shape — they describe a method, not a deliverable.
- `source-summary` entries do not need their own quality checklist — they're descriptive of someone else's work.
- `prompt` entries that are conversational (elicit variables through dialogue rather than a fixed input block) still need a Variables section, but should explicitly say the prompt is conversational and list the conceptual variables.

## YAML differences by type

| Field | `prompt` | `prompt-context` | `prompt-pattern` | `source-summary` | `automation-prompt` | `agent-instruction` |
|---|---|---|---|---|---|---|
| `prompt_version` | required | required (file version) | required | n/a (use `source_date`) | required | required |
| `doc_version` | optional | required | optional | required | optional | optional |
| `model_tested` | required | required | optional (mostly model-agnostic) | optional | required | required |
| `linked_patterns` | required | required | required (composes-with list) | required (which patterns the source uses) | required | required |
| `linked_automations` | optional | optional | optional | optional | required (the automation itself) | required (the agent itself) |

## When to suggest creating a new type

If you're documenting an asset that genuinely doesn't fit any of the six types, do not stretch one to fit. Tell the user, suggest a name for the new type, and proceed by following the closest existing type's structure with explicit notes about where it diverges. Add it to `Open questions` for the library taxonomy.
