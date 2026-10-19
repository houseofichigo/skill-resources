# Content Radar — Profile

<!--
The user-controlled source of truth for this brand. Store the completed copy in a
user-chosen workspace or host configuration, outside the installed skill directory.
Never commit a completed profile or include it in a distribution ZIP. Do not store
credentials, private personal data or confidential source material here.
-->

company:            <fictional example: Northstar Analytics>
website:            <https://example.com>
industry:           <one line — what you do and for whom>
audience:           <primary personas / buying roles, comma-separated>
languages_regions:  <e.g. EN, FR · global / EU / GCC>
goals:              <what this content program should achieve>
constraints:        <legal, regulatory, brand, budget or timing constraints>
restricted_topics:  <topics or claims that require review or must be avoided>
review_owner:       <role, not personal contact details>
external_actions:   <draft only / approval required before publishing or messaging>

# The core topics you want to own (aim for 5–12)
topics:
  - <topic 1>
  - <topic 2>
  - <topic 3>

# Direct + content competitors. Note the channels each is active on and anything notable.
competitors:
  - name: <competitor A>
    channels: [web, li, yt, rd]
    note: <what they own>
  - name: <competitor B>
    channels: [web, li]
    note: <what they own>

# 1–3 competitors to ALWAYS surface (fast movers, category leaders, threats)
priority_watch:
  - <name — why>

# Which channels are in scope and their role
channels:
  - Website (SEO·AEO·GEO) — demand capture + citation
  - LinkedIn — <role, e.g. executive distribution>
  - YouTube — <role, e.g. searchable proof>
  - Reddit (+ Quora) — <role, e.g. LLM feeder; expert participation, not brand posting>

# Subreddits/communities where your audience is (with each one's posting rules)
communities:
  - r/<x> — <why it matters> — <rules: promo allowed? AI content? AMAs?>

# Brand voice
brand_voice: <tone · preferred structure · what to avoid>

# Open, no-API sources the skills scan (usually leave as-is)
open_sources:
  - Google News RSS (news.google.com/rss/search)
  - Google Trends
  - Reddit (.json / old.reddit.com)
  - YouTube search + channel pages
  - Wikipedia "Current events" portal
  - Competitor blogs + /sitemap.xml

# Optional approved sector sources. Use public URLs only; never put credentials here.
approved_sources:
  - <https://example.com/industry-source>
