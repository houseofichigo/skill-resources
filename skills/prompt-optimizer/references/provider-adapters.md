# Provider adaptation

Provider behavior changes. Use these links as discovery anchors, open the current official documentation when adaptation matters, and report any unverified assumption.

## Shared adaptation rules

- Identify the exact target: chat UI, API message, reusable prompt object, agent instructions, project instructions, or another surface.
- Verify current message roles, tool/schema controls, supported model family, and any deprecated mechanism.
- Keep runtime controls outside prompt text unless the interface only accepts a single text field.
- Prefer a provider-neutral prompt when the target is unknown.
- Do not transpose one provider's message hierarchy or schema behavior onto another.

## OpenAI

Primary anchors:

- Prompt engineering: https://developers.openai.com/api/docs/guides/prompt-engineering
- Reasoning best practices: https://developers.openai.com/api/docs/guides/reasoning-best-practices
- Structured outputs: https://developers.openai.com/api/docs/guides/structured-outputs

For current reasoning models, prefer a clear goal, constraints, and verifiable output over requests to expose chain-of-thought. Verify current model and message-role guidance before making a model-specific recommendation.

## Anthropic

Primary anchor:

- Prompting best practices: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

Use examples or XML-style boundaries only when they reduce real ambiguity. Verify current model-specific and long-context guidance rather than treating it as universal.

## Google Gemini

Primary anchor:

- Prompt design strategies: https://ai.google.dev/gemini-api/docs/prompting-strategies

Treat prompt design as iterative and model-specific. Verify current structured-output, tool, and system-instruction support on the target Gemini surface.

## Microsoft and Mistral

Use product-specific official documentation. Microsoft guidance can be scoped to a particular Copilot rather than all Microsoft AI products. For Mistral, verify whether native custom structured output, JSON mode, or textual formatting is appropriate for the selected endpoint.
