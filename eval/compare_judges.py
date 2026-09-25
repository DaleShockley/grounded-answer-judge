"""Compares judge configurations (prompt x model), each run several times.

    python -m eval.compare_judges

Reads every results/judge_<prompt>_<model>[_<tag>].jsonl, groups runs by
(prompt, model), and reports per configuration:

- Anchor accuracy: seeded flaws (did it fail the targeted criterion?) and
  rubric cases (eval/anchor_cases.json). The right answer to these doesn't
  depend on any judge, so this is the headline number.
- Agreement with data/reviewed_labels.jsonl (partly circular for v1; see
  LESSONS_LEARNED.md).
- Consistency: share of answer x criterion verdicts identical in every run.
- Cost per full run and median latency.

Writes results/phase4_report.md.
"""

import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

from eval.score_agreement import CRITERIA, FLAW_TARGET, cohens_kappa
from src.run_judge import ANSWERS, RESULTS_DIR, read_jsonl

ROOT = Path(__file__).parent.parent
ANCHORS = Path(__file__).parent / "anchor_cases.json"
REVIEWED = ROOT / "data" / "reviewed_labels.jsonl"
REPORT = RESULTS_DIR / "phase4_report.md"
# Model ids have no underscores, so any other tag (e.g. "_probe") doesn't match and is skipped.
_RUN_FILE = re.compile(r"^judge_(v\d+)_([^_]+)(?:_(r\d+))?$")


def anchor_cases(answers: list[dict]) -> list[dict]:
    seeded = [
        {"id": r["id"], "criterion": FLAW_TARGET[r["seeded_flaw"]], "expected": "fail",
         "kind": "seeded", "rule": r["seeded_flaw"]}
        for r in answers if r.get("seeded_flaw")
    ]
    rubric = [{**c, "kind": "rubric"} for c in json.loads(ANCHORS.read_text(encoding="utf-8"))["cases"]]
    return seeded + rubric


def anchor_misses(run: dict[str, dict], anchors: list[dict]) -> list[dict]:
    return [a for a in anchors if run[a["id"]][a["criterion"]] != a["expected"]]


def consistency(runs: list[dict[str, dict]]) -> float | None:
    """Share of (answer, criterion) pairs with the same verdict in every run."""
    if len(runs) < 2:
        return None
    ids = set.intersection(*(set(r) for r in runs))
    stable = sum(len({r[i][c] for r in runs}) == 1 for i in ids for c in CRITERIA)
    return stable / (len(ids) * len(CRITERIA))


def load_runs(results_dir: Path = RESULTS_DIR) -> dict[tuple[str, str], list[dict[str, dict]]]:
    configs: dict[tuple[str, str], list[dict[str, dict]]] = defaultdict(list)
    for path in sorted(results_dir.glob("judge_*.jsonl")):
        match = _RUN_FILE.match(path.stem)
        if not match:
            continue
        rows = read_jsonl(path)
        configs[(match.group(1), match.group(2))].append({r["id"]: r for r in rows})
    return dict(configs)


def summarize(runs: list[dict[str, dict]], anchors: list[dict], reviewed: dict[str, dict]) -> dict:
    complete = [r for r in runs if all(a["id"] in r for a in anchors)]
    per_run = [anchor_misses(r, anchors) for r in complete]
    n_seeded = sum(a["kind"] == "seeded" for a in anchors)
    n_rubric = len(anchors) - n_seeded

    agree = {}
    for c in CRITERIA:
        scores = []
        for run in runs:
            ids = sorted(set(run) & set(reviewed))
            h = [reviewed[i][c] for i in ids]
            j = [run[i][c] for i in ids]
            scores.append((sum(x == y for x, y in zip(h, j)) / len(ids), cohens_kappa(h, j)))
        agree[c] = (statistics.mean(s[0] for s in scores),
                    statistics.mean(s[1] for s in scores if s[1] is not None))

    misses = defaultdict(int)
    for run_misses in per_run:
        for m in run_misses:
            misses[(m["id"], m["criterion"], m["expected"], m["rule"])] += 1

    return {
        "runs": len(runs),
        "seeded": [n_seeded - sum(m["kind"] == "seeded" for m in pr) for pr in per_run],
        "rubric": [n_rubric - sum(m["kind"] == "rubric" for m in pr) for pr in per_run],
        "n_seeded": n_seeded,
        "n_rubric": n_rubric,
        "agreement": agree,
        "consistency": consistency(runs),
        "cost": statistics.mean(sum(r["cost_usd"] for r in run.values()) for run in runs),
        "latency": statistics.median(r["latency_s"] for run in runs for r in run.values()),
        "misses": dict(misses),
        "verdicts": [run for run in runs],
    }


def _range(values: list[int], total: int) -> str:
    if not values:
        return "–"
    lo, hi = min(values), max(values)
    return f"{lo}/{total}" if lo == hi else f"{lo}–{hi}/{total}"


def render(summaries: dict[tuple[str, str], dict]) -> str:
    lines = [
        "# Phase 4: judge comparison",
        "",
        "Each configuration was run on all 47 answers; ranges cover its repeated runs.",
        "",
        "## Anchor accuracy (right answer known independently of any judge)",
        "",
        "| Prompt | Model | Runs | Seeded flaws caught | Rubric cases right | Consistency | Cost / run | Median latency |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for (prompt, model), s in summaries.items():
        cons = "n/a (1 run)" if s["consistency"] is None else f"{s['consistency']:.0%}"
        lines.append(
            f"| {prompt} | `{model}` | {s['runs']} | {_range(s['seeded'], s['n_seeded'])} | "
            f"{_range(s['rubric'], s['n_rubric'])} | {cons} | ${s['cost']:.2f} | {s['latency']:.1f}s |"
        )

    lines += [
        "",
        "## Agreement with reviewed labels (mean over runs)",
        "",
        "Partly circular for v1: the reviewed labels were settled with v1's verdicts on screen.",
        "",
        "| Prompt | Model | Faithful | Relevant | Cited correctly |",
        "|---|---|---|---|---|",
    ]
    for (prompt, model), s in summaries.items():
        cells = [f"{a:.0%} (κ {k:.2f})" for a, k in (s["agreement"][c] for c in CRITERIA)]
        lines.append(f"| {prompt} | `{model}` | " + " | ".join(cells) + " |")

    lines += ["", "## Anchor misses", ""]
    for (prompt, model), s in summaries.items():
        lines.append(f"**{prompt} · `{model}`**")
        if not s["misses"]:
            lines += ["", "None.", ""]
            continue
        lines.append("")
        for (id_, crit, expected, rule), count in sorted(s["misses"].items()):
            got = sorted({run[id_][crit] for run in s["verdicts"] if run[id_][crit] != expected})
            lines.append(f"- `{id_}` · {crit}: expected **{expected}**, got {'/'.join(got)} "
                         f"in {count} of {s['runs']} run(s) ({rule})")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    answers = read_jsonl(ANSWERS)
    anchors = anchor_cases(answers)
    reviewed = {r["id"]: r for r in read_jsonl(REVIEWED)}
    summaries = {cfg: summarize(runs, anchors, reviewed) for cfg, runs in load_runs().items()}
    report = render(summaries)
    REPORT.write_text(report, encoding="utf-8")
    print(report)
    print(f"Saved {REPORT}")
