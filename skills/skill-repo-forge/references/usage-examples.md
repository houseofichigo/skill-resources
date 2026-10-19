# Usage Examples

## Hunt first

User: "Find me a Skill for invoice OCR, check the best one, improve it if needed, install it for Codex, then turn our version into a repo."

Route: hunt → audit top candidates → comparison matrix → improve (authorized) → install with `--agent codex --execute` → audit installed copy → forge repo → verify.

## Direct conversion

User: "Turn this uploaded Skill ZIP into a GitHub-ready repo."

Route: audit ZIP → report blockers (fix only if asked) → confirm license → `build_repo.py --out <dir> --owner <owner>` → `verify_repo.py <dir> --run-checks` → return repo and `dist/skill.zip`. No discovery.

## Audit only

User: "Is this Skill safe and well built?"

Route: `audit_skill.py <path> --target all` → qualitative review → findings by severity and evidence class. No edits, installs or pushes.

## Make it work everywhere

User: "This Skill works in Claude Code but not in Codex. Fix it."

Route: audit with `--target all` → read host-compat.md → fix frontmatter (drop non-portable keys, quote values, name equals folder), add a fallback for Claude-only tools, add `agents/openai.yaml` → re-audit → before/after.

## Improve then package

User: "Improve this SKILL.md and give me the downloadable Skill."

Route: audit draft → rewrite → add required resources → re-audit → `package_skill.py <skill> --out <name>.zip` → deliver the ZIP. A full repository only if asked.

## Publish

User: "Create a public GitHub repo for the final Skill under my organization."

Route: verify repo → confirm organization name and public visibility → `gh repo create <org>/<repo> --public --source . --push` (or the GitHub connector) → return URL and install command. Never pick the organization or visibility without grounding.
