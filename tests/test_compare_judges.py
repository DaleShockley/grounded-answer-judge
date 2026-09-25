import json

from eval.compare_judges import anchor_cases, anchor_misses, consistency, load_runs


def _v(f, r, c):
    return {"faithful": f, "relevant": r, "cited_correctly": c}


def test_consistency_counts_answer_criterion_pairs_identical_across_runs():
    run1 = {"a": _v("pass", "pass", "pass"), "b": _v("fail", "pass", "na")}
    run2 = {"a": _v("pass", "pass", "pass"), "b": _v("fail", "fail", "na")}
    assert consistency([run1, run2]) == 5 / 6
    assert consistency([run1]) is None


def test_anchor_cases_combine_seeded_targets_and_rubric_file():
    answers = [{"id": "q05-wrong_citation", "seeded_flaw": "wrong_citation"},
               {"id": "q05-original", "seeded_flaw": None}]
    anchors = anchor_cases(answers)
    seeded = [a for a in anchors if a["kind"] == "seeded"]
    assert seeded == [{"id": "q05-wrong_citation", "criterion": "cited_correctly",
                       "expected": "fail", "kind": "seeded", "rule": "wrong_citation"}]
    assert len([a for a in anchors if a["kind"] == "rubric"]) == 9


def test_anchor_misses():
    anchors = [{"id": "a", "criterion": "relevant", "expected": "pass", "kind": "rubric", "rule": "r"},
               {"id": "b", "criterion": "cited_correctly", "expected": "na", "kind": "rubric", "rule": "r"}]
    run = {"a": _v("pass", "pass", "pass"), "b": _v("pass", "pass", "fail")}
    assert [m["id"] for m in anchor_misses(run, anchors)] == ["b"]


def test_load_runs_groups_tagged_runs_by_prompt_and_model(tmp_path):
    for name in ("judge_v1_claude-sonnet-5.jsonl", "judge_v2_claude-haiku-4-5_r1.jsonl",
                 "judge_v2_claude-haiku-4-5_r2.jsonl", "report_v1_claude-sonnet-5.md"):
        (tmp_path / name).write_text(json.dumps({"id": "a", **_v("pass", "pass", "pass")}) + "\n")
    runs = load_runs(tmp_path)
    assert {k: len(v) for k, v in runs.items()} == {("v1", "claude-sonnet-5"): 1,
                                                    ("v2", "claude-haiku-4-5"): 2}
