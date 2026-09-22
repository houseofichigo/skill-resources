# Source Patterns

Use this reference when hunting for or comparing existing Agent Skill tooling.

## Standards

- Agent Skills specification: https://agentskills.io/specification. The shared format every host builds on. Reference validator: `skills-ref validate <dir>` (https://github.com/agentskills/agentskills).

## Patterns worth reusing

### OpenAI skill creator

Source: https://github.com/openai/skills

Useful patterns:
- minimal canonical Skill structure centered on `SKILL.md`
- progressive disclosure through `scripts/`, `references/`, and `assets/`
- UI metadata in `agents/openai.yaml`
- deterministic initialization and packaging
- keep repository/user documentation out of the Skill payload itself

### Anthropic skills repository

Source: https://github.com/anthropics/skills

Useful patterns:
- public Agent Skills distribution through Git repositories
- skill folders as reusable units
- packaged Skill workflows and examples

### zztimur/skill-forge

Source: https://github.com/zztimur/skill-forge

Useful patterns:
- separate deterministic package inspection from qualitative agent review
- inspect folders, ZIPs, and drafts
- bound archive/file inspection
- scan for malformed metadata, missing references, risky paths, secrets, and dangerous commands
- distinguish static validation from runtime evidence
- release-gate thinking and CI checks

MIT-licensed. Skill Repo Forge reimplements these ideas rather than copying its code; if code is ever reused, keep its copyright notice.

### Adit-Jain-srm/skill-forge

Source: https://github.com/Adit-Jain-srm/skill-forge

Useful patterns:
- discovery across GitHub and the skills CLI
- repo scaffolding around a Skill
- installation through `npx skills add`
- explicit publish workflows

MIT-licensed. Avoid carrying over growth/networking automation into this Skill. Discovery and publishing should serve the user's task, not autonomous promotion.

### vercel-labs/skills

Source: https://github.com/vercel-labs/skills

Useful patterns:
- open cross-agent CLI
- install from GitHub shorthand, URLs, local paths, and archives
- project versus global scope
- `find`, `add`, `use`, `list`, `update`, and `remove` lifecycle
- support for 70+ agent hosts (`--agent claude-code`, `codex`, `cursor`, `opencode`, …)
- discovers Skills at the repository root or under `skills/<name>/`

Use `npx skills add` as the preferred portable install path when available instead of inventing another installer format.

## Candidate evaluation

When comparing external Skill candidates, check:

1. Does the repository contain a real `SKILL.md` entrypoint?
2. Is the Skill's trigger specific enough for the user's need?
3. Are required resources present?
4. Does it bundle executable code? If yes, inspect before execution.
5. Is a license present and compatible with intended reuse?
6. Is the repository current enough for changing APIs/tools?
7. Is installation documented through a standard mechanism?
8. Does it depend on a host-specific feature the user does not have?
9. Does it solve the whole job or just one reusable component?
10. Would adaptation be cheaper and safer than rebuilding?
