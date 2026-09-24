from types import SimpleNamespace
from unittest.mock import MagicMock

from src.build_answer_set import FlawedAnswer, build, parse_cited_sources, swap_citation


def _record(qid="q05", answer="Order matters.\n\nSources: path-params.md"):
    return {
        "id": qid,
        "question": "Why does route order matter?",
        "expected_docs": ["path-params.md"],
        "answer": answer,
        "cited_sources": parse_cited_sources(answer),
        "retrieved": [{"doc": "path-params.md", "text": "Path operations are evaluated in order."}],
    }


def test_swap_citation_picks_a_doc_that_does_not_hold_the_answer():
    answer, note = swap_citation(_record())

    cited = parse_cited_sources(answer)
    assert len(cited) == 1 and cited[0] != "path-params.md"
    assert answer.startswith("Order matters.")  # answer text itself untouched
    assert "path-params.md" in note and cited[0] in note


def test_swap_citation_adds_sources_line_when_missing():
    answer, _ = swap_citation(_record(answer="Order matters."))
    assert parse_cited_sources(answer) not in ([], ["path-params.md"])


def test_build_keeps_originals_and_adds_one_record_per_planned_flaw():
    client = MagicMock()
    client.messages.parse.return_value = SimpleNamespace(
        stop_reason="end_turn",
        parsed_output=FlawedAnswer(
            answer="Order matters, and FastAPI sorts routes alphabetically.\n\nSources: path-params.md",
            flaw_note="Added the false claim that routes are sorted alphabetically.",
        ),
    )
    plan = [{"source": "q05", "flaw": "fabricated_detail"}, {"source": "q05", "flaw": "wrong_citation"}]

    records = build([_record()], plan, client)

    assert [r["id"] for r in records] == ["q05-original", "q05-fabricated_detail", "q05-wrong_citation"]
    assert records[0]["seeded_flaw"] is None and records[0]["variant"] == "original"
    fabricated = records[1]
    assert fabricated["question_id"] == "q05" and fabricated["variant"] == "flawed"
    assert "alphabetically" in fabricated["answer"]
    assert fabricated["retrieved"] == records[0]["retrieved"]  # same evidence, different answer
    assert client.messages.parse.call_count == 1  # wrong_citation is done in code, no API call


def test_prose_on_sources_line_is_not_a_source():
    assert parse_cited_sources("Sources: None of the provided excerpts contain this.") == []
    assert parse_cited_sources("**Sources:** body.md, query-params.md") == ["body.md", "query-params.md"]
