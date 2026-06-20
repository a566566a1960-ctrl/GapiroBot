import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8750954453:AAFWL7XzhN27MXVLP4JAdGmyvNFYUkeJEuo"
bot = telebot.TeleBot(BOT_TOKEN)

games = {}
GAME_CONFIG = {
    "🎲 تاس": {"emoji": "🎲", "targets": {"تاس ۶": [6], "زوج": [2, 4, 6], "فرد": [1, 3, 5]}},
    "🎰 کازینو": {"emoji": "🎰", "targets": {"۳ تا ۷": [64], "۳ تا انگور": [43], "۳ تا لیمو": [22], "۳ تا BAR": [1]}},
    "🏀 بسکتبال": {"emoji": "🏀", "targets": {"گل قطعی (۵)": [5]}},
    "🎯 دارت": {"emoji": "🎯", "targets": {"مرکز (۶)": [6]}}
}

# 1. راهنمای جامع
@bot.message_handler(commands=['help', 'help@Hamid_18bot'])
def send_help(message):
    text = ("🎮 راهنمای جامع بازی گپیرو (Gapiro):\n\n"
            "۱. ایجاد بازی: دستور /newgame را در گروه بزنید.\n"
            "۲. تنظیمات: نوع استیکر و هدف را انتخاب کنید.\n"
            "۳. ثبت‌نام: با «➕ ورود» عضو شوید (۲ تا ۵ نفر).\n"
            "۴. شروع: فقط سازنده بازی دکمه «🚀 شروع» را بزند.\n"
            "۵. قوانین: فقط در نوبت خود استیکر بفرستید.\n"
            "۶. پیروزی: بازی تا آخرین نفر ادامه می‌یابد و در پایان رتبه‌بندی ۵ تایی نمایش داده می‌شود.")
    bot.reply_to(message, text)

# 2. شروع بازی
@bot.message_handler(commands=['newgame'])
def handle_newgame(message):
    if message.chat.type == 'private': return
    cid = message.chat.id
    games[cid] = {"creator": message.from_user.id, "game": None, "target": None, "win_values": [], 
                  "players": [message.from_user.id], "player_names": {message.from_user.id: message.from_user.first_name}, 
                  "status": "setting", "turn_index": 0, "winners": []}
    markup = InlineKeyboardMarkup(row_width=1)
    for g in GAME_CONFIG: markup.add(InlineKeyboardButton(g, callback_data=f"type_{g}"))
    bot.send_message(cid, "🎮 نوع استیکر مسابقه را انتخاب کنید:", reply_markup=markup)

# 3. هندلر دکمه‌ها و بازگشت
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    cid, uid = call.message.chat.id, call.from_user.id
    data = call.data
    if cid not in games: return
    g = games[cid]

    if data.startswith("type_"):
        g["game"] = data.split("_")[1]
        markup = InlineKeyboardMarkup(row_width=1)
        for t in GAME_CONFIG[g["game"]]["targets"]: markup.add(InlineKeyboardButton(t, callback_data=f"tgt_{t}"))
        markup.add(InlineKeyboardButton("🔙 بازگشت به لیست بازی‌ها", callback_data="back_main"))
        bot.edit_message_text("🎯 هدف را انتخاب کنید:", cid, call.message.message_id, reply_markup=markup)
    elif data.startswith("tgt_"):
        g["target"] = data.split("_")[1]
        g["win_values"] = GAME_CONFIG[g["game"]]["targets"][g["target"]]
        update_reg(cid, call.message.message_id)
    elif data == "join" and len(g["players"]) < 5:
        if uid not in g["players"]:
            g["players"].append(uid); g["player_names"][uid] = call.from_user.first_name
        update_reg(cid, call.message.message_id)
    elif data == "start":
        if uid != g["creator"]: bot.answer_callback_query(call.id, "❌ فقط سازنده شروع می‌کند!")
        elif len(g["players"]) < 2: bot.answer_callback_query(call.id, "❌ حداقل ۲ نفر!")
        else:
            g["status"] = "play"
            bot.edit_message_text(f"🚀 بازی شروع شد!\nنوبت: {g['player_names'][g['players'][0]]}", cid, call.message.message_id)
    elif data == "back_main": handle_newgame(call.message)
    elif data == "back_target":
        markup = InlineKeyboardMarkup(row_width=1)
        for gn in GAME_CONFIG: markup.add(InlineKeyboardButton(gn, callback_data=f"type_{gn}"))
        bot.edit_message_text("🎮 نوع استیکر مسابقه را انتخاب کنید:", cid, call.message.message_id, reply_markup=markup)

def update_reg(cid, mid):
    g = games[cid]
    text = f"📝 لیست ثبت‌نام\nبازی: {g['game']}\nهدف: {g['target']}\n\nبازیکنان:\n" + "\n".join([f"👤 {n}" for n in g['player_names'].values()])
    m = InlineKeyboardMarkup(row_width=1)
    m.add(InlineKeyboardButton("➕ ورود", callback_data="join"), InlineKeyboardButton("🚀 شروع", callback_data="start"), InlineKeyboardButton("🔙 بازگشت", callback_data="back_target"))
    bot.edit_message_text(text, cid, mid, reply_markup=m)

# 4. منطق بازی
@bot.message_handler(content_types=['dice'])
def handle_dice(m):
    cid = m.chat.id
    if cid not in games or games[cid]["status"] != "play": return
    g = games[cid]
    if m.from_user.id != g["players"][g["turn_index"]] or m.dice.emoji != GAME_CONFIG[g["game"]]["emoji"]: return
    
    if m.dice.value in g["win_values"]:
        g["winners"].append(g["player_names"][m.from_user.id])
        bot.reply_to(m, "🎉 تبریک! شما برنده شدید. لطفاً تا پایان بازی منتظر بمانید.")
        g["players"].remove(m.from_user.id)
        if not g["players"]:
            res = "🏁 پایان بازی! رتبه‌بندی نهایی:\n" + "\n".join([f"مقام {i+1}: {g['winners'][i] if i<len(g['winners']) else '---'}" for i in range(5)])
            bot.send_message(cid, res); games.pop(cid, None); return
    else: g["turn_index"] = (g["turn_index"] + 1) % len(g["players"])
    bot.send_message(cid, f"👉 نوبت بعدی: {g['player_names'][g['players'][g['turn_index']]]}")

bot.infinity_polling()
