import os
import random
import asyncio
import threading
from telegram import Bot
from flask import Flask
from waitress import serve

# ---------------------
# Load environment variables
# ---------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in Railway environment variables")

raw_ids = os.getenv("CHANNEL_IDS", "")

# Dictionary: { channel_id : message_filename }
CHANNEL_MAP = {}

for item in raw_ids.split(","):
    item = item.strip()
    if ":" not in item:
        continue

    chat_id_str, filename = item.split(":", 1)
    chat_id_str = chat_id_str.strip()
    filename = filename.strip()

    if chat_id_str.lstrip("-").isdigit():
        CHANNEL_MAP[int(chat_id_str)] = filename

if not CHANNEL_MAP:
    raise ValueError("CHANNEL_IDS must be in format: -100123:messages_1.txt")

# Interval in minutes (default 10)
INTERVAL_MINUTES = int(os.getenv("INTERVAL_MINUTES", 10))
DELETE_DELAY_MINUTES = int(os.getenv("DELETE_DELAY_MINUTES", 10))  # default 10 min deletion

bot = Bot(token=BOT_TOKEN)

# ---------------------
# Read messages from specific file
# ---------------------
def get_messages(filename):
    """Load messages for a specific channel"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return [f"⚠️ No messages found in {filename}. Please upload the file."]

# ---------------------
# Async delete message after delay
# ---------------------
async def delete_later(chat_id, message_id, delay=600):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        print(f"Deleted message {message_id} from {chat_id}")
    except Exception as e:
        print(f"Failed to delete message {message_id}: {e}")

# ---------------------
# Async send messages
# ---------------------
async def send_message_async():
    for channel_id, filename in CHANNEL_MAP.items():

        messages = get_messages(filename)
        if not messages:
            continue

        text = random.choice(messages)

        try:
            msg = await bot.send_message(chat_id=channel_id, text=text)
            print(f"Sent to {channel_id} (from {filename}): {text}")

            # Auto delete after X minutes
            asyncio.create_task(delete_later(
                channel_id,
                msg.message_id,
                delay=DELETE_DELAY_MINUTES * 60
            ))

        except Exception as e:
            print(f"Failed to send to {channel_id}: {e}")

# ---------------------
# Async scheduler (interval loop)
# ---------------------
def run_schedule():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def job():
        while True:
            await send_message_async()
            await asyncio.sleep(INTERVAL_MINUTES * 60)

    loop.run_until_complete(job())

# ---------------------
# Flask server (keep-alive)
# ---------------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

# ---------------------
# Start everything
# ---------------------
if __name__ == "__main__":
    # Start scheduler in a background thread
    threading.Thread(target=run_schedule, daemon=True).start()

    # Start Waitress server
    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
