# Brand Factory

Build a machine-readable, self-checking brand system and generate the installable
brand Skill that keeps later work aligned with it.

The factory uses one configuration file to generate design tokens, CSS, written
rules, a browser-measured brand book, working templates and a per-brand Agent Skill.
Its checks cover contrast, palette distance, typography, clipping, font fallback,
synthetic italics, density, template compliance and source divergence.

- Canonical repository: <https://github.com/houseofichigo/brand-factory>
- Skill definition: [`SKILL.md`](SKILL.md)
- Upload package: [`dist/skill.zip`](dist/skill.zip)

Install from the canonical repository:

```bash
npx skills add houseofichigo/brand-factory --skill brand-factory
```

The factory requires Python 3.9+, Node 18+, Playwright, Chromium and one-time npm
registry access for its declared open font packages. It creates brand systems; it is
not a logo-design tool or a replacement for design judgement.
