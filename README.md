# House of Ichigo skills

Open, installable AI skills created by [House of Ichigo](https://houseofichigo.com).
Each folder is self-contained: the skill, its references, source material, teaching
artifacts and a ready-to-install ZIP live together.

## Skills

| Skill | What it does | Installable ZIP |
|---|---|---|
| [Which AI Model](skills/which-ai-model/) | Routes a task through capability, product and tooling constraints before recommending a model tier. | [Download](skills/which-ai-model/dist/which-ai-model.zip) |
| [Skill Repo Forge](skills/skill-repo-forge/) | Finds, audits, improves, installs and packages portable Agent Skills. [Standalone repository](https://github.com/houseofichigo/skill-repo-forge). | [Download](skills/skill-repo-forge/dist/skill.zip) |

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
