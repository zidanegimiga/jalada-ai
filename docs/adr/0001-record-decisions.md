# 0001. Record architecture decisions

Status: Accepted
Date: 2026-10-09

## Context
Zidane reviews every line and wants a clear record of why each choice was made. Decisions made in chat or in code comments get lost.

## Decision
Every choice of library, service, data store or design pattern gets a short decision record in this folder, using `0000-template.md`, before it lands in code.

## Consequences
- A little writing before each decision.
- Anyone, including Claude Code in a new session, can see why things are the way they are.
- The early scaffolding in `app/` is not decided until a record confirms it.
