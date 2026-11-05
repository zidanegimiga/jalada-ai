import logging

# These libraries log every request address at INFO. Telegram puts the bot token in the
# address, so their request lines must never be written.
QUIET_LIBRARIES = ("httpx", "httpx2", "httpcore", "httpcore2")


def configure_logging(level: str) -> None:
    logging.basicConfig(level=level)
    for name in QUIET_LIBRARIES:
        logging.getLogger(name).setLevel(logging.WARNING)
