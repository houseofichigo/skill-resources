# Host Compatibility

What each platform requires of a Skill, and where Skills live. Rules were checked against official sources in September 2026; platforms change, so re-check a source when a finding looks wrong.

## The portable baseline (all hosts)

From the open Agent Skills specification (https://agentskills.io/specification):

| Field | Required | Rule |
|---|---|---|
| `name` | yes | 1–64 chars; `a-z`, `0-9`, `-`; no leading/trailing or double hyphen; **must equal the folder name** |
| `description` | yes | 1–1024 chars; says what the Skill does and when to use it |
| `license` | no | license name, or the name of a bundled license file |
| `compatibility` | no | 1–500 chars; environment needs (product, packages, network) |
| `metadata` | no | map of string keys to string values |
| `allowed-tools` | no | space-separated pre-approved tools; experimental, support varies |

Structure: `SKILL.md` at the folder root; optional `scripts/`, `references/`, `assets/`. Keep SKILL.md under 500 lines (about 5,000 tokens) and reference files one level deep.

## Claude (Claude Code, Claude apps, Claude API)

Source: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview

- `name` must not contain the reserved words `anthropic` or `claude`.
- `name` and `description` must not contain XML tags.
- Claude Code: personal Skills in `~/.claude/skills/<name>/`, project Skills in `.claude/skills/<name>/`.
- Claude apps: upload a ZIP (one `<name>/` folder inside) in the Skills settings. Requires code execution to be enabled.
- Claude API: upload through the `/v1/skills` endpoints; shared across the workspace.
- Skills do not sync between these surfaces; install on each.

## OpenAI (Codex, ChatGPT)

Sources: https://developers.openai.com/codex/skills and the skill-creator in https://github.com/openai/skills

- Codex needs `name` and `description`, and builds on the open standard.
- OpenAI's skill-creator validator accepts only `name`, `description`, `license`, `allowed-tools`, `metadata`. It rejects `compatibility` and any other key, and rejects `<` or `>` in the description.
- Codex locations: `.agents/skills/` in the working folder or repository root, `$HOME/.agents/skills/` for the user, `/etc/codex/skills` for admins.
- Optional `agents/openai.yaml` adds UI metadata:
  - `interface.display_name`: display title
  - `interface.short_description`: 25–64 characters
  - `interface.default_prompt`: one short sentence that mentions the Skill as `$skill-name`
  - `interface.icon_small`, `interface.icon_large`: relative paths under `./assets/`
  - `interface.brand_color`: hex color
  - `policy.allow_implicit_invocation`: default true
  - `dependencies.tools[]`: currently `type: "mcp"`, with `value`, `description`, `transport`, `url`
  - quote every string value

## Other hosts (Cursor, OpenCode, Cline, Windsurf, Copilot and more)

The `skills` CLI (https://github.com/vercel-labs/skills) installs into 70+ agents and knows each one's folder:

```bash
npx skills add <owner>/<repo> --skill <name> --agent <agent-id>   # e.g. cursor, opencode, cline
```

It discovers Skills at the repository root or under `skills/<name>/` (up to three levels deep), which is the layout Skill Repo Forge generates.

## Safest cross-host choices

- Frontmatter: `name`, `description`, and optionally `license` and `metadata`. Leave out `compatibility` if OpenAI tooling matters, and say environment needs in the body instead.
- Quote any description containing `: ` or ` #`.
- No angle brackets anywhere in `name` or `description`.
- Write host-specific steps as "if X is available… otherwise…" so the Skill degrades gracefully.
- Scripts: Python standard library or POSIX shell, with dependencies stated.
