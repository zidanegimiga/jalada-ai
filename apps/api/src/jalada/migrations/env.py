from alembic import context
from sqlalchemy import create_engine

from jalada.core.database.base import Base
from jalada.tables import ALL_TABLES  # noqa: F401  every table must be imported to be seen

database_url = context.config.attributes["database_url"]
engine = create_engine(database_url)

with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
