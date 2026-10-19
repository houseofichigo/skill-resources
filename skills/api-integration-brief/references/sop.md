# Api Integration SOP

## Inputs

- Approved process and immutable Use Case context.
- Selected Api Integration capability profile.
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

1. Name the selected API providers, API versions, transport and implementation runtime from supplied evidence; unresolved choices remain explicit gaps.
2. Map each approved process step to documented operations, request and response fields, pagination and errors. Never invent endpoints, quotas or idempotency support.
3. Use a supported OpenAPI version when describing HTTP APIs; the OpenAPI specification is a format reference, not evidence that a vendor endpoint exists.
4. Describe least-privilege authentication, server-side secret references, tenant authorization and explicit confirmation before consequential writes. Never include secret values.
5. Specify bounded timeouts, rate-limit handling and retry eligibility per operation. Do not blindly retry non-idempotent writes; document duplicate detection and recovery from partial effects.
6. Define redacted correlation logs, error ownership, integration tests and deployment/rollback assumptions. Produce a reviewable brief only; do not call APIs, provision resources or deploy.

## Result

A versioned draft implementation package with source citations and no external side effects.
