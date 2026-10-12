# Contributing

Corrections and evidence-backed additions are welcome.

- Follow [`STANDARD.md`](STANDARD.md); operational instructions must work for an
  arbitrary organization and keep company profiles outside the package.
- Keep every package under `skills/<package-name>/` and list each executable skill in
  `catalog.json`.
- Keep `SKILL.md` at the declared skill root and make its `name` match the catalogue
  ID.
- Preserve House of Ichigo publisher attribution and applicable licence notices.
- Do not hardcode time-sensitive model names when live verification is possible.
- Include licences and notices for redistributed third-party material.
- Rebuild changed distributable ZIPs and run `python3 scripts/validate_catalog.py`.

Do not include credentials, private client material, personal data or proprietary
documents in issues, commits or pull requests.
