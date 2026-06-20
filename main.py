import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading

TOKEN = "8750954453:AAFWL7XzhN27MXVLP4JAdGmyvNFYUkeJEuo"
bot = telebot.TeleBot(TOKEN)

games = {}

# تنظیمات بازی (تعریف هدف‌ها)
GAME_CONFIG = {
    "🎲": {"name": "🎲 تاس", "win_values": [6]},
    "🏀": {"name": "🏀 بسکتبال", "win_values": [4, 5]} # بسکتبال معمولا ۵ است، ۴ را هم اضافه کردم
}

@bot.message_handler(commands=['newgame'])
def new_game(m):
    cid = m.chat.id
    # انتخاب بازی به صورت پیشفرض تاس (می‌توانید با آرگومان تغییرش دهید)
    games[cid] = {
        "creator": m.from_user.id,
        "game_type": "🎲", 
        "players": [m.from_user.id],
        "player_names": {m.from_user.id: m.from_user.first_name},
        "status": "reg",
        "turn_index": 0,
        "winners": []
    }
    bot.reply_to(m, "✅ بازی جدید ساخته شد (تاس). دیگران /join بزنند و بعد /startgame.")

@bot.message_handler(commands=['join'])
def join_game(m):
    cid = m.chat.id
    if cid in games and games[cid]["status"] == "reg":
        if m.from_user.id not in games[cid]["players"]:
            games[cid]["players"].append(m.from_user.id)
            games[cid]["player_names"][m.from_user.id] = m.from_user.first_name
            bot.reply_to(m, f"👤 {m.from_user.first_name} وارد شد.")

@bot.message_handler(commands=['startgame'])
def start_game(m):
    cid = m.chat.id
    if cid in games:
        games[cid]["status"] = "play"
        bot.reply_to(m, f"🚀 بازی شروع شد! نوبت {games[cid]['player_names'][games[cid]['players'][0]]}")

@bot.message_handler(content_types=['dice'])
def handle_dice(m):
    cid = m.chat.id
    if cid not in games or games[cid]["status"] != "play": return
    
    g = games[cid]
    current_uid = g["players"][g["turn_index"]]
    
    # بررسی اینکه آیا نوبتِ این بازیکن است
    if m.from_user.id != current_uid:
        return

    # بررسی نتیجه بر اساس نوع بازی
    win_values = GAME_CONFIG[m.dice.emoji]["win_values"]
    
    if m.dice.value in win_values:
        g["winners"].append(g["player_names"][m.from_user.id])
        g["players"].pop(g["turn_index"]) # حذف برنده از لیست بازیکنان
        bot.reply_to(m, "🎉 تبریک! شما امتیاز لازم را گرفتید و برنده شدید.")
    else:
        # اگر نبرد، فقط نوبت نفر بعدی می‌شود
        g["turn_index"] += 1
    
    # تنظیم نوبت (گردشی)
    if not g["players"]:
        res = "🏁 پایان بازی! رتبه‌بندی:\n" + "\n".join([f"مقام {i+1}: {name}" for i, name in enumerate(g['winners'])])
        bot.send_message(cid, res)
        del games[cid]
    else:
        g["turn_index"] %= len(g["players"])
        bot.send_message(cid, f"👉 نوبت بعدی: {g['player_names'][g['players'][g['turn_index']]]}")

print("Bot is ready...")
bot.infinity_polling()
