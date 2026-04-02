#!/usr/bin/env python3
"""
MAXBoты Demo Bot #1 — FAQ / Support
MAX Messenger Bot API: https://dev.max.ru/

Usage:
  export MAX_BOT_TOKEN=<your_bot_token>
  python3 bot.py

The bot demonstrates:
  - Long-polling updates
  - Main menu with inline/quick-reply buttons
  - 10 FAQ topics (price, timeline, examples, MAX info, integrations, AI, ...)
  - Keyword matching for free-text input
  - Fallback to main menu for unrecognized input
"""

import os
import sys
import time
import logging
import requests

from faqs import FAQ_ENTRIES, MENU_BUTTONS, BUTTON_TO_FAQ_ID

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ─── Config ────────────────────────────────────────────────────────────────

TOKEN = os.environ.get("MAX_BOT_TOKEN")
if not TOKEN:
    sys.exit("ERROR: MAX_BOT_TOKEN environment variable is not set.\n"
             "Get a token from @MasterBot in MAX messenger, then:\n"
             "  export MAX_BOT_TOKEN=<your_token>\n"
             "  python3 bot.py")

API_BASE = "https://botapi.max.ru"
POLL_TIMEOUT = 30  # seconds for long polling

# ─── API helpers ───────────────────────────────────────────────────────────

session = requests.Session()
session.params = {"access_token": TOKEN}


def api(method: str, **kwargs) -> dict:
    """Call MAX Bot API. method = HTTP verb + path, e.g. ('GET', '/updates')."""
    verb, path = method.split(" ", 1)
    r = session.request(verb, API_BASE + path, **kwargs)
    r.raise_for_status()
    return r.json()


def get_updates(marker: int | None = None) -> dict:
    params = {"timeout": POLL_TIMEOUT}
    if marker is not None:
        params["marker"] = marker
    return api("GET /updates", params=params, timeout=POLL_TIMEOUT + 10)


def send_message(chat_id: int, text: str, buttons: list[str] | None = None) -> dict:
    payload: dict = {
        "chat_id": chat_id,
        "text": text,
        "format": "markdown",
    }
    if buttons:
        payload["attachments"] = [
            {
                "type": "inline_keyboard",
                "payload": {
                    "buttons": [[{"type": "callback", "text": b, "payload": b}] for b in buttons]
                },
            }
        ]
    return api("POST /messages", json=payload)


def answer_callback(callback_id: str) -> dict:
    return api("POST /answers", json={"callback_id": callback_id, "notification": ""})


# ─── Bot logic ─────────────────────────────────────────────────────────────

WELCOME = (
    "👋 Привет! Я демо-бот *MAXBoты* — агентства по разработке ботов для мессенджера MAX.\n\n"
    "Выберите тему или задайте вопрос в свободной форме:"
)

FALLBACK = (
    "🤔 Не нашёл ответа на ваш вопрос.\n\n"
    "Попробуйте выбрать тему из меню или напишите нам напрямую:\n"
    "hello@maxboty.ru"
)


def find_faq(text: str) -> dict | None:
    """Find a matching FAQ entry by keyword in user message text."""
    t = text.lower().strip()
    for entry in FAQ_ENTRIES:
        for trigger in entry["triggers"]:
            if trigger in t:
                return entry
    return None


def faq_by_id(faq_id: str) -> dict | None:
    for entry in FAQ_ENTRIES:
        if entry["id"] == faq_id:
            return entry
    return None


def handle_text(chat_id: int, text: str) -> None:
    text = text.strip()

    # Main menu command
    if text in ("/start", "/menu", "Главное меню", "главное меню"):
        send_message(chat_id, WELCOME, MENU_BUTTONS)
        return

    # Button mapped to FAQ ID
    faq_id = BUTTON_TO_FAQ_ID.get(text)
    if faq_id:
        faq = faq_by_id(faq_id)
        if faq:
            send_message(chat_id, faq["answer"], faq.get("buttons"))
            return

    # Free-text keyword search
    faq = find_faq(text)
    if faq:
        send_message(chat_id, faq["answer"], faq.get("buttons"))
        return

    # Fallback
    send_message(chat_id, FALLBACK, MENU_BUTTONS)


def process_update(update: dict) -> None:
    update_type = update.get("update_type")

    if update_type == "bot_started":
        chat_id = update["chat_id"]
        log.info("bot_started: chat_id=%s", chat_id)
        send_message(chat_id, WELCOME, MENU_BUTTONS)

    elif update_type == "message_created":
        msg = update.get("message", {})
        chat_id = update.get("chat_id") or msg.get("recipient", {}).get("chat_id")
        text = msg.get("body", {}).get("text", "")
        log.info("message_created: chat_id=%s text=%r", chat_id, text[:80])
        if chat_id and text:
            handle_text(chat_id, text)

    elif update_type == "message_callback":
        callback = update.get("callback", {})
        payload = callback.get("payload", "")
        callback_id = callback.get("callback_id")
        chat_id = update.get("chat_id") or callback.get("chat_id")
        log.info("message_callback: chat_id=%s payload=%r", chat_id, payload)
        if callback_id:
            answer_callback(callback_id)
        if chat_id and payload:
            handle_text(chat_id, payload)


# ─── Main loop ─────────────────────────────────────────────────────────────

def main() -> None:
    log.info("MAXBoты Demo Bot starting (long polling)...")
    marker = None

    while True:
        try:
            data = get_updates(marker)
            updates = data.get("updates", [])
            if data.get("marker"):
                marker = data["marker"]

            for update in updates:
                try:
                    process_update(update)
                except Exception as e:
                    log.error("Error processing update %s: %s", update.get("update_id"), e)

        except requests.exceptions.HTTPError as e:
            log.error("API HTTP error: %s", e)
            time.sleep(5)
        except requests.exceptions.ConnectionError as e:
            log.warning("Connection error: %s — retrying in 10s", e)
            time.sleep(10)
        except KeyboardInterrupt:
            log.info("Stopped by user.")
            break
        except Exception as e:
            log.error("Unexpected error: %s", e)
            time.sleep(5)


if __name__ == "__main__":
    main()
