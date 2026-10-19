# Archetypes

Most builds are a variant of one of six shapes. Find the closest one, borrow its spine, and pay attention to its named failure — that's the rule people forget, every time, on every platform.

Don't force a build into an archetype it isn't. These are starting points, not moulds.

---

## 1. Tutor / learning assistant
Teaches a subject to a learner over repeated sessions.

**Spine:** diagnose level → explain at that level → check understanding with a question → adapt.
**Non-negotiable rules:** never give the final answer to a graded exercise outright; ask before assuming prior knowledge; one concept at a time.
**Signature failure:** it answers the homework. Design the refusal explicitly — "when asked for a solution to an assessed exercise, give the method and the next step, not the answer."

## 2. Research assistant
Finds, synthesizes, and summarizes information for someone who will act on it.

**Spine:** clarify the question → gather → synthesize → state confidence and gaps.
**Non-negotiable rules:** separate sourced claims from inference, always; cite; say what it couldn't find.
**Signature failure:** fluent synthesis with invented specifics. Force the split: "label every claim as [source] or [inference]."

## 3. Internal knowledge assistant
Answers questions from a company's own documents (policy, process, product).

**Spine:** route via the index → answer from the authoritative doc → quote → cite → escalate on miss.
**Non-negotiable rules:** files beat priors; never generalize a policy that isn't written; name the escalation route (who the human is).
**Signature failure:** invents a plausible policy. This is the archetype where "not in the files → say so" is load-bearing. See `knowledge-design.md`.

## 4. Support / FAQ assistant
Handles a bounded set of customer or user questions, usually with an approved answer set.

**Spine:** identify the intent → answer from approved content → offer the next step → hand off cleanly.
**Non-negotiable rules:** approved answers only; never improvise commitments (refunds, deadlines, prices); every unresolved case gets a hand-off path, not an apology loop.
**Signature failure:** it makes promises the business must honor. Enumerate what it may never commit to.

## 5. Writing / editing assistant
Drafts or improves text in a specific voice and format.

**Spine:** understand purpose and audience → draft or critique against named criteria → deliver in the required format.
**Non-negotiable rules:** state the criteria it edits against; preserve the author's meaning; flag rather than silently fix factual claims.
**Signature failure:** it flattens everything into the same voice. Give it explicit voice rules and at least one worked example of "good" — examples beat adjectives here more than anywhere else.

## 6. Workflow / task assistant
Runs a repeatable multi-step procedure, often with a tool at the end.

**Spine:** collect the required inputs → validate them → execute the steps in order → confirm before anything irreversible → report what happened.
**Non-negotiable rules:** never proceed on missing inputs — ask; confirm before side effects; state the failure contract (what it says when a step or a tool call fails).
**Signature failure:** it skips a step or fires the tool on ambiguous intent. Number the steps, name the preconditions, and make the confirmation gate explicit.

---

## Choosing

| If the job is mostly… | Use |
|---|---|
| Explaining, over time, to a learner | Tutor |
| Finding and condensing outside information | Research |
| Answering from *our* documents | Internal knowledge |
| Deflecting a known question set | Support / FAQ |
| Producing or improving text | Writing / editing |
| Doing a procedure, in order | Workflow |

Two archetypes at once (e.g. "answers from our docs *and* drafts the reply") is common and fine — but write the workflow so the two modes are explicitly separated, otherwise the drafting mode will start inventing the facts the knowledge mode was supposed to look up.
