# Apps Script SOP

## Inputs

- Approved process and immutable Use Case context.
- Selected Apps Script capability profile.
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

1. Map the approved process to explicit functions, Google services and entry points; identify whether the script is bound, standalone or a web app.
2. Declare least-privilege OAuth scopes in the manifest plan and document the execution identity for every entry point. An installable trigger runs as its creator.
3. Distinguish simple from installable triggers and specify event validation, duplicate-event protection and trigger ownership; never claim a trigger has been installed.
4. Refer to current quota documentation rather than hardcoding limits; define bounded batches, concurrency protection, retry limits and terminal failure reporting as design requirements.
5. Preserve approval before consequential writes and test denied scopes, revoked authorization, quota exhaustion and duplicate events.
6. Produce a reviewable implementation brief only; do not run scripts, install triggers, grant scopes or deploy a web app.

## Result

A versioned draft implementation package with source citations and no external side effects.
