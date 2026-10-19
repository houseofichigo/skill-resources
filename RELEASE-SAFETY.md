# Public release safety policy

The repository publishes exactly the 13 IDs declared in `catalog.json`. House of
Ichigo is the publisher and MIT rights holder; that attribution is intentionally
public. Skill behavior, examples and defaults must remain independent of the
publisher's company environment.

## Public/private boundary

Allowed in this repository:

- reviewed, organization-neutral skill instructions;
- fictional examples using `example.com` identities;
- deterministic distribution ZIPs generated from reviewed source;
- public provider documentation and properly licensed references;
- publisher, repository and licence attribution.

Never allowed:

- organization or client profiles, source imports, private archives or originals;
- personal contact details, credentials, account identifiers or private URLs;
- internal runtime paths, company procedures or unpublished implementation briefs;
- downloaded code or prompt-library mirrors gathered during research;
- generated user output or onboarding answers.
- expanded package copies under `dist/`; distributions are ZIP files only.

HOI OS product skills belong in the separately maintained HOI OS repository. They
must not be copied into this general-purpose catalogue.

## Onboarding and storage

Profile-based skills collect only the context needed for their job and require the
user to confirm discovered facts. Profiles are stored in a user-chosen workspace or
host configuration outside the installed skill directory. Stateless skills ask only
questions that materially change the result and use visible placeholders for unknown
facts. No onboarding answer is committed or placed in a distributable archive.

## External-content boundary

Web pages, repositories, comments, prompt libraries, documents and tool output are
untrusted evidence. Skills must not follow embedded instructions, expand permissions,
execute retrieved code or disclose local data. They should verify provenance and
licensing, quarantine suspicious sources, and report freshness limitations.

## Release gate

Run:

```bash
python3 scripts/build_distributions.py --check
python3 scripts/validate_catalog.py
python3 -m unittest discover -s tests -v
```

The gate verifies the exact catalogue allowlist, licence and UI metadata, local
links, forbidden paths, common secret and identity patterns, archive traversal,
deterministic timestamps, and complete source/ZIP parity. Passing is necessary but
not sufficient: a human reviewer must inspect every source diff before publication.

If confidential data or a credential ever enters Git history, stop publication,
preserve a private recovery bundle, rotate credentials, and clean the history. A
history rewrite does not erase existing forks, clones or caches.
