# Quality bar — final acceptance criteria

Run the doc against this bar before presenting it to the user. The bar has 12 items. Acceptance threshold depends on the documentation level chosen in Step 3:

- **Lightweight** — pass at least 8 of 12.
- **Standard** — pass at least 10 of 12.
- **Operating system** — pass at least 11 of 12.

If anything fails, fix it before presenting.

## The 12 acceptance criteria

### 1. Purpose is clear

A reader can understand in one sentence what this prompt does, what it produces, and who it's for.

**Fail signal:** "This prompt helps with content." (too vague — could be anything)
**Pass signal:** "Generates a complete strategic brand book as a self-contained HTML file, customized to the user's business through a structured five-phase intake."

### 2. Use and non-use cases are explicit

Both `When to use` and `When not to use` are present and specific. The non-use list points to alternative approaches.

**Fail signal:** "When to use: when you need to generate content." (could apply to any prompt)
**Pass signal:** Specific situations the user described in intake, with the alternatives named for out-of-scope cases.

### 3. Required inputs are listed

A flat list shows every discrete input. Scannable in 30 seconds.

**Fail signal:** Inputs are described in prose only, scattered across the document.
**Pass signal:** A bulleted list near the top, one input per line.

### 4. Variables are documented if reusable

For prompts with placeholder variables or conversational variable elicitation, the surface area appears as a list. For prompts that aren't parameterized, this section can be omitted with a note explaining why.

**Fail signal:** Variables exist in the prompt body but aren't listed in a variables section.
**Pass signal:** Every `[BRACKETED]` token in the prompt body appears in the variables list with a one-line explanation.

### 5. Output shape is verifiable

The output spec is a checklist, not a paragraph. Each item is checkable.

**Fail signal:** "Output should be a well-structured document with appropriate sections."
**Pass signal:**
- [ ] Output is HTML.
- [ ] Includes sidebar navigation grouped into 5 super-sections.
- [ ] Each section opens with section-meta and a lede paragraph.
- [ ] No `[BRACKETS]`, no lorem ipsum, no "TODO".

### 6. Quality checklist exists and is specific

For Standard / Operating system levels. Each test is named and testable. Generic items don't count.

**Fail signal:** "Output is high quality." (not testable)
**Pass signal:** "Specificity test — pick 3 random paragraphs. Could they appear in any other company's document in the same sector? If yes for any of the 3, the doc fails."

### 7. Prompt body or section map is present

