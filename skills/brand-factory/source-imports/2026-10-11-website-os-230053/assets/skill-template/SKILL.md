---
name: {{slug}}-brand
description: The single source of truth for the {{brand}} brand and every surface it appears on. Use whenever {{brand}} is mentioned, and for any request to design, draft, prototype, mock up, build, restyle or write copy for a {{brand}} surface — websites, landing pages, decks, documents, reports, one-pagers, proposals, RFP responses, product UI, stationery, social posts, signage — and for brand questions or reviews of existing work. Includes ready-to-fill templates, machine-readable tokens and a checker that exits non-zero on a violation. Version {{version}}. Retired colours that must never appear: {{retired}}. Type is {{faces}}, self-hosted — never link a font service.
---

# {{brand}} branding

Everything needed to produce on-brand {{brand}} work, and to verify it
before it ships. Version {{version}}, {{date}}. Supersedes {{supersedes}}.

{{positioning}}

## Start here, every time

1. **Read `BRAND.md`.** The complete rule set. Non-negotiable.
2. **Scaffold from `templates/`** rather than starting from nothing.
3. **Check before you ship:**
   ```bash
   python3 scripts/check.py out/your-file.html
   ```
   It exits non-zero on a violation. It catches mechanical failures only
   — it cannot tell you whether the margin is right.

## Where things live

| You need | Read |
|---|---|
| Any rule | `BRAND.md` |
| A value, in code | `references/tokens.json` |
| The stylesheet | `references/tokens.css` |
| Working markup | `templates/` |
| The human reference | `references/` — the brand book |
| Fonts | `references/fonts/` + `fonts-embedded.css` |

## The rules that break most often

- **A retired colour reappears** — {{retired}}. Their presence identifies
  old material.
- **A font service is linked** instead of self-hosting. A page that links
  one renders in a fallback face without failing loudly: it looks right
  to whoever made it and wrong to everyone else.
- **`opacity` used as a hover state.** Use the fixed ramp — opacity lets
  the surface behind show through, so a button over an image changes
  colour with the image.
- **A logo image with no `align-self` guard.** Logos are flex children on
  most surfaces and `align-items:stretch` overrides `width:auto`. The
  mark becomes an oval and nobody can say why.
- **A bare `@media (max-width:…)`.** Chromium uses the CSS page width as
  the print viewport, so it fires during PDF export and collapses every
  column. Always `@media screen and (…)`.
- **`box-shadow` at any elevation.** Separation is surface, border weight
  and a scrim.
- **Print type sizes inside the product,** or product density in print.
  They are separate scales and neither is a fallback for the other.

## Non-negotiables, in one place

Primary actions are always the brand colour. Body copy is always ink.
Accent colours are wayfinding only — never a button, never body copy.
All numerals in the mono face. No gradients, no shadows. Fonts are
self-hosted.

## The surfaces

Eight templates, each a working file that already passes the checker.
**Start from the closest one and delete what you do not need** — starting
from nothing is how a surface drifts.

| Template | Surface | Geometry |
|---|---|---|
| `templates/deck.html` | slides, any presentation | 254 × 143mm — 16:9, exports to PDF at PowerPoint proportions |
| `templates/web.html` | website, landing page | responsive, 1280px container |
| `templates/document.html` | report, advisory paper, memo | A4 portrait, multi-page |
| `templates/proposal.html` | proposal, quote, SOW | A4 portrait, 5 pages in decision order |
| `templates/brief.html` | creative or project brief | A4 portrait, one page |
| `templates/onepager.html` | leave-behind, sell sheet | A4 portrait, one side |
| `templates/card.html` | business card | 85 × 55mm with bleed and safety guides |
| `templates/social.html` | social posts | 1200² · 1200 × 628 · 1080 × 1350 |

Things worth knowing before you use them:

- **Print and screen are separate scales.** The deck sets type large
  because it is read from the third row; the document sets it small because
  it is read at arm's length. Neither is a fallback for the other, and
  moving a size between them is the most common way work goes wrong.
- **`card.html` carries print geometry** — 3mm bleed, 4mm safety. The
  dashed guides are for proofing on screen; delete the `guides` class
  before sending to print.
- **`social.html` renders at 1:1 pixels**, so a screenshot at 100% is the
  asset. Export at `deviceScaleFactor: 2` for retina.
- **Media frames are frames, not files.** Replace the placeholder and
  delete its label; never ship the words `REPLACE WITH IMAGE`.
- **A surface that does not exist here gets added here**, not improvised
  once in one file. That is the whole difference between a system and a
  folder.

## Files

```
BRAND.md                    the rule set — read first
references/tokens.json      machine-readable, with measured contrast
references/tokens.css       custom properties, base classes, the logo guard
references/fonts/           self-hosted woff2
templates/                  eight ready-to-fill surfaces
scripts/check.py            verify output — exits non-zero on a violation
```
