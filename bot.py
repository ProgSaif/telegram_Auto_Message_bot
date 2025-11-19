import os
import time
import random
import schedule
import threading
from telegram import Bot, error
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
# Delete message after delay (10 minutes)
# ---------------------
def delete_later(chat_id, message_id, delay=60):
    """Delete message after delay (600 sec = 10 minutes)"""
    def worker():
        time.sleep(delay)
        try:
            bot.delete_message(chat_id=chat_id, message_id=message_id)
            print(f"Deleted message {message_id} from {chat_id}")
        except Exception as e:
            print(f"Failed to delete message {message_id}: {e}")
    threading.Thread(target=worker, daemon=True).start()

# ---------------------
# Send message and schedule deletion
# ---------------------
def send_message():
    messages = get_messages()
    if not messages:
        print("No messages found to send.")
        return

    text = random.choice(messages)

    for channel_id in CHANNEL_IDS:
        try:
            msg = bot.send_message(chat_id=channel_id, text=text)
            print(f"Sent to {channel_id}: {text}")

            # Delete the message after 10 minutes
            delete_later(channel_id, msg.message_id, delay=60)

        except error.TelegramError as e:
            print(f"Failed to send to {channel_id}: {e}")

# ---------------------
# Scheduler
# ---------------------
schedule.every(2).minutes.do(send_message)  # Change interval if needed

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# ---------------------
# Flask keep-alive server
# ---------------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

# ---------------------
# Start everything
# ---------------------
if __name__ == "__main__":
    threading.Thread(target=run_schedule, daemon=True).start()
    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
