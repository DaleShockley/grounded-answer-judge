# Grading Rubric

How every answer in `data/answers.jsonl` is graded, by a human or by the judge. Three criteria, each graded **independently**: a correct answer with the wrong citation is *faithful: pass, relevant: pass, cited correctly: fail*.

Grade against the **retrieved excerpts** shown with the answer, not against the full docs or what you know about FastAPI.

---

## 1. Faithful

**Is every claim in the answer supported by the retrieved excerpts?**

| Pass | Fail |
|---|---|
| Every claim can be found in, or directly follows from, the excerpts | Any claim goes beyond or contradicts the excerpts |
| The answer says the excerpts don't cover the question (that's a claim about the excerpts, and it's true) | A claim that's **true in real life but not in the excerpts** (e.g. `q01-fabricated_detail`: "`fastapi dev` auto-reloads") |
| | A **hedged** unsupported claim ("it appears you would need to import `BaseModel` from Pydantic", q10). Hedging doesn't make it supported. |

Tip: read the answer one sentence at a time and find each sentence in the excerpts.

## 2. Relevant

**Does the answer actually answer the question that was asked?**

| Pass | Fail |
|---|---|
| Addresses the question directly and covers what it specifically asks | Answers a different, related question (`off_topic`) |
| Honestly says the excerpts don't cover it, **and they really don't** | Leaves out something the question specifically asks for (`incomplete`, e.g. q12 names no HTTP methods) |
| | Says the excerpts don't cover it **when they do** |

Relevance is judged against the excerpts: if retrieval missed the right section, an honest "the excerpts don't cover this" **passes**. That's a retrieval failure, not an answer failure, and it's tracked separately (see q04, q10, q17, q18 in `data/README.md`).

## 3. Cited correctly

**Does the Sources line name the doc that holds the main answer?**

| Pass | Fail | n.a. |
|---|---|---|
| The doc holding the **core answer** is cited | The doc holding the core answer is **not** cited | The answer cites nothing |
| An extra cited doc, or an uncited doc behind a minor point, doesn't change this | The only cited doc(s) don't contain the answer (`wrong_citation`) | The answer declines to answer, even if it names a doc anyway (e.g. q30: "first-steps.md (only shows development server usage)") |

Use the `[Source: ...]` tags on the excerpts to see which doc each passage came from.

---

## Worked examples

| Answer | Faithful | Relevant | Cited | Why |
|---|---|---|---|---|
| `q05-wrong_citation` | pass | pass | **fail** | Answer is correct and complete; cites handling-errors.md, but the answer is in path-params.md |
| `q01-fabricated_detail` | **fail** | pass | pass | "Auto-reload" is true of FastAPI but not in the excerpts |
| `q09-contradiction` | **fail** | pass | pass | Says `None` makes a parameter *required*; the excerpt says the opposite |
| `q08-off_topic` | pass | **fail** | pass | Explains what query parameters are; never says how to make one optional |
| `q27-original` | pass | pass | n.a. | Correctly says the excerpts don't cover CORS |
| `q27-unanswerable_hallucination` | **fail** | pass | **fail** | Confident CORS tutorial with nothing in the excerpts behind it, cited to first-steps.md |

## Grading notes

- Write a one-line reason for every answer. Disagreements with the judge are settled by comparing reasons.
- When unsure, pick the stricter grade and say why in the reason.
- These rules were set on 2026-09-25, after the first labeling pass (see `LESSONS_LEARNED.md`). The judge prompt from v2 on follows them.
