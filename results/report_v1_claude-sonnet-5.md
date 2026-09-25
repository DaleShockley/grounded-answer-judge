# Judge report: `judge_v1_claude-sonnet-5.jsonl`

Model `claude-sonnet-5`, prompt `v1`, 47 answers graded, total cost $0.330, median latency 3.2s.

## Agreement with human labels (`human_labels.jsonl`)

47 answers labeled by both.

| Criterion | Agreement | Cohen's kappa | human→judge counts |
|---|---|---|---|
| faithful | 68% | 0.19 | fail->fail: 5, fail->pass: 9, pass->fail: 6, pass->pass: 27 |
| relevant | 72% | 0.17 | fail->fail: 3, fail->pass: 10, pass->fail: 3, pass->pass: 31 |
| cited_correctly | 57% | 0.14 | fail->fail: 5, fail->na: 3, fail->pass: 8, pass->fail: 7, pass->na: 2, pass->pass: 22 |

### Disagreements (48)

- **q01-fabricated_detail** · faithful: human **pass**, judge **fail**
  - Human: _(no note)_
  - Judge: Most claims (command, server URL, docs URL) match first-steps.md excerpt, but the claim about auto-reload being enabled by default is not present anywhere in the excerpts.
- **q04-original** · faithful: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The answer only states that the excerpts don't explain the validation mechanism, and references the singular types mention from body.md which is accurate; no unsupported claims are made.
- **q07-fabricated_detail** · faithful: human **pass**, judge **fail**
  - Human: - `enabled`
  - Judge: The answer adds 'enabled' as a truthy value, which is not present in the excerpt that lists only '1', 'True', 'true', 'on', and 'yes'.
- **q07-original** · faithful: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The answer lists the exact values (1, True, true, on, yes) with any-case variation and states other values become False, matching the excerpt verbatim.
- **q09-contradiction** · faithful: human **pass**, judge **fail**
  - Human: _(no note)_
  - Judge: The excerpt explicitly states that setting a default value to None makes a parameter OPTIONAL, and that to make a parameter REQUIRED you should NOT declare any default value. The answer inverts this, claiming that setting default=None makes a parameter required, directly contradicting the source.
- **q12-incomplete** · faithful: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The excerpt states GET body behavior is undefined, but the answer omits the actual recommended methods (POST, PUT, DELETE, PATCH) and instead adds an inference 'GET should be avoided' which is a reasonable paraphrase but the answer fails to state the recommended methods at all, which is the core question.
- **q13-fabricated_detail** · faithful: human **pass**, judge **fail**
  - Human: _(no note)_
  - Judge: The answer adds an unsupported claim that omitting status_code makes HTTPException default to 400, which is not stated anywhere in the retrieved excerpts.
- **q17-original** · faithful: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The answer only states that the excerpts lack information on return types, which is an accurate reflection of the provided excerpts and makes no unsupported claims.
- **q18-original** · faithful: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The answer only states what is explicitly in the excerpts, noting the validation process applies to path parameters too, and does not claim specific behavior for float-to-int mismatches beyond what's supported.
- **q19-fabricated_detail** · faithful: human **pass**, judge **fail**
  - Human: _(no note)_
  - Judge: The claim about FastAPI automatically prepending a leading slash before matching the route is not present anywhere in the excerpts; the excerpts only describe the :path convertor syntax.
- **q21-contradiction** · faithful: human **pass**, judge **fail**
  - Human: _(no note)_
  - Judge: The excerpt says inheriting from str lets API docs know values must be of type 'string', but the answer misquotes it as 'integer', which contradicts the source.
