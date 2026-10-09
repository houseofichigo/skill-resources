# HOI OS skill package

## Published community skills — 0.2.0-alpha.1

[Public repository](https://github.com/houseofichigo/hoi-os) · [Published commit](https://github.com/houseofichigo/hoi-os/commit/66fcc668b3a4e0085bdc3eb3d23209fadb2ba052) · [Exact local publication copy](publications/0.2.0-alpha.1/README.md).

Published on 2026-09-29: 21 skills under MIT, open for reuse and forks. The default branch is skills-only; the separate app remains unpublished. Existing releases and history remain intact. The public installer edition explicitly explains app availability; the product development installer remains separate. All 21 static audits passed, all 22 archives verified, and the remote Git tree matches the reviewed local tree.


## Current community candidate — unpublished

[Setup and reuse guide](community/2026-09-29-candidate-1/README.md) · [21-skill collection](community/2026-09-29-candidate-1/hoi-os-community-skills.zip) · [Individual packages](community/2026-09-29-candidate-1/individual/) · [Checksums](community/2026-09-29-candidate-1/SHA256SUMS).

The current candidate uses generic, user-selected setup. Its 21 skill folders match the product sources; static audits found zero blockers and warnings. It requires a compatible engine snapshot and is not a replacement app or a published release. Company data and credentials are excluded; product identity, licence attribution and upstream links remain.

Rebuild into a new directory using `tools/prepare-community.py --product <product-root> --audit-script <skill-repo-forge-auditor> --output <new-candidate-directory>`. Never overwrite prior candidates. The builder only packages explicitly selected skills and public metadata.

## Historical package — 2026-09-22

This is the single House of Ichigo catalogue entry for the complete HOI OS skill suite.

- Canonical repository: <https://github.com/houseofichigo/hoi-os>
- Canonical source: <https://github.com/houseofichigo/hoi-os/tree/main/skills>
- Included skills: 15
- Package: [`dist/hoi-os-skills.zip`](dist/hoi-os-skills.zip)

The archive contains the 15 canonical `hoi-*` skill folders, the machine-readable
catalogue, the HOI OS licence, and a package README. It is a multi-skill bundle,
not a single-skill upload. The HOI OS repository remains the source of truth;
this folder is an ingestion record and distributable package, not a second source.

For installation and runtime requirements, follow the canonical
[HOI OS README](https://github.com/houseofichigo/hoi-os#readme).
