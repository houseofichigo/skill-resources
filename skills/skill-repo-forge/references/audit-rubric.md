# Audit Rubric

## Severity

- **Blocker**: unsafe, malformed, or will fail to load on a targeted host. Examples: bad frontmatter, missing entrypoint or referenced file, exposed secret, traversal or symlink, name/folder mismatch.
- **Warning**: likely quality, portability or maintenance problem; fix before sharing widely.
- **Note**: optional improvement or host-specific consideration.

Target decides severity for host rules: with `--target all` every host's rules are blockers; with `portable` the Claude/OpenAI-only rules drop to warnings. See host-compat.md.

## Deterministic checks (audit_skill.py)

### Package and path safety
- exactly one selected Skill root; several means list and ask, then `--select`. A SKILL.md nested inside another Skill's folder is content, not a second Skill
- no `../`, absolute or drive-letter ZIP paths; no symlinks; no duplicate or case-colliding entries
- bounded file count, depth, per-file size and total size; ZIP extraction capped even if headers lie
- `__MACOSX/`, caches and `.pyc` ignored

### SKILL.md
- frontmatter opens and closes with `---`; parses as the supported YAML subset
- YAML pitfalls flagged on every line, including continuations: unquoted `: ` (invalid on most hosts), ` #` comments that truncate a value, leading indicator characters, and values YAML reads as numbers, booleans, null or dates (`name: 123`, `description: yes`)
- SKILL.md must be UTF-8
- `name`: spec format, 64 chars, equals folder name, no `claude`/`anthropic`, no angle brackets
- `description`: present, ≤1024 chars, no XML tags or angle brackets, mentions when to use it, no placeholders
- only spec keys; `compatibility` flagged for OpenAI tooling; `metadata` is a flat string map
- body present; over 500 lines flagged; TODO/placeholder markers flagged

### Resources
- markdown links must resolve inside the Skill (blocker); bare `scripts/…`, `references/…`, `assets/…`, `agents/…` mentions that don't resolve are warnings
- scripts never mentioned in SKILL.md flagged as orphans
- `agents/openai.yaml` fields checked when present (display name, 25–64 char short description, `$name` in default prompt, icon files exist, hex color)

### Secret and code scan
- provider tokens (OpenAI, Anthropic, GitHub, AWS, Google, Slack, Stripe, private keys): blocker anywhere
- generic `api_key = "…"` style assignments: blocker in code/config, warning in prose; obvious placeholders are ignored
- credential-like files (`.env*` except `.env.example`/`.sample`/`.template`, `id_rsa`, `.pem`, `.key`, `.netrc`, `.npmrc`, `.pypirc`): blocker, and always left out of packages
- remote content piped into a shell, recursive deletes of root or home, raw disk writes, mkfs, fork bombs: blocker in scripts, warning in markdown code (the agent may copy it)

All scanning is heuristic and non-exhaustive; say so.

## Qualitative checks

### Trigger quality
The description answers: what does it do, when should it fire, which concrete phrases or file types trigger it? Too broad steals unrelated requests; too narrow never fires.

### Input contract
Accepted inputs, and what happens with missing input, wrong file type, an ambiguous target, or several candidate Skills.

### Output contract
A future agent can tell what "done" looks like: files, format, where they go, what to report.

### Workflow quality
- steps in execution order
- read-only review separated from edits and other side effects
- external side effects explicit and gated on a user request
- risky or expensive operations bounded

### Progressive disclosure
SKILL.md is the control plane; detail lives in `references/`, repeatable work in `scripts/`, output resources in `assets/`. Each reference is linked from SKILL.md with a clear "read this when…".

### Portability
Identify assumptions tied to one host: tool names, connectors, file paths, shell availability, network access, UI features. Each should have a fallback or be stated as a requirement. Do not call a Skill portable because its markdown parses.

### Runtime evidence
Distinguish and only claim what was obtained:
static package pass → script unit/smoke tests → install test → host invocation test → real task evaluation.
