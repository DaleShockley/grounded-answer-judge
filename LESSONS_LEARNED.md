# Lessons Learned

A running log for this project and the two it builds on ([rag-docs-assistant](https://github.com/DaleShockley/rag-docs-assistant) and [sprint-risk-agent](https://github.com/DaleShockley/sprint-risk-agent)). Every claim here is backed by a number from a real run. Updated after each phase.

**Status:** Phases 0–6 complete: answer set, human labels, judge v1 and v2, a four-model generator comparison, and a CI quality gate. Next: Phase 7, the write-up.

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

**Read the right-hand column with care.** The reviewed labels were made with the judge's answers on screen, and most disputes were settled its way, so this agreement is partly circular (lesson 28). The remaining 6 disagreements are all citation or "not covered" cases where judge v1's prompt predates the rubric. Judge v2 will be scored on cases whose right answer doesn't depend on any judge: the 17 seeded flaws and the 9 rubric cases.

### Judge v2 (Phase 4): prompt built on `RUBRIC.md`, 3 runs per model

Full tables: [`results/phase4_report.md`](results/phase4_report.md), [`results/bias_report.md`](results/bias_report.md).

| Prompt · model | Seeded flaws | Rubric cases | Consistency | Cost / run |
|---|---|---|---|---|
| v1 · `claude-sonnet-5` (1 run) | 17/17 | 5/9 | – | $0.33 |
| v2 · `claude-haiku-4-5` | 17/17 | 7–8/9 | 94% | $0.15 |
| v2 · `claude-sonnet-5` | 17/17 | 8–9/9 | 95% | $0.38 |

*Consistency* is the share of the 141 verdicts (47 answers × 3 criteria) that were identical in all 3 runs. The 9 rubric cases helped shape prompt v2, so treat that column as a development check, not a held-out test.

| Bias probe | Haiku 4.5 | Sonnet 5 |
|---|---|---|
| **Padded:** correct answer + a verbatim quote from a cited doc. Should still pass all 3 | 10/10 | 9/10 |
| **Confident:** "This is explicitly documented…" added to a fabricated/contradicted answer. Should still fail faithful | 7/7 | 7/7 |

Agreement with the reviewed labels, faithful / relevant / cited: v1 100% / 98% / 89%; v2 Sonnet 99% / 94% / 85%; v2 Haiku 89% / 95% / 82%.

### Answer generators (Phase 5): same questions, same retrieved excerpts

Full tables: [`results/phase5_report.md`](results/phase5_report.md). Graded by judge v2 · `claude-sonnet-5`.

| Generator | Fully correct | Answered usefully | Declined (answerable) | Cost / 1k answers | Median latency | Avg output tokens |
|---|---|---|---|---|---|---|
| `claude-haiku-4-5` | 30/30 | 22/26 | q04, q10, q17, q18 | $1.18 | 1.6 s | 111 |
| `claude-sonnet-4-5` (current default) | 29/30 | 22/26 | q04, q17, q18 | $3.63 | 3.0 s | 118 |
| `claude-sonnet-5` | 29/30 | 22/26 | q04, q17, q18 | $2.72 | 1.8 s | 111 |
| `claude-opus-5-5` | 30/30 | 23/26 | q04, q17, q18 | $8.47 | 3.8 s | 262 |

All four correctly declined the 4 unanswerable questions. Second opinion (judge v2 · Haiku): 28, 29, 29, 30 of 30. Phase 5 cost $1.78 ($0.48 generating, $1.30 grading).

### Quality gate (Phase 6)

`eval/quality_gate.py` with minimums in `eval/gate_thresholds.json`. It runs on every push against the committed results (free), and on demand against fresh API runs (`.github/workflows/live-eval.yml`, about $0.60).

| Check | Minimum | Judge v2 · Sonnet 5 | Deliberately softened prompt (`judge_lenient`) |
|---|---|---|---|
| Judge: seeded flaws caught | 17/17 | 17/17 ✅ | 14/17 ❌ (let through q01-fabricated_detail, q12-incomplete, q23-incomplete) |
| Judge: rubric cases right | 8/9 | 8/9 ✅ | 4/9 ❌ |
| Answers: faithful (Sonnet 5 answers) | 28/30 | 29/30 ✅ | – |
| Answers: fully correct (Sonnet 5 answers) | 28/30 | 29/30 ✅ | – |

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

**13. Writing the rubric into the prompt fixed the judgment calls, not the model.**
Same model, new prompt: rubric cases went from 5/9 (v1) to 8–9/9 (v2). Every v1 miss was a rule v1 had never been given (declining answers get n.a., the core source rule, "not covered" graded against the excerpts). A bigger model wouldn't have known those rules either.

**14. Run-to-run instability lives in the rubric's gray zones.**
About 5% of verdicts changed between identical runs (7 of 141 for Sonnet, 9 for Haiku). Nearly all were in the same few places: is a confident, made-up answer to the question *relevant*? What's the right citation for an off-topic answer? Is "you'd import `BaseModel` from Pydantic" a hedged claim (fail) or one that "directly follows" from the excerpts (pass)? *Takeaway:* repeated runs are a cheap way to find where the rubric is underspecified. Where the rules are clear, verdicts are stable.

**15. A cheaper judge can match on the easy cases and still blur criteria.**
Haiku 4.5 caught all 17 seeded flaws at 40% of Sonnet 5's cost. But it failed off-topic and incomplete answers on *faithful* too, letting a relevance problem bleed into another criterion (89% faithful agreement vs Sonnet's 99%). It's fine as a cheap first screen and weaker as the grader of record.

**16. The judge wasn't swayed by length or confident tone.**
Adding a verbatim quote left 19 of 20 fully-passing answers passing (the one change was the judge re-examining a claim already in the original answer, not the padding). Adding "This is explicitly documented, so you can rely on it" to 7 fabricated or contradicted answers never flipped *faithful* to pass, for either model. Lesson 4's length signal exists in the data, but this judge doesn't appear to use it.

**17. Agreement that drops when the judge changes shows the labels were anchored.**
v2 follows the rubric better than v1 on every anchor, yet its agreement with the reviewed labels is *lower* (cited correctly 89% → 85%). That's the automation bias from lesson 28 showing up in the numbers: the labels partly encode v1. Anchors with judge-independent answers are the better yardstick.

### Choosing a model

**18. Retrieval sets the ceiling; the generator can't raise it.**
All four models declined the same three answerable questions (q04, q17, q18), because the right section was never retrieved. A model at 7× the price answers no more of them. The fix for those questions is in chunking and retrieval (lesson 1), not in the model.

**19. On an easy eval, every model looks the same, and that's a finding about the eval.**
Every generator scored 29–30/30, a spread smaller than the judge's own run-to-run noise. The set can't tell these models apart: its answers come straight from one or two excerpts. Separating them would take harder questions (combining sections, reading code, precise edge cases), which is the next dataset to build.

**20. When quality ties, cost and speed decide.**
Haiku 4.5 matched the others at $1.18 per 1,000 answers and 1.6 s. Opus 5.5 cost 7× more and took over twice as long, mostly by writing 2.4× longer answers. Sonnet 5 matched Sonnet 4.5, the current default, at 25% lower cost and 40% lower latency, so the default is worth changing.

**21. Where models do differ, it's in the rubric's gray zones.**
The one real split was q10 (the `BaseModel` import): Haiku declined, while the Sonnets and Opus inferred the answer from context. That's the same inference-vs-hedging gap found in Phase 4 (open rubric gap 1): the models disagree exactly where the rules are unclear.

**22. Check any headline that looks too clean.**
The first Phase 5 report said Haiku declined 0 answerable questions. The metric counted an answer as declined only if it cited nothing, but most declining answers still list docs. Reading the four hardest answers from each model exposed it: every model declined at least 3. The grader's n.a. verdict is now the measure.

**23. Look for a judge favoring its own model's answers.**
Sonnet 5 judging Sonnet 5's answers could inflate them, so a Haiku judge graded everything too. It rated Haiku's own answers *lowest* (28/30) and agreed within noise elsewhere, so there's no sign of self-preference at this scale.

### Quality gates

**24. A degraded judge can still look good, so set the bar where the good one is.**
The softened prompt ("be generous; general knowledge is fine") still caught 14 of 17 seeded flaws, 82%, which a loose "80% is fine" bar would accept. What it lost were the subtle cases a judge exists for: the true-but-unsupported claim and the incomplete answers. The gate's minimums sit at what the known-good judge actually scores, with room only for measured noise.

**25. Gate the grader separately from the thing it grades.**
A lenient judge makes the answers look *better*, not worse: it would push the answer checks up while quality stayed the same, or even dropped. If CI only checked "answer quality ≥ X", a broken judge would sail through and hide real regressions. The judge has to be checked against answers whose right grade is known independently: the seeded flaws and rubric cases.

**26. Anchor cases are what make an automated judge check possible.**
Without the 17 seeded flaws and 9 rubric cases, the only way to check the judge would be fresh human labels every time. With them, CI can catch a bad prompt edit in a few minutes for under a dollar. The time spent building the answer set in Phase 1 is what pays for this.

### Human labeling

**27. Human labels aren't automatically ground truth.**
The first blind pass caught 6 of 17 planted flaws. The judge caught all 17. Every wrong citation and every added fake detail got through, including an answer that says setting `None` makes a parameter *required* (the docs say the opposite). "The judge agrees with a human X% of the time" means nothing until the human labels have been checked too.

**28. Showing reviewers the AI's answer anchors them (automation bias).**
With the judge's grade and reasoning on screen, 46 of 48 disputes were settled its way, and 3 of the 4 rubric violations found afterwards copied the judge exactly, even though the judge's prompt predates the rubric. Agreement jumped from 57–72% to 89–100%, but much of that jump is the judge grading itself. *Next time:* show the two grades as "Grade A / Grade B" without saying which came from the judge, require a reason before moving on, and review a sample of agreed cases too.

**29. Separate criteria get collapsed into one gut call.**
On the first pass, 44 of 47 answers got the same grade on all three criteria, so it was really one "is this answer good?" call. Independent criteria take a written rubric and worked examples (a correct answer with the wrong citation is pass / pass / **fail**). After the rubric, 21 of 47 did.

**30. Write the rubric before labeling, not after.**
The first pass was graded against one-line definitions, and the rules for edge cases ("not covered" answers, extra citations, incomplete answers) were only settled afterwards. Some of the disagreement was about grading different rules, not grading carelessly. The labels also carry almost no reasons (1 of 47), which makes each disagreement hard to settle.

### Working with model output

**31. Models don't reliably follow format instructions, so parse defensively.**
- The sprint-risk agent was told "only JSON, no prose" and still wrapped its answer in a ```` ```json ```` fence or added a preamble. That crashed 3 of the first 4 live runs.
- The RAG assistant was told to end with a "Sources:" line and sometimes wrote a sentence there ("None of the provided excerpts contain…"), which the parser took for a filename.

The fixes (extract the JSON array; only accept `*.md` names) are each covered by tests built from the real outputs. For new code, structured outputs (`messages.parse` with a pydantic model, used in `build_answer_set.py`) avoid the problem altogether.

**32. Mocked tests can't catch model-behavior bugs.**
All 14 sprint-risk tests passed while the live agent crashed on its first real response, because the mocks returned the tidy JSON the code expected. Both bugs above were found only by running the real thing. Mocked tests keep CI fast and free; they still need a periodic live run.

### Setup and tooling

**33. Claude Pro and the Claude API are billed separately.** Pro covers chatting with Claude; code calling the API needs its own prepaid credit from console.anthropic.com. This whole project costs a few dollars.

**34. Windows path length limits bite quietly.** Git failed to clone into a deeply nested folder, and later couldn't read a commit-message file from one ("Filename too long"). Keeping projects at a short path (`C:\Users\dale_\code`) avoided both.

**35. Secrets stay local.** The API key lives in a `.env` file that `.gitignore` excludes in every repo. Before each push, `git ls-files .env` confirmed it wasn't tracked.

---

## Rubric decisions (settled 2026-09-25)

The open questions from Phase 1 are now rules in [`RUBRIC.md`](RUBRIC.md):

1. An honest "not covered" answer is graded against the **excerpts**: it passes **relevant** when the excerpts really lack the answer (q04, q17, q18). The retrieval miss is tracked separately (lesson 1).
2. Incomplete answers **fail relevant**.
3. An answer that declines gets **n.a.** for citation, even if it names a doc (q30).
4. Citations follow the **core source rule**: pass if the doc holding the main answer is cited.

## Open rubric gaps (found by Phase 4 instability, lesson 14)

1. **Inference vs. hedging (q10).** "It appears you'd import `BaseModel` from Pydantic" can be read as a hedged unsupported claim (fail) or as something that "directly follows" from excerpts calling these "Pydantic models" that inherit from `BaseModel` (pass). The rubric currently says both.
2. **Relevance of a made-up answer.** A confident fabricated tutorial is on topic. Is it *relevant* (it answers the question) or not (it doesn't answer from the docs)?
3. **Citation for an off-topic answer.** If the answer doesn't answer the question, is the citation judged against the question's answer or the answer's own content?

## Decision so far

The **grader of record is prompt v2 on `claude-sonnet-5`**: best on every anchor, 95% consistent, $0.38 per 47 answers. Haiku 4.5 is a reasonable cheap screen for clear-cut flaws (lesson 15).

## Next

- **Phase 7:** write-up and portfolio.
- **Later:** a harder question set (lesson 19) and better section-level retrieval (lessons 1 and 18).
