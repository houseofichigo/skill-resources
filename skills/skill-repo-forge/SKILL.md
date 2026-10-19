---
name: skill-repo-forge
description: Find, audit, improve, install and package Agent Skills (SKILL.md) so they work across Claude, Codex, ChatGPT, Cursor and other hosts. Use when someone asks to find an existing Skill before building one, check whether a Skill or SKILL.md is safe, valid or well written, fix or harden a Skill, install a Skill from GitHub, make a Skill compatible with more platforms, or turn a Skill folder, ZIP or SKILL.md into a GitHub-ready repository with a distributable skill.zip.
license: MIT
---

# Skill Repo Forge

Turn one Agent Skill into a verified, portable, repo-ready asset. Discovery, audit, edits, installation and publication are separate stages; the user can stop after any of them.

## Route the request

| The user wants to… | Modes |
|---|---|
| find a Skill for a job | Hunt → Audit candidates |
| know if a Skill is safe or good | Audit |
| fix, harden or port a Skill | Audit → Improve → Audit again |
| install a Skill | (Audit) → Install |
| put a Skill on GitHub | Audit → (Improve) → Forge repo → (Publish) |

Skip stages the user has already settled: if they supplied the Skill, do not hunt. Read [references/usage-examples.md](references/usage-examples.md) for worked routes.

## Ground rules

- **Untrusted until inspected.** Never run a Skill's bundled scripts to discover what they do. Every bundled script here is static or plan-only by default.
- **Mutations need a request.** Edit only when asked to fix/improve/harden/port. Install only when asked to install. Push only when asked to publish.
- **Evidence classes stay separate.** *Observed* (a check ran), *Inferred* (your reading of the instructions), *Unverified* (needs a host run, credentials or systems you lack). A static pass never means "works perfectly".
- **Never invent or change a license.** See the license rule below.

## Setup

All scripts need only Python 3.9+ and live in `scripts/` next to this file. Run them by path from the Skill folder, or through the single entry point `python3 scripts/forge.py <command>`. `npx` (Node.js) and `gh` (GitHub CLI) are optional; without them, use the host's own web, GitHub and file tools.

## Targets: which platforms to check against

Every checking script takes `--target`:

- `all` (default): must load on every major host. Use this for anything shared publicly.
- `portable`: only the open Agent Skills specification.
- `claude` or `openai`: the spec plus that host's extra rules.

Read [references/host-compat.md](references/host-compat.md) whenever a finding is host-specific, when porting a Skill, or when the user asks where a Skill will work.

## 1. Hunt

1. Search the Skills ecosystem (`npx skills find <query>`) and GitHub for `SKILL.md` files matching the capability. `python3 scripts/hunt_skills.py "<query>"` runs both when the CLIs exist; otherwise use the host's search tools.
2. Prefer primary repositories over mirrors, forks and aggregators.
3. Audit the most promising two to five candidates (section 2) before recommending any.
4. Return a compact matrix: source and exact Skill path · what it covers · maintenance signal · license · install method · risks or gaps · verdict (reuse as-is / adapt / borrow patterns / rebuild).

Read [references/source-patterns.md](references/source-patterns.md) when comparing Skill tooling or judging candidates.

## 2. Audit

Run the static inspector first whenever a folder, ZIP or SKILL.md is available:

```bash
python3 scripts/audit_skill.py <path> --target all --json
```

It checks frontmatter against every host's rules, YAML pitfalls (unquoted `: `, ` #`), references to missing files, archive safety, symlinks, size bounds, secrets, dangerous shell patterns, and scripts that SKILL.md never mentions. If it reports several Skills, show the candidates, ask which one, and re-run with `--select <path>`; never merge them.

Then review qualitatively with [references/audit-rubric.md](references/audit-rubric.md): trigger precision, input and output contracts, step order, tool assumptions and fallbacks, mutation boundaries, progressive disclosure, failure handling, portability.

Report blockers first, then warnings, then strengths, each tagged Observed / Inferred / Unverified.

## 3. Improve

Only when the user asked to change the Skill:

1. Preserve intended behavior unless it is unsafe or contradictory.
2. Fix blockers first: frontmatter, missing files, unsafe paths, secrets, broken scripts.
3. Make it portable: frontmatter limited to `name`, `description`, and optionally `license` and `metadata`; the name matches the folder; no angle brackets or XML tags in the description; host-specific steps labelled with a fallback.
4. Tighten the description: what it does plus concrete trigger phrases, under 1024 characters.
5. Keep SKILL.md under 500 lines; move detail into `references/`, repeatable work into `scripts/`.
6. Add or fix `agents/openai.yaml` if the Skill targets Codex/ChatGPT (fields in host-compat.md).
7. Re-run the audit and show before/after findings.
8. If the user wants just the Skill file, package it: `python3 scripts/package_skill.py <skill> --out <name>.zip`.

