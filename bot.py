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
CHANNEL_IDS = []
for x in raw_ids.split(","):
    x = x.strip()
    if x.isdigit() or (x.startswith("-100") and x[1:].isdigit()):
        CHANNEL_IDS.append(int(x))

if not CHANNEL_IDS:
    raise ValueError("CHANNEL_IDS not set correctly. Must be numeric IDs.")

bot = Bot(token=BOT_TOKEN)

# ---------------------
# Read messages from file
# ---------------------
def get_messages():
    """Load messages from messages.txt"""
    try:
        with open("messages.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return ["No messages found! Please add text in messages.txt"]

# ---------------------
# Async delete message after delay
# ---------------------
async def delete_later(chat_id, message_id, delay=60):
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
    messages = get_messages()
    if not messages:
        return
    text = random.choice(messages)

    for channel_id in CHANNEL_IDS:
        try:
            msg = await bot.send_message(chat_id=channel_id, text=text)
            print(f"Sent to {channel_id}: {text}")
            # Schedule deletion in background
            asyncio.create_task(delete_later(channel_id, msg.message_id, delay=600))
        except Exception as e:
            print(f"Failed to send to {channel_id}: {e}")

# ---------------------
# Async scheduler
# ---------------------
def run_schedule():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def job():
        while True:
            await send_message_async()
            await asyncio.sleep(600)  # every 10 minutes, adjust as needed

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
    # Start scheduler in a separate thread
    threading.Thread(target=run_schedule, daemon=True).start()
    # Start Waitress server
    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
