# Compile target: OpenAI Custom GPT

A Custom GPT is configuration, not training. You are orchestrating four levers — Instructions, Knowledge, Capabilities, Actions — on top of a model you don't control. Everything you can't put in one of those four levers, you can't have.

Build in the **Configure** tab, not the conversational "Create" wizard. The wizard writes vague instructions that read well and grade badly.

## The fields to fill (emit one paste-ready block per field)

| Field | What goes in it |
|---|---|
| **Name** | Function-first, not clever. The user picks it from a list of GPTs six months from now. |
| **Description** | One or two lines: what it does, who it's for. Shown before anyone opens it. |
| **Instructions** | The behavior spec. The main artifact. Character-capped — keep it tight (verify the cap in the UI). |
| **Conversation starters** | 3–4. Real first questions, not slogans. These are the only onboarding most users get. |
| **Knowledge** | Uploaded files. See `knowledge-design.md` before recommending any. |
| **Capabilities** | Web browsing, image generation, code interpreter & data analysis. Toggle on only what the job needs. |
| **Actions** | OpenAPI schema + auth. Only if it must reach an external system. |

## Instruction anatomy that survives contact with users

Write in this order. It maps to how the model reads under pressure — role and scope up top, edge behavior at the bottom where it's still visible after a long context.

```
# Role
One sentence. What competence, for whom.

# Objective
The outcome. What a good session produces.

# Scope
In scope: ...
Out of scope: ... → what you do instead (redirect, escalate, decline)

# Workflow
1. ... 2. ... 3. ...   (the steps it runs on a typical request)

# Knowledge rules
- The uploaded files are authoritative for X, Y, Z.
- When the files disagree with your prior knowledge, the files win — and say so.
- When the answer is not in the files, say it is not in the files. Do not fill the gap from general knowledge.

# Constraints
- Never ...
- Always ...
- Ask before ...

# Uncertainty
When you are not confident: state the uncertainty, name what would resolve it, offer the best available partial answer.

# Refusals
Decline: ... Redirect to: ...

# Tone and output
Register, default length, default format. Give one worked example of a good answer if format matters.
```

Two failure modes worth designing against explicitly, because they're near-universal:

- **Instruction drift** — the GPT obeys for four turns and forgets by turn twelve. Cause: rules buried in prose. Fix: short imperative lines, grouped under headers, no narrative.
- **Confident gap-filling** — the GPT invents a policy that isn't in the policy PDF. Cause: no explicit miss behavior. Fix: the "not in the files" rule above, stated as a rule, not a hope.

## Capabilities — decide, don't default

Every capability you leave on is a behavior you now have to test and a surface you now have to secure.

- **Web browsing** — on only if the job needs current information. It will otherwise pull public web answers over your knowledge base and quietly contradict it.
- **Code interpreter / data analysis** — on if the GPT computes, parses, or charts uploaded data. Note that it lets users *download* what's in the sandbox; treat it as raising the exposure of anything you upload.
- **Image generation** — on only if it produces images. Otherwise it's noise.

## Actions — only when the GPT must reach outside

Actions are API calls defined by an OpenAPI schema, with auth (API key or OAuth). Use them for live data or side effects. Do not use them to "give it knowledge" — that's what knowledge files are for.

Design rules that prevent the usual damage:

- **Scope the endpoints.** Expose the two operations the assistant needs, not the whole API. Anything exposed is callable by anyone using the GPT.
- **Mark side-effecting operations as consequential** so the user is asked to confirm before it writes, sends, deletes, or pays.
- **Never inline a credential** in the instructions or the schema — auth belongs in the auth config, and even there, assume the GPT will be probed for it.
- **Keep responses small.** A verbose endpoint payload eats the context window and degrades everything after it. Put a thin middleware in front of a chatty API and return only the fields the assistant reasons over.
- **Write the error contract.** What the GPT says when the call fails, times out, or returns empty — otherwise it will invent a plausible result.

When the requirement is deep, standardized, or multi-tool integration rather than a couple of endpoints, say so and point at the MCP/Apps path instead of bolting on ten Actions — but don't assert current MCP/Apps availability or requirements from memory; verify (see `portability-and-drift.md`).

## Sharing tiers

Private (builder only) → link/workspace (anyone with the link, or the org) → public (store). The safety bar rises steeply at each step, and it is a one-way door in practice: once a link is out, assume it's out.

Public publishing additionally implies name/branding review (don't imply affiliation with OpenAI or any brand you don't own), a privacy policy if it calls external Actions, and store review that can restrict or reject.

## Ship checklist

- [ ] Instructions are rules, not adjectives — a tester could grade each line
- [ ] Explicit "not in the files" behavior exists
- [ ] Explicit uncertainty and refusal behavior exists
- [ ] Only necessary capabilities are on
- [ ] Knowledge files contain nothing that can't be published (assume extraction)
- [ ] No credentials, keys, or personal data in instructions, knowledge, or schema
- [ ] Consequential Actions require confirmation
- [ ] Actions have a failure contract
- [ ] 8–12 test prompts run in a fresh chat, including a knowledge-miss and a refusal
- [ ] Conversation starters are real questions
- [ ] An owner and a review date exist
- [ ] If public: naming, privacy policy, and store rules checked in the current docs
