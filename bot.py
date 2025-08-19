import os
import time
import random
import schedule
import threading
from telegram import Bot, error
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # Must be integer, e.g., -1001234567890

bot = Bot(token=BOT_TOKEN)

def get_messages():
    """Load messages from messages.txt"""
    try:
        with open("messages.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return ["No messages found! Please add text in messages.txt"]

def send_message():
    messages = get_messages()
    text = random.choice(messages)
    try:
        bot.send_message(chat_id=CHANNEL_ID, text=text)
        print(f"Sent: {text}")
    except error.BadRequest as e:
        print(f"Failed to send message: {e}")

# Schedule: every hour (change as needed)
schedule.every(5).seconds.do(send_message)

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
    # Run scheduler in a separate thread
    threading.Thread(target=run_schedule).start()
    # Start Flask web server
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
