"""Runs the judge over the answer set and saves one verdict per line.

    python -m src.run_judge [--model claude-sonnet-5] [--prompt v1] [--limit N] [--ids a,b] [--tag run1]

Writes results/judge_<prompt>_<model>[_<tag>].jsonl. Re-running resumes:
answers that already have a verdict in that file are skipped, so a
crash or an interruption costs nothing to recover from. Use --tag to keep
repeated runs of the same setup apart (e.g. for consistency checks).
"""

import argparse
import json
from pathlib import Path

import anthropic

from src.judge import DEFAULT_MODEL, DEFAULT_PROMPT_VERSION, judge_answer

ROOT = Path(__file__).parent.parent
ANSWERS = ROOT / "data" / "answers.jsonl"
RESULTS_DIR = ROOT / "results"


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def results_path(prompt_version: str, model: str, tag: str | None = None) -> Path:
    suffix = f"_{tag}" if tag else ""
    return RESULTS_DIR / f"judge_{prompt_version}_{model}{suffix}.jsonl"


def run(client, records: list[dict], out: Path, model: str, prompt_version: str) -> dict:
    done = {r["id"] for r in read_jsonl(out)}
    todo = [r for r in records if r["id"] not in done]
    out.parent.mkdir(parents=True, exist_ok=True)

    graded, failed = 0, []
    with out.open("a", encoding="utf-8") as f:
        for i, record in enumerate(todo, 1):
            try:
                row = judge_answer(client, record, model=model, prompt_version=prompt_version)
            except (anthropic.APIError, RuntimeError) as exc:
                # Leave it out of the file so the next run retries it.
                failed.append(record["id"])
                print(f"  [{i}/{len(todo)}] {record['id']}: FAILED ({exc})")
                continue
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            graded += 1
            verdicts = " ".join(f"{k[:4]}={row[k]}" for k in ("faithful", "relevant", "cited_correctly"))
            print(f"  [{i}/{len(todo)}] {record['id']}: {verdicts}")

    return {"skipped": len(done), "graded": graded, "failed": failed}


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT_VERSION)
    parser.add_argument("--limit", type=int, help="grade only the first N answers")
    parser.add_argument("--ids", help="comma-separated answer ids to grade")
    parser.add_argument("--tag", help="suffix for the results file, to keep repeated runs apart")
    args = parser.parse_args()

    records = read_jsonl(ANSWERS)
    if args.ids:
        wanted = set(args.ids.split(","))
        records = [r for r in records if r["id"] in wanted]
    if args.limit:
        records = records[: args.limit]

    out = results_path(args.prompt, args.model, args.tag)
    summary = run(anthropic.Anthropic(), records, out, args.model, args.prompt)

    rows = read_jsonl(out)
    total_cost = sum(r["cost_usd"] for r in rows)
    print(f"\n{summary['graded']} graded, {summary['skipped']} already done, {len(summary['failed'])} failed")
    print(f"{out.name}: {len(rows)} verdicts, total cost ${total_cost:.3f}")
