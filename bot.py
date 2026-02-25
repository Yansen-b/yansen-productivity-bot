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
from datetime import date, timedelta

TOKEN = os.environ.get("TOKEN")
DATA_FILE = "data.json"

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
    return str(date.today())

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
            "reason": "",
            "streak_valid": False
        }
    return data

def calculate_streak(data):
    streak = 0
    today = date.today()

    for i in range(365):
        day_key = str(today - timedelta(days=i))
        if day_key in data and data[day_key].get("streak_valid"):
            streak += 1
        else:
            break

    return streak

# =========================
# STATE
# =========================

user_state = {}

# =========================
# PLAN
# =========================

async def plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("CHAT ID:", update.effective_chat.id)
    context.user_data["WAITING_PLAN"] = True
    await update.message.reply_text(
        "BESAR:\n1. \n2. \n3. \n\nKECIL:\n4. \n5. "
    )

async def handle_plan_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if user_state.get(update.effective_chat.id) != "WAITING_PLAN":
        return

    text = update.message.text

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

    data = load_data()
    data = init_day(data)
    today = today_key()

    data[today]["big_tasks"] = [{"name": t, "done": False} for t in big_tasks]
    data[today]["small_tasks"] = [{"name": t, "done": False} for t in small_tasks]
    data[today]["improvement_tasks"] = []
    data[today]["score"] = 2
    data[today]["review_done"] = True
    data[today]["completed_day"] = False
    data[today]["streak_valid"] = False

    save_data(data)

    user_state[update.effective_chat.id] = None

    await update.message.reply_text("Plan tersimpan. +2 poin.")

# =========================
# STATUS
# =========================

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    today = today_key()

    if today not in data:
        await update.message.reply_text("Belum ada plan hari ini.")
        return

    day = data[today]

    total_tasks = (
        len(day["big_tasks"]) +
        len(day["small_tasks"]) +
        len(day["improvement_tasks"])
    )

    done_tasks = (
        sum(t["done"] for t in day["big_tasks"]) +
        sum(t["done"] for t in day["small_tasks"]) +
        sum(t["done"] for t in day["improvement_tasks"])
    )

    message = f"Progress: {done_tasks}/{total_tasks}\nSkor: {day['score']}\n\n"

    message += "BIG:\n"
    for i, t in enumerate(day["big_tasks"], 1):
        icon = "✅" if t["done"] else "❌"
        message += f"{i}. {icon} {t['name']}\n"

    message += "\nSMALL:\n"
    for i, t in enumerate(day["small_tasks"], 4):
        icon = "✅" if t["done"] else "❌"
        message += f"{i}. {icon} {t['name']}\n"

    if day["improvement_tasks"]:
        message += "\nIMPROVEMENT:\n"
        for i, t in enumerate(day["improvement_tasks"], 6):
            icon = "✅" if t["done"] else "❌"
            message += f"{i}. {icon} {t['name']}\n"

    await update.message.reply_text(message)

# =========================
# DONE
# =========================

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gunakan: /done nomor")
        return

    try:
        task_number = int(context.args[0])
    except:
        await update.message.reply_text("Nomor tidak valid.")
        return

    data = load_data()
    today = today_key()

    if today not in data:
        await update.message.reply_text("Belum ada plan.")
        return

    day = data[today]
    all_tasks = (
        day["big_tasks"] +
        day["small_tasks"] +
        day["improvement_tasks"]
    )

    index = task_number - 1

    if index < 0 or index >= len(all_tasks):
        await update.message.reply_text("Nomor tidak valid.")
        return

    if all_tasks[index]["done"]:
        await update.message.reply_text("Sudah selesai sebelumnya.")
        return

    all_tasks[index]["done"] = True

    if index < 3:
        day["score"] += 3
    else:
        day["score"] += 1

    save_data(data)

    await status(update, context)

# =========================
# COMPLETE
# =========================

async def complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    today = today_key()

    if today not in data:
        await update.message.reply_text("Belum ada plan.")
        return

    day = data[today]

    incomplete = [
        t["name"] for t in (
            day["big_tasks"] + day["small_tasks"]
        ) if not t["done"]
    ]

    if incomplete:
        await update.message.reply_text(
            "Masih ada task belum selesai:\n- " +
            "\n- ".join(incomplete)
        )
        return

    if not day["completed_day"]:
        day["score"] += 5
        day["completed_day"] = True
        day["streak_valid"] = True
        save_data(data)

        await update.message.reply_text("Hari sukses. +5 poin.")
    else:
        await update.message.reply_text("Sudah dikonfirmasi.")

# =========================
# IMPROVE
# =========================

async def improve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gunakan: /improve nama_task")
        return

    new_task = " ".join(context.args)

    data = load_data()
    data = init_day(data)
    today = today_key()

    data[today]["improvement_tasks"].append({
        "name": new_task,
        "done": False
    })

    save_data(data)

    await update.message.reply_text("Improvement task ditambahkan.")

# =========================
# EDIT
# =========================

async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Gunakan: /edit nomor nama_baru")
        return

    try:
        task_number = int(context.args[0])
    except:
        await update.message.reply_text("Nomor tidak valid.")
        return

    new_name = " ".join(context.args[1:])

    data = load_data()
    today = today_key()

    if today not in data:
        await update.message.reply_text("Belum ada plan.")
        return

    day = data[today]
    all_tasks = (
        day["big_tasks"] +
        day["small_tasks"] +
        day["improvement_tasks"]
    )

    index = task_number - 1

    if index < 0 or index >= len(all_tasks):
        await update.message.reply_text("Nomor tidak valid.")
        return

    all_tasks[index]["name"] = new_name
    save_data(data)

    await update.message.reply_text("Task diupdate.")

# =========================
# STREAK
# =========================

async def streak(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    current_streak = calculate_streak(data)
    await update.message.reply_text(f"Streak saat ini: {current_streak} hari.")

# =========================
# HELP
# =========================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/plan\n"
        "/status\n"
        "/done nomor\n"
        "/complete\n"
        "/improve nama\n"
        "/edit nomor nama_baru\n"
        "/streak"
    )

# =========================
# MAIN
# =========================

async def setup_commands(app):
    commands = [
        BotCommand("plan", "Buat plan hari ini"),
        BotCommand("status", "Lihat progress"),
        BotCommand("done", "Tandai task selesai"),
        BotCommand("complete", "Konfirmasi hari selesai"),
        BotCommand("improve", "Tambah improvement task"),
        BotCommand("edit", "Edit task"),
        BotCommand("streak", "Lihat streak"),
        BotCommand("help", "Lihat menu")
    ]
    await app.bot.set_my_commands(commands)

def main():
    if not TOKEN:
        print("TOKEN tidak ditemukan.")
        return

    app = ApplicationBuilder().token(TOKEN).post_init(setup_commands).build()

    app.add_handler(CommandHandler("plan", plan))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("complete", complete))
    app.add_handler(CommandHandler("improve", improve))
    app.add_handler(CommandHandler("edit", edit))
    app.add_handler(CommandHandler("streak", streak))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_plan_input))

    print("Core Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()

