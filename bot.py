from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import json
import os
from datetime import date

# Ambil token dari environment variable (Railway)
TOKEN = os.environ.get("TOKEN")

DATA_FILE = "data.json"

# Load data
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# Save data
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# Ambil tanggal hari ini
def today_key():
    return str(date.today())

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 Project 100% Yansen Aktif.\n\n"
        "Gunakan:\n"
        "/done (+1)\n"
        "/focus (+2)\n"
        "/deep (+3)\n"
        "/score"
    )

async def add_score(update: Update, context: ContextTypes.DEFAULT_TYPE, points: int):
    data = load_data()
    today = today_key()

    if today not in data:
        data[today] = 0

    data[today] += points
    save_data(data)

    await update.message.reply_text(f"💪 Skor hari ini: {data[today]}")

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await add_score(update, context, 1)

async def focus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await add_score(update, context, 2)

async def deep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await add_score(update, context, 3)

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    today = today_key()

    total = data.get(today, 0)

    await update.message.reply_text(f"📊 Total skor hari ini: {total}")

def main():
    if not TOKEN:
        print("TOKEN tidak ditemukan. Pastikan sudah diset di Environment Variables.")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("focus", focus))
    app.add_handler(CommandHandler("deep", deep))
    app.add_handler(CommandHandler("score", score))

    print("Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()