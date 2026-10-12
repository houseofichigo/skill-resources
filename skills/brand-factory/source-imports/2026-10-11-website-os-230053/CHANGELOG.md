# Changelog

All notable changes to this Skill are documented here. This project uses [Semantic Versioning](https://semver.org/).

## [2.0.0-alpha.1] - 2026-10-10 — config v2

- `brand.config.json` v2: `mode` (reproduce | create), `sources` with hashes, inline provenance (`$src`, `$conf`, `$gap`, exact-path overrides), a `reconcile` ledger, and the blocks the sixteen-section architecture needs — identity, voice (principles, tone, locale formats, microcopy rules), logo, colour roles/states/tints/dark/dataviz, type families and scale per breakpoint, layout, elevation, `effects.policy`, icons, imagery, motion, components as data, patterns, applications, SEO, governance. Schema in `assets/schema/`.
- `build/config.py`: the config gate, `out/CONFIRM.md`, `out/provenance.json`, and a v1-shaped view so every v1 generator and gate runs unchanged.
- `effects.policy` replaces the prohibitions hard-coded in `check.py`, `verify.js` and `selftest.py`. New policy checks: blur, image filters, transform on press, opacity hover, scroll-linked motion; radius in any unit and corner; `-webkit-gradient`; `drop-shadow`.
- `tokens.py` fails when a stated state colour drifts from its derivation; originality collisions can be accepted by name and stay reported.
- `examples/house-of-ichigo/`: House of Ichigo 3.3 reproduced from its own book.
- Fixed: verify.js measured the Arabic face before it loaded; selftest's off-palette probe could be a retired colour.
- Breaking: v1 configs are rejected. See `references/config-v2.md` for the mapping.

## [1.0.0] - 2026-09-23

- Initial repository.
- Add an end-to-end factory verification workflow.
- Make the generated-checker placeholder valid Python until the build replaces it.
