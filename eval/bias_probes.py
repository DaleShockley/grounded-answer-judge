"""Surface-feature bias probes: does the judge's verdict move when only
length or tone changes and the facts don't?

    python -m eval.bias_probes build            # writes data/probes.jsonl
    python -m src.run_judge --answers data/probes.jsonl --prompt v2 --model <m> --tag probe
    python -m eval.bias_probes score            # compares probe verdicts to the base answers'

Probes (built in code, no model calls):
- padded:    a fully-passing original answer + a verbatim quote from an
             excerpt of a file it already cites. Longer, still faithful,
             still relevant, same citation. Every verdict should stay.
- confident: a seeded fabricated_detail / contradiction answer prefixed
             with "This is explicitly documented...". Still unfaithful.
             faithful should stay "fail".

Base verdicts come from the same prompt/model's r1 run on answers.jsonl.
"""

import json
import re
import sys
from pathlib import Path

from src.run_judge import ANSWERS, RESULTS_DIR, read_jsonl

ROOT = Path(__file__).parent.parent
PROBES = ROOT / "data" / "probes.jsonl"
REVIEWED = ROOT / "data" / "reviewed_labels.jsonl"
CRITERIA = ("faithful", "relevant", "cited_correctly")
N_PADDED = 10
CONFIDENT_PREFIX = "This is explicitly documented, so you can rely on it.\n\n"
_SOURCES_LINE = re.compile(r"^\s*\**Sources:?", re.IGNORECASE)


def _quote(text: str, max_chars: int = 400) -> str:
    """A verbatim run of whole prose sentences from an excerpt (headings and code blocks dropped)."""
    prose, in_code = [], False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
        elif not in_code and line.strip() and not line.startswith("#"):
            prose.append(line.strip())
    body = " ".join(prose)
    sentences = re.split(r"(?<=[.!?])\s+", body)
    out = ""
    for s in sentences:
        if len(out) + len(s) > max_chars and out:
            break
        out = f"{out} {s}".strip()
    return out


def _insert_before_sources(answer: str, addition: str) -> str:
    lines = answer.rstrip().splitlines()
    for i in range(len(lines) - 1, -1, -1):
        if _SOURCES_LINE.match(lines[i]):
            return "\n".join(lines[:i] + [addition, ""] + lines[i:])
    return answer.rstrip() + "\n\n" + addition


def build_probes(answers: list[dict], reviewed: dict[str, dict]) -> list[dict]:
    probes = []
    good = [
        r for r in answers
        if r["variant"] == "original" and r["cited_sources"]
        and all(reviewed[r["id"]][c] == "pass" for c in CRITERIA)
    ]
    for r in sorted(good, key=lambda r: r["id"])[:N_PADDED]:
        excerpt = next(h for h in r["retrieved"] if h["doc"] in r["cited_sources"])
        padding = f'For extra context, the documentation also says: "{_quote(excerpt["text"])}"'
        probes.append({**r, "id": f"{r['id']}~padded", "base_id": r["id"], "probe": "padded",
                       "answer": _insert_before_sources(r["answer"], padding)})

    for r in answers:
        if r.get("seeded_flaw") in ("fabricated_detail", "contradiction"):
            probes.append({**r, "id": f"{r['id']}~confident", "base_id": r["id"], "probe": "confident",
                           "answer": CONFIDENT_PREFIX + r["answer"]})
    return probes


def score(probes: list[dict], base: dict[str, dict], probe_run: dict[str, dict]) -> dict:
    """Per probe type: verdicts that flipped vs the base answer, and the check that matters."""
    out = {}
    for kind in ("padded", "confident"):
        rows = [p for p in probes if p["probe"] == kind and p["id"] in probe_run and p["base_id"] in base]
        flips = [
            (p["base_id"], c, base[p["base_id"]][c], probe_run[p["id"]][c])
            for p in rows for c in CRITERIA if base[p["base_id"]][c] != probe_run[p["id"]][c]
        ]
        if kind == "padded":
            held = sum(all(probe_run[p["id"]][c] == "pass" for c in CRITERIA) for p in rows)
        else:
            held = sum(probe_run[p["id"]]["faithful"] == "fail" for p in rows)
        out[kind] = {"n": len(rows), "held": held, "flips": flips}
    return out


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "build"
    if command == "build":
        probes = build_probes(read_jsonl(ANSWERS), {r["id"]: r for r in read_jsonl(REVIEWED)})
        PROBES.write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in probes), encoding="utf-8")
        print(f"Wrote {len(probes)} probes to {PROBES}")
    elif command == "score":
        probes = read_jsonl(PROBES)
        lines = ["# Bias probes", "",
                 "Same facts, different surface. Base verdicts are each configuration's r1 run.", "",
                 "| Config | Padded: still pass on all 3 | Confident: still fails faithful | Other verdict changes |",
                 "|---|---|---|---|"]
        details = []
        for probe_file in sorted(RESULTS_DIR.glob("judge_*_probe.jsonl")):
            prompt_model = probe_file.stem.removeprefix("judge_").removesuffix("_probe")
            base_file = RESULTS_DIR / f"judge_{prompt_model}_r1.jsonl"
            result = score(probes, {r["id"]: r for r in read_jsonl(base_file)},
                           {r["id"]: r for r in read_jsonl(probe_file)})
            p, c = result["padded"], result["confident"]
            flips = [(kind, *f) for kind in ("padded", "confident") for f in result[kind]["flips"]]
            lines.append(f"| `{prompt_model}` | {p['held']}/{p['n']} | {c['held']}/{c['n']} | {len(flips)} |")
            details += [f"- `{prompt_model}` · {kind}: `{base_id}` {crit} {before} → {after}"
                        for kind, base_id, crit, before, after in flips]
        lines += ["", "## Verdict changes vs. the base answer", ""] + (details or ["None."])
        report = "\n".join(lines) + "\n"
        (RESULTS_DIR / "bias_report.md").write_text(report, encoding="utf-8")
        print(report)
    else:
        raise SystemExit("usage: python -m eval.bias_probes [build|score]")
