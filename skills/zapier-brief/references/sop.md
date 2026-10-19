# Zapier SOP

## Inputs

- Approved process and immutable Use Case context.
- Selected Zapier capability profile.
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

1. Define exactly one grounded trigger followed by ordered actions; identify every source field and required destination field without inventing app events or fields.
2. Use a Filter when a non-match should stop the Zap and Paths when distinct outcomes need separate branches; record AND, OR, fallback and always-run semantics explicitly.
3. For every required field, identify its upstream value, a justified fallback or a filter/path guard so missing input cannot silently trigger an incorrect action.
4. List connected app accounts, scopes and ownership as placeholders only; never include credentials or claim an account is connected.
5. Add a bounded error-handling and run-history review plan for fallible actions, noting plan-dependent capabilities and replay limitations instead of assuming they are available.
6. Require explicit human approval before consequential actions and preserve the existing human approval boundary; a Zapier step or AI decision never grants authorization.
7. Produce a reviewable brief only. Do not run SDK or CLI commands, publish a Zap, connect an account or mutate Zapier.

## Result

A versioned draft implementation package with source citations and no external side effects.
