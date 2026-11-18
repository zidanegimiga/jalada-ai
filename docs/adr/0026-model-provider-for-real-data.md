# 0026. A model provider for real users' data

Status: Proposed. Accepted once the photo and assistant evals have been run with paid keys and the steps under "Before switching on" are done.
Date: 2026-11-18
Builds on: 0012 (free tiers only for invented data), 0021 (catalogue and fallback), 0025 (the assistant)

## Context
Production has no model. Photos are read by Tesseract alone, so a blurry receipt ends in "type it in yourself", and the assistant cannot be switched on. Decision 0012 allows real users' records only on a provider whose terms exclude training on them, and the app refuses to start in production with a model until `JALADA_MODEL_ALLOWED_FOR_REAL_DATA` is true.

Two things have to be settled: which provider, and what the Data Protection Act needs before records leave Kenya.

## What the providers' terms say (checked 18 November 2026)
- **Google Gemini API, paid.** Prompts and responses on paid services are not used to improve Google's products. Once a project has an active billing account, all its Gemini API and AI Studio use counts as paid for this purpose. Projects with billing keep logs for up to 55 days by default; logging can be turned off for the project, and logs are only used for improvement if they are shared as a dataset or as feedback. A "Contributor Tier" trades up to 50% off for training use on select models; it is invite-only and has to be turned on. ([logs policy](https://aistudio.google.com/docs/logs-policy), [additional terms](https://ai.google.dev/terms))
- **OpenAI API.** Not used for training unless the customer opts in. Inputs and outputs can be kept up to 30 days for abuse monitoring. Zero data retention is available to approved customers. ([zero data retention](https://openai.com/index/offering-zero-data-retention-for-frontier-models))
- **Anthropic API.** The commercial terms say Anthropic may not train models on customer content. API inputs and outputs are deleted within 30 days by default, with zero retention by agreement. ([commercial terms](https://www.anthropic.com/legal/commercial-terms))

All three meet the rule in 0012. None offers processing in Kenya.

## What the Data Protection Act asks (not legal advice)
- Sending records to a provider's servers abroad is a transfer out of Kenya under Part VI. Section 48 lists the grounds; section 49 asks for appropriate safeguards and, for sensitive personal data, the person's consent.
- Section 2 counts "property details" as sensitive personal data. M-Pesa records and receipts may fall under it, so the safe reading is to treat them as sensitive and ask for consent.
- The 2021 General Regulations and the Commissioner's guidance on cross-border transfers expect the safeguards to be written down, such as the provider's data processing terms, and shown to the Commissioner on request.

## Decision
**Primary: Gemini on a paid, billed project.** It is already built and priced in the catalogue, it reads photos, and its flash-lite models are cheap enough for one call per receipt. `gemini-3.5-flash-lite` first, as in development. The evals confirm or change this before it is accepted.

**Fallback: one model from a second provider**, so an outage at Google does not send every photo to manual review. OpenAI or Anthropic, whichever scores better on `evals/run_photo_evals.py` and `evals/agent/run_agent_evals.py --model`. It goes in through `JALADA_EXTRA_MODELS` and the `openai_compatible` adapter, with no code.

## Before switching on
1. Create the Google Cloud project with billing on; turn logging off on the Logs page; never join the Contributor Tier. Accept Google's data processing terms for the project.
2. Run the photo and assistant evals with the paid keys for the primary and both fallback candidates, and record the scores, cost and time in this file.
3. Ask for consent at sign-up, in plain words: which provider reads receipts and questions, that it is outside Kenya, and that it does not train on them. Existing users are asked before their records are sent.
4. Name the provider and the transfer in the privacy notice, and keep a record of the safeguards for the Commissioner.
5. Have a Kenyan data protection practitioner check steps 3 and 4.
6. Then set `JALADA_MODEL_CHAIN` (and the assistant's chains), `JALADA_MODEL_PROVIDERS`, and `JALADA_MODEL_ALLOWED_FOR_REAL_DATA=true` on the host.

## Consequences
- Each photo or question costs money; the evals print what each model costs, and the per-run budget limits it.
- The data rule stays enforced at startup. Setting `JALADA_MODEL_ALLOWED_FOR_REAL_DATA` is the deliberate last step, after the checklist.
- Terms change: re-check them when renewing this decision, and at least yearly.
