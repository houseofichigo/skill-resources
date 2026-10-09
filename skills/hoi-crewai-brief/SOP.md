# Crewai SOP

## Inputs

- Approved process and immutable Use Case context.
- Selected Crewai capability profile.
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

1. Select sequential, hierarchical or Flow orchestration explicitly. Preserve source branches; do not flatten a nonlinear process into a crew task list.
2. Bind every task and tool to recorded source facts. Proposed agent roles do not change human ownership or confer authorization. Trigger and human steps remain outside autonomous agent execution.
3. Keep output guardrails separate from authorization. Consequential tool effects require current source access and explicit human confirmation, including retries and resumed execution.
4. Bound iterations, time and retries; guardrail retries cannot replay non-idempotent writes. Model, SDK version and native configuration require current implementation review.
5. Scope any future state to organization, user and source record; memory and persistence remain unconfigured pending data review. Never export credentials or raw payload logs.
6. Generate a Markdown implementation review only, with no native Python, YAML, JSONC, deployment or execution. The pinned upstream skill licence evidence remains unresolved; do not copy its code or mark it published.

## Result

A versioned draft implementation package with source citations and no external side effects.
