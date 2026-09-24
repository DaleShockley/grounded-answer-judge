"""Builds the Phase 1 answer set: every real RAG answer, plus deliberately
flawed copies of some of them, so the judge has known failures to catch.

    python -m src.build_answer_set

Reads  data/rag_answers.jsonl  (exported by rag-docs-assistant)
       data/flaw_plan.json      (which answers get which flaw)
Writes data/answers.jsonl

Each flawed record gets exactly one seeded flaw. `wrong_citation` is done
in code (swap the Sources line); the rest are written by Claude, told to
keep the answer's length, tone and format so the flaw isn't given away by
style alone. `seeded_flaw` is what we *tried* to inject -- the human labels
in Phase 2, not this field, are the ground truth.
"""

import json
import re
from pathlib import Path

import anthropic
from pydantic import BaseModel

DATA_DIR = Path(__file__).parent.parent / "data"
FLAW_MODEL = "claude-sonnet-5"
CORPUS_DOCS = ["body.md", "first-steps.md", "handling-errors.md", "path-params.md", "query-params.md"]

FLAW_INSTRUCTIONS: dict[str, str] = {
    "fabricated_detail": (
        "Add exactly one specific, plausible-sounding claim that is NOT supported by the "
        "excerpts (for example an extra option, a default value, a flag, or a behavior). "
        "Keep everything else the same and blend the new claim in naturally."
    ),
    "contradiction": (
        "Change one key fact so it directly contradicts the excerpts. Keep the rest the "
        "same, and keep the answer confident and fluent."
    ),
    "off_topic": (
        "Rewrite the answer so it confidently answers a closely related but different "
        "question, using facts from the excerpts, without ever actually answering the "
        "question that was asked."
    ),
    "incomplete": (
        "Remove the most important part of the answer, so what remains is accurate but "
        "leaves out something essential the question asks for. Do not add anything false."
    ),
    "unanswerable_hallucination": (
        "The excerpts do not answer this question. Write a confident, helpful-sounding "
        "answer from general FastAPI knowledge, as if the docs covered it. Do not mention "
        "that the excerpts are missing the information."
    ),
}

SYSTEM_PROMPT = """You help build a test set for an automated grader of RAG (retrieval-augmented) answers.

You'll get a question, the documentation excerpts a RAG system retrieved, and the answer it gave.
Rewrite the answer to contain exactly ONE deliberate defect of the requested type.

Rules:
- Match the original's length, tone and formatting, so the defect can't be spotted from style alone.
- End with a line of the form "Sources: <file>.md" naming file(s) from the excerpts, like the original.
- In flaw_note, say in one sentence exactly what you changed, so a human can verify it."""

_SOURCES_LINE = re.compile(r"^\s*\**Sources:?\**:?\s*(.+)$", re.IGNORECASE | re.MULTILINE)
_DOC_NAME = re.compile(r"[\w.-]+\.md\b")


class FlawedAnswer(BaseModel):
    answer: str
    flaw_note: str


def parse_cited_sources(answer: str) -> list[str]:
    """Doc names from the answer's own "Sources:" line (the last one wins)."""
    matches = _SOURCES_LINE.findall(answer)
    if not matches:
        return []
    # Only filenames count: the model sometimes writes prose here ("None of the excerpts...").
    return _DOC_NAME.findall(matches[-1])


def swap_citation(record: dict) -> tuple[str, str]:
    """Replaces the answer's Sources line with a corpus doc that doesn't contain the answer."""
    avoid = set(record.get("expected_docs", [])) | set(record.get("cited_sources", []))
    candidates = [d for d in CORPUS_DOCS if d not in avoid]
    # Deterministic but varied across questions, so it's reproducible without always picking the same doc.
    wrong = candidates[sum(map(ord, record["id"])) % len(candidates)]

    lines = record["answer"].rstrip().splitlines()
    for i in range(len(lines) - 1, -1, -1):
        if _SOURCES_LINE.match(lines[i]):
            lines[i] = f"Sources: {wrong}"
            break
    else:
        lines += ["", f"Sources: {wrong}"]

    right = ", ".join(record.get("cited_sources") or record.get("expected_docs") or ["(none)"])
    return "\n".join(lines), f"Changed the cited source from {right} to {wrong}."


def inject_flaw(client: anthropic.Anthropic, record: dict, flaw: str) -> tuple[str, str]:
    excerpts = "\n\n---\n\n".join(f"[Source: {r['doc']}]\n{r['text']}" for r in record["retrieved"])
    response = client.messages.parse(
        model=FLAW_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Defect type: {flaw}\nInstruction: {FLAW_INSTRUCTIONS[flaw]}\n\n"
                    f"Question: {record['question']}\n\n"
                    f"Documentation excerpts:\n\n{excerpts}\n\n"
                    f"Original answer:\n{record['answer']}"
                ),
            }
        ],
        output_format=FlawedAnswer,
    )
    if response.stop_reason == "refusal" or response.parsed_output is None:
        raise RuntimeError(f"No flawed answer for {record['id']} ({flaw}): {response.stop_reason}")
    return response.parsed_output.answer, response.parsed_output.flaw_note


def build(rag_answers: list[dict], flaw_plan: list[dict], client: anthropic.Anthropic | None) -> list[dict]:
    # Re-parse citations so every record, original or flawed, goes through the same parser.
    rag_answers = [{**r, "cited_sources": parse_cited_sources(r["answer"])} for r in rag_answers]
    by_id = {r["id"]: r for r in rag_answers}
    records = [
        {**r, "id": f"{r['id']}-original", "question_id": r["id"],
         "variant": "original", "seeded_flaw": None, "flaw_note": None}
        for r in rag_answers
    ]

    for item in flaw_plan:
        source, flaw = by_id[item["source"]], item["flaw"]
        if flaw == "wrong_citation":
            answer, note = swap_citation(source)
        else:
            answer, note = inject_flaw(client, source, flaw)
        records.append(
            {**source, "id": f"{source['id']}-{flaw}", "question_id": source["id"],
             "answer": answer, "cited_sources": parse_cited_sources(answer),
             "variant": "flawed", "seeded_flaw": flaw, "flaw_note": note}
        )
        print(f"  {source['id']}: {flaw}")
    return records


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    rag_answers = _read_jsonl(DATA_DIR / "rag_answers.jsonl")
    flaw_plan = json.loads((DATA_DIR / "flaw_plan.json").read_text(encoding="utf-8"))

    records = build(rag_answers, flaw_plan, anthropic.Anthropic())

    out = DATA_DIR / "answers.jsonl"
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    flawed = sum(r["variant"] == "flawed" for r in records)
    print(f"Wrote {len(records)} records ({len(records) - flawed} original, {flawed} flawed) to {out}")
