# Contributing

Corrections and evidence-backed additions are welcome.

- Follow [`STANDARD.md`](STANDARD.md); operational instructions must work for an
  arbitrary organization and keep company profiles outside the package.
- Keep exactly one skill under `skills/<skill-id>/`, one matching entry in
  `catalog.json`, and one generated archive at `dist/<skill-id>.zip`.
- Keep `SKILL.md` at the declared skill root and make its `name` match the catalogue
  ID.
- Preserve House of Ichigo publisher attribution and applicable licence notices.
- Do not hardcode time-sensitive model names when live verification is possible.
- Include licences and notices for redistributed third-party material.
- Use only fictional examples and keep onboarding profiles outside skill directories.
- Do not add `archives/`, `originals/`, `private/` or `source-imports/` directories.
- Rebuild distributions with `python3 scripts/build_distributions.py`, inspect the
  exact diff, and run the complete release gate documented in
  [`RELEASE-SAFETY.md`](RELEASE-SAFETY.md).

Do not include credentials, private client material, personal data or proprietary
documents in issues, commits or pull requests.
