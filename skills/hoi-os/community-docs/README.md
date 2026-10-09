# HOI OS community skills

**Unpublished local candidate.** This collection contains 21 skills: one installation guide and 20 operational skills. It contains instructions, not an application, assistant subscription or account connection.

Use your own identity, organization, private workspace, source selections and credentials. No company workspace, client records, transcripts, OAuth tokens, API keys or configured webhook is included. The HOI OS name and stable `hoi-*` identifiers identify the product; copyright and upstream repository references identify its origin, not a configured organization.

## Requirements

Use the matching engine source snapshot identified in `manifest.json`. Its current contract is engine API 1 and workspace schema 17. The historical `0.1.0-alpha.2` download predates this functionality: a matching version string alone is insufficient. Do not install this candidate over that release and assume compatibility.

Operational skills require a local compatible engine, an explicitly selected private workspace and an optional Codex or Claude Code adapter. A web-chat upload does not gain access to a local workspace. Static package validation is not proof of host installation or execution.

## Start with your own workspace

From a verified compatible engine checkout, with Node 22.14+ and npm:

```sh
npm ci
npm run setup -- --workspace "../My Workspace" --hosts none --non-interactive
node bin/hoi.mjs doctor --workspace "../My Workspace" --host local --json
npm start -- --workspace "../My Workspace" --host local
```

App-only setup is valid. The engine provides ingestion, retrieval, reviews and the map without installing assistant skills. Select your timezone, profile and desired first result during onboarding. Begin with one fictional or deliberately selected document; do not import an entire organization as a setup side effect.

For an optional adapter, close setup and use the engine's managed installer:

```sh
node bin/hoi.mjs adapter install codex --workspace "../My Workspace" --host local --json
node bin/hoi.mjs adapter status --workspace "../My Workspace" --host local --json
```

Choose `claude` or `both` when appropriate. Reload that workspace in the chosen assistant and verify discovery before invoking `hoi-onboard`. Preserve edited manuals and resolve reported conflicts. Removing an adapter must not delete private data. Assistant requests must use their own host identity, never impersonate `local`.

## Importing individual skills

`individual/<skill-name>.zip` contains one skill folder and its MIT licence. Where supported, use the app's Skills import preview, inspect requirements and instructions, import a draft, then explicitly review activation. Do not upload the complete collection as one skill. Bundled skills already available in the app do not need duplicate imports.

Skills cannot create executable tools, grant provider disclosure permission, approve their own changes or connect accounts. Configure your own supported providers and connector scopes separately in the app. No API key is required for explicit assistant handoff; in-app paid generation needs separate configuration and permissions.

## Recovery and evidence

Before upgrading an existing workspace, verify a backup and restore it into a separate directory using compatible engine guidance. Keep that backup outside a public repository. Never open a newer database with an older engine as a rollback strategy.

See `VALIDATION.json` for this candidate's static results and `SHA256SUMS` for file integrity. Fresh assistant-session execution, clean Mac/Windows installation, live providers and real-use pilot acceptance remain separate checks. This is an alpha candidate, not a certified or published release.

## Reuse and attribution

The MIT licence permits reuse subject to its notice requirements. Preserve `LICENSE` and included notices. Use your own organization and content; do not copy developer workspaces or `.local`, `.verification`, archives or credential files into a release. Public upstream links in installer guidance refer to historical releases unless explicitly labelled otherwise.
