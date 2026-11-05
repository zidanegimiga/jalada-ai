from alembic import context
from sqlalchemy import create_engine

from jalada.adapters.database.tables import Base

database_url = context.config.attributes["database_url"]
engine = create_engine(database_url)

with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
