# Content Radar Skills

An industry-agnostic suite of seven independently installable skills for trend discovery, competitor monitoring, responsible newsjacking, channel ideas, and SEO/AEO/GEO content briefs.

Canonical repository: https://github.com/houseofichigo/content-radar-skills

## Included skills

- `content-radar-setup` — creates and confirms the reusable company profile.
- `content-radar` — orchestrates a complete weekly content-intelligence sweep.
- `trend-radar` — finds and ranks timely themes.
- `newsjacking` — identifies current events a company can responsibly address.
- `competitor-scan` — maps competitor activity and content white space.
- `content-ideas` — produces channel-specific, on-brand ideas.
- `seo-aeo-geo` — creates answer-first content briefs for search and AI citation.

On first use, onboarding collects the adopting company's industry, audiences,
regions, topics, competitors, channels, communities, goals, constraints, restricted
topics, approved sources and review requirements. The confirmed `profile.md` belongs
in a user-chosen workspace or host configuration outside the installed skill folder.
No completed profile or client-specific example is bundled.

## Install

Install all seven skills:

```bash
npx skills add houseofichigo/content-radar-skills --skill '*'
```

Install one skill:

```bash
npx skills add houseofichigo/content-radar-skills --skill trend-radar
```

Run `content-radar-setup` first, choose an external profile location and approve the
generated `profile.md` before using the other skills. Profile presence never
authorizes posting, messaging or scheduling.

## Downloads

- [Full seven-skill suite](dist/content-radar-skills.zip)
- [competitor-scan](dist/competitor-scan.zip)
- [content-ideas](dist/content-ideas.zip)
- [content-radar](dist/content-radar.zip)
- [content-radar-setup](dist/content-radar-setup.zip)
- [newsjacking](dist/newsjacking.zip)
- [seo-aeo-geo](dist/seo-aeo-geo.zip)
- [trend-radar](dist/trend-radar.zip)

Released under the [MIT License](LICENSE).
