from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8000)

# این را قبل از شروع اجرای اصلی ربات تلگرام قرار دهید
t = Thread(target=run)
t.start()
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading

BOT_TOKEN = "8750954453:AAFWL7XzhN27MXVLP4JAdGmyvNFYUkeJEuo"
bot = telebot.TeleBot(BOT_TOKEN)

games = {}
lock = threading.Lock()

# ---------------- GAME CONFIG ----------------
GAME_CONFIG = {
    "🎲 تاس": {
        "emoji": "🎲",
        "targets": {
            "تاس ۶": [6],
            "زوج": [2, 4, 6],
            "فرد": [1, 3, 5]
        }
    },
    "🏀 بسکتبال": {
        "emoji": "🏀",
        "targets": {
            "گل قطعی (۵)": [5],
            "شوت خوب (۴)": [4],
            "شوت معمولی (۳)": [3],
            "شوت ضعیف (۲)": [2],
            "خطا (۱)": [1]
        }
    },
    "🎯 دارت": {
        "emoji": "🎯",
        "targets": {
            "مرکز (۶)": [6],
            "خیلی نزدیک (۵)": [5],
            "نزدیک (۴)": [4],
            "لبه (۳)": [3],
            "دور (۲)": [2],
            "خارج (۱)": [1]
        }
    }
}

# ---------------- HELP ----------------
HELP_TEXT = """🎮 به ربات گپیرو (Gapiro) خوش آمدید!

راهنمای جامع بازی:
۱. ایجاد بازی: در گروه دستور /newgame را بزنید.
۲. تنظیمات: نوع استیکر و شرط پیروزی را انتخاب کنید.
۳. ثبت‌نام: اعضا با دکمه پیوست به بازی اضافه می‌شوند (۲ تا ۵ نفر).
۴. شروع: سازنده دکمه شروع را می‌زند.
۵. قوانین حرکت: هر بازیکن فقط در نوبت خود باید استیکر مربوطه را بفرستد.
۶. پیروزی: اولین کسی که به هدف بزند برنده است. بازی تا مشخص شدن تمام رتبه‌ها ادامه می‌یابد.

پشتیبانی: @Hamid_18
"""

# ---------------- START / HELP ----------------
@bot.message_handler(commands=['start', 'help'])
def help_cmd(m):
    bot.send_message(m.chat.id, HELP_TEXT)

# ---------------- NEW GAME ----------------
@bot.message_handler(commands=['newgame'])
def newgame(m):
    if m.chat.type == "private":
        bot.send_message(m.chat.id, "❌ فقط داخل گروه")
        return

    cid = m.chat.id  

    with lock:  
        games[cid] = {  
            "creator": m.from_user.id,  
            "game": None,  
            "target": None,  
            "win_values": [],  
            "players": [],  
            "player_names": {},  
            "status": "reg",  
            "turn_index": 0,  
            "winners": [],  
            "initial_count": 0,  
            "menu_msg_id": None  
        }  

        games[cid]["players"].append(m.from_user.id)  
        games[cid]["player_names"][m.from_user.id] = m.from_user.first_name  

    kb = InlineKeyboardMarkup(row_width=1)  
    for g in GAME_CONFIG:  
        kb.add(InlineKeyboardButton(g, callback_data=f"type_{g}"))  

    msg = bot.send_message(cid, "🎮 نوع بازی را انتخاب کنید:", reply_markup=kb)  
    games[cid]["menu_msg_id"] = msg.message_id

