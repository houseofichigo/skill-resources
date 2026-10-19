# Prompt Contract and proportional tiers

Use this reference for general optimization and persistent instructions. The contract is a diagnostic model, not a mandatory output template.

## Six elements

1. **Goal** — the terminal outcome and main action. Always make this recoverable from the prompt.
2. **Context** — facts, inputs, audience, and background needed for the task. Keep dynamic retrieved material separate from durable instructions when the runtime can inject it.
3. **Rules** — real constraints, priorities, exclusions, permissions, and edge-case handling. Prefer affirmative behavior over repeated negative rules.
4. **Output Contract** — shape, fields, order, length, language, or destination. Make it explicit when another system or a strict review depends on it; it can remain implicit for obvious conversational output.
5. **Success Criteria** — observable conditions for correctness or quality. Replace “world-class” and numeric self-ratings with criteria a reviewer or test can check.
6. **Examples** — demonstrations needed to disambiguate format, classification boundaries, tone, or difficult edge cases. Do not add examples by habit.

Audit every element; mark an element unnecessary internally rather than forcing a heading into the result.

## Minimum sufficient tiers

| Tier | Use when | Typical content |
|---|---|---|
| Minimal | One-step, low-risk, obvious output | Goal |
| Standard | Context or format meaningfully affects the result | Goal, Context, Output Contract |
| Reliable | Errors matter or constraints must be testable | Goal, Rules, Output Contract, Success Criteria; optional functional perspective |
| Reusable | Prompt will be saved, shared, or parameterized | All applicable contract elements with named variables and defaults |
| Operational | Tools, state, permissions, retries, or handoffs are involved | Reusable contract plus tool boundaries, state, failure handling, stopping and escalation |

Move up a tier only for a concrete reason. A simple translation, proofreading request, short extraction, or direct question should not become a long contract.

## Overlays

Apply only when useful:

- **Functional perspective:** analytical method, professional standard, or risk posture. It is not a biography or prestige claim.
- **Audience and tone:** communication requirements, not decorations.
- **Sources and evidence:** acceptable source types, date range, citation expectations, and uncertainty handling.
- **Tools and permissions:** available capabilities and actions requiring authorization.
- **Reasoning effort:** runtime control when supported; not a request to reveal hidden reasoning.
- **Schema enforcement:** native runtime schema when available; textual formatting otherwise.

## Conflict resolution

- Preserve the user's actual objective before improving style.
- Resolve contradictory rules by asking when the choice changes the result; otherwise retain the more specific instruction and surface the assumption only if the user requested analysis.
- Do not add facts, permissions, integrations, or success claims that the user did not provide.
- Separate user-supplied content from instructions with headings or delimiters when confusion is plausible, but do not claim delimiters form a security boundary.
