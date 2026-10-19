# Compile target: Gemini Gem

A Gem is a saved, reusable Gemini persona: **instructions** + optional **knowledge files** + a name, created in the Gem manager/editor. It's the lightest of the three targets — the strength is Google Workspace proximity (Drive files, Docs/Sheets context), the weakness is that there's no Actions-style external API layer to configure per-Gem, and the configuration surface is thin.

So: pick this when the assistant lives inside someone's Google-centric workflow, and don't promise it integrations it can't have. If the requirement is "call our internal API and write to it", this is the wrong target — say so rather than faking it.

## The fields to fill (emit one paste-ready block per field)

| Field | What goes in it |
|---|---|
| **Gem name** | Function-first, scannable in a list of Gems. |
| **Instructions** | The whole behavior spec. This is nearly the entire product. |
| **Knowledge files** | Uploaded/attached reference files, typically from Drive. Verify the current file count and type limits in the editor. |

Some Gemini surfaces offer to "rewrite"/expand your instructions for you. Treat the output as a first draft only — it tends to inflate persona language and drop the hard rules that make the assistant testable. Keep the rules.

## Instruction anatomy

Gemini responds well to an explicitly structured, four-part frame. Use it as the skeleton and hang the rest of the spec on it:

```
# Persona
Who it is and what competence it brings. One or two lines. Competence, not costume.

# Task
What it does, step by step. Number the steps — this is where Gems most often go loose.
1. ...
2. ...
3. ...

# Context
Who it's for, what they already know, what they'll supply, and what the attached files are
authoritative for. State what to do when the answer is not in the attached files:
say it isn't there. Do not fill the gap silently.

# Format
The shape of a good answer: length, structure, what to include, what to leave out.
One short worked example beats three paragraphs of description.

# Boundaries
Out of scope → what it does instead.
Refusals → what it declines and where it redirects.
Uncertainty → what it says when it doesn't know.
```

Two things specific to this target:

- **Be more explicit about the workflow steps than you'd need to be elsewhere.** Thin configuration surface plus a strong general model means the persona will happily improvise past your intent. Numbered tasks hold better than described ones.
- **Name the files by name in the instructions.** "Use the attached Pricing 2026 sheet for all figures" ties the behavior to the knowledge; "use the attached files" doesn't.

## Sharing

Gems are personal by default; sharing runs through the Workspace/Drive sharing model rather than a public store. Confirm what your Workspace tier actually permits before promising a team rollout — this varies by plan and moves. Assume anyone you share with can see the instructions and the files.

## Ship checklist

- [ ] Persona / Task / Context / Format / Boundaries all present
- [ ] Workflow steps are numbered, not narrated
- [ ] Attached files are referenced by name in the instructions
- [ ] Explicit "not in the attached files" behavior exists
- [ ] Explicit uncertainty and refusal behavior exists
- [ ] Nothing in instructions or files is unfit for everyone it's shared with
- [ ] No credentials or personal data anywhere
- [ ] 8–12 test prompts run in a fresh chat, including a knowledge-miss and a refusal
- [ ] The integration story is honest — no promised API calls the Gem can't make
- [ ] An owner and a review date exist
