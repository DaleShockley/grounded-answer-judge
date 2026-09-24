"""The judge: grades one RAG answer on faithful / relevant / cited_correctly.

The judge sees only what a production grader would have -- the question,
the retrieved excerpts and the answer. It does NOT see expected_docs or
anything about seeded flaws.

Prompts live in prompts/judge_<version>.txt so each revision is a
readable diff; the version is recorded with every verdict.
"""

import time
from pathlib import Path
from typing import Literal

import anthropic
from pydantic import BaseModel, Field

from src.pricing import cost_usd

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
DEFAULT_MODEL = "claude-sonnet-5"
DEFAULT_PROMPT_VERSION = "v1"
CRITERIA = ("faithful", "relevant", "cited_correctly")


# Reasoning comes before the verdict on purpose: the model writes its
# justification first and commits to a verdict after.
class CriterionVerdict(BaseModel):
    reasoning: str = Field(description="One or two sentences citing the specific claim or excerpt.")
    verdict: Literal["pass", "fail"]


class CitationVerdict(BaseModel):
    reasoning: str = Field(description="One or two sentences citing the specific claim or excerpt.")
    verdict: Literal["pass", "fail", "na"]


class JudgeVerdict(BaseModel):
    faithful: CriterionVerdict
    relevant: CriterionVerdict
    cited_correctly: CitationVerdict


def load_prompt(version: str) -> str:
    return (PROMPTS_DIR / f"judge_{version}.txt").read_text(encoding="utf-8")


def build_user_message(record: dict) -> str:
    excerpts = "\n\n---\n\n".join(f"[Source: {r['doc']}]\n{r['text']}" for r in record["retrieved"])
    return (
        f"Question:\n{record['question']}\n\n"
        f"Retrieved documentation excerpts:\n\n{excerpts}\n\n"
        f"Answer to grade:\n{record['answer']}"
    )


def judge_answer(
    client: anthropic.Anthropic,
    record: dict,
    model: str = DEFAULT_MODEL,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
) -> dict:
    """Grades one answer. Returns a flat, JSON-ready result row."""
    started = time.perf_counter()
    response = client.messages.parse(
        model=model,
        max_tokens=4096,
        system=load_prompt(prompt_version),
        messages=[{"role": "user", "content": build_user_message(record)}],
        output_format=JudgeVerdict,
    )
    latency = time.perf_counter() - started

    if response.stop_reason == "refusal" or response.parsed_output is None:
        raise RuntimeError(f"Judge returned no verdict for {record['id']}: {response.stop_reason}")

    verdict: JudgeVerdict = response.parsed_output
    usage = response.usage
    return {
        "id": record["id"],
        **{c: getattr(verdict, c).verdict for c in CRITERIA},
        "reasoning": {c: getattr(verdict, c).reasoning for c in CRITERIA},
        "model": model,
        "prompt_version": prompt_version,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "cost_usd": round(cost_usd(model, usage.input_tokens, usage.output_tokens), 6),
        "latency_s": round(latency, 2),
    }
