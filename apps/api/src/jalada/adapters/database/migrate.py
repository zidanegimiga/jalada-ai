"""Run database migrations.

jalada-migrate                          apply every pending migration
jalada-migrate revision "add evidence"  write a new migration from the table definitions
"""

import sys

from alembic import command
from alembic.config import Config

from jalada.config.settings import load_settings


def alembic_config(database_url: str) -> Config:
    config = Config()
    config.set_main_option("script_location", "jalada.adapters.database:migrations")
    config.attributes["database_url"] = database_url
    return config


def main(arguments: list[str] | None = None) -> None:
    arguments = sys.argv[1:] if arguments is None else arguments
    config = alembic_config(load_settings().database_url)
    if arguments[:1] == ["revision"] and len(arguments) == 2:
        command.revision(config, message=arguments[1], autogenerate=True)
    elif not arguments:
        command.upgrade(config, "head")
    else:
        sys.exit(__doc__)
