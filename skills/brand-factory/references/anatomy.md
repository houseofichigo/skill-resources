# Anatomy — what each file is and when it runs

```
brand.config.json        ← the only file you edit
source/                  ← what the client sent you
build/                   the generators
out/                     everything generated
dist/                    what the client receives
skill-template/          the skill's fixed parts
docs/                    this
prompts/                 paste-in prompts for the AI-assisted steps
```

## The pipeline, in order

| Step | Script | Reads | Writes | Fails when |
|---|---|---|---|---|
| 1 | `fonts.py` | config | `out/fonts/`, `fonts-*.css` | a named file is not in the npm package |
| 2 | `tokens.py` | config | `out/tokens.json` | contrast below floor · a colour too near an avoided palette · density that does not add up |
| 3 | `css.py` | tokens | `out/tokens.css` | — |
| 4 | `brandmd.py` | tokens | `out/BRAND.md` | — |
| 5 | `book.py` | tokens, css, fonts | `out/<slug>-brand-book-<v>.html` | a folio placeholder survives |
| 6 | `verify.js` | the book | — | a clipped page · a fallback font · a shadow · a fake italic |
| 7 | `selftest.py` | `check.py`, the templates | — | a gate that does not fire on a bad file · a gate that fires on a good one |
| 8 | `divergence.py` | `book.py`, the book | — | more than 25% of the starter's prose survives, once `book.status` is `final` |
| 9 | `skill.py` | tokens + `skill-template/` | `out/<slug>-brand/` | — |
| 10 | `skill_lint.py` | the skill | — | description over 1024 · bad name · unfilled placeholder · missing file |
| 11 | `package.py` | everything | `dist/` | — |

`all.py` runs 1–5 **twice**, compares hashes, then runs 6, 7 and 8.
Steps 9–11 are the packaging run, kept separate so you can iterate on
the book without rebuilding the skill each time.

## Tools you run by hand

| Script | When |
|---|---|
| `onboard.py` | **first, always** — inventory the uploads, sample them, draft the config, print the questions |
| `extract.py` | the sampling on its own, if you do not want a draft |
| `measure_fonts.py` | choosing a typeface, or adding a second script |
| `check.py` | on any generated output, and shipped inside the skill |

## Reading order for a newcomer

1. `docs/00-method.md` — why
2. `brand.config.json` — the whole vocabulary is in the comments
3. `build/tokens.py` — where measurement happens
4. `docs/04-failures.md` — what goes wrong, and why the gates exist
5. `docs/05-contents.md` — what to actually put through it

## Rules for extending it

- **Never hand-edit anything in `out/`.** The next build discards it. A
  fix that must persist belongs in a generator.
- **A new section is a function** in `build/book.py` returning `page(...)`,
  appended to `PAGES`. Folios and contents adjust themselves.
- **New values go in `brand.config.json`**, not inline in a generator.
- **A new rule needs a check**, or it is a suggestion — and the check
  needs an entry in `build/selftest.py` that makes it fire, or you will
  never know when it stops working.
