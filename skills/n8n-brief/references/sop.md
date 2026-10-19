# N8n SOP

## Inputs

- Approved process and immutable Use Case context.
- Selected N8n capability profile.
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

1. Validate the complete workflow before review, then retrieve and verify the saved workflow after any future create or update operation.
2. Use n8n credential references and placeholders; never place secret values in workflow parameters, expressions, headers or documentation.
3. Add an explicit error path for every fallible production node and return appropriate caller errors for webhook workflows.
4. Use stateless subworkflows for reusable units and pass all required context as inputs.
5. Do not invent node parameters, node versions, credentials, connectors or expressions that are absent from reviewed evidence.
6. Require human review before activation or any external deployment; this package never publishes a workflow.

## Result

A versioned draft implementation package with source citations and no external side effects.
