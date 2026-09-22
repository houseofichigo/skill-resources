# Where to check the current answer

Always prefer a provider's own documentation over a blog round-up. Round-ups
go stale and repeat each other's errors.

## Official lineups and pricing

| Provider | What to check | Where |
|---|---|---|
| OpenAI | Model catalogue, positioning, pricing | https://developers.openai.com/api/docs/models |
| OpenAI | How to choose between their models | https://developers.openai.com/api/docs/guides/model-selection |
| OpenAI | What ChatGPT's modes map to, by plan | https://help.openai.com |
| Anthropic | Model overview and specifications | https://platform.claude.com/docs/en/docs/about-claude/models/overview |
| Anthropic | Choosing a model | https://platform.claude.com/docs/en/docs/about-claude/models/choosing-a-model |
| Anthropic | Plans, limits, product features | https://support.claude.com |
| Google | Gemini model list and capabilities | https://ai.google.dev/gemini-api/docs/models |
| Google | Gemini apps: modes, plans, Deep Think | https://support.google.com/gemini |

## Independent comparison

Useful as a secondary signal only. Never as the deciding authority.

| Source | What it gives | Caveat |
|---|---|---|
| Artificial Analysis — https://artificialanalysis.ai | Intelligence index, price, speed, latency across hundreds of models | Composite indices hide task-specific differences |
| LMArena | Human preference rankings | Preference ≠ correctness on your task |
| Public benchmark leaderboards (coding, tool use, long context) | Shortlisting evidence | Harness, scaffold and tool access change results as much as the model does |

## How to read a benchmark score responsibly

A score means little without knowing: which benchmark version, which model
snapshot, how much reasoning effort was allowed, what agent harness ran it,
what tools it had, and when it was measured. Two numbers from different
harnesses are not comparable.

Benchmarks also leak. Newer versions of well-known coding benchmarks have found
that contaminated or flawed tasks materially inflated earlier scores — treat
any single dramatic result with suspicion until it is reproduced.

Use benchmarks to build a shortlist of two or three candidates. Decide between
them with a short test on the person's own real work.

## The test that beats every leaderboard

Take three real examples of the task. Run them through two or three candidates.
Judge the outputs blind if you can. Ten minutes of this is worth more than any
amount of benchmark reading, and it is the only evidence that reflects the
person's actual house style, data and quality bar.

## Related open-source work

Worth knowing about, though these solve the *programmatic* routing problem
rather than the human "what should I use" problem:

- RouteLLM — https://github.com/lm-sys/RouteLLM — learns strong-vs-weak routing
- LiteLLM — https://github.com/BerriAI/litellm — gateway with fallbacks and load balancing
- vLLM Semantic Router — https://github.com/vllm-project/semantic-router — policy-based routing
- awesome-ai-model-routing — https://github.com/Not-Diamond/awesome-ai-model-routing — curated map of the field
