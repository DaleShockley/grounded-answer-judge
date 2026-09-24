"""Scores a judge run two ways and writes a markdown report.

1. Agreement with human labels (the real test, needs data/human_labels.jsonl):
   per criterion -- raw agreement, Cohen's kappa, confusion counts -- plus
   every disagreement with the judge's reasoning next to the human's note.
2. Seeded-flaw recall (works without human labels): for each flawed
   answer, did the judge fail the criterion that flaw targets?

    python -m eval.score_agreement results/judge_v1_claude-sonnet-5.jsonl
"""

import argparse
from collections import Counter
from pathlib import Path

from src.run_judge import ANSWERS, read_jsonl

ROOT = Path(__file__).parent.parent
HUMAN_LABELS = ROOT / "data" / "human_labels.jsonl"
CRITERIA = ("faithful", "relevant", "cited_correctly")

# Which criterion each seeded flaw is designed to break (see data/README.md).
FLAW_TARGET = {
    "fabricated_detail": "faithful",
    "contradiction": "faithful",
    "unanswerable_hallucination": "faithful",
    "wrong_citation": "cited_correctly",
    "off_topic": "relevant",
    "incomplete": "relevant",
}


def cohens_kappa(a: list[str], b: list[str]) -> float | None:
    """Agreement corrected for chance. 1 = perfect, 0 = chance level, <0 = worse than chance.

    None when chance agreement is already 1 (both raters used a single identical
    label throughout), where kappa is undefined.
    """
    if not a or len(a) != len(b):
        raise ValueError("need two equal-length, non-empty label lists")
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    count_a, count_b = Counter(a), Counter(b)
    expected = sum(count_a[c] * count_b[c] for c in set(a) | set(b)) / (n * n)
    if expected == 1:
        return None
    return (observed - expected) / (1 - expected)


def agreement(human: dict[str, dict], judge: dict[str, dict]) -> dict:
    ids = sorted(set(human) & set(judge))
    out = {"n": len(ids), "criteria": {}, "disagreements": []}
    for c in CRITERIA:
        h = [human[i][c] for i in ids]
        j = [judge[i][c] for i in ids]
        out["criteria"][c] = {
            "agreement": sum(x == y for x, y in zip(h, j)) / len(ids) if ids else 0.0,
            "kappa": cohens_kappa(h, j) if ids else None,
            "confusion": Counter(f"{x}->{y}" for x, y in zip(h, j)),  # human->judge
        }
        for i, x, y in zip(ids, h, j):
            if x != y:
                out["disagreements"].append({
                    "id": i, "criterion": c, "human": x, "judge": y,
                    "human_note": human[i].get("note", ""),
                    "judge_reasoning": judge[i]["reasoning"][c],
                })
    return out


def seeded_flaw_recall(answers: list[dict], judge: dict[str, dict]) -> dict:
    by_flaw: dict[str, list[bool]] = {}
    for r in answers:
        flaw = r.get("seeded_flaw")
        if flaw and r["id"] in judge:
            by_flaw.setdefault(flaw, []).append(judge[r["id"]][FLAW_TARGET[flaw]] == "fail")
    originals = [judge[r["id"]] for r in answers if r["variant"] == "original" and r["id"] in judge]
    flagged = [row["id"] for row in originals if any(row[c] == "fail" for c in CRITERIA)]
    return {"by_flaw": by_flaw, "originals": len(originals), "originals_flagged": flagged}


def _fmt_kappa(k: float | None) -> str:
    return "n/a" if k is None else f"{k:.2f}"


def render_report(run_file: Path, judge_rows: list[dict], agree: dict | None, recall: dict) -> str:
    cost = sum(r["cost_usd"] for r in judge_rows)
    latency = sorted(r["latency_s"] for r in judge_rows)
    first = judge_rows[0]
    lines = [
        f"# Judge report: `{run_file.name}`",
        "",
        f"Model `{first['model']}`, prompt `{first['prompt_version']}`, {len(judge_rows)} answers graded, "
        f"total cost ${cost:.3f}, median latency {latency[len(latency) // 2]:.1f}s.",
        "",
    ]

    lines += ["## Agreement with human labels", ""]
    if agree is None:
        lines += ["_No `data/human_labels.jsonl` yet._", ""]
    else:
        lines += [f"{agree['n']} answers labeled by both.", "",
                  "| Criterion | Agreement | Cohen's kappa | human→judge counts |", "|---|---|---|---|"]
        for c, s in agree["criteria"].items():
            counts = ", ".join(f"{k}: {v}" for k, v in sorted(s["confusion"].items()))
            lines.append(f"| {c} | {s['agreement']:.0%} | {_fmt_kappa(s['kappa'])} | {counts} |")
        lines += ["", f"### Disagreements ({len(agree['disagreements'])})", ""]
        for d in agree["disagreements"]:
            lines += [f"- **{d['id']}** · {d['criterion']}: human **{d['human']}**, judge **{d['judge']}**",
                      f"  - Human: {d['human_note'] or '_(no note)_'}",
                      f"  - Judge: {d['judge_reasoning']}"]
        lines.append("")

    lines += ["## Seeded-flaw recall", "",
              "Did the judge fail the criterion each planted flaw targets? (A sanity check, not ground truth.)", "",
              "| Flaw | Targets | Caught |", "|---|---|---|"]
    for flaw, hits in sorted(recall["by_flaw"].items()):
        lines.append(f"| {flaw} | {FLAW_TARGET[flaw]} | {sum(hits)}/{len(hits)} |")
    total = [h for hits in recall["by_flaw"].values() for h in hits]
    if total:
        lines.append(f"| **all** | | **{sum(total)}/{len(total)}** |")
    flagged = recall["originals_flagged"]
    lines += ["", f"Original (unseeded) answers the judge failed on at least one criterion: "
                  f"{len(flagged)}/{recall['originals']}" + (f" ({', '.join(flagged)})" if flagged else "") + ". "
                  "Not necessarily false alarms: some originals are genuinely flawed (see data/README.md).", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run_file", type=Path)
    args = parser.parse_args()

    judge_rows = read_jsonl(args.run_file)
    if not judge_rows:
        raise SystemExit(f"No verdicts in {args.run_file}")
    judge = {r["id"]: r for r in judge_rows}
    human = {r["id"]: r for r in read_jsonl(HUMAN_LABELS)}

    report = render_report(
        args.run_file,
        judge_rows,
        agreement(human, judge) if human else None,
        seeded_flaw_recall(read_jsonl(ANSWERS), judge),
    )
    out = args.run_file.with_name(args.run_file.stem.replace("judge_", "report_") + ".md")
    out.write_text(report, encoding="utf-8")
    print(report)
    print(f"Saved {out}")
