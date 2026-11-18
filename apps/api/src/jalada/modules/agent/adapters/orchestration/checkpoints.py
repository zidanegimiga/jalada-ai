"""Where LangGraph keeps a turn while it runs, in the app's own Postgres.

Its tables live in their own schema, so Alembic, which manages the app's tables, never sees
them. LangGraph creates and upgrades them itself.
"""

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import Connection, sql
from psycopg.rows import DictRow, dict_row
from psycopg_pool import ConnectionPool

SCHEMA = "assistant_turns"


def postgres_checkpoints(database_url: str, schema: str = SCHEMA) -> PostgresSaver:
    """Creates the schema and tables when missing. Call once, when the app starts."""
    conninfo = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    pool = ConnectionPool(
        conninfo,
        connection_class=Connection[DictRow],
        # Free hosting allows few connections: none are held while nobody is asking.
        min_size=0,
        max_size=2,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
            "options": f"-c search_path={schema}",
        },
        open=True,
    )
    with pool.connection() as connection:
        connection.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema)))
    saver = PostgresSaver(pool)
    saver.setup()
    return saver
