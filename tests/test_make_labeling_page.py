import json

from src.make_labeling_page import blind_items, render_page


def _records():
    out = []
    for q in range(1, 6):
        for variant in ("original", "fabricated_detail"):
            out.append({
                "id": f"q0{q}-{variant}", "question": f"Question {q}", "expected_docs": ["body.md"],
                "answer": "An answer </script> with a tag", "retrieved": [{"doc": "body.md", "text": "x"}],
                "variant": variant, "seeded_flaw": None if variant == "original" else variant,
                "flaw_note": "secret", "generator_model": "m",
            })
    return out


def test_blinding_drops_everything_that_reveals_the_flaw():
    items = blind_items(_records())
    assert len(items) == 10
    for item in items:
        assert set(item) == {"id", "question", "expected_docs", "answer", "retrieved"}


def test_answers_to_the_same_question_are_not_adjacent():
    items = blind_items(_records())
    qids = [it["id"].split("-")[0] for it in items]
    assert all(a != b for a, b in zip(qids, qids[1:]))


def test_order_is_reproducible():
    assert blind_items(_records()) == blind_items(_records())


def test_rendered_page_embeds_data_without_breaking_the_script_tag():
    template = "<script>const ITEMS = /*__DATA__*/[]; const DATASET = \"/*__DATASET__*/\";</script>"
    page = render_page(blind_items(_records()), template)

    assert "/*__DATA__*/" not in page and "/*__DATASET__*/" not in page
    assert page.count("</script>") == 1  # the one in the answer text got escaped
    embedded = page.split("const ITEMS = ", 1)[1].split("; const DATASET", 1)[0]
    assert len(json.loads(embedded)) == 10
