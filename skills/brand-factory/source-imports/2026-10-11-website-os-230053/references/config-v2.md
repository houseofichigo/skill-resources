# brand.config.json v2

The one hand-edited file. Read this before writing or migrating a config.
The schema is `assets/schema/brand.config.v2.schema.json`; the gate is
`build/config.py`; the worked example is
`examples/house-of-ichigo/brand.config.json` (House of Ichigo 3.3,
reproduced from its own book).

## Mode

| `mode` | When | What the gate does |
| --- | --- | --- |
| `reproduce` | The brand exists: a book, a PDF, a site, a token file | Every value cites a source. A value the sources do not hold is `null` with a `$gap`. A `guess` with no reconcile item fails the build. Fidelity is gated (step 3 onward). |
| `create` | No brand yet | Values may be proposals (`$src: "WO"`, `$conf: "default"`). Fidelity is not run. |

Reproduce mode never invents. If a generator needs a value the brand does
not have, the config says so — a gap, or a website-os default marked as one
— and `out/CONFIRM.md` lists it for the owner.

## Provenance

Any object may carry:

| Key | Meaning |
| --- | --- |
| `$src` | A source id from `sources`, optionally with a locator: `S2:p23`, `S1:ui.radius`, `WO`. Applies to everything beneath it. |
| `$conf` | `high` stated · `medium` stated but contradicted, or read from a practised file · `derived` computed from other values · `guess` sampled · `default` a website-os default, not the brand |
| `$gap` | Why this is empty. The node and everything under it is a gap. |
| `$src_<x>` · `$conf_<x>` · `$gap_<x>` | The same, for the descendant whose path relative to this object is **exactly** `x` (keys joined by `_`, list indices dropped). `$src_roles_px_phone` on `type.scale` reaches `type.scale.roles[*].px.phone`. |
| `$note` · `$comment` | Prose for people. Never a value. |

Precedence, innermost wins: the node's own `$src`/`$conf`/`$gap`; then the
nearest ancestor's override whose path matches exactly; then inheritance.
An explicit `$src` ends both an override and an inherited gap. A fresh
`$src` without `$conf` is `high` (or `default` for `WO`); an override
without `$conf` keeps the confidence it inherited.

**null is never a value.** It is a gap, or — under a node with a `policy`,
`rule` or `$note` — an empty slot explained in place. Absent by design is
the string `"none"`, which is a value.

Every `sources` entry with a `path` must exist; one with `sha256` must
still hash to it (prefix match), so a citation cannot silently point at
changed evidence. A `locator: page` source should state `pages`; citations
past the last page fail.

## Reconcile

`reconcile.items` is the ledger of every place the sources disagree, and
every value reproduce mode needed that the sources do not hold.

```json
{ "id": "R1", "path": "effects.policy.radius_max_px", "status": "confirm",
  "candidates": [ { "value": 2, "src": "S2:p73" }, { "value": 4, "src": "S1:ui.radius" } ],
  "chosen": 4, "why": "…", "question": "…", "affects": ["effects.policy.radius_max_px", "shape.floating"] }
```

`status`: `resolved` (decided with a reason, no owner input) · `confirm`
(goes to CONFIRM.md; needs `question` and `affects`) · `confirmed` (the
owner answered; put the answer in `answer`, edit the leaves in `affects`).
`chosen` is what the config uses until then — a value, or `null`.

## Token references

Components (and later every generated file) refer to tokens by the names
the generators emit, never by literal values:

| Reference | Resolves to |
| --- | --- |
| `{color.<role>}` | `color.roles.<role>` — bg, fg, accent, accent_on, accent_on_dark, muted, muted_on_dark, surface, border, border_strong, border_input |
| `{color.state.<x>}` | `color.states.<x>` |
| `{color.semantic.<x>}` | `color.semantic.<x>` with a hex |
| `{color.pillar.<x>}` | `color.accents.<x>` |
| `{color.dataviz.chart.<n>}` | `color.dataviz.chart.<n>` |
| `{radius.surface\|control\|floating}` | `shape.*` |
| `{space.<step>}` · `{type.<role>}` · `{motion.<duration>}` · `{ease.<name>}` · `{elevation.<level>}` · `{component.<name>}` | the matching block |

A **style slot** is any key named for paint — `bg`, `fg`, `color`, `fill`,
`border`, `outline`, `edge`, `track`, `ring`, `rule`, `scrim`, alone or as
a suffix (`row_rule`, `chip_fg`). It holds a reference, a keyword (`none`,
`transparent`, `currentColor`, `inherit`, `underline`), a number, or a
composite: `{width, style, color[, offset]}` for borders and outlines,
`{color, alpha}` for a translucent colour. A literal colour or prose in a
slot fails the gate.

Naming trap: shadcn's `accent` is a hover tint. The brand's `{color.accent}`
is the brand colour. `components.shadcn.map` is the only place they meet.

## effects.policy

The brand's prohibitions. `check.py`, `verify.js` and `selftest.py` read
them; v1 hard-coded one brand's.

| Key | Values | Checked by |
| --- | --- | --- |
| `shadow` | `none` · `tokens` · `allowed` | check (box-, text-shadow, drop-shadow), verify (computed style) |
| `gradient` | `none` · `allowed` | check |
| `blur` · `filter` | `none` · `allowed` | check |
| `radius_max_px` | number | check, any unit, any corner, `--radius*` vars; `50%` is left to the brand's circle rule |
| `elevation` | `border` · `shadow` · `both` | the generators |
| `transform_on_press` · `opacity_hover` · `scroll_linked_motion` | boolean | check |
| `font_service_links` | `none` · `allowed` | chassis rule today; check bans font services for every brand |
| `decorative_animation` · `card_grids` | boolean | audit-only (site-audit); a regex cannot see them |

`selftest.py` proves both directions: what the policy forbids fires on a bad
file; what it allows stays silent on a clean one.

## Required blocks a brand may not have

`density`, `a11y.floors`, `motion` and `type.scale` are required because the
generators cannot run without them. A brand that never stated them (a
print-only identity, say) copies the starter's block and marks it
`"$src": "WO"`: the build runs, the values are counted as defaults, and
CONFIRM.md lists them. That is not invention: it is a declared stand-in.

## Migrating a v1 config

| v1 | v2 |
| --- | --- |
| `color.ground/ink/brand/brand_on_dark/muted/surface/line` | `color.roles.bg/fg/accent/accent_on_dark/muted/surface/border` (+ `accent_on`, required) |
| `color.semantic.<k>.text: "ink"\|"ground"` | `color.semantic.<k>.on: "fg"\|"bg"`; brand names as keys, v1 chassis names in `component_name` |
| `type.display/text/mono/arabic` | `type.families.*`; `weights` becomes `{axis: [min, max]}` or `{static: [...]}` |
| `type.tracking.xl/lg/md/sm` | `type.tracking.bands[]`, each with `family` and `min_px` |
| — | `type.scale.roles[]`, keyed by `layout.breakpoints.order` |
| `locales: [...]` | `locales: {default, list, rtl}` |
| `voice.banned: [...]` | `voice.banned.list` |
| prohibitions inside check.py | `effects.policy` |
| — | `mode`, `sources`, `$src`/`$conf`, `reconcile` |

`build/config.py` hands the v1 scripts a v1-shaped view (`v1_view`), so
`tokens.py`, `css.py`, `book.py` and `brandmd.py` run unchanged while the v2
generators are written.
