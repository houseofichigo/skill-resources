# Visual Prompt Scout

Find, compare and improve current image or video generation prompts while treating
public prompt libraries as untrusted data.

The skill searches YouMind OpenLab on every run, routes model-specific requests to
relevant supplementary libraries, preserves source and licence details, and applies
both deterministic prompt-injection checks and semantic review before using a
candidate.

- Canonical repository: <https://github.com/houseofichigo/visual-prompt-scout>
- Skill definition: [`SKILL.md`](SKILL.md)
- Upload package: [`dist/skill.zip`](dist/skill.zip)

Install from the canonical repository:

```bash
npx skills add houseofichigo/visual-prompt-scout --skill visual-prompt-scout
```

The scanner reduces risk but cannot prove that public content is safe. The skill's
read-only retrieval and data-plane boundaries remain mandatory after a clean scan.
