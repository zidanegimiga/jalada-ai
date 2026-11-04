# Claude Code notes

The project rules live in `AGENTS.md` so that any coding agent can read them. They are imported here:

@AGENTS.md

## Claude-specific notes
- Skills in `.claude/skills/` load on demand. They are local only and Git ignores them. Check the skill list before starting work in an area.
- Do not run `git commit` yourself. Give Zidane the command, and leave out any AI co-author line.
- Use plan mode or a short numbered plan in chat before any change, and wait for approval.
