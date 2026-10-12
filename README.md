# House of Ichigo Skill Resources

Reusable, installable AI skills created and maintained by
[House of Ichigo](https://houseofichigo.com). The publisher identity and licence
remain House of Ichigo; the operational instructions are organization-neutral so
teams can supply their own company, industry, audience, competitors, sources and
constraints during onboarding.

## Catalogue

| Package | Included skill IDs | Installable ZIP |
|---|---|---|
| [Brand Factory](skills/brand-factory/) | `brand-factory` | [Download](skills/brand-factory/dist/skill.zip) |
| [Content Radar](skills/content-radar-skills/) | `content-radar-setup`, `content-radar`, `trend-radar`, `competitor-scan`, `newsjacking`, `content-ideas`, `seo-aeo-geo` | [Download suite](skills/content-radar-skills/dist/content-radar-skills.zip) |
| [Prompt Optimizer](skills/prompt-optimizer/) | `prompt-optimizer` | [Download](skills/prompt-optimizer/dist/skill.zip) |
| [Skill Repo Forge](skills/skill-repo-forge/) | `skill-repo-forge` | [Download](skills/skill-repo-forge/dist/skill.zip) |
| [Vibe Prompt Architect](skills/vibe-prompt-architect/) | `vibe-prompt-architect` | [Download](skills/vibe-prompt-architect/dist/skill.zip) |
| [Visual Prompt Scout](skills/visual-prompt-scout/) | `visual-prompt-scout` | [Download](skills/visual-prompt-scout/dist/skill.zip) |
| [Which AI Model](skills/which-ai-model/) | `which-ai-model` | [Download](skills/which-ai-model/dist/which-ai-model.zip) |

Machine-readable paths, onboarding classes and distribution files are recorded in
[`catalog.json`](catalog.json). All packages follow the reusable-skill contract in
[`STANDARD.md`](STANDARD.md).

## Onboarding model

- **Profile onboarding** is used when a skill needs durable business context. The
  skill asks for only relevant details and stores them outside the distributable
  package: organization, industry, audience, competitors, regions/languages, goals,
  constraints, approved sources, output channels and review ownership.
- **Task intake** is used for stateless skills. The skill asks only questions that
  materially affect the result and makes assumptions visible instead of inventing
  company facts.

No package contains a House of Ichigo client profile or requires House of Ichigo's
internal workspace. Publisher attribution, repository URLs and MIT copyright notices
are intentionally retained.

## Install

Download the ZIP linked above or copy the relevant skill directory into the skills
directory supported by your host. A suite ZIP may contain several independent skill
folders. Read the package README for host-specific instructions and dependencies.

## Validation

```bash
python3 scripts/validate_catalog.py
```

The validator checks the catalogue, skill frontmatter, onboarding declarations,
local links, ZIP/source agreement and operational-content neutrality. GitHub Actions
runs the same check on every change.

## Licence and ownership

Unless a package says otherwise, original code and content are copyright House of
Ichigo and released under the [MIT License](LICENSE). Third-party material keeps its
own licence and attribution. See a package's notices before redistributing it.

Created by House of Ichigo.
