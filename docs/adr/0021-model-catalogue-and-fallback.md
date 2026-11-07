# 0021. Model catalogue, provider registry and fallback chain

Status: Accepted
Date: 2026-11-07
Builds on: 0012 (models behind a port; free tiers only for invented data)

## Context
One model was chosen in settings with an `if` per provider, so adding a provider meant editing the builder, and any failure (a rate limit, an outage, an answer in the wrong shape, an input too large) sent the evidence straight to manual review. Model names and prices also change often: Google retires `gemini-2.5-flash` on 1 December 2026.

## Decision
Four patterns, each where it pays for itself:

- **Adapter with a registry (factory).** Every provider is an adapter behind the `LanguageModel` port and registers itself by name with `@provider("gemini")`. The builder asks the registry, so it never changes when a provider is added. Three adapters exist: `gemini`, `ollama`, and `openai_compatible`, which reaches any provider speaking the OpenAI chat completions API (OpenAI, OpenRouter, Groq, Together, DeepSeek, Mistral, vLLM) through settings alone.
- **A catalogue of models as data.** `catalogue.toml` describes each model: its provider, the provider's id, whether it reads photos, its context window, its timeout and its prices with the date they were checked. More can be added through `JALADA_EXTRA_MODELS`. Accounts (keys and addresses) are separate and secret: `JALADA_MODEL_PROVIDERS`. Which models run, in which order, is `JALADA_MODEL_CHAIN`. Adding or swapping a model is a settings change.
- **Chain of responsibility.** `ModelChain` is itself a `LanguageModel`, so the pipeline does not know how many models there are. It is built on `FallbackChain` in `core/resilience`, which knows nothing about models and is meant for any provider: OCR, email, eTIMS, Docket. Failures are typed (`FailureKind`): timeouts, rate limits and outages are retried on the same model with exponential backoff and jitter, honouring the wait a provider asks for; wrong output, input too large, refusals and bad settings move on to the next model. A circuit breaker skips a model that keeps failing for a minute, and a misconfigured one at once.
- **Strategy.** Which models may take a call is a `Selection`; the default, `ByCapability`, sends photos only to models that read them and skips models whose context window is too small. The retry policy is also a swappable value.

Answers are checked against the schema they were asked for before they are accepted, so a wrong answer falls through to the next model instead of reaching the ledger. Every attempt, failed ones included, is recorded on the pipeline step with the model, the outcome and the time taken; when every model fails, the step says which failed and why. Provider messages are never kept, because they can repeat the evidence.

## Consequences
- A new model of a known kind is one catalogue entry or one `JALADA_EXTRA_MODELS` entry. A new kind of provider is one adapter module.
- The data rule from 0012 is unchanged: in production the app does not start with a model unless `JALADA_MODEL_ALLOWED_FOR_REAL_DATA` is true, which means every model in the chain is on terms that exclude training. Gemini's free tier does not qualify; its paid tier does.
- Prices in the catalogue go stale; each entry carries the date it was checked.
- Settings replaced: `JALADA_MODEL_PROVIDER`, `JALADA_MODEL_NAME`, `JALADA_GEMINI_API_KEY`, `JALADA_OLLAMA_URL`, `JALADA_MODEL_INPUT_PRICE` and `JALADA_MODEL_OUTPUT_PRICE`.
