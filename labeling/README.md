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
