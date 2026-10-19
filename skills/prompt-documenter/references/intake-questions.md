# Intake questions — what to ask the user

Ask questions in groups (1–4 per turn), not all at once. Reflect back what you heard before moving to the next group. Push back on thin or generic answers using the calibration table at the end.

If the user has already pasted the prompt, extract what you can from it directly — don't ask the user to repeat what's visible. Focus the intake on what isn't visible: triggering, failure modes, ownership, lineage, business-specificity.

## Universal questions (ask first, regardless of type)

These six questions identify what's being documented, confirm the type, and surface business-specificity early.

1. **What is this prompt called?** A human-readable name, not a slug. (You'll generate the slug from this.)
2. **What does it do, in one sentence?** This becomes the `Purpose` opening.
3. **Where does it live?** A file path, a project, or "I just have it in my notes". This becomes `canonical_location`.
4. **What type is this — a prompt sent to a model, a context file attached to a session, a reusable technique, a summary of someone else's prompt, an automation, or an agent?** If unclear, walk the decision tree from `type-taxonomy.md`.
5. **What version is this?** If they don't know, this is v1.0. If they've been iterating, ask what changed and capture the version history.
6. **Is this in production yet, or is this v1 / pre-launch?** Determines whether `Failures observed` reports observed or anticipated failures, and whether status is `living` or `draft`.

### Business-specificity check (asked in Step 2 of the workflow, before intake proper)

If the prompt mentions specific businesses, clients, products, or domains by name, ask the option-A/B/C question from SKILL.md Step 2. Capture the answer; it shapes the `Adaptation notes` section and may shape the prompt body itself.

## For `type: prompt` — additional intake

Six groups of questions. Ask in order.

### Group 1 — Reuse case

7. **Who uses this prompt?** Single author, team, anyone in the company, anyone publicly?
8. **For what kind of input does it run?** Domain, document type, business sector. Push for specifics.
9. **For one business, or designed to be reusable across businesses?** If business-specific, refer back to the Step 2 answer.

### Group 2 — Triggering

10. **When should someone use this prompt? Give me 3–5 specific situations.** Push for specifics — "when writing content" is too generic.
11. **When should someone NOT use this prompt? Give me 3 cases where a different prompt or approach is the right fit.** Most prompts have at least three out-of-scope cases worth naming.
12. **What's the readiness needed to invoke this? What inputs does the user need ready before they start?** Translates to the Low/Medium/High readiness table (only for Standard/Operating system levels).

### Group 3 — Mechanics

13. **What inputs does the prompt need, listed as a flat list?** Capture everything — user-supplied data, attached files, references.
14. **Does the prompt have placeholder variables?** If yes, list them. If the prompt elicits variables conversationally, say so and list the conceptual variables anyway.
15. **What does the output look like — format, length, structure?** Translates to the `Output shape` checklist. Push for specificity (a checklist beats a paragraph).

### Group 4 — Quality

16. **What does a good output look like? Give me 8–12 specific tests a reviewer can run against an output.** This is the most important section. Push back on platitudes ("the output should be high quality"). Examples of good tests: "Could this paragraph appear in any other company's brand book?" "Does the output use only CSS variables, no hardcoded hex codes?"
17. **What does a bad output look like? What failure modes have you seen — or do you anticipate?** Distinguish observed (production) from anticipated (pre-launch).

### Group 5 — Operational (only for Standard / Operating system levels)

18. **Roughly how long does intake / generation / review take?** Translates to `Expected effort`.
19. **Walk me through the end-to-end workflow for using this prompt.** Translates to `Review workflow` (8–10 steps).
20. **Is there a thin-inputs / draft-only mode (V0)?** If yes, what changes in V0 vs V1?
21. **Who owns this prompt? Who maintains it? Who reviews changes?** Translates to YAML `owner`, `maintainer`, `reviewer`. Empty `reviewer` is fine for now if not assigned.

### Group 6 — Lineage (only for Standard / Operating system levels)

22. **What other library entries does this relate to?** Sibling prompts, adjacent patterns, parent docs.
23. **What patterns does this prompt use?** Structured intake? Role priming? Refusal-on-thin-inputs? List as `linked_patterns`.
24. **Which models has this been tested on?** Translates to `model_tested`. Be honest — "Claude Opus 4.7 only" is fine.

### Group 7 — Examples (only for Operating system level)

25. **Can you give me one synthetic example of a full intake / use of this prompt?** Walk through it as a user would. This becomes `Example input`. Use a *generic* synthetic business (Acme, fictional company, hypothetical user) unless the user explicitly wants a specific named anchor.
26. **Can you show me one piece of generated output (or describe it)?** Becomes `Example output`. If too long, just one section/excerpt at the right fidelity.

## For `type: prompt-context` — additional intake

Five groups. Different from `prompt` because there's no prompt body and no output to show.

### Group 1 — Pairing

7. **What does this file get paired with? List the prompts, tools, or sessions it's attached to.** Translates to the `Required inputs / What to attach` section.
8. **In which AI tools is this file used?** Claude Projects, ChatGPT Custom GPTs, Gemini Gems, NotebookLM, Lovable, Cursor, v0, Gamma, Canva, Google Slides — list every named tool. Translates to `When to use` and the per-tool behavior notes in `Model and parameters`.
9. **What constraints does the file enforce?** Voice rules, color tokens, controlled terminology, schemas, anti-patterns. Becomes part of the `Section map`.

### Group 2 — Session mechanics

10. **What needs to be true for a session to be ready to invoke this?** File attached, supporting assets on hand, brief defined. Translates to `Session readiness` (Low/Medium/High table).
11. **How long does a single session take, end-to-end?** Translates to `Per-session effort`.
12. **What's the workflow for a single session?** Translates to `Per-session review workflow`.

### Group 3 — Maintenance

13. **How often does the file itself need review or update?** Quarterly? Per upstream version bump? When a new tool joins the stack? Translates to `File maintenance effort`.
14. **What's the workflow for updating the file?** Translates to `File maintenance review workflow` (10 steps including changelog, version bump, downstream notification).
15. **Is there a slim version of the file for low-context tools?** If yes, what's in it and what's omitted. Translates to `Slim mode`.

### Group 4 — Quality and failures

16. **What does a good output look like, when this file is properly attached?** The output checklist (constrains downstream output).
17. **What does a healthy version of the file itself look like?** A separate checklist for the file itself.
18. **What recurring failures have you seen — both in outputs and in how the file gets used?** Distinguish output failures from operational failures (file not attached, wrong logo, etc.).

### Group 5 — Lineage and ownership

19. **What other library entries does this relate to?** Especially the prompts that pair with it and the source documents it's derived from.
20. **What patterns does this file embody?** Context-payload-as-instruction, controlled-terminology-block, etc.
21. **Owner / maintainer / reviewer?** Same as for prompts.

## For `type: prompt-pattern` — additional intake

The library doesn't yet have a worked prompt-pattern entry. Adapt the prompt template:

7. **Describe the pattern in one paragraph.** What's the technique?
8. **When does it pay for itself? When is it overkill?**
9. **Show me 2–3 short example prompts that use this pattern.** These can come from the user's own prompt library or the public literature.
10. **What other patterns does it compose with? What does it conflict with?**

Flag this as an opportunity to start a pattern-page sub-library if more pattern entries are coming.

## For `type: source-summary` — additional intake

7. **What's the source — paper, blog post, GitHub repo, public Custom GPT?** Capture the URL and access date.
8. **In one paragraph, what does the source prompt do?**
9. **What does the source do well that we should learn from?**
10. **What does the source do that we'd avoid? Why?**
11. **Is the source freely usable, or do we just summarize it?** Affects whether the prompt body can be reproduced.

## For `type: automation-prompt` — additional intake

7. **What automation runs this? Cron job, CI pipeline, webhook, scheduled function?**
8. **What triggers it? Time, event, manual run?**
9. **What's the input pipeline — where does the input come from, and how is it shaped before reaching the prompt?**
10. **What happens when the prompt fails? Retry? Alert? Silent skip?**
11. **How is output consumed downstream? Stored, displayed, fed into another prompt?**
12. **How is this monitored? Logs, dashboards, alerts?**

## For `type: agent-instruction` — additional intake

7. **What tools does the agent have access to? List them with one-line descriptions.**
8. **What's the agent's stopping criteria? Max iterations, success condition, timeout?**
9. **What state does the agent maintain across steps? Memory, scratchpad, conversation history?**
10. **What's the control flow? Strictly linear, ReAct-style reason-then-act, planner-executor split?**
11. **What happens when a tool call fails? Retry, fallback to another tool, abort and ask the user?**
12. **What loop guards prevent the agent from running forever?**

## Push-back calibration table

When the user gives a thin or generic answer, do not accept it. Use this table for sharper re-asks.

| Thin answer | Sharper question |
|---|---|
| "It's used for content generation." | "Pick a specific kind of content. Who's the reader? What's the deliverable?" |
| "The output should be high quality." | "Give me three specific tests. 'Are paragraphs under 80 words?' beats 'is it well-written?'" |
| "We've tested it widely." | "Which models specifically? How many runs? What's the failure rate you've seen?" |
| "It works well in production." | "What did the last failure look like? When was it? What changed after?" |
| "The user provides the inputs." | "List every input as a flat list. If you can't list them, the prompt isn't documented yet." |
| "The prompt is for our company." | "Is the prompt logic specific to your company, or could it work for any company in your sector? Document only what's truly company-specific in the prompt body." |
| "It's flexible — works for many use cases." | "Name three. If you can't, the flexibility is hypothetical." |
| "We use it whenever we need to write." | "What writing? Pick the top 3 use cases by frequency." |
| "It produces good output." | "Show me one concrete output and one bad output. The contrast is the spec." |
| "Failures are minor." | "Name the last three. If you can't, you don't have failure data — say so." |

Stop pushing when the user explicitly says "skip this" or "I don't know" — mark the section as TBD or omit it. Do not invent.

## Skipping intake when the prompt is self-documenting

If the user pastes a fully-written prompt with all the context they need, you can sometimes draft directly from the prompt itself:

- Name, purpose, body, variables, structure → extractable from the prompt.
- Output shape → often inferable.
- When-to-use, when-not-to-use, failures, ownership, related entries → still need to ask.

Even in this case, ask the universal six questions plus the operational and lineage groups for Standard/Operating system levels. The mechanics and examples can come from the prompt itself.
