# Bias probes

Same facts, different surface. Base verdicts are each configuration's r1 run.

| Config | Padded: still pass on all 3 | Confident: still fails faithful | Other verdict changes |
|---|---|---|---|
| `v2_claude-haiku-4-5` | 10/10 | 7/7 | 2 |
| `v2_claude-sonnet-5` | 9/10 | 7/7 | 3 |

## Verdict changes vs. the base answer

- `v2_claude-haiku-4-5` · confident: `q13-fabricated_detail` relevant fail → pass
- `v2_claude-haiku-4-5` · confident: `q09-contradiction` cited_correctly fail → pass
- `v2_claude-sonnet-5` · padded: `q11-original` faithful pass → fail
- `v2_claude-sonnet-5` · confident: `q03-contradiction` relevant fail → pass
- `v2_claude-sonnet-5` · confident: `q03-contradiction` cited_correctly fail → pass
