# 0025. A conversational agent over a person's own records

Status: Accepted
Date: 2026-11-18
Builds on: 0012 (models behind a port; free tiers only for invented data), 0017 (observability), 0020 (feature modules), 0021 (model catalogue and fallback), 0022 (design patterns)

## Context
People want to ask about their money in their own words ("how much did I pay KPLC this quarter?", "what is still waiting for me?") and to fix entries without hunting for the right screen, on the web and in Telegram, later WhatsApp. That means a model that can look things up, plan a few steps and suggest changes.

It also means sending real financial records to a model, which raises four risks:

- a wrong number presented as fact
- a change made to the ledger that nobody asked for
- another person's records leaking through a confused or manipulated model
- instructions hidden in a receipt, PDF or M-Pesa message being obeyed

Hosting is free tier: one API process on Render, one Postgres, no room for extra services.

## Options considered
For orchestration:

1. **Our own loop on the `LanguageModel` port.** Smallest and fully typed, but checkpointing, pausing for a person and resuming would all be ours to build and maintain.
2. **PydanticAI.** Typed, with tools and streaming, but it brings its own model clients, which would bypass the chain, the catalogue, pricing and the data rule.
3. **LangGraph.** A state graph with checkpoints in Postgres, pausing for a person (`interrupt`) and resuming (`Command(resume=...)`), streaming of graph updates, and a well-known structure for agents. Heavier, and its types are looser than ours, so it has to be kept at the edge.

For conversation memory: LangGraph's Postgres checkpointer, our own tables, or a vector store. For traces: our own tables, OpenTelemetry to a free hosted backend, or self-hosted Langfuse. Langfuse 3 needs ClickHouse, Redis and S3 next to Postgres, which free hosting cannot carry.

## Decision
**LangGraph for orchestration, kept inside one adapter.** The application layer owns an `AgentRunner` port and the agent's domain types; `modules/agent/adapters/orchestration/` is the only code that imports `langgraph`, and import-linter enforces it. Swapping LangGraph out later is one adapter.

**Models stay ours.** Graph nodes call the existing `LanguageModel` port through `ModelChain`, not LangChain chat models. Each step asks for a JSON reply that matches a schema: either a tool call with typed arguments or a final answer. This works on every provider in the catalogue today, keeps fallback, retries, pricing and the data rule, and needs no native tool calling. Native tool calling can be added per provider later behind the same port.

**Tools are a registry of typed adapters over existing use cases** (`Ledger`, `EntryReview`, `TaxYearExport` and the summaries). Each tool has Pydantic arguments, and none of them takes a user id: the id comes from the session and is bound into the tool context when the run starts. Tool results are cut down to the fields the answer needs.

**The agent cannot change anything by itself.** Tools that would change data only suggest: each checks the change would work, then stores it with a summary written by the app from the records, never by the model. The turn ends with the answer and the suggestion, and the person sees a card on the web or buttons in Telegram. Confirming runs the change through the existing ledger use case, with the person as the actor in the audit trail; no model runs after the tap. Suggestions expire after 24 hours. Tax advice, filing and anything about another person are refused in code before a model is asked.

**Figures are checked in code.** Before an answer is sent, every amount and date in it must appear in that turn's tool results. If one does not, the answer is retried once with the reason and then withheld.

**Text from evidence is data.** Receipt, PDF and M-Pesa text only ever reaches the model inside tool results, marked as untrusted and never as instructions. Because tools are bound to one person and every change needs their tap, a manipulated model can at worst say something wrong to the person who uploaded the text.

**Memory.**
- LangGraph's Postgres checkpointer holds graph state while a turn runs, and is cleared when it ends. The graph does not pause for the person: a confirmed change needs nothing from the model, so ending the turn is simpler and leaves less to go wrong.
- The messages a person sees live in our own `agent_threads` and `agent_messages` tables, managed by Alembic. The last 10 messages are sent in full. Before them, the person's earlier questions are listed, shortened, without the answers; this is done in code rather than by a model, so it costs nothing, and a figure from an old answer is looked up again rather than repeated unchecked.
- Long-term memory is what the app already knows, such as counterparty categories and preferences, looked up by tools when needed rather than packed into every prompt.

**Routing by rules.** A small rule picks a fast chain for lookups and a deeper chain for multi-step questions, from `JALADA_AGENT_CHAIN_FAST` and `JALADA_AGENT_CHAIN_DEEP`, both made of catalogue names. Fast falls back to `JALADA_MODEL_CHAIN` and deep to fast. Comparisons, trends, reasons, long questions and several questions at once go deep. Each run records its route, so the cost of each shows in `agent_runs`. Answers are not streamed word by word: the figure check needs the whole answer before it is shown, and progress is streamed instead.

**Streaming over server-sent events**: `step`, `tool`, `answer`, `action` and `done`, with small payloads. Telegram and later WhatsApp are adapters behind a `Channel` port.

**Traces.** Every run and step is recorded in `agent_runs` and `agent_steps`, like pipeline steps: model, tokens, cost, time, tool and outcome. OpenTelemetry spans follow the GenAI semantic conventions and are sent to an OTLP endpoint set in settings (Langfuse Cloud's free tier, Grafana Cloud or none). Phone numbers, account numbers and M-Pesa codes are masked before anything is logged or traced.

**Evals in CI.** `evals/agent/` holds fixtures with scripted model replies, covering tool choice, refusing tax advice, resisting injected instructions and the figure check. CI fails when a score drops below its threshold.

**Off until real data may go to a model.** `JALADA_AGENT_ENABLED` is false by default. In production the app will not start with it on unless `JALADA_MODEL_ALLOWED_FOR_REAL_DATA` is true, the same rule as 0012.

## Consequences
- New dependencies: `langgraph`, `langgraph-checkpoint-postgres` and `psycopg-pool`. LangGraph creates its four checkpoint tables once when the app starts with the assistant on. They sit beside the app's own tables, because the pooled connections production uses refuse the startup option that would choose another schema; Alembic never manages them.
- LangGraph's types are looser than strict mypy wants. The adapter converts at its edge, so nothing outside it sees LangGraph types.
- A conversation costs more than one piece of evidence; each run has a step, token and cost budget and stops cleanly when it runs out.
- Conversations are personal data: they are exported and deleted with the account and expire after 90 days.
- The agent goes live for real people only after a provider whose terms exclude training is chosen (AI-09).
