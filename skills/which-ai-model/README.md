# Which AI Model

An installable, organization-neutral skill that helps people choose the current AI
product, mode and model for a specific task. It evaluates the needed capability and
available product tools before selecting a model tier.

The skill never names a current model from memory. It searches official provider
documentation first, uses independent evidence where helpful, and marks its dated
offline snapshot as a fallback.

## Install

Download [`dist/which-ai-model.zip`](dist/which-ai-model.zip) and upload or extract it
using your host's Agent Skills instructions. The archive contains one portable
`which-ai-model/` folder.

For a local skills directory:

```bash
mkdir -p /path/to/skills
unzip dist/which-ai-model.zip -d /path/to/skills
```

## Use

Ask in plain language, for example:

- “Which current model and product mode should we use to summarize 40 interviews?”
- “Which subscription best fits our team's document-analysis workflow?”
- “Why is our current assistant weak at spreadsheet work?”

The skill asks only for missing constraints that could change the recommendation. It
does not create or persist a company profile.

## Package contents

- `SKILL.md` — routing and workflow
- `references/` — decision tree, capability map, dated fallback and source guidance
- `agents/openai.yaml` — optional host metadata
- `LICENSE.txt` — MIT licence and House of Ichigo copyright

Created by [House of Ichigo](https://houseofichigo.com) and released under MIT.
