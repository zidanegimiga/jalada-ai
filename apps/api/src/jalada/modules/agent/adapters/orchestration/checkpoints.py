"""Where LangGraph keeps a turn while it runs, in the app's own Postgres.

LangGraph creates and upgrades its four tables (checkpoints, checkpoint_blobs,
checkpoint_writes and checkpoint_migrations) itself. They hold a turn only while it runs.

Pooled connections, such as Neon's, run each statement on whichever server connection is
free and refuse startup options, so a schema cannot be chosen for them per connection. In
production the tables therefore sit beside the app's own. A separate schema is only for
direct connections, such as the tests'.
"""

from typing import Any

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import Connection, sql
from psycopg.rows import DictRow, dict_row
from psycopg_pool import ConnectionPool


def connection_settings(schema: str | None) -> dict[str, Any]:
    """How each checkpoint connection is opened. A schema is only set when one is asked for,
    since a pooler refuses the startup option that sets it."""
    settings: dict[str, Any] = {
        "autocommit": True,
        # Poolers cannot keep prepared statements between transactions.
        "prepare_threshold": 0,
        "row_factory": dict_row,
    }
    if schema:
        settings["options"] = f"-c search_path={schema}"
    return settings


def postgres_checkpoints(database_url: str, schema: str | None = None) -> PostgresSaver:
    """Creates the tables when missing. Call once, when the app starts."""
    conninfo = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    pool = ConnectionPool(
        conninfo,
        connection_class=Connection[DictRow],
        # Free hosting allows few connections: none are held while nobody is asking.
        min_size=0,
        max_size=2,
        kwargs=connection_settings(schema),
        open=True,
    )
    if schema:
        with pool.connection() as connection:
            connection.execute(
                sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema))
            )
    saver = PostgresSaver(pool)
    saver.setup()
    return saver
