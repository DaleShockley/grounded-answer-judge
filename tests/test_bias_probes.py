from eval.bias_probes import CONFIDENT_PREFIX, build_probes, score


def _answer(id_, variant="original", flaw=None, cited=("body.md",)):
    return {
        "id": id_, "question": "Q?", "variant": variant, "seeded_flaw": flaw,
        "answer": "Use a Pydantic model.\n\nSources: body.md", "cited_sources": list(cited),
        "retrieved": [
            {"doc": "query-params.md", "text": "Unrelated. Text here."},
            {"doc": "body.md", "text": "## Heading\nTo declare a body, use Pydantic. It validates data."},
        ],
    }


def _grades(f="pass", r="pass", c="pass"):
    return {"faithful": f, "relevant": r, "cited_correctly": c}


def test_padding_quotes_a_cited_doc_verbatim_and_keeps_sources_last():
    answers = [_answer("q10-original")]
    probes = build_probes(answers, {"q10-original": _grades()})

    padded = probes[0]
    assert padded["id"] == "q10-original~padded" and padded["base_id"] == "q10-original"
    assert '"To declare a body, use Pydantic. It validates data."' in padded["answer"]
    assert "Heading" not in padded["answer"] and "Unrelated" not in padded["answer"]
    assert padded["answer"].rstrip().endswith("Sources: body.md")


def test_only_fully_passing_cited_originals_get_padded_and_only_faithful_flaws_get_confident():
    answers = [
        _answer("q01-original"),
        _answer("q02-original"),                        # reviewed as a fail -> skipped
        _answer("q03-original", cited=()),               # cites nothing -> skipped
        _answer("q04-fabricated_detail", "flawed", "fabricated_detail"),
        _answer("q05-wrong_citation", "flawed", "wrong_citation"),  # not a faithfulness flaw -> skipped
    ]
    reviewed = {"q01-original": _grades(), "q02-original": _grades(f="fail"), "q03-original": _grades(c="na"),
                "q04-fabricated_detail": _grades(f="fail"), "q05-wrong_citation": _grades(c="fail")}

    probes = build_probes(answers, reviewed)

    assert [p["id"] for p in probes] == ["q01-original~padded", "q04-fabricated_detail~confident"]
    assert probes[1]["answer"].startswith(CONFIDENT_PREFIX)


def test_score_reports_flips_against_the_base_answer():
    probes = [{"id": "a~padded", "base_id": "a", "probe": "padded"},
              {"id": "b~confident", "base_id": "b", "probe": "confident"}]
    base = {"a": _grades(), "b": _grades(f="fail")}
    run = {"a~padded": _grades(r="fail"), "b~confident": _grades(f="fail")}

    result = score(probes, base, run)

    assert result["padded"] == {"n": 1, "held": 0, "flips": [("a", "relevant", "pass", "fail")]}
    assert result["confident"] == {"n": 1, "held": 1, "flips": []}
