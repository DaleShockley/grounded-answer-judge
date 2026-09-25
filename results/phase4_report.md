# Phase 4: judge comparison

Each configuration was run on all 47 answers; ranges cover its repeated runs.

## Anchor accuracy (right answer known independently of any judge)

| Prompt | Model | Runs | Seeded flaws caught | Rubric cases right | Consistency | Cost / run | Median latency |
|---|---|---|---|---|---|---|---|
| v1 | `claude-sonnet-5` | 1 | 17/17 | 5/9 | n/a (1 run) | $0.33 | 3.2s |
| v2 | `claude-haiku-4-5` | 3 | 17/17 | 7–8/9 | 94% | $0.15 | 3.5s |
| v2 | `claude-sonnet-5` | 3 | 17/17 | 8–9/9 | 95% | $0.38 | 3.3s |

## Agreement with reviewed labels (mean over runs)

Partly circular for v1: the reviewed labels were settled with v1's verdicts on screen.

| Prompt | Model | Faithful | Relevant | Cited correctly |
|---|---|---|---|---|
| v1 | `claude-sonnet-5` | 100% (κ 1.00) | 98% (κ 0.90) | 89% (κ 0.80) |
| v2 | `claude-haiku-4-5` | 89% (κ 0.71) | 95% (κ 0.79) | 82% (κ 0.67) |
| v2 | `claude-sonnet-5` | 99% (κ 0.96) | 94% (κ 0.73) | 85% (κ 0.72) |

## Anchor misses

**v1 · `claude-sonnet-5`**

- `q04-original` · cited_correctly: expected **na**, got fail in 1 of 1 run(s) (Answer declines)
- `q11-original` · cited_correctly: expected **pass**, got fail in 1 of 1 run(s) (Core source rule)
- `q18-original` · cited_correctly: expected **na**, got pass in 1 of 1 run(s) (Answer declines)
- `q18-original` · relevant: expected **pass**, got fail in 1 of 1 run(s) (Honest 'not covered' and the excerpts really lack it)

**v2 · `claude-haiku-4-5`**

- `q10-original` · faithful: expected **fail**, got pass in 3 of 3 run(s) (Hedged unsupported claim)
- `q17-original` · relevant: expected **pass**, got fail in 1 of 3 run(s) (Honest 'not covered' and the excerpts really lack it)

**v2 · `claude-sonnet-5`**

- `q10-original` · faithful: expected **fail**, got pass in 2 of 3 run(s) (Hedged unsupported claim)
