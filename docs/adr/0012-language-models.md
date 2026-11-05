# 0012. Language models behind a port: Ollama and Gemini

Status: Accepted
Date: 2026-11-05

## Context
The extractor and classifier use a language model when rules cannot cope, including reading receipt photos. Cost should be zero while building. Real users' data is personal financial data under the Data Protection Act.

## Options considered
1. **Ollama running locally.** Free and private, but too heavy for free hosting, and small local models are weaker at reading images.
2. **Google Gemini free tier.** Free, good with images and structured output, but Google may use free-tier prompts to improve its products.
3. **Paid APIs (Gemini paid tier, Anthropic Claude, OpenAI).** Terms exclude training on API data, but they cost money per call.

## Decision
A `LanguageModel` port with one method: answer in JSON that matches a given schema, from text or a photo. The pipeline owns the prompts and schemas for extracting and classifying, so they are the same for every provider. Adapters for Ollama and Gemini first, both over plain HTTP with httpx2 and no provider SDK. The adapter is chosen in settings. Ollama runs as an optional docker compose profile. Every call records tokens, cost and duration.

Free tiers and local models only ever see invented data, in development and evaluations. Real users' evidence goes only to a provider whose terms exclude training on it.

## Consequences
- Switching providers is one adapter and one setting.
- The evaluation suite can compare providers on the same fixtures.
- Before launch, a paid adapter is needed, which brings a running cost per user.
- The rule is enforced at startup: in production, settings refuse any model provider unless `JALADA_MODEL_ALLOWED_FOR_REAL_DATA` is true.
- Model answers are untrusted. Amounts must be text that parses as shillings, dates must be real dates, categories must exist and fit the direction, and the evidence text is sent as data with instructions to ignore anything written inside it.
