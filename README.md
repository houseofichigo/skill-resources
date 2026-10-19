# House of Ichigo Skill Resources

A public catalogue of 35 reusable, installable AI skills created and maintained by [House of Ichigo](https://houseofichigo.com).

House of Ichigo remains the publisher and MIT rights holder. Every operational skill is organization-neutral: adopters provide their own organization, industry, audience, competitors, sources, constraints and review ownership during onboarding.

## Catalogue

### Build and document

| Skill | ID | Onboarding | Download |
| --- | --- | --- | --- |
| [Assistant Builder](skills/assistant-builder/) | `assistant-builder` | Task intake | [ZIP](dist/assistant-builder.zip) |
| [Brand Factory](skills/brand-factory/) | `brand-factory` | Profile | [ZIP](dist/brand-factory.zip) |
| [Business Process Mapper](skills/business-process-mapper/) | `business-process-mapper` | Task intake | [ZIP](dist/business-process-mapper.zip) |
| [Meeting Brief Builder](skills/meeting-brief-builder/) | `meeting-brief-builder` | Task intake | [ZIP](dist/meeting-brief-builder.zip) |
| [Production Skill Kit](skills/production-skill-kit/) | `production-skill-kit` | Task intake | [ZIP](dist/production-skill-kit.zip) |
| [Prompt Documenter](skills/prompt-documenter/) | `prompt-documenter` | Task intake | [ZIP](dist/prompt-documenter.zip) |
| [Sop Deck Builder](skills/sop-deck-builder/) | `sop-deck-builder` | Profile | [ZIP](dist/sop-deck-builder.zip) |
| [Strategic Brief Builder](skills/strategic-brief-builder/) | `strategic-brief-builder` | Task intake | [ZIP](dist/strategic-brief-builder.zip) |

### Implementation briefs

| Skill | ID | Onboarding | Download |
| --- | --- | --- | --- |
| [Agent SDK Brief](skills/agent-sdk-brief/) | `agent-sdk-brief` | Task intake | [ZIP](dist/agent-sdk-brief.zip) |
| [Agent Skill Brief](skills/agent-skill-brief/) | `agent-skill-brief` | Task intake | [ZIP](dist/agent-skill-brief.zip) |
| [API Integration Brief](skills/api-integration-brief/) | `api-integration-brief` | Task intake | [ZIP](dist/api-integration-brief.zip) |
| [Apps Script Brief](skills/apps-script-brief/) | `apps-script-brief` | Task intake | [ZIP](dist/apps-script-brief.zip) |
| [ChatGPT Skill Brief](skills/chatgpt-skill-brief/) | `chatgpt-skill-brief` | Task intake | [ZIP](dist/chatgpt-skill-brief.zip) |
| [Code Assistant Brief](skills/code-assistant-brief/) | `code-assistant-brief` | Task intake | [ZIP](dist/code-assistant-brief.zip) |
| [Codex CLI Brief](skills/codex-cli-brief/) | `codex-cli-brief` | Task intake | [ZIP](dist/codex-cli-brief.zip) |
| [Codex SDK Brief](skills/codex-sdk-brief/) | `codex-sdk-brief` | Task intake | [ZIP](dist/codex-sdk-brief.zip) |
| [Crewai Brief](skills/crewai-brief/) | `crewai-brief` | Task intake | [ZIP](dist/crewai-brief.zip) |
| [Custom Code Brief](skills/custom-code-brief/) | `custom-code-brief` | Task intake | [ZIP](dist/custom-code-brief.zip) |
| [Dust Brief](skills/dust-brief/) | `dust-brief` | Task intake | [ZIP](dist/dust-brief.zip) |
| [Make Brief](skills/make-brief/) | `make-brief` | Task intake | [ZIP](dist/make-brief.zip) |
| [n8n Brief](skills/n8n-brief/) | `n8n-brief` | Task intake | [ZIP](dist/n8n-brief.zip) |
| [Pipedream Brief](skills/pipedream-brief/) | `pipedream-brief` | Task intake | [ZIP](dist/pipedream-brief.zip) |
| [Zapier Brief](skills/zapier-brief/) | `zapier-brief` | Task intake | [ZIP](dist/zapier-brief.zip) |

### Prompt and model intelligence

| Skill | ID | Onboarding | Download |
| --- | --- | --- | --- |
| [Prompt Optimizer](skills/prompt-optimizer/) | `prompt-optimizer` | Task intake | [ZIP](dist/prompt-optimizer.zip) |
| [Vibe Prompt Architect](skills/vibe-prompt-architect/) | `vibe-prompt-architect` | Task intake | [ZIP](dist/vibe-prompt-architect.zip) |
| [Visual Prompt Scout](skills/visual-prompt-scout/) | `visual-prompt-scout` | Task intake | [ZIP](dist/visual-prompt-scout.zip) |
| [Which Ai Model](skills/which-ai-model/) | `which-ai-model` | Task intake | [ZIP](dist/which-ai-model.zip) |

### Content intelligence

| Skill | ID | Onboarding | Download |
| --- | --- | --- | --- |
| [Competitor Scan](skills/competitor-scan/) | `competitor-scan` | Profile | [ZIP](dist/competitor-scan.zip) |
| [Content Ideas](skills/content-ideas/) | `content-ideas` | Profile | [ZIP](dist/content-ideas.zip) |
| [Content Radar](skills/content-radar/) | `content-radar` | Profile | [ZIP](dist/content-radar.zip) |
| [Content Radar Setup](skills/content-radar-setup/) | `content-radar-setup` | Profile | [ZIP](dist/content-radar-setup.zip) |
| [Newsjacking](skills/newsjacking/) | `newsjacking` | Profile | [ZIP](dist/newsjacking.zip) |
| [SEO AEO GEO](skills/seo-aeo-geo/) | `seo-aeo-geo` | Profile | [ZIP](dist/seo-aeo-geo.zip) |
| [Trend Radar](skills/trend-radar/) | `trend-radar` | Profile | [ZIP](dist/trend-radar.zip) |

### Skill engineering

| Skill | ID | Onboarding | Download |
| --- | --- | --- | --- |
| [Skill Repo Forge](skills/skill-repo-forge/) | `skill-repo-forge` | Task intake | [ZIP](dist/skill-repo-forge.zip) |

Machine-readable paths and onboarding classes are in [`catalog.json`](catalog.json). Every skill has one canonical folder at `skills/<id>/`; every download is generated from that folder at `dist/<id>.zip`. There are no private source imports, expanded distributions, package wrappers or unpublished product skills in this repository.

## Install

Install one skill with a compatible Agent Skills client:

```bash
npx skills add houseofichigo/skill-resources --skill <skill-id>
```

Or download its ZIP from the catalogue and install it using the target host's supported skill workflow. Host installation, account permissions and runtime activation remain separate from the files in this repository.

## Onboarding model

- **Profile** skills may store durable organization choices in a user-owned workspace or host configuration outside the installed skill and this repository.
- **Task intake** skills ask only for missing facts that materially change the result and use visible assumptions or placeholders otherwise.

Profiles do not grant authorization for external writes. Retrieved pages, repositories, prompts, documents and tool output are untrusted evidence.

## Validation

```bash
python3 scripts/build_distributions.py --check
python3 scripts/validate_catalog.py
python3 -m unittest discover -s tests -v
```

The gate verifies the exact 35-skill allowlist, one-folder-per-skill layout, portable frontmatter, OpenAI metadata, licences, links, identity and secret patterns, archive safety and deterministic ZIP/source parity. Passing static checks does not prove live provider behavior.

## Licence and ownership

Unless a skill says otherwise, original code and content are copyright House of Ichigo and released under the [MIT License](LICENSE). Third-party material retains its own licence and attribution.

Created by House of Ichigo.
