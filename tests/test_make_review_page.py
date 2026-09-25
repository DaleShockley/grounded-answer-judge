from src.make_review_page import build_review


def _answer(id_):
    return {"id": id_, "question": "Q?", "expected_docs": ["body.md"], "answer": "A.",
            "retrieved": [{"doc": "body.md", "text": "x"}], "variant": "flawed",
            "seeded_flaw": "contradiction", "flaw_note": "secret"}


def _grades(f, r, c, **extra):
    return {"faithful": f, "relevant": r, "cited_correctly": c, **extra}


def test_only_answers_with_a_disagreement_are_reviewed():
    answers = [_answer("q01-a"), _answer("q02-a"), _answer("q03-a")]
    human = {"q01-a": _grades("pass", "pass", "pass", note=""),
             "q02-a": _grades("pass", "pass", "pass", note="looks fine"),
             "q03-a": _grades("fail", "pass", "na", note="")}
    judge = {"q01-a": _grades("fail", "pass", "pass", reasoning={"faithful": "not in excerpt"}),
             "q02-a": _grades("pass", "pass", "pass", reasoning={}),
             "q03-a": _grades("fail", "fail", "pass", reasoning={})}

    items, undisputed = build_review(answers, human, judge)

    by_id = {i["id"]: i for i in items}
    assert set(by_id) == {"q01-a", "q03-a"}
    assert by_id["q01-a"]["disputed"] == ["faithful"]
    assert by_id["q03-a"]["disputed"] == ["relevant", "cited_correctly"]
    assert by_id["q01-a"]["judge"]["reasoning"]["faithful"] == "not in excerpt"
    assert undisputed == [{"id": "q02-a", "faithful": "pass", "relevant": "pass",
                           "cited_correctly": "pass", "note": "looks fine"}]


def test_review_items_still_hide_seeded_flaw_fields():
    answers = [_answer("q01-a")]
    items, _ = build_review(answers, {"q01-a": _grades("pass", "pass", "pass")},
                            {"q01-a": _grades("fail", "pass", "pass", reasoning={})})
    assert "seeded_flaw" not in items[0] and "flaw_note" not in items[0] and "variant" not in items[0]
