"""Builds labeling/label.html: a self-contained page for grading the
answer set by hand, blind to which answers had flaws seeded into them.

    python -m src.make_labeling_page

Open the generated file in a browser. Progress is saved in the browser as
you go; "Export labels" downloads human_labels.jsonl -- move it to
data/human_labels.jsonl when you're done.

Blinding: the page never shows seeded_flaw, flaw_note, variant or the
record id (ids like "q05-wrong_citation" would give the flaw away), and
the order is shuffled with a fixed seed so paired original/flawed answers
aren't next to each other.
"""

import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).parent.parent
ANSWERS = ROOT / "data" / "answers.jsonl"
TEMPLATE = ROOT / "labeling" / "template.html"
STYLE = ROOT / "labeling" / "style.css"
OUTPUT = ROOT / "labeling" / "label.html"

# Only what a human grader needs. Everything that reveals the seeded flaw stays out.
VISIBLE_FIELDS = ("id", "question", "expected_docs", "answer", "retrieved")
SHUFFLE_SEED = 20260924


def blind_items(records: list[dict], seed: int = SHUFFLE_SEED) -> list[dict]:
    pool = [{k: r[k] for k in VISIBLE_FIELDS} for r in records]
    random.Random(seed).shuffle(pool)
    # Keep answers to the same question apart, so a flawed copy isn't read right after its original.
    ordered: list[dict] = []
    while pool:
        pick = next((i for i, it in enumerate(pool) if not ordered or _qid(it) != _qid(ordered[-1])), 0)
        ordered.append(pool.pop(pick))
    return ordered


def _qid(item: dict) -> str:
    return item["id"].split("-", 1)[0]


def render_page(items: list[dict], template: str, style: str = "") -> str:
    data = json.dumps(items, ensure_ascii=False).replace("</", "<\\/")  # can't close the <script> early
    dataset = hashlib.sha256(data.encode("utf-8")).hexdigest()[:12]  # new answer set -> fresh saved progress
    return (
        template.replace("/*__STYLE__*/", style)
        .replace("/*__DATA__*/[]", data)
        .replace("/*__DATASET__*/", dataset)
    )


if __name__ == "__main__":
    records = [json.loads(line) for line in ANSWERS.read_text(encoding="utf-8").splitlines() if line.strip()]
    items = blind_items(records)
    page = render_page(items, TEMPLATE.read_text(encoding="utf-8"), STYLE.read_text(encoding="utf-8"))
    OUTPUT.write_text(page, encoding="utf-8")
    print(f"Wrote {OUTPUT} ({len(items)} answers). Open it in your browser to start labeling.")
