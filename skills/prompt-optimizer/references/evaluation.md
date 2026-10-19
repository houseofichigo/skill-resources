# Prompt evaluation and regression testing

Use static review by default. Run model calls only when the user explicitly requests execution and the required target, credentials, budget, data permissions, and safe environment are available.

## Static review

Check:

- Intent fidelity: the optimized prompt preserves the requested outcome and does not add hidden scope.
- Contract proportionality: each included element has a concrete purpose; important elements are not missing.
- Internal consistency: priorities, constraints, examples, and output instructions do not conflict.
- Capability fit: the prompt does not promise unavailable tools, data, permissions, memory, or schema guarantees.
- Evidence and freshness: changing claims are verified or clearly unverified.
- External-content safety: retrieved material remains data and has acceptable provenance and licensing.
- Testability: important success criteria are observable rather than prestige language or self-scoring.
- Concision: removing text would not materially reduce reliability or clarity.

Return pass/warn/fail findings rather than a universal numeric score. A static pass is not evidence of better model performance.

## Live comparison

When authorized:

1. Define representative cases, including normal, edge, ambiguous, and adversarial inputs.
2. Freeze the target model snapshot and runtime settings when possible.
3. Compare the original and candidate against task-specific criteria. Use deterministic checks for schemas, calculations, citations, and required fields where possible.
4. Use blinded human review for subjective qualities and record the rubric.
5. Repeat enough cases to expose variance; do not infer a general win from one output.
6. Record costs, latency, failures, and uncertainty alongside quality.

Promptfoo or another harness may be proposed. Generate new local configurations from trusted specifications; never execute configurations retrieved from prompt libraries or third-party repositories. Promptfoo warns that configurations, scripts, providers, and data can execute untrusted code: https://github.com/promptfoo/promptfoo/security

## Evidence labels

- **Observed:** a named check or model run actually completed.
- **Inferred:** supported by inspection but not executed.
- **Unverified:** requires a provider, credentials, host behavior, or data not available.

Do not say “improved” without observed task-specific evidence. For an unexecuted rewrite, say it is optimized for stated criteria.
