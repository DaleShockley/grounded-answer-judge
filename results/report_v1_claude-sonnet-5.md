# Judge report: `judge_v1_claude-sonnet-5.jsonl`

Model `claude-sonnet-5`, prompt `v1`, 47 answers graded, total cost $0.330, median latency 3.2s.

## Agreement with human labels

_No `data/human_labels.jsonl` yet._

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
