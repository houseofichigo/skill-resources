# House of Ichigo skills

Open, installable AI skills created by [House of Ichigo](https://houseofichigo.com).
Each entry is self-contained as either a standalone skill or an aggregate suite
package, with its verified source link and distributable archive.

## Skills

| Skill | What it does | Installable ZIP |
|---|---|---|
| [Which AI Model](skills/which-ai-model/) | Routes a task through capability, product and tooling constraints before recommending a model tier. | [Download](skills/which-ai-model/dist/which-ai-model.zip) |
| [Skill Repo Forge](skills/skill-repo-forge/) | Finds, audits, improves, installs and packages portable Agent Skills. [Standalone repository](https://github.com/houseofichigo/skill-repo-forge). | [Download](skills/skill-repo-forge/dist/skill.zip) |
| [Visual Prompt Scout](skills/visual-prompt-scout/) | Finds and improves current image or video prompts with live source retrieval, provenance controls and prompt-injection quarantine. [Standalone repository](https://github.com/houseofichigo/visual-prompt-scout). | [Download](skills/visual-prompt-scout/dist/skill.zip) |
| [Brand Factory](skills/brand-factory/) | Builds a machine-readable, self-checking brand system and generates its installable brand Skill. [Standalone repository](https://github.com/houseofichigo/brand-factory). | [Download](skills/brand-factory/dist/skill.zip) |
| [Prompt Optimizer](skills/prompt-optimizer/) | Creates, improves, researches and evaluates proportionate prompts with adaptive web research, source provenance and prompt-injection quarantine. [Standalone repository](https://github.com/houseofichigo/prompt-optimizer). | [Download](skills/prompt-optimizer/dist/skill.zip) |
| [HOI OS](skills/hoi-os/) | Complete 15-skill HOI OS suite. The [HOI OS repository](https://github.com/houseofichigo/hoi-os) is the single canonical source. | [Download package](skills/hoi-os/dist/hoi-os-skills.zip) |

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

New resources belong under `skills/<skill-or-package-name>/`. A standalone skill
keeps its installable files at the folder root. A suite such as HOI OS uses one
aggregate package entry and links to its canonical repository instead of duplicating
each constituent skill as a separate catalogue item. Every House of Ichigo-created
or -published skill or suite must be represented here and linked to its verified
public source.

## Install a skill

Use the instructions in the entry's README. Standalone skills can be installed from
their `skills/<skill-name>/` folder. Aggregate suites such as HOI OS must follow the
canonical repository's setup instructions; their ZIP is a multi-skill bundle, not a
single-skill upload.

## Licence

Unless a skill folder says otherwise, original House of Ichigo code and content are
released under the [MIT License](LICENSE). Third-party material keeps its original
licence; notices live inside the relevant skill folder.

Built by House of Ichigo. Equipped to run.
