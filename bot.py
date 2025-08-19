import os
import time
import random
import schedule
import threading
from telegram import Bot, error
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
# List multiple channel IDs separated by commas in Railway env variable
CHANNEL_IDS = [int(x) for x in os.getenv("CHANNEL_IDS", "").split(",")]

bot = Bot(token=BOT_TOKEN)

def get_messages():
    try:
        with open("messages.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return ["No messages found! Please add text in messages.txt"]

def send_message():
    messages = get_messages()
    text = random.choice(messages)
    for channel_id in CHANNEL_IDS:
        try:
            bot.send_message(chat_id=channel_id, text=text)
            print(f"Sent to {channel_id}: {text}")
        except error.BadRequest as e:
            print(f"Failed to send to {channel_id}: {e}")

# Schedule: every hour
schedule.every(1).hours.do(send_message)

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Flask web server to keep Railway alive
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

if __name__ == "__main__":
    threading.Thread(target=run_schedule).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
