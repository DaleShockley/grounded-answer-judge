# Answer set

`answers.jsonl` is what the judge grades: **47 answers to 30 questions** about FastAPI's tutorial docs.

| Part | Count | Where it came from |
|---|---|---|
| Original answers | 30 | Real output of [rag-docs-assistant](https://github.com/DaleShockley/rag-docs-assistant) (`claude-sonnet-4-5`, header-aware chunking, top-5 retrieval) |
| Seeded flaws | 17 | A copy of an original answer with exactly one deliberate defect |

## Questions (`questions.json`)

- **q01–q15**: the retrieval eval set from rag-docs-assistant
- **q16–q26**: new answerable questions, spread across all five docs
- **q27–q30**: questions the docs *can't* answer (CORS, databases, background tasks, production workers). The right answer is to say so.

## Seeded flaws (`flaw_plan.json`)

| Flaw | Count | What changed | Which criterion should fail |
|---|---|---|---|
| `fabricated_detail` | 4 | One plausible claim added that the excerpts don't support | Faithful |
| `contradiction` | 3 | One fact flipped to contradict the excerpts | Faithful |
| `unanswerable_hallucination` | 3 | An honest "the docs don't cover this" replaced with a confident made-up answer | Faithful |
| `wrong_citation` | 3 | Answer untouched, Sources line swapped to a doc that doesn't hold the answer (done in code) | Cited correctly |
| `off_topic` | 2 | Answers a related question instead of the one asked | Relevant |
| `incomplete` | 2 | The key part of the answer removed; nothing false added | Relevant (arguably) |

Everything except `wrong_citation` was written by `claude-sonnet-5` (`src/build_answer_set.py`). Each record's `flaw_note` says what was changed. I checked all 17 by hand to confirm the flaw is there.

`seeded_flaw` is what we *tried* to inject. **It is not the ground truth.** The Phase 2 human labels are. The labeling step should hide `seeded_flaw` and `flaw_note` so labels stay blind.

## Things worth knowing before labeling

- **Real failures, not seeded:** q04, q17 and q18 are answerable from the docs, but the retriever didn't surface the right section, so the assistant said it didn't have enough information. These answers are *faithful* to what was retrieved but don't help the user. q04 is the same question the rag-docs-assistant retrieval eval flagged.
- **True but unsupported:** the fabricated detail in `q01-fabricated_detail` (auto-reload in `fastapi dev`) is true of real FastAPI, just not stated in the excerpts. A judge that relies on its own knowledge instead of the evidence will wrongly pass it.
- **Paired records:** every flawed answer shares its question and retrieved chunks with an original, so the judge can be compared on the same evidence with and without the defect.

## Record fields

`id`, `question_id`, `question`, `expected_docs`, `answer`, `cited_sources` (parsed from the answer's own Sources line), `retrieved` (the chunks the answer was grounded on), `generator_model`, `chunking`, `variant` (`original`/`flawed`), `seeded_flaw`, `flaw_note`.

## Rebuilding

```bash
# in rag-docs-assistant: regenerate the original answers (~30 API calls)
python -m src.export_answers ../grounded-answer-judge/data/questions.json ../grounded-answer-judge/data/rag_answers.jsonl

# in grounded-answer-judge: inject the planned flaws (~14 API calls)
python -m src.build_answer_set
```

Model output varies between runs, so a rebuild gives a similar but not identical set.
