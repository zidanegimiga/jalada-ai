# Pipeline evaluations

Each file in `fixtures/` is one invented piece of evidence and the result the pipeline should give: its kind, the outcome (proposed, needs review or duplicate), the fields it should extract, and the category it should choose. Nothing here is real data.

`run_evals.py` runs every fixture through the pipeline and scores:

- **extraction**: the expected fields came out exactly, or nothing came out when nothing should.
- **classification**: the expected category and purpose, or unsure when no rule or past choice applies.
- **verifier rejections**: fixtures with broken fields (a future date, tax that does not add up) were rejected.

CI fails if extraction drops below 90%, classification below 80%, or verifier rejections below 95%.

To add a fixture, copy a similar file, give it the next number, change the text and the expected result, and run `uv run python evals/run_evals.py`.
