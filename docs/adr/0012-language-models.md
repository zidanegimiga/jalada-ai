# 0012. Language models behind a port: Ollama and Gemini

Status: Proposed
Date: 2026-11-05

## Context
The extractor and classifier use a language model when rules cannot cope, including reading receipt photos. Cost should be zero while building. Real users' data is personal financial data under the Data Protection Act.

## Options considered
1. **Ollama running locally.** Free and private, but too heavy for free hosting, and small local models are weaker at reading images.
2. **Google Gemini free tier.** Free, good with images and structured output, but Google may use free-tier prompts to improve its products.
3. **Paid APIs (Gemini paid tier, Anthropic Claude, OpenAI).** Terms exclude training on API data, but they cost money per call.

## Decision
A `LanguageModel` port with two methods: extract fields into a given schema from text or an image, and classify. Adapters for Ollama and Gemini first. The adapter is chosen in settings. Ollama runs as an optional docker compose profile. Every call records tokens, cost and duration.

Proposed rule, awaiting confirmation: free tiers only ever see invented data (development and evaluations). Real users' evidence goes only to a provider whose terms exclude training on it.

## Consequences
- Switching providers is one adapter and one setting.
- The evaluation suite can compare providers on the same fixtures.
- Before launch, a paid adapter is needed, which brings a running cost per user.