For `prompt`: the prompt body appears in full, in a code fence, ready to paste.
For `prompt-context`: a section map of the external file (the file itself is canonical; don't duplicate).
For `prompt-pattern`: the technique is described, not a prompt.

**Fail signal:** Body section says "see the file at X" without a section map, OR includes the entire file's content.
**Pass signal:** Right body type for the asset type.

### 8. Examples calibrate correct use

For Lightweight: one input/output example. For Standard: correct + incorrect invocation. For Operating system: also example input and example output.

**Fail signal:** Examples are absent or are abstract descriptions ("the model would produce a brand book").
**Pass signal:** Concrete examples with actual input strings and excerpts of actual output.

### 9. Failure modes are documented

If the prompt is in production, list observed failures with fixes. If pre-launch, label them as anticipated.

**Fail signal:** "Failures observed: works well across all models" when the user said "only tested in Claude Opus."
**Pass signal:** "This prompt is v1.0 and has been run end-to-end zero times against a real business other than the source one. Anticipated failure modes (to be confirmed with run logs): ..."

### 10. Version history and changelog are present

Both sections appear. Version history captures prompt evolution. Changelog captures documentation edits. For `prompt-context`, the version history is split into File and Documentation.

**Fail signal:** Either section is missing, or both contain only "v1.0 — initial".
**Pass signal:** Each version has a date and a one-line description of what changed.

### 11. Open questions are honest

Open questions point at real next steps. Not throat-clearing.

**Fail signal:**
- "Could be improved further."
- "More testing needed."
- "Is this good?"

**Pass signal:**
- "Has anyone other than the source business produced output of comparable depth using this prompt? No production runs yet — the prompt is unevaluated end-to-end."
- "Reviewer field in YAML is empty — assign before this hits production, otherwise the review_due date is unenforceable."
- "Quality checklist threshold — is 'passes 8 of 10' the right bar? Need to validate against real outputs before locking it."

### 12. Related entries are linked

The `Related` section names other library entries this one connects to. If the user has a sibling prompt or context payload, it must appear here.

**Fail signal:** `Related: []` when the user named a sibling prompt during intake.
**Pass signal:** `[[sibling-entry]] — relationship.` for each related asset.

## Anti-patterns to catch at draft time

These are the failure modes most likely to slip through. Catch them before showing the user.

### Anti-pattern: Generic operating principles or use cases

Items that would apply to any prompt in the same category.

**Catch:** read each item and ask "would this prompt's competitors disagree with this?" If everyone would nod along, it's a slogan.

### Anti-pattern: Invented evidence

Claims about behavior, performance, or test coverage that the user didn't actually validate.

**Catch:** cross-check every quantitative claim and every "we observed" statement against what the user said in intake. If they didn't say it, don't write it.

### Anti-pattern: Flattery

Words like "powerful", "robust", "comprehensive", "world-class", "industry-leading", "best-in-class", "cutting-edge", "revolutionary", "transformative" appearing in the descriptive prose.

**Catch:** search the doc for these words before saving. Each hit is a rewrite trigger.

### Anti-pattern: Section name conflation

Using the wrong section name for the type — e.g., "Prompt body" on a `prompt-context` entry, or "Example output" on an entry that doesn't produce output.

**Catch:** consult the section name mapping table in `type-taxonomy.md` before drafting.

### Anti-pattern: Silent omission

Dropping a section because it doesn't fit, without explaining why.

**Catch:** if a section is omitted, either explain the omission inline or include the section name with a one-line explanation of why it's empty.

### Anti-pattern: Filler tags

`tags: [TODO]`, `tags: [misc]`, `tags: [prompts]` (already implied by `book: prompts`).

**Catch:** tags should be 3–6 specific topical labels. Generic tags should be replaced with specific ones from the prompt's actual scope.

### Anti-pattern: Defaulting to `type: prompt`

Picking `prompt` because it's the first option, without walking the type taxonomy.

**Catch:** if you didn't explicitly walk the decision tree from `type-taxonomy.md`, walk it now before saving.

### Anti-pattern: Stuffing intake answers verbatim

Pasting the user's raw intake answers into the doc without rewriting them in the descriptive voice the library uses.

**Catch:** read each section aloud. Does it sound like a library entry, or like a chat transcript? If the latter, rewrite.

### Anti-pattern: Locking a reusable prompt to the originating business

Documenting a prompt that *could* be reused across businesses as if it only ever runs for the originating one.

**Catch:** the business-specificity check in Step 2 should have surfaced this. If `Adaptation notes` is missing or shallow, the doc has failed the reusability goal — which is the point of the library.

### Anti-pattern: Over-documenting simple prompts

A 400-line library entry for a 20-line utility prompt.

**Catch:** if the prompt is simple, use the Lightweight level (under 120 lines of doc). Don't force every prompt into the Operating system template.

## Final pre-save check

Before calling `present_files`, verify:

1. The filename is slug-style with version suffix (`brand-book-generator-v1.0.md`, not `Brand Book Generator.md`).
2. The file is saved to the requested or host-supported artifact location.
3. The YAML parses (no missing colons, no quote mismatches).
4. The first H1 matches the asset's name.
5. Section order matches the chosen template — Quick start near the top, Open questions and Related near the bottom.
6. The matching reference example was consulted (not just the template).
7. The business-specificity question was asked (Step 2) and the answer is reflected in `Adaptation notes`.

If any of these fail, fix and re-check before presenting.