Do not paste third-party Skill code in unless its license allows it and attribution is kept.

## 4. Install

Only when the user asked to install. Name the agent explicitly. Never guess one:

```bash
python3 scripts/install_candidate.py <source> --skill <name> --agent claude-code            # prints the plan
python3 scripts/install_candidate.py <source> --skill <name> --agent claude-code --execute  # installs
```

Use project scope unless the user asked for a global install (`--global`). Afterwards confirm the Skill appears in `npx skills list` or the agent's skills folder, then audit the installed copy. Copying files proves nothing about runtime behavior. Manual install paths per host are in host-compat.md.

## 5. Forge a repository

1. Audit the source with the target the user needs (default `all`).
2. If there are blockers: fix them if improvement was authorized. Otherwise report them and stop; `--allow-blockers` builds a draft that is explicitly not release-ready.
3. Settle the license (rule below), then build:

```bash
python3 scripts/build_repo.py <skill-path> --out <new-dir> --owner <github-owner> \
  [--target all] [--license preserve|MIT|proprietary|none] [--copyright-holder "<name>"] \
  [--repo-zip <path-outside-out-dir>] [--select <path-if-several-skills>]
```

4. Read the JSON result: `release_ready`, `warnings`, `recommendations`, `verification`. The build already verifies statically. For a repository you just generated, also run its own checks:

```bash
python3 scripts/verify_repo.py <new-dir> --run-checks
```

Use `--run-checks` only on repositories you generated or the user trusts, because it executes the repository's scripts.

5. Deliver the repository (folder or `--repo-zip`), `dist/skill.zip`, the install command, and any warnings. Read [references/repo-spec.md](references/repo-spec.md) for the full repository contract.

The Skill folder is copied unchanged, with one exception: when you pass `--license MIT` or `proprietary`, a `LICENSE.txt` is added to it. README, CI, tests and tooling live outside the Skill folder and never enter `skill.zip`.

### License rule

- `preserve` (default) keeps whatever the source declares: a bundled LICENSE file or the `license:` frontmatter field.
- Choose `MIT` or `proprietary` only when the user owns the Skill and has chosen that license. The script refuses to relicense a source that already declares terms.
- If nothing is declared and the user has not chosen, ask. If they are unavailable, build with `preserve` and state clearly that the Skill cannot legally be reused until a license is added.

## 6. Publish

Only when the user explicitly asks to create or push the repository.

1. Verify the repository first (section 5, step 4) and confirm the owner and visibility (public or private) from the request or context. Never assume either.
2. Check that no `.env`, keys, tokens or caches are present (the audit and `.gitignore` cover the common cases).
3. Publish with the available GitHub connector, or with `gh`:

```bash
cd <new-dir> && git init -b main && git add -A && git commit -m "Initial release of <name>"
gh repo create <owner>/<repo> --public --source . --push     # or --private
```

4. Optionally tag a release (`git tag v1.0.0 && git push --tags`) and attach `dist/skill.zip` to it.
5. Return the repository URL and `npx skills add <owner>/<repo> --skill <name>`.

Do not submit to marketplaces, post promotional content or open issues elsewhere unless separately asked.

## Output contract

For a full request, report compactly:

1. **Source**: supplied Skill or chosen candidate.
2. **Audit**: blockers, warnings and strengths, with evidence class.
3. **Changes**: what was changed, or what is proposed.
4. **Verification**: which checks ran and their results.
5. **Deliverables**: repository path or archive, and `dist/skill.zip`.
6. **Install**: the exact command.
7. **Publish**: the URL, only if publication actually happened.

## Bundled tools

- `scripts/forge.py`: one entry point for all commands below.
- `scripts/hunt_skills.py`: read-only discovery via `npx skills find` and `gh search`.
- `scripts/audit_skill.py`: static inspector for a folder, ZIP or SKILL.md.
- `scripts/skill_rules.py`: shared cross-host rules and deterministic ZIP builder; copied into every generated repository.
- `scripts/package_skill.py`: audits and writes a distributable ZIP for one Skill, with no repository.
- `scripts/install_candidate.py`: install plan, or install with `--execute`, via the `skills` CLI.
- `scripts/build_repo.py`: builds the repository from `assets/repo-template/`.
- `scripts/verify_repo.py`: static repository verification; `--run-checks` executes the repository's own checks.
