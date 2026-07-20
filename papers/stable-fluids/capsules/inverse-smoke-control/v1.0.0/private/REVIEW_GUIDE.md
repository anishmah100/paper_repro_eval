# Review guide: Inverse Smoke-Control Research Challenge

Review the evaluator-generated canonical artifacts before the candidate-selected demo.

- Does the implementation reproduce the core source mechanism?
- Does the quantitative score agree with what the replay visibly shows?
- Are the hardest successful and first failing levels both represented?
- Could the candidate be exploiting the visible cases, renderer, learned model, or score proxy?
- Are invalid states, crashes, timeouts, or cherry-picked seeds hidden by the report?
- Are comparisons made under identical evaluator-generated conditions?
- Does REPORT.md distinguish measured evidence from interpretation?
- Is the result useful to learn from even if it loses?

Primary metric: Compact smoke target-match quality. Scores within the declared tolerance remain tied.
Record qualitative conclusions in NOTES.md; do not manufacture an LLM-judge score.