- **q22-off_topic** · faithful: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The answer's claims about path operation ordering and route matching precedence are directly supported by the 'Order matters' excerpt from path-params.md.
- **q25-original** · faithful: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The answer states the two facts directly from the excerpt: 'Use None to make it just optional' and 'When a model attribute has a default value, it is not required; otherwise, it is required.' The added examples like Optional[str] or str | None are reasonable elaborations consistent with the excerpt's mention of using None, though not explicitly stated with that syntax.
- **q28-original** · faithful: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The answer only states that the excerpts lack information on the topic and summarizes what they do cover, without introducing unsupported claims about the library.
- **q30-original** · faithful: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The answer only states what the excerpts contain and explicitly says they lack production/worker info, which matches the excerpts provided.
- **q03-contradiction** · relevant: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The answer addresses the question about class inheritance, though with incorrect content.
- **q04-original** · relevant: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The question asks how FastAPI validates int path parameters, and the answer correctly notes the excerpts don't contain this information, which is a relevant response given the limited context.
- **q07-original** · relevant: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The question asks what values are accepted as truthy for bool query params, and the answer directly lists them.
- **q08-off_topic** · relevant: human **pass**, judge **fail**
  - Human: _(no note)_
  - Judge: The question specifically asks how to make a query parameter optional with default None, but the answer only explains general query parameter concepts and type conversion, never addressing the 'Optional parameters' section content about setting default to None.
- **q09-contradiction** · relevant: human **pass**, judge **fail**
  - Human: _(no note)_
  - Judge: The question asks how to make a parameter required, but the answer describes the exact opposite mechanism (which actually makes it optional per the source), so it fails to correctly answer what was asked.
- **q10-original** · relevant: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The answer directly addresses the question about what to import for a request body model, explaining what is and isn't covered in the excerpts.
- **q17-original** · relevant: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The answer addresses the question by explaining that the retrieved excerpts do not cover return value types, which is a direct (if negative) response to the question.
- **q23-incomplete** · relevant: human **pass**, judge **fail**
  - Human: _(no note)_
  - Judge: The question specifically asks how FastAPI distinguishes between path, query, and body parameters, but the answer lumps query and body together as 'either a query parameter or a request body' without explaining the actual distinguishing rule (singular type vs Pydantic model) that is present in the body.md excerpt, leaving the core of the question unanswered.
- **q27-unanswerable_hallucination** · relevant: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The answer directly addresses how to enable CORS for cross-domain frontend access, which is exactly what was asked.
- **q28-original** · relevant: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The question asks how to connect FastAPI to PostgreSQL via SQLAlchemy, and the answer correctly identifies that the excerpts don't cover this, which is a relevant response given the lack of information.
- **q28-unanswerable_hallucination** · relevant: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The answer directly addresses the question of connecting FastAPI to PostgreSQL via SQLAlchemy with a step-by-step guide.
- **q30-original** · relevant: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The question asks how to run FastAPI in production with multiple workers, and the answer correctly identifies that the excerpts don't cover this, directly addressing the question's answerability.
- **q30-unanswerable_hallucination** · relevant: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The answer directly addresses the question of running FastAPI in production with multiple workers, providing concrete commands and strategies.
- **q05-wrong_citation** · cited_correctly: human **pass**, judge **fail**
  - Human: _(no note)_
  - Judge: The answer relies entirely on content from path-params.md but cites handling-errors.md, which is not among the retrieved excerpts and doesn't contain this information.
- **q07-fabricated_detail** · cited_correctly: human **fail**, judge **pass**
  - Human: - `enabled`
  - Judge: The cited file query-params.md does contain the relevant excerpt about bool conversion, though the answer includes an extra unsupported value.
- **q07-original** · cited_correctly: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The information comes directly from the query-params.md excerpt about type conversion, which is the cited source.
- **q09-contradiction** · cited_correctly: human **pass**, judge **fail**
  - Human: _(no note)_
  - Judge: query-params.md does contain the relevant section on required parameters, but the answer's core claim (that None makes it required) is not what that file says—it says the opposite—so the file does not support the information relied upon.
