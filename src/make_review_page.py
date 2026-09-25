"""Builds labeling/review.html: a page for settling every disagreement
between the first-pass human labels and a judge run, using RUBRIC.md.

    python -m src.make_review_page [--judge results/judge_v1_claude-sonnet-5.jsonl]

Only answers with at least one disputed criterion are shown. For each,
the page shows both grades and the judge's reasoning; the reviewer picks
the final grade. Undisputed criteria start at the agreed grade and can
still be changed.

"Export reviewed labels" downloads reviewed_labels.jsonl covering all
answers (reviewed ones plus undisputed ones carried over) -- save it as
data/reviewed_labels.jsonl. data/human_labels.jsonl is never modified.

This step is deliberately NOT blind to the judge: it's adjudication, not
labeling. Seeded-flaw fields stay hidden.
"""

import argparse
import json
from pathlib import Path

from src.make_labeling_page import ANSWERS, STYLE, blind_items, render_page
from src.run_judge import read_jsonl

ROOT = Path(__file__).parent.parent
HUMAN_LABELS = ROOT / "data" / "human_labels.jsonl"
DEFAULT_JUDGE = ROOT / "results" / "judge_v1_claude-sonnet-5.jsonl"
TEMPLATE = ROOT / "labeling" / "review_template.html"
OUTPUT = ROOT / "labeling" / "review.html"
CRITERIA = ("faithful", "relevant", "cited_correctly")


def build_review(answers: list[dict], human: dict[str, dict], judge: dict[str, dict]) -> tuple[list[dict], list[dict]]:
    """Returns (items to review, undisputed first-pass rows to carry over)."""
    items, undisputed = [], []
    for item in blind_items(answers):  # same shuffled order as labeling; seeded-flaw fields already dropped
        h, j = human[item["id"]], judge[item["id"]]
        disputed = [c for c in CRITERIA if h[c] != j[c]]
        if disputed:
            items.append({
                **item,
                "disputed": disputed,
                "first_pass": {c: h[c] for c in CRITERIA},
                "judge": {**{c: j[c] for c in CRITERIA}, "reasoning": j["reasoning"]},
            })
        else:
            undisputed.append({"id": item["id"], **{c: h[c] for c in CRITERIA}, "note": h.get("note", "")})
    return items, undisputed


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--judge", type=Path, default=DEFAULT_JUDGE)
    args = parser.parse_args()

    answers = read_jsonl(ANSWERS)
    human = {r["id"]: r for r in read_jsonl(HUMAN_LABELS)}
    judge = {r["id"]: r for r in read_jsonl(args.judge)}
    missing = [r["id"] for r in answers if r["id"] not in human or r["id"] not in judge]
    if missing:
        raise SystemExit(f"Need both a human label and a judge verdict for every answer; missing: {missing}")

    items, undisputed = build_review(answers, human, judge)
    page = render_page(items, TEMPLATE.read_text(encoding="utf-8"), STYLE.read_text(encoding="utf-8"))
    page = page.replace("/*__UNDISPUTED__*/[]", json.dumps(undisputed, ensure_ascii=False).replace("</", "<\\/"))
    OUTPUT.write_text(page, encoding="utf-8")
    disputes = sum(len(i["disputed"]) for i in items)
    print(f"Wrote {OUTPUT}: {len(items)} answers to review ({disputes} disputed grades), "
          f"{len(undisputed)} undisputed carried over.")
