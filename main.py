from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import asyncio, random

# 🔹 توکن ربات خودت رو اینجا بذار
TOKEN = "8598401358:AAH0caVct3dMVg5R-eN1l7pRtZwREPdtmqg"

# 🔹 سوال‌ها و جواب‌ها
QUESTIONS = [
    ("پایتخت ایران کجاست؟", "تهران"),
    ("نتیجه 5 + 7 چند است؟", "12"),
    ("رنگ آسمان چیست؟", "آبی"),
    ("چند روز در هفته داریم؟", "7"),
    ("کدام حیوان پارس می‌کند؟", "سگ"),
]

players = []
scores = {}
active_game = False
current_player = None
current_answer = None
time_limit = 10  # ثانیه

# ===== دستورات =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 سلام! به بازی سؤال و جواب خوش اومدی!\n"
        "دستورات:\n"
        "/single - بازی تک نفره\n"
        "/double - بازی دو نفره\n"
        "/stop - توقف بازی"
    )

async def single(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active_game, scores
    user = update.effective_user
    active_game = True
    scores = {user.id: 0}
    await update.message.reply_text(f"{user.first_name} بازی تک‌نفره شروع شد 🎯")
    await ask_question(context, user)

async def double(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players, active_game, scores
    user = update.effective_user
    if user.id in [p.id for p in players]:
        await update.message.reply_text("منتظر حریف باش...")
        return

    players.append(user)
    await update.message.reply_text(f"{user.first_name} به بازی دو نفره اضافه شد 👥")

    if len(players) == 2:
        active_game = True
        scores = {players[0].id: 0, players[1].id: 0}
        for p in players:
            await context.bot.send_message(p.id, "بازی دو نفره شروع شد! 🚀")
        await ask_question(context, random.choice(players))

async def ask_question(context, player):
    global current_player, current_answer
    q, a = random.choice(QUESTIONS)
    current_player = player
    current_answer = a.lower()
    await context.bot.send_message(player.id, f"❓ سوال برای {player.first_name}:\n{q}\n(۱۰ ثانیه فرصت داری...)")
    try:
        await asyncio.wait_for(wait_for_answer(), timeout=time_limit)
    except asyncio.TimeoutError:
        await context.bot.send_message(player.id, "⏰ وقت تموم شد!")

async def wait_for_answer():
    await asyncio.sleep(time_limit)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_player, current_answer, scores, players, active_game
    if not active_game or not current_player:
        return

    user = update.effective_user
    text = update.message.text.strip().lower()

    if user.id != current_player.id:
        return

    if text == current_answer:
        scores[user.id] += 1
        await update.message.reply_text(f"✅ درست! امتیازت: {scores[user.id]}")
    else:
        await update.message.reply_text("❌ اشتباه بود!")

    # بررسی پایان بازی
    if len(players) == 1 and scores[user.id] >= 5:
        await update.message.reply_text("🎉 تبریک! برنده شدی!")
        await stop(update, context)
    elif len(players) == 2 and max(scores.values()) >= 5:
        await end_game(context)
    else:
        next_player = players[1] if len(players) == 2 and current_player == players[0] else players[0] if len(players) == 2 else user
        await ask_question(context, next_player)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active_game, players, scores
    active_game = False
    players = []
    scores = {}
    await update.message.reply_text("🛑 بازی متوقف شد.")

async def end_game(context):
    global players, scores, active_game
    p1, p2 = players
    s1, s2 = scores[p1.id], scores[p2.id]

    if s1 > s2:
        msg = f"🏆 {p1.first_name} برد با امتیاز {s1}-{s2}"
    elif s2 > s1:
        msg = f"🏆 {p2.first_name} برد با امتیاز {s2}-{s1}"
    else:
        msg = f"🤝 مساوی شد! ({s1}-{s2})"

    for p in players:
        await context.bot.send_message(p.id, msg)
    active_game = False
    players = []

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("single", single))
    app.add_handler(CommandHandler("double", double))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ ربات آماده است (در حال اجرا...)")
    app.run_polling()  # حالت blocking، بدون هشدارهای asyncio

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
