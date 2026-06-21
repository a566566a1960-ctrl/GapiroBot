import os
from flask import Flask
from threading import Thread
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading

# 1. تنظیمات اولیه
BOT_TOKEN = "8750954453:AAFWL7XzhN27MXVLP4JAdGmyvNFYUkeJEuo"
bot = telebot.TeleBot(BOT_TOKEN)
games = {}
lock = threading.Lock()

# 2. راه اندازی وب سرور برای بیدار ماندن ربات
app = Flask('')
@app.route('/')
def home():
    return "GapiroBot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

# اجرای وب سرور در ترد جداگانه
t = Thread(target=run_flask)
t.start()

# ---------------- تنظیمات بازی ----------------
GAME_CONFIG = {
    "🎲 تاس": {"emoji": "🎲", "targets": {"تاس ۶": [6], "زوج": [2, 4, 6], "فرد": [1, 3, 5]}},
    "🏀 بسکتبال": {"emoji": "🏀", "targets": {"گل قطعی (۵)": [5], "شوت خوب (۴)": [4], "شوت معمولی (۳)": [3], "شوت ضعیف (۲)": [2], "خطا (۱)": [1]}},
    "🎯 دارت": {"emoji": "🎯", "targets": {"مرکز (۶)": [6], "خیلی نزدیک (۵)": [5], "نزدیک (۴)": [4], "لبه (۳)": [3], "دور (۲)": [2], "خارج (۱)": [1]}}
}

HELP_TEXT = """🎮 به ربات گپیرو (Gapiro) خوش آمدید!
راهنمای جامع:
۱. ایجاد بازی: دستور /newgame
۲. ثبت‌نام: پیوستن اعضا (۲ تا ۵ نفر)
۳. شروع: توسط سازنده
پشتیبانی: @Hamid_18"""

# ---------------- دستورات ربات ----------------
@bot.message_handler(commands=['start', 'help'])
def help_cmd(m):
    bot.send_message(m.chat.id, HELP_TEXT)

@bot.message_handler(commands=['newgame'])
def newgame(m):
    if m.chat.type == "private":
        bot.send_message(m.chat.id, "❌ فقط داخل گروه")
        return
    cid = m.chat.id
    with lock:
        games[cid] = {"creator": m.from_user.id, "game": None, "target": None, "win_values": [], "players": [m.from_user.id], "player_names": {m.from_user.id: m.from_user.first_name}, "status": "reg", "turn_index": 0, "winners": [], "initial_count": 0, "menu_msg_id": None}
    kb = InlineKeyboardMarkup(row_width=1)
    for g in GAME_CONFIG: kb.add(InlineKeyboardButton(g, callback_data=f"type_{g}"))
    msg = bot.send_message(cid, "🎮 نوع بازی را انتخاب کنید:", reply_markup=kb)
    games[cid]["menu_msg_id"] = msg.message_id

@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    cid, uid = call.message.chat.id, call.from_user.id
    bot.answer_callback_query(call.id)
    g = games.get(cid)
    if not g: return
    data = call.data
    if data.startswith("type_"):
        game_name = data.split("_", 1)[1]
        with lock: g["game"] = game_name
        kb = InlineKeyboardMarkup()
        for t in GAME_CONFIG[game_name]["targets"]: kb.add(InlineKeyboardButton(t, callback_data=f"tgt_{t}"))
        bot.edit_message_text("🎯 هدف را انتخاب کنید:", cid, g["menu_msg_id"], reply_markup=kb)
    elif data.startswith("tgt_"):
        t = data.split("_", 1)[1]
        with lock: 
            g["target"] = t
            g["win_values"] = GAME_CONFIG[g["game"]]["targets"][t]
        update_reg(cid, g["menu_msg_id"])
    elif data == "join":
        with lock:
            if uid not in g["players"] and len(g["players"]) < 5:
                g["players"].append(uid)
                g["player_names"][uid] = call.from_user.first_name
        update_reg(cid, g["menu_msg_id"])
    elif data == "start":
        with lock:
            if uid == g["creator"] and len(g["players"]) >= 2:
                g["status"] = "play"
                bot.edit_message_text(f"🚀 بازی شروع شد!\n👉 نوبت: {g['player_names'][g['players'][0]]}", cid, g["menu_msg_id"])

def update_reg(cid, mid):
    g = games[cid]
    text = "📝 ثبت‌نام\n\n" + "\n".join([f"👤 {n}" for n in g["player_names"].values()])
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("➕ پیوستن", callback_data="join"), InlineKeyboardButton("🚀 شروع", callback_data="start"))
    bot.edit_message_text(text, cid, mid, reply_markup=kb)

@bot.message_handler(content_types=['dice'])
def dice(m):
    cid, uid = m.chat.id, m.from_user.id
    g = games.get(cid)
    if not g or g["status"] != "play" or uid != g["players"][g["turn_index"]] or m.dice.emoji != GAME_CONFIG[g["game"]]["emoji"]: return
    if m.dice.value in g["win_values"]:
        bot.send_message(cid, f"🎉 {g['player_names'][uid]} برنده شد!")
        games.pop(cid, None)
    else:
        with lock: g["turn_index"] = (g["turn_index"] + 1) % len(g["players"])
        bot.send_message(cid, f"👉 نوبت بعدی: {g['player_names'][g['players'][g['turn_index']]]}")

# 3. اجرای نهایی تلگرام
if __name__ == "__main__":
    bot.infinity_polling()
                
