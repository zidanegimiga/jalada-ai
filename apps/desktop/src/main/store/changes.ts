import type { Database } from "better-sqlite3-multiple-ciphers";

import type { ChangeState, LocalChange } from "@shared/records";

/** A change waiting to be sent, as the sender needs it. */
export type QueuedChange = {
  id: string;
  kind: string;
  payload: unknown;
  attempts: number;
};

type NewChange = {
  id: string;
  kind: string;
  payload: unknown;
  summary: string;
  createdAt: string;
};

/**
 * Changes made on this computer, kept in its database until the server has them (decision
 * 0029). Each keeps its id from start to end: it is the Idempotency-Key, so a change sent
 * twice after a dropped reply is applied once.
 */
export class ChangeStore {
  constructor(private readonly db: Database) {}

  add(change: NewChange): void {
    this.db
      .prepare(
        `INSERT INTO changes (id, kind, payload, summary, state, created_at)
         VALUES (?, ?, ?, ?, 'saved', ?)`,
      )
      .run(
        change.id,
        change.kind,
        JSON.stringify(change.payload),
        change.summary,
        change.createdAt,
      );
  }

  /**
   * The oldest change not yet accepted. One left "sending" was cut off by a closed app or a
   * dropped connection; it goes again with the same key.
   */
  next(): QueuedChange | null {
    const row = this.db
      .prepare(
        `SELECT id, kind, payload, attempts FROM changes
         WHERE state IN ('saved', 'sending') ORDER BY seq LIMIT 1`,
      )
      .get() as
      | { id: string; kind: string; payload: string; attempts: number }
      | undefined;
    return row ? { ...row, payload: JSON.parse(row.payload) } : null;
  }

  sending(id: string): void {
    this.db
      .prepare(
        "UPDATE changes SET state = 'sending', attempts = attempts + 1 WHERE id = ?",
      )
      .run(id);
  }

  /** Not sent this time, for a reason that passes: it waits for the next try. */
  later(id: string): void {
    this.settle(id, "saved", null, null);
  }

  confirmed(id: string, at: string): void {
    this.settle(id, "confirmed", null, at);
  }

  needsAttention(id: string, problem: string, at: string): void {
    this.settle(id, "needs_attention", problem, at);
  }

  /**
   * The person asks for a refused change to go again. It keeps its place, so it still goes
   * in the order it was made; if refused again, it is set aside again and the rest go on.
   */
  tryAgain(id: string): boolean {
    return (
      this.db
        .prepare(
          `UPDATE changes SET state = 'saved', problem = NULL, settled_at = NULL
           WHERE id = ? AND state = 'needs_attention'`,
        )
        .run(id).changes === 1
    );
  }

  /**
   * The person drops a change the server has not taken. One on its way cannot be dropped:
   * the server may already have it.
   */
  discard(id: string): boolean {
    return (
      this.db
        .prepare(
          "DELETE FROM changes WHERE id = ? AND state IN ('saved', 'needs_attention')",
        )
        .run(id).changes === 1
    );
  }

  /** Sent changes are in the ledger now; the list only keeps them for a while. */
  clearSentBefore(at: string): void {
    this.db
      .prepare(
        "DELETE FROM changes WHERE state = 'confirmed' AND settled_at < ?",
      )
      .run(at);
  }

  /** Newest first, for the window. */
  list(limit = 50): LocalChange[] {
    return this.db
      .prepare(
        `SELECT id, summary, state, problem, created_at FROM changes
         ORDER BY seq DESC LIMIT ?`,
      )
      .all(limit)
      .map(toLocalChange);
  }

  /** Changes the server does not have yet: lost if the person signs out now. */
  unsent(): number {
    return (
      this.db
        .prepare(
          "SELECT count(*) AS n FROM changes WHERE state IN ('saved', 'sending')",
        )
        .get() as { n: number }
    ).n;
  }

  private settle(
    id: string,
    state: ChangeState,
    problem: string | null,
    at: string | null,
  ): void {
    this.db
      .prepare(
        "UPDATE changes SET state = ?, problem = ?, settled_at = ? WHERE id = ?",
      )
      .run(state, problem, at, id);
  }
}

function toLocalChange(row: unknown): LocalChange {
  const r = row as {
    id: string;
    summary: string;
    state: ChangeState;
    problem: string | null;
    created_at: string;
  };
  return {
    id: r.id,
    summary: r.summary,
    state: r.state,
    problem: r.problem,
    createdAt: r.created_at,
  };
}
