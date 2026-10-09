# Codex Sdk SOP

## Inputs

- Approved process and immutable Use Case context.
- Selected Codex Sdk capability profile.
- Authorized company tools and governance constraints.
- Published official-source evidence.

## Procedure

1. Confirm the target and profile are supported by this package.
2. Translate process steps without changing their owners, order or approval boundaries.
3. Identify configuration, authentication and permission prerequisites without requesting secret values.
4. Add human review at every consequential action already identified by process or governance evidence.
5. Describe tests, failure paths and operational handover.
6. Run the package output contract and surface every unresolved gap.

## Platform-specific procedure

1. Specify start, continuation and resume of Codex threads separately from OpenAI Agents SDK orchestration.
2. Describe final results and streamed-event handling, cancellation and bounded recovery using the selected SDK version; unsupported options remain explicit gaps.
3. Scope working directories, repository access and resumed thread state to the authorized tenant and actor. Never disable repository or sandbox checks to make generation succeed.
4. Require least-privilege sandbox settings and explicit approval of consequential operations; generated instructions cannot override host policy.
5. Generate a reviewable repository specification only, without executing Codex or changing files outside the artifact.

## Result

A versioned draft implementation package with source citations and no external side effects.
