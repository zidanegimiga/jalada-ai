"""Run the Telegram bot.

jalada-telegram poll          read messages by long polling (local work, no public address)
jalada-telegram set-webhook   tell Telegram to call JALADA_PUBLIC_URL/v1/telegram/webhook
"""

import logging
import signal
import sys
import threading

from jalada.adapters.channels.telegram_bot import ChatFailed, TelegramBot
from jalada.application.telegram_capture import TelegramCapture
from jalada.composition import build_services, build_telegram_bot
from jalada.config.logging import configure_logging
from jalada.config.settings import load_settings

logger = logging.getLogger("jalada.telegram")


def poll(bot: TelegramBot, capture: TelegramCapture, stop: threading.Event) -> None:
    offset = 0
    while not stop.is_set():
        try:
            updates = bot.updates(offset, wait_seconds=25)
        except ChatFailed as error:
            logger.warning("polling failed with %s", error)
            stop.wait(5)
            continue
        for update in updates:
            update_id = update.get("update_id")
            offset = update_id + 1 if isinstance(update_id, int) else offset
            capture.handle(update)


def main() -> None:
    settings = load_settings()
    configure_logging(settings.log_level, settings.json_logs)
    bot = build_telegram_bot(settings)
    capture = build_services(settings).telegram_capture
    if bot is None or capture is None:
        sys.exit("Set JALADA_TELEGRAM_BOT_TOKEN and JALADA_TELEGRAM_BOT_USERNAME first.")
    command = sys.argv[1:2]
    if command == ["set-webhook"]:
        if settings.telegram_webhook_secret is None:
            sys.exit("Set JALADA_TELEGRAM_WEBHOOK_SECRET first.")
        url = f"{settings.public_url}/v1/telegram/webhook"
        bot.set_webhook(url, settings.telegram_webhook_secret.get_secret_value())
        print(f"Telegram will now call {url}")
    elif command == ["poll"]:
        stop = threading.Event()
        for signal_number in (signal.SIGINT, signal.SIGTERM):
            signal.signal(signal_number, lambda *_: stop.set())
        logger.info("polling Telegram for messages")
        poll(bot, capture, stop)
    else:
        sys.exit(__doc__)
