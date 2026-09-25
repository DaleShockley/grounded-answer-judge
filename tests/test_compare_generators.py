import pytest

from eval.compare_generators import fully_correct, render, summarize


def _v(f="pass", r="pass", c="pass"):
    return {"faithful": f, "relevant": r, "cited_correctly": c}


def _a(id_, expected=("body.md",), cited=("body.md",), latency=1.0, stop="end_turn"):
    return {"id": id_, "expected_docs": list(expected), "cited_sources": list(cited),
            "generator_model": "claude-haiku-4-5", "input_tokens": 1000, "output_tokens": 200,
            "latency_s": latency, "stop_reason": stop}


def test_fully_correct_allows_na_but_not_fail():
    assert fully_correct(_v(c="na"))
    assert not fully_correct(_v(c="fail"))
    assert not fully_correct(_v(r="fail"))


def test_summarize_counts_quality_behavior_and_cost():
    answers = [
        _a("q01", latency=1.0),
        _a("q02", latency=2.0),                             # answerable but declined (grader: n.a.), still lists a doc
        _a("q03", latency=3.0, stop="max_tokens"),
        _a("q27", expected=(), cited=(), latency=4.0),      # unanswerable
    ]
    verdicts = {"q01": _v(), "q02": _v(c="na"), "q03": _v(f="fail"), "q27": _v(c="na")}
    second = {"q01": _v(), "q02": _v(r="fail"), "q03": _v(), "q27": _v(c="na")}

    s = summarize(answers, verdicts, second)

    assert s["fully_correct"] == 3 and s["second_fully_correct"] == 3
    assert (s["cited_pass"], s["cited_graded"]) == (2, 2)
    assert s["declined_answerable"] == ["q02"] and s["n_answerable"] == 3
    assert s["answerable_wrong"] == 1  # q03: answered, but unfaithful
    assert (s["unanswerable_ok"], s["n_unanswerable"]) == (1, 1)
    assert s["truncated"] == ["q03"]
    assert s["failing"] == [("q03", ["faithful"])]
    # 1000 in * $1/M + 200 out * $5/M = $0.002 per answer -> $2.00 per 1k
    assert s["cost_per_1k"] == pytest.approx(2.0)
    assert s["latency_median"] == 2.5


def test_render_includes_every_generator():
    s = summarize([_a("q01")], {"q01": _v()})
    report = render({"claude-haiku-4-5": s, "claude-opus-5-5": s})
    assert "`claude-haiku-4-5`" in report and "`claude-opus-5-5`" in report
