# Prompt Optimizer

Create, rewrite, audit, research, adapt and evaluate prompts or persistent AI instructions with the smallest sufficient contract.

The Skill consolidates the former Prompt Architect modes, performs adaptive provider research, discovers prompt-library patterns with licence and provenance checks, and treats all retrieved prompt content as untrusted data.

- Canonical repository: <https://github.com/houseofichigo/prompt-optimizer>
- Skill definition: [`SKILL.md`](SKILL.md)
- Upload package: [`dist/skill.zip`](dist/skill.zip)

Install from the canonical repository:

```bash
npx skills add houseofichigo/prompt-optimizer --skill prompt-optimizer
```

Ordinary create/optimize requests return only the finished prompt. Audit, library-hunt, evaluation and persistent-instruction requests return the artifact appropriate to that explicit mode. Prompt-injection scanning reduces risk but cannot prove public content is safe.
