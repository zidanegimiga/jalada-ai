# 0014. Telegram bot for chat capture

Status: Accepted
Date: 2026-11-05

## Context
Users should be able to send a receipt or forward an M-Pesa message from their chat app without opening the web app.

## Options considered
1. **WhatsApp Cloud API.** Where most users already are, but it needs a verified business, and conversations are charged.
2. **SMS or USSD through Africa's Talking.** Works on basic phones, but costs per message and cannot carry photos.
3. **Telegram Bot API.** Free, takes photos, documents and forwarded text, and needs no business verification.

## Decision
A Telegram bot behind a `ChatChannel` port, receiving updates by webhook at `/v1/telegram/webhook`, verified with Telegram's secret token header. Accounts are linked with a one-time code from the web app. Calls go through httpx2, with no bot framework.

## Consequences
- Free to run, and WhatsApp, SMS and USSD can be added as other adapters on the same port later.
- Locally there is no public address for a webhook, so `jalada-telegram poll` reads the same messages by long polling and hands them to the same code.
- The bot token is part of every Telegram address, so the adapter never logs addresses and reports errors by type only.
- Telegram keeps its own copy of anything sent to the bot, which the privacy notice must say.
- Fewer Kenyan users have Telegram than WhatsApp, so the web app remains the main way in.
