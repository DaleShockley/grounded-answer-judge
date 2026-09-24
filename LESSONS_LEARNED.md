# Lessons Learned

A running log for this project and the two it builds on ([rag-docs-assistant](https://github.com/DaleShockley/rag-docs-assistant) and [sprint-risk-agent](https://github.com/DaleShockley/sprint-risk-agent)). Every claim here is backed by a number from a real run. Updated after each phase.

**Status:** Phases 0–1 complete. Phase 2 (human labels) in progress. Phase 3 judge v1 built and run; agreement with human labels pending.

---

## The data so far

### Answer set (`data/answers.jsonl`)

| | Count |
|---|---|
| Questions | 30 (26 answerable from the docs, 4 not) |
| Original RAG answers | 30 |
| Seeded-flaw copies | 17 |
| **Total answers to grade** | **47** (64% original / 36% flawed) |

| Seeded flaw | Count | Avg. length (chars) |
|---|---|---|
| `fabricated_detail` | 4 | 508 |
| `contradiction` | 3 | 450 |
| `wrong_citation` | 3 | 647 |
| `off_topic` | 2 | 831 |
| `incomplete` | 2 | 396 |
| `unanswerable_hallucination` | 3 | 1,435 |
| *Original answers (median)* | *30* | *529* |

### How the RAG assistant did on its own 30 questions

`claude-sonnet-4-5`, header-aware chunking, top-5 retrieval.

| Outcome | Result |
|---|---|
| Answerable questions answered fully from the excerpts, citing the right doc | **22 / 26** |
| Answerable questions where it said it had "not enough information" (fully or partly) | 4 / 26 (q04, q10, q17, q18) |
| Unanswerable questions where it correctly said the docs don't cover it | **4 / 4** |
| Right **doc** somewhere in the top 5 retrieved | 26 / 26 |
| Right **section** in the top 5 for the four misses | 0 / 4 |

*q10 was first counted as a success because it cited the right doc. The Phase 3 judge caught it: the answer hedges ("it appears you would need to import `BaseModel` from Pydantic") because the "Import Pydantic's BaseModel" section wasn't retrieved.*

### Judge v1 (`claude-sonnet-5`, prompt `v1`), all 47 answers

| Measure | Result |
|---|---|
| Seeded flaws caught on the criterion they target | **17 / 17** |
| Original answers failed on at least one criterion | 4 / 30 (q04, q10, q11, q18) |
| Cost | $0.33 total ($0.005–0.014 per answer) |
| Latency | median 3.2 s, max 12 s |

### Sprint-risk-agent eval (same 8 labeled issues, date pinned to 2026-09-08)

| Approach | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| Rule-based baseline | 6/8 | 6/8 | 6/8 |
| Claude agent (`claude-sonnet-4-5`) | 6/8 | 7/8 | 6/8 |

---

## Lessons

### Evaluation design

**1. Doc-level retrieval metrics overstate quality.**
rag-docs-assistant scores retrieval as "was the right *file* in the top k?". On this set that's 26/26, a perfect score. Yet the assistant still fell short on 4 questions, because in each case the right file came back but the wrong *sections* of it. For example, q18 retrieved path-params.md at rank 1, but its "Predefined values" section, not "Data validation", which holds the answer. *Takeaway:* measure retrieval at the level the answer actually lives: the chunk or section, not the file.

**2. Real failures are worth more than seeded ones.**
The most interesting records in the answer set weren't planted. They're the RAG assistant honestly saying "I don't have enough information" when the answer existed (q04, q10, q17, q18). Those answers are mostly **faithful** (nothing false is claimed) but **unhelpful**. A rubric that only checks faithfulness would pass them. That tension is the first thing the Phase 2 rubric has to settle.

**3. Faithful is not the same as true.**
`q01-fabricated_detail` adds the claim that `fastapi dev` auto-reloads. That's true of real FastAPI, but it isn't in the retrieved excerpts. A judge that grades from its own knowledge instead of the evidence will pass it. This record specifically tests whether the judge stays grounded.

**4. Seeded flaws can leak through surface features.**
Flawed answers average 711 characters vs 529 for originals, but that gap comes almost entirely from one type: the made-up tutorials (`unanswerable_hallucination`, avg 1,435) replace short "the docs don't cover this" answers. Every other flaw type is within the normal range. A judge, or a person, could learn "long answer to an off-topic question = suspicious" without checking any facts. *Takeaway:* check whether a simple feature like length predicts the label before trusting a judge's accuracy. This goes into the Phase 4 bias tests.

**5. Blind labeling takes deliberate design.**
Record ids like `q05-wrong_citation` would have given away the answer, so the labeling page hides ids, seeded-flaw fields and notes, and shuffles the order so an original and its flawed copy are never back to back. Showing an id "just for reference" would have quietly biased the ground truth.

**6. An eval can catch a *spec* problem, not just a model problem.**
In sprint-risk-agent, the agent missed issue #107 (assignee out for three weeks) in all 3 runs. Its prompt defines `unowned` as "no assignee", and #107 has one, so the agent followed its instructions exactly. The fix belongs in the definition, not in prompt tweaks tuned until one of 8 cases passes.

**7. Single-label scoring hides legitimate ambiguity.**
Sprint-risk issue #110 is both labeled `blocked` and 15 days idle. The agent chose `blocked` once and `stale` twice. Both are defensible, but only one scores. A multi-label scheme would measure this fairly.

**8. One run is not a result.**
Same agent, same 8 inputs: 6/8, 7/8, 6/8. Any single run would tell a misleading story. LLM evals get repeated runs.

**9. Pin "today" in any eval that involves time.**
The sprint-risk baseline scored 6/8 when written and 5/8 two weeks later, with no code change, because "days idle" was measured from the real current date. Pinning the eval date (`as_of`) made scores reproducible again. The agent also needed to be *told* the date: it had been guessing.

### Judging

**10. Catching planted flaws is the easy test.**
Judge v1 caught 17/17 seeded flaws. That's a useful sanity check (the plumbing works, and the judge stays grounded: it failed `q01-fabricated_detail`, the true-but-unsupported claim), but planted flaws are one clean defect each. The judge's real value showed up on the *unplanted* answers, where it found q10, a failure the Phase 1 check had missed. Agreement with human labels is still the real test.

**11. When the rubric is silent, the judge is inconsistent.**
q04, q17 and q18 are the same situation: an honest "the excerpts don't say" when the docs did. The judge passed **relevant** for q04 and q17 but failed it for q18. The prompt never says how to treat that case, so the judge decided differently each time. A human grader faces the same gap. The fix is a rubric rule, not a stronger model. This is the first input to prompt v2.

**12. A stricter judge isn't necessarily a wrong judge.**
For q11 the judge failed **cited correctly** because one sentence ("you don't have to declare them in any specific order") comes from query-params.md, which the answer didn't cite. That's stricter than a person skimming would be, but defensible. Whether it counts as a disagreement depends on the rubric, which is why the rubric gets written down.

### Working with model output

**13. Models don't reliably follow format instructions, so parse defensively.**
- The sprint-risk agent was told "only JSON, no prose" and still wrapped its answer in a ```` ```json ```` fence or added a preamble. That crashed 3 of the first 4 live runs.
- The RAG assistant was told to end with a "Sources:" line and sometimes wrote a sentence there ("None of the provided excerpts contain…"), which the parser took for a filename.

The fixes (extract the JSON array; only accept `*.md` names) are each covered by tests built from the real outputs. For new code, structured outputs (`messages.parse` with a pydantic model, used in `build_answer_set.py`) avoid the problem altogether.

**14. Mocked tests can't catch model-behavior bugs.**
All 14 sprint-risk tests passed while the live agent crashed on its first real response, because the mocks returned the tidy JSON the code expected. Both bugs above were found only by running the real thing. Mocked tests keep CI fast and free; they still need a periodic live run.

### Setup and tooling

**15. Claude Pro and the Claude API are billed separately.** Pro covers chatting with Claude; code calling the API needs its own prepaid credit from console.anthropic.com. This whole project costs a few dollars.

**16. Windows path length limits bite quietly.** Git failed to clone into a deeply nested folder, and later couldn't read a commit-message file from one ("Filename too long"). Keeping projects at a short path (`C:\Users\dale_\code`) avoided both.

**17. Secrets stay local.** The API key lives in a `.env` file that `.gitignore` excludes in every repo. Before each push, `git ls-files .env` confirmed it wasn't tracked.

---

## Open questions for the Phase 2 rubric

1. An honest "not enough information" when the answer *was* in the docs (q04, q10, q17, q18): pass or fail **relevant**? Judge v1 couldn't decide consistently either (lesson 11).
2. An answer that's accurate but incomplete (`q12-incomplete`, `q23-incomplete`): pass or fail **relevant**?
3. An answer that declines but still names a doc on its Sources line (q30 cites first-steps.md "only shows development server usage"): is **cited correctly** a pass or n.a.?

## Human labels (Phase 2)

*To be filled in from `data/human_labels.jsonl`:* how often the seeded flaws were caught, which flaw types were hardest to spot, and where the labels disagree with `seeded_flaw`.
