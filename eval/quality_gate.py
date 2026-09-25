"""Quality gate: fails (exit code 1) if the judge or the answers fall below
the minimums in eval/gate_thresholds.json.

Two checks, answering two different questions:
- Judge gate  -- can we still trust the grader? A judge run over
  data/answers.jsonl must catch the seeded flaws and get the rubric anchor
  cases right (answers whose right grade doesn't depend on any judge).
- Answer gate -- is the RAG system still good? The grader's verdicts on the
  default generator's answers must stay faithful and fully correct.

    python -m eval.quality_gate                          # checks the committed results (free; runs on every push)
    python -m eval.quality_gate --judge-run results/judge_v2_claude-sonnet-5_ci.jsonl \\
                                --answers-run results/judge_v2_claude-sonnet-5_ci-gen.jsonl

The live CI workflow (.github/workflows/live-eval.yml) produces fresh runs
first and then calls this with them.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from eval.compare_generators import fully_correct
from eval.compare_judges import anchor_cases
from src.run_judge import ANSWERS, RESULTS_DIR, read_jsonl

THRESHOLDS = Path(__file__).parent / "gate_thresholds.json"
DEFAULT_JUDGE_RUN = RESULTS_DIR / "judge_v2_claude-sonnet-5_r1.jsonl"
DEFAULT_ANSWERS_RUN = RESULTS_DIR / "judge_v2_claude-sonnet-5_gen-claude-sonnet-5.jsonl"


def judge_checks(run: dict[str, dict], answers: list[dict], limits: dict) -> list[dict]:
    anchors = anchor_cases(answers)
    missing = [a["id"] for a in anchors if a["id"] not in run]
    if missing:
        raise ValueError(f"judge run is missing anchor answers: {sorted(set(missing))}")
    hits = {kind: sum(run[a["id"]][a["criterion"]] == a["expected"] for a in anchors if a["kind"] == kind)
            for kind in ("seeded", "rubric")}
    totals = {kind: sum(a["kind"] == kind for a in anchors) for kind in ("seeded", "rubric")}
    return [
        {"check": "Judge: seeded flaws caught", "value": hits["seeded"], "total": totals["seeded"],
         "min": limits["seeded_flaws_min"]},
        {"check": "Judge: rubric cases right", "value": hits["rubric"], "total": totals["rubric"],
         "min": limits["rubric_cases_min"]},
    ]


def answer_checks(run: dict[str, dict], limits: dict) -> list[dict]:
    verdicts = list(run.values())
    return [
        {"check": "Answers: faithful", "value": sum(v["faithful"] == "pass" for v in verdicts),
         "total": len(verdicts), "min": limits["faithful_min"]},
        {"check": "Answers: fully correct", "value": sum(fully_correct(v) for v in verdicts),
         "total": len(verdicts), "min": limits["fully_correct_min"]},
    ]


def render(checks: list[dict], judge_run: Path, answers_run: Path) -> str:
    lines = [
        "## Quality gate",
        "",
        f"Judge run: `{judge_run.name}` · Answer run: `{answers_run.name}`",
        "",
        "| Check | Result | Minimum | Status |",
        "|---|---|---|---|",
    ]
    for c in checks:
        status = "✅ pass" if c["value"] >= c["min"] else "❌ FAIL"
        lines.append(f"| {c['check']} | {c['value']}/{c['total']} | {c['min']} | {status} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--judge-run", type=Path, default=DEFAULT_JUDGE_RUN)
    parser.add_argument("--answers-run", type=Path, default=DEFAULT_ANSWERS_RUN)
    args = parser.parse_args(argv)

    limits = json.loads(THRESHOLDS.read_text(encoding="utf-8"))
    checks = judge_checks({r["id"]: r for r in read_jsonl(args.judge_run)}, read_jsonl(ANSWERS), limits["judge"])
    checks += answer_checks({r["id"]: r for r in read_jsonl(args.answers_run)}, limits["answers"])

    report = render(checks, args.judge_run, args.answers_run)
    print(report)
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):  # shows the table on the GitHub Actions run page
        with open(summary, "a", encoding="utf-8") as f:
            f.write(report)

    failed = [c["check"] for c in checks if c["value"] < c["min"]]
    if failed:
        print(f"Quality gate FAILED: {', '.join(failed)}")
        return 1
    print("Quality gate passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
