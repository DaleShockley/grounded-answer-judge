# Labeling

A small, self-contained page for grading `data/answers.jsonl` by hand. These labels are the ground truth the judge gets measured against.

```bash
python -m src.make_labeling_page   # writes labeling/label.html (not committed; it's generated)
```

Open `labeling/label.html` in a browser. No server is needed.

- **Blind by design.** The page never shows `seeded_flaw`, `flaw_note`, `variant` or the record id, and shuffles the order (fixed seed) so an original and its flawed copy are never back to back.
- **Three pass/fail calls per answer:** faithful, relevant, cited correctly (the last one also allows *n.a.*), plus a one-line reason.
- **Progress saves in the browser as you go.** It's per browser and per file, so export when you finish a session. **Import** restores from an exported file.
- **Export labels** downloads `human_labels.jsonl` (one line per answer: `id`, `faithful`, `relevant`, `cited_correctly`, `note`, `labeled_at`). Save it as `data/human_labels.jsonl`.

Keyboard: `1`/`2` faithful, `3`/`4` relevant, `5`/`6`/`7` cited (pass/fail/n.a.), `←`/`→` to move.

## Review: settling disagreements with the judge

```bash
python -m src.make_review_page   # writes labeling/review.html from human_labels.jsonl + the judge run
```

After a judge run, open `labeling/review.html`. It shows only answers where the first-pass label and the judge disagree on at least one criterion, with both grades and the judge's reasoning side by side, plus the matching rule from `RUBRIC.md`. Pick the final grade for each criterion and write a one-line reason.

- **Not blind to the judge, on purpose.** This is adjudication: deciding which grade the rubric supports. You can overrule the judge whenever it's wrong. Seeded-flaw fields stay hidden.
- **Export reviewed labels** downloads `reviewed_labels.jsonl` with every answer: the reviewed ones plus the undisputed ones carried over from the first pass. Save it as `data/reviewed_labels.jsonl`. `data/human_labels.jsonl` is never changed.
- Score against it with `python -m eval.score_agreement <judge run> --labels data/reviewed_labels.jsonl`.
- **Limitation:** answers where the first pass and the judge *agree* aren't reviewed, so a mistake they share stays in.
