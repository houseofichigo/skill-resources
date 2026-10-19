# Compile target: Claude Project

A Project is a persistent workspace: **project knowledge** (documents and context available to every conversation in it) + **custom instructions** (how Claude behaves inside it) + the conversations themselves. It's the right target for document-heavy, reasoning-heavy, team-shared internal work.

What it is *not*: a public product. There is no store, no store review, no anonymous distribution. Sharing is to people who share your workspace. That means the safety bar is "would I be comfortable if a colleague read this" rather than "would I be comfortable if the internet read this" — but the extraction rule still holds: anyone in the project can get at the knowledge and the instructions, so nothing goes in that shouldn't reach every member.

## The fields to fill (emit one paste-ready block per field)

| Field | What goes in it |
|---|---|
| **Project name** | Function-first. Colleagues will scan a list. |
| **Project description** | One or two lines — what this project is for, so people don't use the wrong one. |
| **Custom instructions** | The behavior spec. The main artifact. |
| **Project knowledge** | The documents. Usually a small, curated set plus an index doc. |

There are no capability toggles or Action schemas to fill in — tool access comes from the workspace's configured tools/connectors rather than from a per-assistant form. So don't emit a "capabilities" block. If the assistant needs to reach a live system, say plainly that this depends on what's connected to their workspace and that they should confirm it before designing a workflow around it.

## Instruction anatomy

Same spine as any assistant, with the emphases Claude actually rewards:

```
# Role and objective
One sentence each.

# How to use the project knowledge
- [doc name] is authoritative for [what].
- Cite the source document when you use it.
- If the answer isn't in project knowledge, say so explicitly before reasoning from general knowledge — and label which is which.

# Workflow
The 3–6 steps for a typical request.

# Reasoning and rigor
- Where to think carefully before answering (name the high-stakes cases).
- Where a fast direct answer is the right call — otherwise it over-thinks trivia.

# Constraints and refusals
Hard rules. What it declines, and where it routes instead.

# Uncertainty
What "I don't know" looks like here, and what it offers instead.

# Output
Default shape. When to produce a document/artifact versus answering in chat.
```

Two things specific to this target:

- **Say when to write a document versus answer inline.** Left unsaid, the model guesses, and you get either a wall of chat or a document for a one-line question. Name the threshold: "produce a document for deliverables the user will send elsewhere; answer in chat for questions, reviews, and decisions."
- **Ask for source attribution.** With project knowledge, "cite which document this came from" is cheap and it turns a hallucination into a checkable claim.

## Knowledge

The project knowledge window is finite and shared by every conversation. Curate: 6 sharp documents beat 40 mediocre ones, and a bloated project degrades every answer in it, not just the one that needed the extra file. Include an index document that says what each file is for and when to use it — see `knowledge-design.md`.

Don't paste a policy manual into custom instructions because it "feels safer there". Instructions are read on every turn and rot under length; knowledge is retrieved when needed. Long lookup content goes in knowledge.

## Ship checklist

- [ ] Instructions are rules, not adjectives
- [ ] Explicit "not in project knowledge" behavior exists
- [ ] Source attribution is requested
- [ ] Document-vs-chat threshold is stated
- [ ] Knowledge is curated and indexed, not dumped
- [ ] Nothing in knowledge or instructions is unfit for every project member to read
- [ ] No credentials or personal data anywhere
- [ ] 8–12 test prompts run in a fresh conversation, including a knowledge-miss and a refusal
- [ ] An owner and a review date exist