- **q10-original** · cited_correctly: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The claim about inheriting from BaseModel and using Pydantic models originates from body.md, which is the source cited.
- **q11-original** · cited_correctly: human **pass**, judge **fail**
  - Human: _(no note)_
  - Judge: The 'no specific order' claim comes from query-params.md ('Multiple path and query parameters'), but only body.md is cited, missing a source for that part of the answer.
- **q12-incomplete** · cited_correctly: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The claim about GET's undefined behavior is indeed found in body.md, so the citation is accurate for what is stated, even though the answer is incomplete.
- **q16-wrong_citation** · cited_correctly: human **pass**, judge **fail**
  - Human: _(no note)_
  - Judge: The information about the openapi.json endpoint comes from first-steps.md, but the answer cites body.md instead, which only discusses JSON Schemas being part of the OpenAPI schema, not the raw schema location.
- **q17-original** · cited_correctly: human **fail**, judge **na**
  - Human: _(no note)_
  - Judge: The answer cites no source file, consistent with stating it cannot answer, so citation grading is not applicable.
- **q18-original** · cited_correctly: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The answer cites query-params.md, which does contain the quoted text about validation processes applying to path parameters, so the citation matches the content relied upon.
- **q19-fabricated_detail** · cited_correctly: human **pass**, judge **fail**
  - Human: _(no note)_
  - Judge: The core syntax information comes from path-params.md, which is cited, but the unsupported claim about leading slash prepending is not backed by this or any source.
- **q21-contradiction** · cited_correctly: human **pass**, judge **fail**
  - Human: _(no note)_
  - Judge: The relevant information does come from path-params.md, but the answer misstates the content (string vs integer), making the citation not accurately reflect the source content.
- **q21-original** · cited_correctly: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The information used comes from the 'Create an Enum class' section of path-params.md, which is the cited source.
- **q22-off_topic** · cited_correctly: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The answer relies entirely on the 'Order matters' content, which does come from path-params.md as cited, so the citation matches the source of the information used.
- **q25-original** · cited_correctly: human **fail**, judge **pass**
  - Human: _(no note)_
  - Judge: The relevant information about optional fields and default values comes from the 'Create your data model' section, which is tagged [Source: body.md], matching the citation.
- **q26-wrong_citation** · cited_correctly: human **pass**, judge **fail**
  - Human: _(no note)_
  - Judge: The answer cites 'first-steps.md' but the actual information comes from 'handling-errors.md' as shown in the excerpts; first-steps.md is not even provided as a source.
- **q27-original** · cited_correctly: human **pass**, judge **na**
  - Human: _(no note)_
  - Judge: The answer cites no file since it states none of the excerpts are relevant, which is appropriate given the excerpts indeed lack CORS info.
- **q28-original** · cited_correctly: human **fail**, judge **na**
  - Human: _(no note)_
  - Judge: The answer cites no file, consistent with stating it cannot answer the question.
- **q29-original** · cited_correctly: human **pass**, judge **na**
  - Human: _(no note)_
  - Judge: The answer explicitly states no sources are cited since none contain relevant information, which is appropriate given the excerpts don't address background tasks.
- **q30-original** · cited_correctly: human **fail**, judge **na**
  - Human: _(no note)_
  - Judge: The answer cites first-steps.md but clarifies it only shows dev server usage, not production info; since the answer is essentially declining to answer the question, this is effectively a no-information case, though it did name a source rather than citing none.

## Seeded-flaw recall

Did the judge fail the criterion each planted flaw targets? (A sanity check, not ground truth.)

| Flaw | Targets | Caught |
|---|---|---|
| contradiction | faithful | 3/3 |
| fabricated_detail | faithful | 4/4 |
| incomplete | relevant | 2/2 |
| off_topic | relevant | 2/2 |
| unanswerable_hallucination | faithful | 3/3 |
| wrong_citation | cited_correctly | 3/3 |
| **all** | | **17/17** |

Original (unseeded) answers the judge failed on at least one criterion: 4/30 (q04-original, q10-original, q11-original, q18-original). Not necessarily false alarms: some originals are genuinely flawed (see data/README.md).
