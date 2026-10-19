# Ship gate: is this production skill done?

Run top to bottom before you call the new skill shippable. Any "no" is a blocker, not a nice-to-have. Written to be read as the last step of the kit's workflow.

## Structure
- [ ] SKILL.md is under ~2,500 words and contains only: non-negotiables, workflow, quality floor, traps.
- [ ] Every `references/` file is linked from exactly one workflow step and read only there.
- [ ] No reference material has leaked into SKILL.md (no background the model already knows).
- [ ] The folder matches the shape in [architecture.md](architecture.md) — references/, assets/templates/, and scripts/ only if needed.

## Triggering
- [ ] The description names the deliverable, the trigger phrases, AND what the skill is *not* for.
- [ ] It does not overlap a sibling skill the user already has (if it does, the description says what makes this one distinct).
- [ ] A cold reader can tell from the description alone when this skill should fire and when it should not.

## The contract
- [ ] The what-bends / never-bends split is stated once, near the top, as a table or short list.
- [ ] "Never bends" defers to the brand's own source of truth (e.g. an approved brand profile) rather than re-specifying colours and fonts.
- [ ] Every downstream instruction respects the split.

## Memory
- [ ] Step 1 of the workflow is "read the profile".
- [ ] The profile template has all four sections: Owner choices, Chosen by assistant, Assumed-not-asked, and a log.
- [ ] Notes on one output are described as becoming standing choices for the next.

## Interview
- [ ] the host question tool, ≤4 per call, every question has "You choose for me".
- [ ] There is an explicit "don't ask" list of what discovery answers.
- [ ] Taste is shown (sample frames/sections), not asked.
- [ ] There is an opinionated default and the skill applies it without asking to confirm.

## Discovery
- [ ] All four input paths (brand files / codebase / URL / nothing) are handled.
- [ ] All four converge on the same profile.
- [ ] A blocked/failed input is a hard stop with a clear ask, never a guess.

## Facts and claims
- [ ] Prices, dates, names, numbers, quotes are taken from the user word for word.
- [ ] There is a claims boundary: what the deliverable may state, what it never states.

## Verification
- [ ] The last workflow step opens the *real produced artifact* and checks it.
- [ ] The checks are named specifically (which values, which counts), not "review the output".
- [ ] For high-stakes output, the check is done by a pass that did not build it.

## Craft
- [ ] The craft file has a "why a first pass comes out flat" section, ranked by impact.
- [ ] Good is defined concretely enough that two runs from the same inputs cannot look years apart.

## Proof it works
- [ ] Dry-run 1: full inputs (a brand book / codebase). Output passed brand review.
- [ ] Dry-run 2: almost no inputs ("just go"). Output was defensible and the assumptions were logged.
- [ ] Every failure from both runs is now a line in the traps section.
- [ ] Every taste note from both runs is now in the craft file or the profile.
