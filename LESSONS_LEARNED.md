# Lessons Learned

A running log for this project and the two it builds on ([rag-docs-assistant](https://github.com/DaleShockley/rag-docs-assistant) and [sprint-risk-agent](https://github.com/DaleShockley/sprint-risk-agent)). Every claim here is backed by a number from a real run. Updated after each phase.

**Status:** Phases 0–3 complete: answer set, human labels (first pass, rubric, review), and judge v1 scored against them. Next: Phase 4, judge v2 built on `RUBRIC.md`.

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

### Human labels, in three stages

| Stage | File | What happened |
|---|---|---|
| 1. First pass (blind) | `human_labels.jsonl` | All 47 graded before a written rubric existed |
| 2. Review | `reviewed_labels.jsonl` | The 29 answers (48 grades) where the first pass and judge v1 disagreed, settled with both grades and the judge's reasoning visible |
| 3. Rubric corrections | `reviewed_labels.jsonl` | 4 grades changed to follow `RUBRIC.md` (each keeps `corrected_from`) |

| Measure | First pass | After review + corrections |
|---|---|---|
| Seeded flaws failed on the criterion they target | 6 / 17 | 17 / 17 |
| Answers given the same grade on all three criteria | 44 / 47 | 21 / 47 |
| One-line reasons written | 1 / 47 | 3 / 47 (the corrections) |

First-pass catch rate by flaw type: `unanswerable_hallucination` 3/3, `contradiction` 1/3, `off_topic` 1/2, `incomplete` 1/2, `fabricated_detail` 0/4, `wrong_citation` 0/3.

In the review, **46 of the 48 disputed grades were settled in the judge's favor**, in about 14 minutes. Checking the 9 cases where `RUBRIC.md` gives a specific answer showed 4 still broke the rubric, 3 of them by copying judge v1, whose prompt predates the rubric. Those 4 were corrected in stage 3.

### Judge v1 agreement with human labels

| Criterion | vs. first pass | vs. reviewed + corrected |
|---|---|---|
| Faithful | 68% (κ 0.19) | 100% (κ 1.00) |
| Relevant | 72% (κ 0.17) | 98% (κ 0.90) |
| Cited correctly | 57% (κ 0.14) | 89% (κ 0.80) |

**Read the right-hand column with care.** The reviewed labels were made with the judge's answers on screen, and most disputes were settled its way, so this agreement is partly circular (lesson 14). The remaining 6 disagreements are all citation or "not covered" cases where judge v1's prompt predates the rubric. Judge v2 will be scored on cases whose right answer doesn't depend on any judge: the 17 seeded flaws and the 9 rubric cases.

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
For q11 the judge failed **cited correctly** because one sentence ("you don't have to declare them in any specific order") comes from query-params.md, which the answer didn't cite. That's stricter than a person skimming would be, but defensible. Whether it counts as a disagreement depends on the rubric, which is why the rubric gets written down. The rubric later settled it with the core source rule: body.md holds the main answer, so q11 **passes**, and v1 was too strict here.

### Human labeling

**13. Human labels aren't automatically ground truth.**
The first blind pass caught 6 of 17 planted flaws. The judge caught all 17. Every wrong citation and every added fake detail got through, including an answer that says setting `None` makes a parameter *required* (the docs say the opposite). "The judge agrees with a human X% of the time" means nothing until the human labels have been checked too.

**14. Showing reviewers the AI's answer anchors them (automation bias).**
With the judge's grade and reasoning on screen, 46 of 48 disputes were settled its way, and 3 of the 4 rubric violations found afterwards copied the judge exactly, even though the judge's prompt predates the rubric. Agreement jumped from 57–72% to 89–100%, but much of that jump is the judge grading itself. *Next time:* show the two grades as "Grade A / Grade B" without saying which came from the judge, require a reason before moving on, and review a sample of agreed cases too.

**15. Separate criteria get collapsed into one gut call.**
On the first pass, 44 of 47 answers got the same grade on all three criteria, so it was really one "is this answer good?" call. Independent criteria take a written rubric and worked examples (a correct answer with the wrong citation is pass / pass / **fail**). After the rubric, 21 of 47 did.

**16. Write the rubric before labeling, not after.**
The first pass was graded against one-line definitions, and the rules for edge cases ("not covered" answers, extra citations, incomplete answers) were only settled afterwards. Some of the disagreement was about grading different rules, not grading carelessly. The labels also carry almost no reasons (1 of 47), which makes each disagreement hard to settle.

### Working with model output

**17. Models don't reliably follow format instructions, so parse defensively.**
- The sprint-risk agent was told "only JSON, no prose" and still wrapped its answer in a ```` ```json ```` fence or added a preamble. That crashed 3 of the first 4 live runs.
- The RAG assistant was told to end with a "Sources:" line and sometimes wrote a sentence there ("None of the provided excerpts contain…"), which the parser took for a filename.

The fixes (extract the JSON array; only accept `*.md` names) are each covered by tests built from the real outputs. For new code, structured outputs (`messages.parse` with a pydantic model, used in `build_answer_set.py`) avoid the problem altogether.

**18. Mocked tests can't catch model-behavior bugs.**
All 14 sprint-risk tests passed while the live agent crashed on its first real response, because the mocks returned the tidy JSON the code expected. Both bugs above were found only by running the real thing. Mocked tests keep CI fast and free; they still need a periodic live run.

### Setup and tooling

**19. Claude Pro and the Claude API are billed separately.** Pro covers chatting with Claude; code calling the API needs its own prepaid credit from console.anthropic.com. This whole project costs a few dollars.

**20. Windows path length limits bite quietly.** Git failed to clone into a deeply nested folder, and later couldn't read a commit-message file from one ("Filename too long"). Keeping projects at a short path (`C:\Users\dale_\code`) avoided both.

**21. Secrets stay local.** The API key lives in a `.env` file that `.gitignore` excludes in every repo. Before each push, `git ls-files .env` confirmed it wasn't tracked.

---

## Rubric decisions (settled 2026-09-25)

The open questions from Phase 1 are now rules in [`RUBRIC.md`](RUBRIC.md):

1. An honest "not covered" answer is graded against the **excerpts**: it passes **relevant** when the excerpts really lack the answer (q04, q17, q18). The retrieval miss is tracked separately (lesson 1).
2. Incomplete answers **fail relevant**.
3. An answer that declines gets **n.a.** for citation, even if it names a doc (q30).
4. Citations follow the **core source rule**: pass if the doc holding the main answer is cited.

## Next: Phase 4

- Judge prompt **v2** encodes `RUBRIC.md`, starting with lesson 11 (inconsistent "not covered" grading) and the core source rule.
- Score v2 on answers with judge-independent right answers: the 17 seeded flaws plus the 9 rubric cases.
- Compare `claude-haiku-4-5` and `claude-sonnet-5` as the judge, run each 3 times for consistency, and test the length bias from lesson 4.
