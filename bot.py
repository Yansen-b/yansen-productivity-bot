from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import os
import json
from datetime import datetime, time, timedelta
import pytz

TOKEN = os.environ.get("TOKEN")
CHAT_ID = int(os.environ.get("CHAT_ID"))
DATA_FILE = "data.json"
TIMEZONE = pytz.timezone("Asia/Makassar")

# =========================
# DATA UTILITIES
# =========================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def today_key():
    return str(datetime.now(TIMEZONE).date())

def init_day(data):
    today = today_key()
    if today not in data:
        data[today] = {
            "big_tasks": [],
            "small_tasks": [],
            "improvement_tasks": [],
            "score": 0,
            "review_done": False,
            "completed_day": False,
            "reason": ""
        }
    return data

# =========================
# AUTO JOBS
# =========================

async def auto_morning(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text="BESAR:\n1. \n2. \n3. \n\nKECIL:\n4. \n5. "
    )

async def auto_evening(context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    today = today_key()

    if today not in data:
        return

    if not data[today]["completed_day"]:
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text="Hari belum complete.\nApa penyebab utama hari ini?"
        )
        context.application.user_data["WAITING_REASON"] = True

async def weekly_review(context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    today = datetime.now(TIMEZONE).date()
    success = 0
    total = 0

    for i in range(7):
        day_key = str(today - timedelta(days=i))
        if day_key in data:
            total += 1
            if data[day_key]["completed_day"]:
                success += 1

    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=f"Weekly Review\nHari sukses: {success}/{total}"
    )

async def interval_check(context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    today = today_key()

    if today not in data:
        return

    incomplete = [
        t for t in (data[today]["big_tasks"] + data[today]["small_tasks"])
        if not t["done"]
    ]

    if incomplete:
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text="Status check: masih ada task belum selesai."
        )

# =========================
# COMMANDS
# =========================

async def plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["WAITING_PLAN"] = True
    await update.message.reply_text(
        "BESAR:\n1. \n2. \n3. \n\nKECIL:\n4. \n5. "
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    data = load_data()
    data = init_day(data)
    today = today_key()

    # HANDLE PLAN
    if context.user_data.get("WAITING_PLAN"):
        if "BESAR:" not in text or "KECIL:" not in text:
            await update.message.reply_text("Format salah.")
            return

        try:
            big_section = text.split("BESAR:")[1].split("KECIL:")[0]
            small_section = text.split("KECIL:")[1]

            big_tasks = [line.strip()[2:].strip()
                         for line in big_section.split("\n")
                         if line.strip().startswith(("1.","2.","3."))]

            small_tasks = [line.strip()[2:].strip()
                           for line in small_section.split("\n")
                           if line.strip().startswith(("4.","5."))]

            if len(big_tasks) != 3 or len(small_tasks) != 2:
                raise Exception

        except:
            await update.message.reply_text("Format tidak valid.")
            return

        data[today]["big_tasks"] = [{"name": t, "done": False} for t in big_tasks]
        data[today]["small_tasks"] = [{"name": t, "done": False} for t in small_tasks]
        data[today]["improvement_tasks"] = []
        data[today]["score"] = 2
        data[today]["review_done"] = True
        data[today]["completed_day"] = False

        save_data(data)
        context.user_data["WAITING_PLAN"] = False

        await update.message.reply_text("Plan tersimpan. +2 poin.")
        return

    # HANDLE REASON
    if context.application.user_data.get("WAITING_REASON"):
        data[today]["reason"] = text
        save_data(data)
        context.application.user_data["WAITING_REASON"] = False
        await update.message.reply_text("Reason tersimpan.")
        return

# =========================
# SET COMMAND MENU
# =========================

async def setup_commands(app):
    commands = [
        BotCommand("plan", "Buat plan hari ini"),
    ]
    await app.bot.set_my_commands(commands)

# =========================
# MAIN
# =========================

def main():
    app = ApplicationBuilder().token(TOKEN).post_init(setup_commands).build()

    app.add_handler(CommandHandler("plan", plan))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Daily Jobs
    app.job_queue.run_daily(auto_morning, time=time(16,27,tzinfo=TIMEZONE))
    app.job_queue.run_daily(auto_evening, time=time(17,5,tzinfo=TIMEZONE))
    app.job_queue.run_daily(weekly_review, time=time(19,0,tzinfo=TIMEZONE), days=(6,))

    # Interval checks
    for hour in [6,7,8,9,10,13,14,15,16]:
        app.job_queue.run_daily(interval_check, time=time(hour,30,tzinfo=TIMEZONE))

    print("Automation Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()

