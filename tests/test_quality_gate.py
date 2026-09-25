import json

from eval.quality_gate import DEFAULT_ANSWERS_RUN, DEFAULT_JUDGE_RUN, answer_checks, main
from src.run_judge import ANSWERS, read_jsonl


def _write(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return path


def _rubber_stamp(ids):
    """A broken judge that passes everything -- what a bad prompt change can look like."""
    return [{"id": i, "faithful": "pass", "relevant": "pass", "cited_correctly": "pass"} for i in ids]


def test_committed_results_pass_the_gate(capsys):
    assert main([]) == 0
    assert "Quality gate passed." in capsys.readouterr().out


def test_a_rubber_stamp_judge_fails_the_gate(tmp_path, capsys):
    ids = [r["id"] for r in read_jsonl(ANSWERS)]
    broken = _write(tmp_path / "judge_broken.jsonl", _rubber_stamp(ids))

    assert main(["--judge-run", str(broken), "--answers-run", str(DEFAULT_ANSWERS_RUN)]) == 1
    out = capsys.readouterr().out
    assert "Judge: seeded flaws caught | 0/17" in out
    assert "Quality gate FAILED" in out


def test_degraded_answers_fail_the_gate(tmp_path, capsys):
    good = read_jsonl(DEFAULT_ANSWERS_RUN)
    degraded = [{**r, "faithful": "fail"} if i < 3 else r for i, r in enumerate(good)]  # 3 more unfaithful answers
    path = _write(tmp_path / "answers_degraded.jsonl", degraded)

    assert main(["--judge-run", str(DEFAULT_JUDGE_RUN), "--answers-run", str(path)]) == 1
    assert "Answers: faithful" in capsys.readouterr().out


def test_answer_checks_count_na_as_fully_correct():
    run = {"a": {"faithful": "pass", "relevant": "pass", "cited_correctly": "na"},
           "b": {"faithful": "pass", "relevant": "pass", "cited_correctly": "fail"}}
    checks = answer_checks(run, {"faithful_min": 2, "fully_correct_min": 2})
    assert [(c["value"], c["total"]) for c in checks] == [(2, 2), (1, 2)]
