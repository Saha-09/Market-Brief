"""
One-time helper to find your TELEGRAM_CHAT_ID.

Steps:
  1. In Telegram, create a bot: message @BotFather -> /newbot -> copy the token.
  2. Open a chat with your new bot and send it any message (e.g. "hi").
  3. Run:  TELEGRAM_BOT_TOKEN=xxxx python get_chat_id.py
  4. Copy the chat id it prints. That's your TELEGRAM_CHAT_ID.
"""
import os
import sys
import requests

token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
if not token:
    sys.exit("Set TELEGRAM_BOT_TOKEN first, e.g.  TELEGRAM_BOT_TOKEN=xxxx python get_chat_id.py")

r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=30)
data = r.json()
if not data.get("result"):
    sys.exit("No messages found. Send your bot a message first, then re-run.")

for upd in data["result"]:
    msg = upd.get("message") or upd.get("edited_message") or {}
    chat = msg.get("chat", {})
    if chat:
        print(f"chat_id = {chat.get('id')}   (from: {chat.get('first_name') or chat.get('title')})")
