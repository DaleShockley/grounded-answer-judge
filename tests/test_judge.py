from types import SimpleNamespace
from unittest.mock import MagicMock

import anthropic
import pytest

from src.judge import (
    CitationVerdict,
    CriterionVerdict,
    JudgeVerdict,
    build_user_message,
    judge_answer,
    load_prompt,
)
from src.run_judge import read_jsonl, run

RECORD = {
    "id": "q09-original",
    "question": "How do I make a query parameter required?",
    "answer": "Don't declare a default value.\n\nSources: query-params.md",
    "retrieved": [{"doc": "query-params.md", "text": "To make it required, don't declare a default."}],
    "expected_docs": ["query-params.md"],
    "seeded_flaw": "should never reach the judge",
    "flaw_note": "should never reach the judge",
}


def _response(stop_reason="end_turn", cited="pass"):
    verdict = JudgeVerdict(
        faithful=CriterionVerdict(reasoning="Matches the excerpt.", verdict="pass"),
        relevant=CriterionVerdict(reasoning="Answers it directly.", verdict="pass"),
        cited_correctly=CitationVerdict(reasoning="query-params.md holds it.", verdict=cited),
    )
    return SimpleNamespace(
        stop_reason=stop_reason,
        parsed_output=None if stop_reason == "refusal" else verdict,
        usage=SimpleNamespace(input_tokens=1000, output_tokens=200),
    )


def _client(*responses):
    client = MagicMock()
    client.messages.parse.side_effect = list(responses)
    return client


def test_prompt_v1_exists_and_defines_all_three_criteria():
    prompt = load_prompt("v1")
    for criterion in ("faithful", "relevant", "cited_correctly"):
        assert criterion in prompt


def test_user_message_is_blind_to_answer_key_and_seeded_flaw():
    message = build_user_message(RECORD)
    assert "[Source: query-params.md]" in message and RECORD["answer"] in message
    assert "should never reach the judge" not in message
    assert "expected" not in message.lower()


def test_judge_answer_returns_flat_row_with_cost():
    row = judge_answer(_client(_response()), RECORD, model="claude-sonnet-5", prompt_version="v1")

    assert row["id"] == "q09-original"
    assert (row["faithful"], row["relevant"], row["cited_correctly"]) == ("pass", "pass", "pass")
    assert row["reasoning"]["cited_correctly"] == "query-params.md holds it."
    # 1000 in * $2/M + 200 out * $10/M
    assert row["cost_usd"] == pytest.approx(0.004)


def test_judge_answer_raises_on_refusal():
    with pytest.raises(RuntimeError):
        judge_answer(_client(_response(stop_reason="refusal")), RECORD)


def test_run_resumes_and_retries_failures(tmp_path):
    out = tmp_path / "judge.jsonl"
    second = {**RECORD, "id": "q09-contradiction"}
    request = MagicMock()
    api_error = anthropic.APIConnectionError(request=request)

    first = run(_client(_response(), api_error), [RECORD, second], out, "claude-sonnet-5", "v1")
    assert first == {"skipped": 0, "graded": 1, "failed": ["q09-contradiction"]}

    client = _client(_response(cited="fail"))
    again = run(client, [RECORD, second], out, "claude-sonnet-5", "v1")
    assert again == {"skipped": 1, "graded": 1, "failed": []}
    assert client.messages.parse.call_count == 1  # only the failed one was re-graded
    assert [r["id"] for r in read_jsonl(out)] == ["q09-original", "q09-contradiction"]
