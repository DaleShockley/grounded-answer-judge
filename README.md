# grounded-answer-judge
Learning project: build an AI grader for RAG answers, prove how far it can be trusted, then use it to compare Claude models on quality, cost and speed
Phase 0: Setup (~1 hr)
Create the repo with src/, data/, eval/, tests/ and CI, matching your other two projects.
Keep it decoupled: rag-docs-assistant exports answers to a JSONL file, and the judge only reads that file. That way the judge can grade any Q&A system later.

Done when: the repo exists, CI passes, and the README has a skeleton.

Phase 1: Build the answer set (~2 hrs)
Start from the 15 questions in rag-docs-assistant and add about 15 more.
Generate answers with your RAG assistant.
Add deliberately bad answers: made-up facts, wrong citations, answers that dodge the question, correct-but-incomplete answers. The judge needs real failures to catch.
Target: about 40 answers, roughly 60% good and 40% flawed.

Done when: data/answers.jsonl has about 40 records, each with the question, the retrieved chunks, the answer and the cited source.

Phase 2: Write the rubric and grade by hand (~2 hrs)
Define three pass/fail criteria. Pass/fail is easier to agree on than a 1–5 scale.
Faithful: every claim in the answer is supported by the retrieved chunks.
Relevant: it actually answers the question asked.
Cited correctly: the cited source is the one that contains the answer.
Grade all 40 answers yourself and write a one-line reason for each.

Done when: data/human_labels.jsonl and RUBRIC.md exist. This is your ground truth.

Phase 3: Judge v1 (~3 hrs)
A Claude prompt that takes the question, chunks and answer, and returns a typed pydantic verdict with a reason for each criterion.
Scoring script: how often it agrees with your grades on each criterion, plus Cohen's kappa (agreement adjusted for chance).
Error analysis: read every case where the judge disagrees with you and sort them by why.

Done when: you have a first agreement table and a list of the ways the judge fails.

Phase 4: Improve and stress-test the judge (~3 hrs)
Revise the prompt based on the Phase 3 failures, and track the score of each version.
Compare Haiku 4.5 vs Sonnet 5 as the judge: is the cheaper model good enough to grade?
Consistency check: run each case 3 times and count how often the verdict changes.
Test for known judge biases, such as rewarding longer answers or being fooled by confident tone.

Done when: you have a table of judge versions and models with their agreement, cost and consistency.

Phase 5: Compare the answer models (~2 hrs)
Run the RAG assistant with Haiku 4.5, Sonnet 5 and Opus 5.5 generating the answers.
Score all three with your best judge.
Build a table of quality, cost per 1,000 answers, and average and slowest response times.

Done when: you have the comparison table and a short "which one I'd ship and why" write-up.

Phase 6: Regression gate in CI (~1 hr)
Unit tests run on every push using fake API responses, so they need no key.
An optional real evaluation runs by manual trigger, using your API key stored as a GitHub secret. It fails if the faithfulness score drops below a set threshold.

Done when: a deliberately broken prompt makes the check fail.

Phase 7: Write-up (~2 hrs)
README: the problem, the architecture diagram, the agreement tables, the model comparison, "what surprised me," and the limitations.
Add the project to your portfolio site and link all three projects as a learning path.

Total: about 16 hours, or roughly 2–3 weekends.

You'll need: an Anthropic API key (Phases 1, 3–5; expect a few dollars in API costs), Python 3.11+, and your existing rag-docs-assistant.
