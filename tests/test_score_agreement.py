import pytest

from eval.score_agreement import agreement, cohens_kappa, seeded_flaw_recall


def test_kappa_perfect_agreement():
    assert cohens_kappa(["pass", "fail", "pass"], ["pass", "fail", "pass"]) == 1.0


def test_kappa_textbook_example():
    # 50 items: both "pass" 20, both "fail" 15, human pass/judge fail 5, human fail/judge pass 10.
    human = ["pass"] * 20 + ["fail"] * 15 + ["pass"] * 5 + ["fail"] * 10
    judge = ["pass"] * 20 + ["fail"] * 15 + ["fail"] * 5 + ["pass"] * 10
    # po = 0.70; pe = 0.5*0.6 + 0.5*0.4 = 0.50; kappa = 0.4
    assert cohens_kappa(human, judge) == pytest.approx(0.4)


def test_kappa_can_be_negative_and_undefined():
    assert cohens_kappa(["pass", "fail"], ["fail", "pass"]) < 0
    assert cohens_kappa(["pass", "pass"], ["pass", "pass"]) is None


def test_kappa_rejects_mismatched_lists():
    with pytest.raises(ValueError):
        cohens_kappa(["pass"], ["pass", "fail"])


def _row(id_, f, r, c):
    return {"id": id_, "faithful": f, "relevant": r, "cited_correctly": c,
            "reasoning": {"faithful": "jf", "relevant": "jr", "cited_correctly": "jc"}}


def test_agreement_counts_only_shared_ids_and_lists_disagreements():
    human = {"a": {**_row("a", "pass", "pass", "pass"), "note": "fine"},
             "b": {**_row("b", "fail", "pass", "na"), "note": "made-up flag"},
             "only-human": _row("only-human", "pass", "pass", "pass")}
    judge = {"a": _row("a", "pass", "pass", "pass"), "b": _row("b", "pass", "pass", "na"),
             "only-judge": _row("only-judge", "fail", "fail", "fail")}

    result = agreement(human, judge)

    assert result["n"] == 2
    assert result["criteria"]["faithful"]["agreement"] == 0.5
    assert result["criteria"]["relevant"]["agreement"] == 1.0
    assert result["disagreements"] == [{
        "id": "b", "criterion": "faithful", "human": "fail", "judge": "pass",
        "human_note": "made-up flag", "judge_reasoning": "jf",
    }]


def test_seeded_flaw_recall_checks_the_targeted_criterion():
    answers = [
        {"id": "q1-original", "variant": "original", "seeded_flaw": None},
        {"id": "q2-original", "variant": "original", "seeded_flaw": None},
        {"id": "q1-contradiction", "variant": "flawed", "seeded_flaw": "contradiction"},
        {"id": "q2-wrong_citation", "variant": "flawed", "seeded_flaw": "wrong_citation"},
    ]
    judge = {
        "q1-original": _row("q1-original", "pass", "pass", "pass"),
        "q2-original": _row("q2-original", "pass", "fail", "pass"),
        "q1-contradiction": _row("q1-contradiction", "fail", "pass", "pass"),     # caught
        "q2-wrong_citation": _row("q2-wrong_citation", "fail", "pass", "pass"),  # wrong criterion: missed
    }

    result = seeded_flaw_recall(answers, judge)

    assert result["by_flaw"] == {"contradiction": [True], "wrong_citation": [False]}
    assert result["originals"] == 2 and result["originals_flagged"] == ["q2-original"]
