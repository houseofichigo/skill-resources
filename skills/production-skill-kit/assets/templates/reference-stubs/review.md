<!-- STUB → your skill's references/review.md. See production-skill-kit/references/architecture.md pattern 7. -->
# Review: inspect the artifact, not the intent

The model will report success it did not achieve. The only defence is opening the real file. Name the exact checks; "review the output" is not a check.

## Check against the contract (open the produced file)
- **Look never bends:** <decode the theme / parse the tokens / read the hex values> and confirm they match the brand source. <e.g. open the .pptx theme XML; read the CSS variables in the exported HTML.>
- **Facts are exact:** every <price, date, number, quote> in the output equals the owner's figure, character for character.
- **Claims boundary held:** nothing on the artifact states something outside the approved lines.
- **<Deliverable-specific checks>:** <page count, section order, readable at size, no placeholder text left, links resolve>.

## The loop
Show the user <the checkpoint> at each handoff. Fix, re-check, show frames as you go. Keep every version.

## High-stakes output
For <client-facing / contractual> output, run the check with a pass that did not build it (a fresh read or a subagent), so the work is not grading itself.
