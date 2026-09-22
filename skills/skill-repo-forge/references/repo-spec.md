# Generated Repository Specification

## Goals

Make the Skill easy to inspect, install on any host, fork, test and publish, without changing the canonical Skill payload.

## Layout

```text
<repo>/
├── README.md                 # purpose, per-host install, validation, license
├── LICENSE                   # when a license is preserved or chosen
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── .gitignore                # mirrors what skill.zip excludes, so clones rebuild identical bytes
├── .gitattributes            # LF endings everywhere so skill.zip stays in sync
├── .github/workflows/validate-skill.yml
├── scripts/                  # repository tooling, standard library only
│   ├── skill_rules.py        # copy of Skill Repo Forge's shared rules
│   ├── validate_skill.py     # host rules + dist sync; target baked in at build time
│   └── build_dist.py         # rebuild dist/skill.zip, or --check it
├── tests/test_skill_layout.py
├── skills/<name>/            # canonical Skill, copied unchanged
│   ├── SKILL.md
│   └── agents/ scripts/ references/ assets/ LICENSE.txt   (as present)
└── dist/skill.zip            # one <name>/ folder, payload only
```

The `skills/<name>/` layout is what `npx skills add owner/repo --skill <name>` discovers.

## README requirements

- plain-language purpose (the Skill's description)
- exact Skill name
- `npx skills add OWNER/REPO --skill NAME`, with `--agent` examples and `npx skills use`
- manual install table: Claude Code, Claude apps, Claude API, Codex, others
- the Skill's file tree, and a note that tooling is outside it
- validation commands and what they do not prove
- license status

Do not claim a host works unless its rules were checked.

## Canonical skill.zip

- exactly one top-level folder named after the Skill
- only payload files: no README, CI, tests, `.git`, caches or audit reports
- byte-reproducible: sorted entries, fixed timestamps, permissions derived from content (0755 for files starting with `#!`, else 0644) so every OS builds the same bytes
- CI fails when it drifts from `skills/<name>/` (content or mode); `python3 scripts/build_dist.py` rebuilds it
- caches and credential files never enter it, even when built with `--allow-blockers`

## CI

- Python 3.10 and 3.13
- runs the validator, the dist sync check and the tests
- never downloads or executes code from the Skill itself

CI validates structure and host rules, not runtime behavior.

## Licensing

- `preserve`: copy the bundled license file to `LICENSE`, or report the `license:` field and warn that the text is missing
- `MIT` / `proprietary`: only for Skills the user owns; writes `LICENSE` and bundles `LICENSE.txt` in the Skill; refused if the source already declares terms
- no license: build anyway, but report it as not release-ready

## Publication

The generator prepares files only. Creating the GitHub repository and pushing to it is a separate, explicit action.
