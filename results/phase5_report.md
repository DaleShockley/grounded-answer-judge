# Phase 5: comparing answer generators

Same 30 questions, same retrieved excerpts, only the answer-writing model changes. Graded by judge v2 on `claude-sonnet-5` (grader of record); `claude-haiku-4-5` is a second opinion.

## Quality vs. cost and speed

| Generator | Fully correct | Answered usefully | Faithful | Relevant | Cited (of graded) | Second opinion | Cost / 1k answers | Median latency | p90 latency |
|---|---|---|---|---|---|---|---|---|---|
| `claude-haiku-4-5` | **30/30** | 22/26 | 30/30 | 30/30 | 22/22 | 28/30 | $1.18 | 1.6s | 2.1s |
| `claude-sonnet-4-5` | **29/30** | 22/26 | 29/30 | 30/30 | 23/23 | 29/30 | $3.63 | 3.0s | 4.2s |
| `claude-sonnet-5` | **29/30** | 22/26 | 29/30 | 30/30 | 23/23 | 29/30 | $2.72 | 1.8s | 2.6s |
| `claude-opus-5-5` | **30/30** | 23/26 | 30/30 | 30/30 | 23/23 | 30/30 | $8.47 | 3.8s | 5.2s |

*Fully correct* = faithful, relevant, and no wrong citation; under RUBRIC.md an honest "the excerpts don't cover this" counts, when true. *Answered usefully* = answerable questions actually answered correctly (not declined). The grader of record changes about 5% of its verdicts between identical runs (Phase 4), so differences of one or two answers are within noise.

## Behavior

| Generator | Declined answerable questions | Declined the 4 unanswerable | Avg output tokens | Cut off |
|---|---|---|---|---|
| `claude-haiku-4-5` | 4/26 (q04, q10, q17, q18) | 4/4 | 111 | none |
| `claude-sonnet-4-5` | 3/26 (q04, q17, q18) | 4/4 | 118 | none |
| `claude-sonnet-5` | 3/26 (q04, q17, q18) | 4/4 | 111 | none |
| `claude-opus-5-5` | 3/26 (q04, q17, q18) | 4/4 | 262 | none |

## Answers not fully correct (grader of record)

- `claude-haiku-4-5`: none
- `claude-sonnet-4-5`: q24 (faithful)
- `claude-sonnet-5`: q25 (faithful)
- `claude-opus-5-5`: none
