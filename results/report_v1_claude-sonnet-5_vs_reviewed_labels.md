# Judge report: `judge_v1_claude-sonnet-5.jsonl`

Model `claude-sonnet-5`, prompt `v1`, 47 answers graded, total cost $0.330, median latency 3.2s.

## Agreement with human labels (`reviewed_labels.jsonl`)

47 answers labeled by both.

| Criterion | Agreement | Cohen's kappa | human→judge counts |
|---|---|---|---|
| faithful | 100% | 1.00 | fail->fail: 11, pass->pass: 36 |
| relevant | 98% | 0.90 | fail->fail: 5, pass->fail: 1, pass->pass: 41 |
| cited_correctly | 89% | 0.80 | fail->fail: 10, fail->pass: 2, na->fail: 1, na->na: 5, na->pass: 1, pass->fail: 1, pass->pass: 27 |

### Disagreements (6)

- **q18-original** · relevant: human **pass**, judge **fail**
  - Human: Corrected per RUBRIC.md: answer declines, so citation is n.a.; excerpts lack the answer, so an honest "not covered" passes relevant.
  - Judge: The question asks specifically what happens when a float is sent for an int path parameter, but the answer admits it cannot find this information, which is a reasonable response given the excerpts but doesn't actually answer the specific question asked.
- **q04-original** · cited_correctly: human **na**, judge **fail**
  - Human: Corrected per RUBRIC.md: answer declines, so citation is n.a..
  - Judge: The answer cites body.md and query-params.md, but since it states it cannot answer the question, no source is truly relied upon to explain the validation mechanism; however it does reference body.md's mention of singular types, so citing it is reasonable, but query-params.md isn't clearly used to support any specific claim in the answer.
- **q07-fabricated_detail** · cited_correctly: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The cited file query-params.md does contain the relevant excerpt about bool conversion, though the answer includes an extra unsupported value.
- **q11-original** · cited_correctly: human **pass**, judge **fail**
  - Human: Corrected per RUBRIC.md: core source rule: body.md holds the main answer.
  - Judge: The 'no specific order' claim comes from query-params.md ('Multiple path and query parameters'), but only body.md is cited, missing a source for that part of the answer.
- **q18-original** · cited_correctly: human **na**, judge **pass**
  - Human: Corrected per RUBRIC.md: answer declines, so citation is n.a.; excerpts lack the answer, so an honest "not covered" passes relevant.
  - Judge: The answer cites query-params.md, which does contain the quoted text about validation processes applying to path parameters, so the citation matches the content relied upon.
- **q21-original** · cited_correctly: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The information used comes from the 'Create an Enum class' section of path-params.md, which is the cited source.

## Seeded-flaw recall

Did the judge fail the criterion each planted flaw targets? (A sanity check, not ground truth.)

| Flaw | Targets | Caught |
|---|---|---|
| contradiction | faithful | 3/3 |
| fabricated_detail | faithful | 4/4 |
| incomplete | relevant | 2/2 |
| off_topic | relevant | 2/2 |
| unanswerable_hallucination | faithful | 3/3 |
| wrong_citation | cited_correctly | 3/3 |
| **all** | | **17/17** |

Original (unseeded) answers the judge failed on at least one criterion: 4/30 (q04-original, q10-original, q11-original, q18-original). Not necessarily false alarms: some originals are genuinely flawed (see data/README.md).
