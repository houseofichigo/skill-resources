# Make SOP

## Inputs

- Approved process and immutable Use Case context.
- Selected Make capability profile.
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

1. Define the trigger, modules, routes, filters and field mappings from the approved process; document missing configuration rather than inventing module identifiers.
2. For workflow use deterministic scenario routes; for agent identify model-selected tools; for hybrid identify the exact boundary between those two modes.
3. List connections and scopes as requirements, never as configured credentials. Recheck authority before consequential writes and preserve explicit human confirmation.
4. Define error routes and replay deduplication for fallible modules. Incomplete executions must be explicitly configured; do not assume they are enabled or that replay reverses earlier external writes.
5. Produce a Markdown build brief, not an importable blueprint. Test representative bundles, empty data, failures and retries before an authorized owner activates the scenario.

## Result

A versioned draft implementation package with source citations and no external side effects.
