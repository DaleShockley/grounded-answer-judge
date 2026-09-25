"""Phase 5: which model writes the best answers for the money?

Every generator answered the same 30 questions from the SAME retrieved
excerpts (retrieval is deterministic), so only the answer-writing model
differs. Each answer set is graded by the grader of record (judge v2 on
claude-sonnet-5) and, as a second opinion, by judge v2 on claude-haiku-4-5
-- a check on a Sonnet judge favouring Sonnet-written answers.

    python -m eval.compare_generators

Reads data/generators/answers_<model>.jsonl and
results/judge_v2_<judge>_gen-<model>.jsonl; writes results/phase5_report.md.
"""

import statistics
from pathlib import Path

from src.pricing import cost_usd
from src.run_judge import RESULTS_DIR, read_jsonl

ROOT = Path(__file__).parent.parent
GENERATORS_DIR = ROOT / "data" / "generators"
REPORT = RESULTS_DIR / "phase5_report.md"
GRADER = "claude-sonnet-5"
SECOND_OPINION = "claude-haiku-4-5"
GENERATORS = ("claude-haiku-4-5", "claude-sonnet-4-5", "claude-sonnet-5", "claude-opus-5-5")


def fully_correct(v: dict) -> bool:
    """Faithful, relevant, and no wrong citation (n.a. is fine: nothing cited or a justified decline)."""
    return v["faithful"] == "pass" and v["relevant"] == "pass" and v["cited_correctly"] != "fail"


def summarize(answers: list[dict], verdicts: dict[str, dict], second: dict[str, dict] | None = None) -> dict:
    answerable = [a for a in answers if a["expected_docs"]]
    unanswerable = [a for a in answers if not a["expected_docs"]]
    cited = [verdicts[a["id"]]["cited_correctly"] for a in answers]
    latencies = sorted(a["latency_s"] for a in answers)
    costs = [cost_usd(a["generator_model"], a["input_tokens"], a["output_tokens"]) for a in answers]

    out = {
        "n": len(answers),
        "fully_correct": sum(fully_correct(verdicts[a["id"]]) for a in answers),
        "faithful": sum(verdicts[a["id"]]["faithful"] == "pass" for a in answers),
        "relevant": sum(verdicts[a["id"]]["relevant"] == "pass" for a in answers),
        "cited_pass": cited.count("pass"),
        "cited_graded": cited.count("pass") + cited.count("fail"),
        # Retrieval is identical across generators, so this isolates how each model handles thin excerpts.
        # A decline is what the grader marks cited_correctly = n.a. (RUBRIC.md) -- declining answers
        # often still list docs on their Sources line, so an empty citation list undercounts them.
        "declined_answerable": [a["id"] for a in answerable if verdicts[a["id"]]["cited_correctly"] == "na"],
        "n_answerable": len(answerable),
        "answerable_wrong": sum(
            not fully_correct(verdicts[a["id"]]) for a in answerable if verdicts[a["id"]]["cited_correctly"] != "na"
        ),
        "unanswerable_ok": sum(verdicts[a["id"]]["faithful"] == "pass" for a in unanswerable),
        "n_unanswerable": len(unanswerable),
        "cost_per_1k": 1000 * statistics.mean(costs),
        "latency_median": statistics.median(latencies),
        "latency_p90": latencies[int(0.9 * (len(latencies) - 1))],
        "output_tokens": statistics.mean(a["output_tokens"] for a in answers),
        "truncated": [a["id"] for a in answers if a["stop_reason"] != "end_turn"],
        "failing": [(a["id"], [c for c in ("faithful", "relevant", "cited_correctly")
                               if verdicts[a["id"]][c] == "fail"]) for a in answers
                    if not fully_correct(verdicts[a["id"]])],
    }
    if second:
        out["second_fully_correct"] = sum(fully_correct(second[a["id"]]) for a in answers)
    return out


def render(summaries: dict[str, dict]) -> str:
    lines = [
        "# Phase 5: comparing answer generators",
        "",
        "Same 30 questions, same retrieved excerpts, only the answer-writing model changes. "
        f"Graded by judge v2 on `{GRADER}` (grader of record); `{SECOND_OPINION}` is a second opinion.",
        "",
        "## Quality vs. cost and speed",
        "",
        "| Generator | Fully correct | Answered usefully | Faithful | Relevant | Cited (of graded) | Second opinion | "
        "Cost / 1k answers | Median latency | p90 latency |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for model, s in summaries.items():
        second = f"{s['second_fully_correct']}/{s['n']}" if "second_fully_correct" in s else "–"
        useful = s["n_answerable"] - len(s["declined_answerable"]) - s["answerable_wrong"]
        lines.append(
            f"| `{model}` | **{s['fully_correct']}/{s['n']}** | {useful}/{s['n_answerable']} | "
            f"{s['faithful']}/{s['n']} | {s['relevant']}/{s['n']} | "
            f"{s['cited_pass']}/{s['cited_graded']} | {second} | ${s['cost_per_1k']:.2f} | "
            f"{s['latency_median']:.1f}s | {s['latency_p90']:.1f}s |"
        )
    lines += [
        "",
        "*Fully correct* = faithful, relevant, and no wrong citation; under RUBRIC.md an honest \"the excerpts "
        "don't cover this\" counts, when true. *Answered usefully* = answerable questions actually answered "
        "correctly (not declined). The grader of record changes about 5% of its verdicts between identical runs "
        "(Phase 4), so differences of one or two answers are within noise.",
        "",
        "## Behavior",
        "",
        "| Generator | Declined answerable questions | Declined the 4 unanswerable | Avg output tokens | Cut off |",
        "|---|---|---|---|---|",
    ]
    for model, s in summaries.items():
        declined = ", ".join(s["declined_answerable"]) or "none"
        lines.append(
            f"| `{model}` | {len(s['declined_answerable'])}/{s['n_answerable']} ({declined}) | "
            f"{s['unanswerable_ok']}/{s['n_unanswerable']} | {s['output_tokens']:.0f} | "
            f"{', '.join(s['truncated']) or 'none'} |"
        )
    lines += ["", "## Answers not fully correct (grader of record)", ""]
    for model, s in summaries.items():
        items = ", ".join(f"{i} ({'/'.join(c) or '—'})" for i, c in s["failing"]) or "none"
        lines.append(f"- `{model}`: {items}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    summaries = {}
    for model in GENERATORS:
        answers_file = GENERATORS_DIR / f"answers_{model}.jsonl"
        grader_file = RESULTS_DIR / f"judge_v2_{GRADER}_gen-{model}.jsonl"
        if not answers_file.exists() or not grader_file.exists():
            print(f"skipping {model}: missing {answers_file.name if not answers_file.exists() else grader_file.name}")
            continue
        second_file = RESULTS_DIR / f"judge_v2_{SECOND_OPINION}_gen-{model}.jsonl"
        summaries[model] = summarize(
            read_jsonl(answers_file),
            {r["id"]: r for r in read_jsonl(grader_file)},
            {r["id"]: r for r in read_jsonl(second_file)} if second_file.exists() else None,
        )
    report = render(summaries)
    REPORT.write_text(report, encoding="utf-8")
    print(report)
    print(f"Saved {REPORT}")
