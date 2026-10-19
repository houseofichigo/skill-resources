<!--
STAMP THIS into your new skill's SKILL.md.
Replace every <placeholder>. Delete guidance comments before shipping.
Keep it under ~2,500 words: reference detail goes in references/, not here.
The description below is what makes the skill fire at the right time — write it last, after the skill exists, and name what it is NOT for.
-->
---
name: <skill-slug-kebab-case>
description: <One or two sentences. Name the deliverable, who it is for, and the concrete outputs. Then the trigger phrases a user would actually type. Then, critically, what this skill is NOT for and which neighbouring skill covers that instead — so it does not fire over a sibling.>
license: <SPDX identifier, for example MIT>
---

# <Deliverable name>

<One paragraph: what this skill turns inputs into, and the one thing that makes its output good rather than merely correct. Point at the craft file.>

Read `references/<craft>.md` before producing anything: it holds the shape and the recipe that separate a flat first pass from the version the client keeps.

## What bends / what never bends

- **Never bends (the look):** <palette, logo, fonts, approved claims, correctness>. Defer to the user's approved external brand source rather than copying private tokens into the skill.
- **Bends (the craft):** <the deliverable-specific craft: density, pacing, structure, emphasis>.

## Non-negotiables

- **Remember.** Read `<path>/PROFILE.md` first; reuse Owner choices; only ask what is new. Write choices back so the next run starts where this one ended.
- **Ask little.** Use the host's question tool when available, with a concise chat fallback; ask no more than four questions at once. Never ask what discovery answered.
- **Real facts only.** <Prices, dates, names, numbers, quotes> come from the user word for word; never invented.
- **<Deliverable-specific invariant>.** <e.g. one message per output; every claim traceable to source.>
- **Verify the artifact.** The last step opens the produced file and checks it against the contract.
- **Ask first** before <committing / sending / publishing>. Keep every version.

## Workflow

1. **Read the profile.** `<path>/PROFILE.md` if it exists — it is the brand; refresh only what changed. See `references/discovery.md` after creating it from the supplied stub.
2. **Discovery.** From whatever the user gave — brand files, codebase, URL, or nothing — fill the profile. See `references/discovery.md`.
3. **Interview.** The variant, the facts, the assets, the one-off choices. See `references/interview.md` after creating it from the supplied stub.
4. **Brief.** Fill `assets/templates/brief.template.md` for this run.
5. **Produce.** Read `references/<craft>.md` and build the deliverable from the profile + brief.
6. **Review.** See `references/review.md` after creating it from the supplied stub: run specific checks against the real artifact. Fix, repeat, and report what changed.
7. **Deliver and remember.** Send the artifact; add it to the profile's log; turn lasting notes into Owner choices.

## Quality floor (whatever the inputs)

- <Invariant 1 — holds regardless of how much brand material existed.>
- <Invariant 2.>
- <Invariant 3.>

## Traps that cost real time (each one happened)

<!-- Seed from your two dry runs. Phrase each as the rule, not the story. Add one every time the skill burns a real deliverable. -->
- <Trap 1.>
- <Trap 2.>
