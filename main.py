import os
import time
import random
import schedule
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # Example: -1001234567890

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
    text = random.choice(messages)  # Pick one random message
    bot.send_message(chat_id=CHANNEL_ID, text=text)
    print(f"Sent: {text}")

# Schedule: send every hour
schedule.every(1).hours.do(send_message)

print("Bot is running...")

while True:
    schedule.run_pending()
    time.sleep(1)
