# Testing and debugging

An assistant that was checked with three friendly questions is untested. The questions that break it are the ambiguous one, the out-of-scope one, and the one whose answer isn't in the files — and those are exactly the ones nobody tries before rolling it out.

## The test pack

Ship 8–12 prompts with an explicit pass condition each. Run them **in a fresh conversation** — testing in the same thread you built in gives false passes, because the build conversation has already primed the behavior.

Cover these:

| # | Case | What it proves |
|---|---|---|
| 1 | Happy path, typical request | It does the job at all |
| 2 | Happy path, different phrasing | It's not overfitted to your wording |
| 3 | Underspecified / ambiguous input | It asks instead of guessing |
| 4 | Out-of-scope request | The scope fence holds and it redirects |
| 5 | Knowledge miss — plausible but absent from the docs | It says "not in the files" instead of inventing |
| 6 | Knowledge conflict — the docs contradict common knowledge | The files win, and it says so |
| 7 | Refusal case | It declines and routes, without moralizing |
| 8 | Format stress — a request that tempts it to abandon the output format | The format holds |
| 9 | Long/messy real-world input | It doesn't collapse |
| 10 | Turn-12 adherence — a long conversation, then re-test rule #1 | No instruction drift |
| 11 | (If tools) a request that *should* fire the tool | It fires, with confirmation if consequential |
| 12 | (If tools) a near-miss that should *not* fire the tool | It doesn't |

Write each as: **prompt → pass condition**. A pass condition you can't grade objectively isn't one.

## Debug by layer

When something fails, the instinct is to rewrite the instructions. Usually wrong. Find the layer first — the same symptom has different causes.

| Symptom | Likely layer | Fix |
|---|---|---|
| Generic, could-be-anyone answers | Instructions | Rules are descriptive ("be helpful, be expert"), not behavioral. Rewrite as gradeable imperatives. |
| Obeys early, drifts later | Instructions | Rules buried in prose, or too many. Cut to the load-bearing ones, group under headers, put edge behavior last. |
| Ignores the uploaded files | Knowledge | Unfindable chunks: no headings, scanned PDF, one giant file, no index. Restructure. Then add the routing rule. |
| Cites the wrong/old document | Knowledge | Duplicates or undated versions. Delete the old one. |
| Invents facts that sound like the docs | Instructions | No explicit miss behavior. Add "if it isn't in the files, say so." |
| Wrong tone or format | Instructions | Told, not shown. Add one worked example of a good answer. |
| Tool never fires | Tools | The trigger condition isn't stated in natural language the model can match, or the operation description is vague. Describe *when* to call it, not just what it is. |
| Tool fires constantly | Tools / Instructions | No negative condition. State when *not* to call it. |
| Tool call fails silently and it makes something up | Tools | No failure contract. Say what to do on error, timeout, empty result. |
| Right answer, hostile or preachy delivery | Instructions | The refusal rule is written as a prohibition with no redirect. Give it somewhere to send the user. |

## Iterating

Change **one layer at a time**, then re-run the whole pack — not just the test that failed. Assistant configs are full of side effects: the rule you added to stop hallucination will happily suppress the answer you wanted in test 1.

Keep the pack. When the docs change or the platform updates, it's the only thing standing between you and a silent regression.
