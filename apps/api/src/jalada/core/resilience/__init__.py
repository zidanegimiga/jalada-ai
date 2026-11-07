"""Calling outside providers reliably: typed failures, retries with backoff, a circuit
breaker, and a chain that falls back from one provider to the next. Nothing here knows
what the providers are: language models, OCR engines, email or anything else."""
