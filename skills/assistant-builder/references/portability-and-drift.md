# Portability and drift

## What carries across platforms

The spec is portable. The plumbing is not.

| Spec element | Custom GPT | Claude Project | Gemini Gem |
|---|---|---|---|
| Role, goal, scope, tone, output | Carries | Carries | Carries |
| Workflow steps | Carries | Carries | Carries — number them, Gems drift most |
| Refusal / uncertainty behavior | Carries | Carries | Carries |
| Knowledge documents | Carries | Carries | Carries (Drive-centric) |
| Conversation starters | Native field | No equivalent — fold the top questions into the project description or an onboarding doc | No equivalent |
| Capability toggles (browsing, code, images) | Per-GPT toggles | Not per-project — depends on the workspace's tools/connectors | Not a per-Gem form |
| External API calls | Actions (OpenAPI + auth) | Via workspace connectors, not a per-project schema | No per-Gem equivalent — don't promise it |
| Public distribution | Store | No — internal sharing only | No — Workspace sharing |

**Consequences when porting:**

- **GPT → Project or Gem:** the Actions layer does not come with you. If the assistant's job depends on live API calls, porting it means losing the job, not just a feature. Say this out loud before you compile.
- **GPT → anything:** conversation starters disappear. Their onboarding value doesn't — put the three questions somewhere the user will see them.
- **Anything → Gem:** tighten and number the workflow. The thinner configuration surface means loose instructions get improvised past.
- **Anything → Project:** add source attribution and a document-vs-chat rule; you now have a surface that produces documents, and it needs to know when to.

## Drift discipline

Every one of these platforms ships changes on a timescale shorter than this skill's shelf life. The following are **drift-prone** and must never be asserted from memory:

- instruction character limits
- knowledge file counts, sizes, and accepted formats
- number of conversation starters
- capability names and toggles
- Actions / MCP / Apps availability, requirements, and terminology
- model names and versions behind each product
- plan tiers, sharing options, admin controls
- store review and publishing requirements

**How to handle them:**

1. **Verify** if web search or current documentation is available. Cite what you find.
2. **If you can't verify:** name the constraint's *purpose*, not its value, and defer to the UI.
   - Good: "The instruction field has a hard character cap — keep this tight and check the counter in the builder."
   - Bad: "You have 8,000 characters."
3. **Design limit-agnostic.** A spec that fits in 8,000 characters and still works at 4,000 is a better spec. Prefer short imperative rules over long prose in every case — it's both better behavior *and* insurance against a cap you didn't check.
4. **Label uncertainty when the user asks a product-fact question.** "That changes often — check the current docs" is a correct answer. A confidently outdated number is a wrong one, and it's the kind of wrong that gets found in front of a client.

## Stable ground

These don't drift, and the build should rest its weight here:

- Instructions define behavior; knowledge holds lookup content; tools reach outside. Getting the lever right matters more than the field limits.
- Behavioral rules beat descriptive persona.
- Assume instructions and knowledge are extractable. Design as if they'll be read.
- No credentials, no personal data, no unpublishable content in either lever.
- Anything with a side effect gets a confirmation gate.
- Untested is unshipped.
