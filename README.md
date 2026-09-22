# House of Ichigo skills

Open, installable AI skills created by [House of Ichigo](https://houseofichigo.com).
Each folder is self-contained: the skill, its references, source material, teaching
artifacts and a ready-to-install ZIP live together.

## Skills

| Skill | What it does | Installable ZIP |
|---|---|---|
| [Which AI Model](skills/which-ai-model/) | Routes a task through capability, product and tooling constraints before recommending a model tier. | [Download](skills/which-ai-model/dist/which-ai-model.zip) |
| [Skill Repo Forge](skills/skill-repo-forge/) | Finds, audits, improves, installs and packages portable Agent Skills. [Standalone repository](https://github.com/houseofichigo/skill-repo-forge). | [Download](skills/skill-repo-forge/dist/skill.zip) |
| [HOI OS — 3D Map](skills/hoi-3d-map/) | Opens the local knowledge map with source-backed and temporal views. [Source](https://github.com/houseofichigo/hoi-os/tree/main/skills/hoi-3d-map). | [Download](skills/hoi-3d-map/dist/hoi-3d-map.zip) |
| [HOI OS — Audit](skills/hoi-audit/) | Inspects evidence health, extraction gaps, connections and memory freshness. [Source](https://github.com/houseofichigo/hoi-os/tree/main/skills/hoi-audit). | [Download](skills/hoi-audit/dist/hoi-audit.zip) |
| [HOI OS — Build Capability](skills/hoi-build-capability/) | Defines, evaluates and activates bounded workflows using registered tools. [Source](https://github.com/houseofichigo/hoi-os/tree/main/skills/hoi-build-capability). | [Download](skills/hoi-build-capability/dist/hoi-build-capability.zip) |
| [HOI OS — Capture](skills/hoi-capture/) | Records supplied decisions, preferences and experience as reviewable memory. [Source](https://github.com/houseofichigo/hoi-os/tree/main/skills/hoi-capture). | [Download](skills/hoi-capture/dist/hoi-capture.zip) |
| [HOI OS — Connect](skills/hoi-connect/) | Checks available Gmail, Calendar, Drive and GitHub host tools. [Source](https://github.com/houseofichigo/hoi-os/tree/main/skills/hoi-connect). | [Download](skills/hoi-connect/dist/hoi-connect.zip) |
| [HOI OS — Consolidate](skills/hoi-consolidate/) | Finds duplicate, stale and proposed memories for review. [Source](https://github.com/houseofichigo/hoi-os/tree/main/skills/hoi-consolidate). | [Download](skills/hoi-consolidate/dist/hoi-consolidate.zip) |
| [HOI OS — Evaluate](skills/hoi-evaluate/) | Runs reproducible evidence-retrieval checks for a capability. [Source](https://github.com/houseofichigo/hoi-os/tree/main/skills/hoi-evaluate). | [Download](skills/hoi-evaluate/dist/hoi-evaluate.zip) |
| [HOI OS — Ingest](skills/hoi-ingest/) | Preserves and registers selected local files or host-exported sources. [Source](https://github.com/houseofichigo/hoi-os/tree/main/skills/hoi-ingest). | [Download](skills/hoi-ingest/dist/hoi-ingest.zip) |
| [HOI OS — Install](skills/hoi-install/) | Guides local HOI OS installation or update for supported assistants. [Source](https://github.com/houseofichigo/hoi-os/tree/main/skills/hoi-install). | [Download](skills/hoi-install/dist/hoi-install.zip) |
| [HOI OS — Meeting Prep](skills/hoi-meeting-prep/) | Prepares cited meeting briefs from local knowledge and read-only connections. [Source](https://github.com/houseofichigo/hoi-os/tree/main/skills/hoi-meeting-prep). | [Download](skills/hoi-meeting-prep/dist/hoi-meeting-prep.zip) |
| [HOI OS — Onboard](skills/hoi-onboard/) | Builds or updates a personal profile through a resumable conversation. [Source](https://github.com/houseofichigo/hoi-os/tree/main/skills/hoi-onboard). | [Download](skills/hoi-onboard/dist/hoi-onboard.zip) |
| [HOI OS — Organize](skills/hoi-organize/) | Applies reviewable working-folder organization while preserving originals. [Source](https://github.com/houseofichigo/hoi-os/tree/main/skills/hoi-organize). | [Download](skills/hoi-organize/dist/hoi-organize.zip) |
| [HOI OS — Retrieve](skills/hoi-retrieve/) | Finds source-backed information and bounded local context. [Source](https://github.com/houseofichigo/hoi-os/tree/main/skills/hoi-retrieve). | [Download](skills/hoi-retrieve/dist/hoi-retrieve.zip) |
| [HOI OS — Session Capture](skills/hoi-session-capture/) | Proposes reviewable memories and wiki updates from the current session. [Source](https://github.com/houseofichigo/hoi-os/tree/main/skills/hoi-session-capture). | [Download](skills/hoi-session-capture/dist/hoi-session-capture.zip) |
| [HOI OS — Wiki](skills/hoi-wiki/) | Builds reviewable current-view wiki pages from cited evidence. [Source](https://github.com/houseofichigo/hoi-os/tree/main/skills/hoi-wiki). | [Download](skills/hoi-wiki/dist/hoi-wiki.zip) |

## Repository structure

```text
skills/
  <skill-name>/
    SKILL.md
    references/
    README.md
    dist/
    ...supporting sources and artifacts
```

New resources belong under `skills/<skill-name>/`. Keep each folder independently
buildable and place the installable agent package at its root as `SKILL.md` plus any
referenced files. Every House of Ichigo-created or -published skill must be added to
this collection, listed in the Skills table, and linked to its verified public
repository or exact published skill URL when one exists.

## Install a skill

Use the instructions in the skill's README. Agents that support the Agent Skills
convention can install directly from `skills/<skill-name>/`.

## Licence

Unless a skill folder says otherwise, original House of Ichigo code and content are
released under the [MIT License](LICENSE). Third-party material keeps its original
licence; notices live inside the relevant skill folder.

Built by House of Ichigo. Equipped to run.
