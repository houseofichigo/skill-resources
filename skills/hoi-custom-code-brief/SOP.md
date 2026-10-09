# Custom Code SOP

## Inputs

- Approved process and immutable Use Case context.
- Selected Custom Code capability profile.
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

1. State the chosen language, runtime, dependency versions, storage and deployment environment only when supplied or explicitly proposed for review; distinguish assumptions from confirmed facts.
2. Map approved process steps and owners to modules, input/output contracts and data ownership without changing process lineage or approval gates.
3. For workflow, agent and hybrid profiles, identify deterministic steps versus model-driven decisions, bounded execution and the owner of each consequential action. Do not introduce agents when the selected profile is workflow.
4. Document authentication, tenant isolation, input validation, server-only secrets and least-privilege access. Model output and generated code never grant authority.
5. Specify unit, integration, negative-authorization and failure-recovery tests, redacted telemetry and operational ownership; unexecuted tests are a plan, not passing evidence.
6. Provide dependency/license review, deployment assumptions and application rollback preserving business history. Return a reviewable build brief, not executed source, infrastructure changes or an automatic deployment.

## Result

A versioned draft implementation package with source citations and no external side effects.