# ---------------- CALLBACK ----------------
@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    if not call.message:
        return

    cid = call.message.chat.id  
    uid = call.from_user.id  
    data = call.data  

    bot.answer_callback_query(call.id)  

    g = games.get(cid)  
    if not g:  
        return  

    if data == "back_home":  
        if uid != g["creator"]:  
            bot.answer_callback_query(call.id, "❌ فقط سازنده")  
            return  
        kb = InlineKeyboardMarkup(row_width=1)  
        for name in GAME_CONFIG:  
            kb.add(InlineKeyboardButton(name, callback_data=f"type_{name}"))  
        bot.edit_message_text("🎮 نوع بازی را انتخاب کنید:", cid, g["menu_msg_id"], reply_markup=kb)  
        return  

    if data.startswith("type_"):  
        with lock:  
            if g["status"] != "reg" or uid != g["creator"]:  
                return  
            game_name = data.split("_", 1)[1]  
            g["game"] = game_name  
        kb = InlineKeyboardMarkup()  
        for t in GAME_CONFIG[game_name]["targets"]:  
            kb.add(InlineKeyboardButton(t, callback_data=f"tgt_{t}"))  
        kb.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_home"))  
        bot.edit_message_text("🎯 هدف را انتخاب کنید:", cid, g["menu_msg_id"], reply_markup=kb)  
        return  

    if data.startswith("tgt_"):  
        with lock:  
            if uid != g["creator"] or not g["game"]:  
                return  
            t = data.split("_", 1)[1]  
            g["target"] = t  
            g["win_values"] = GAME_CONFIG[g["game"]]["targets"][t]  
        update_reg(cid, g["menu_msg_id"])  
        return

    if data == "join":  
        with lock:  
            if uid in g["players"] or len(g["players"]) >= 5:  
                return  
            g["players"].append(uid)  
            g["player_names"][uid] = call.from_user.first_name  
        update_reg(cid, g["menu_msg_id"])  
        return  

    if data == "start":  
        with lock:  
            if uid != g["creator"]:  
                return  
            if len(g["players"]) < 2:  
                bot.answer_callback_query(call.id, "❌ حداقل ۲ نفر")  
                return  
            if not g["win_values"]:  
                bot.answer_callback_query(call.id, "❌ هدف انتخاب نشده")  
                return  
            g["status"] = "play"  
            g["turn_index"] = 0  
            g["initial_count"] = len(g["players"])  
        bot.edit_message_text(  
            f"🚀 بازی شروع شد!\n👉 نوبت: {g['player_names'][g['players'][0]]}",  
            cid,  
            g["menu_msg_id"]  
        )

# ---------------- REGISTER MENU ----------------
def update_reg(cid, mid):
    g = games[cid]
    text = "📝 ثبت‌نام\n\n" + "\n".join([f"👤 {n}" for n in g["player_names"].values()])  
    kb = InlineKeyboardMarkup()  
    kb.add(  
        InlineKeyboardButton("➕ پیوستن", callback_data="join"),  
        InlineKeyboardButton("🚀 شروع", callback_data="start"),  
        InlineKeyboardButton("🔙 بازگشت", callback_data="back_home")  
    )  
    bot.edit_message_text(text, cid, mid, reply_markup=kb)

# ---------------- DICE ----------------
@bot.message_handler(content_types=['dice'])
def dice(m):
    cid = m.chat.id
    uid = m.from_user.id
    g = games.get(cid)  
    if not g or g["status"] != "play":  
        return  
    with lock:  
        players = g["players"]  
        if not players: return  
        if g["turn_index"] >= len(players): g["turn_index"] = 0  
        current_uid = players[g["turn_index"]]  
        if uid != current_uid: return  
        if m.dice.emoji != GAME_CONFIG[g["game"]]["emoji"]: return  
        value = m.dice.value  
        if value in g["win_values"]:  
            winner_name = g["player_names"][uid]  
            g["winners"].append(winner_name)  
            g["players"].remove(uid)  
            bot.send_message(cid, f"🎉 {winner_name} برنده شد!")  
            if g["initial_count"] == 2:  
                bot.send_message(cid, f"🏆 بازی تمام شد!\n\n🥇 برنده: {winner_name}")  
                games.pop(cid, None); return  
            if len(g["players"]) == 0: games.pop(cid, None); return  
            if len(g["players"]) == 1:  
                last = g["player_names"][g["players"][0]]  
                g["winners"].append(last)  
                result = "🏁 پایان بازی!\n\n📊 رتبه‌بندی:\n\n"  
                for i, n in enumerate(g["winners"], 1): result += f"{i}. {n}\n"  
                bot.send_message(cid, result); games.pop(cid, None); return  
        if len(g["players"]) > 0:  
            g["turn_index"] %= len(g["players"])  
        else: return  
        if value not in g["win_values"]:  
            g["turn_index"] = (g["turn_index"] + 1) % len(g["players"])  
        next_player = g["players"][g["turn_index"]]  
        bot.send_message(cid, f"👉 نوبت: {g['player_names'][next_player]}")

bot.infinity_polling()  
            
