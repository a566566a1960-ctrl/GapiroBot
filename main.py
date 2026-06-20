import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8750954453:AAFWL7XzhN27MXVLP4JAdGmyvNFYUkeJEuo"
SUPPORT_ID = "@Hamid_18"
bot = telebot.TeleBot(BOT_TOKEN)

games = {}
GAME_CONFIG = {
    "🎲 تاس": {"emoji": "🎲", "targets": {"تاس (فقط ۶)": [6], "زوج": [2, 4, 6], "فرد": [1, 3, 5]}},
    "🎰 کازینو": {"emoji": "🎰", "targets": {"۳ تا ۷": [64], "۳ تا انگور": [43], "۳ تا لیمو": [22], "۳ تا BAR": [1]}},
    "🏀 بسکتبال": {"emoji": "🏀", "targets": {"گل قطعی (۵)": [5]}},
    "🎯 دارت": {"emoji": "🎯", "targets": {"مرکز (۶)": [6]}}
}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type != 'private': return
    text = (f"سلام! به ربات گپیرو خوش آمدید.\n\n"
            f"پشتیبانی فنی: {SUPPORT_ID}\n"
            "من را به گروه اضافه کنید و دستور /newgame را بزنید.")
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['newgame'])
def handle_newgame(message):
    if message.chat.type == 'private': return
    games[message.chat.id] = {"creator": message.from_user.id, "creator_name": message.from_user.first_name, 
                              "status": "setting", "game": None, "target": None, "win_values": [], 
                              "players": [message.from_user.id], "names": {message.from_user.id: message.from_user.first_name}, 
                              "turn_index": 0, "winners": []}
    
    markup = InlineKeyboardMarkup(row_width=1)
    for g in GAME_CONFIG: markup.add(InlineKeyboardButton(g, callback_data=f"type_{g}"))
    bot.send_message(message.chat.id, f"بازی توسط {message.from_user.first_name} ایجاد شد. نوع استیکر را انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("type_"))
def handle_type(call):
    cid = call.message.chat.id
    g_name = call.data.replace("type_", "")
    games[cid]["game"] = g_name
    markup = InlineKeyboardMarkup(row_width=1)
    for t in GAME_CONFIG[g_name]["targets"]: markup.add(InlineKeyboardButton(t, callback_data=f"tgt_{t}"))
    markup.add(InlineKeyboardButton("بازگشت", callback_data="back_to_menu"))
    bot.edit_message_text(f"استیکر انتخاب شده: {g_name}\nهدف برد را انتخاب کنید:", cid, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("tgt_"))
def handle_target(call):
    cid = call.message.chat.id
    t_name = call.data.replace("tgt_", "")
    games[cid]["target"] = t_name
    games[cid]["win_values"] = GAME_CONFIG[games[cid]["game"]]["targets"][t_name]
    update_reg_menu(cid, call.message.message_id)

def update_reg_menu(cid, mid):
    g = games[cid]
    text = (f"لیست ثبت‌نام رقابت بزرگ\nنوع: {g['game']}\nهدف: {g['target']}\n\n"
            f"بازیکنان حاضر:\n" + "\n".join([f"👤 {name}" for name in g['names'].values()]))
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("➕ موافق (ورود)", callback_data="join"),
               InlineKeyboardButton("🚀 شروع بازی", callback_data="start"),
               InlineKeyboardButton("بازگشت", callback_data="back_to_menu"))
    bot.edit_message_text(text, cid, mid, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["join", "start", "back_to_menu"])
def handle_actions(call):
    cid, uid = call.message.chat.id, call.from_user.id
    if call.data == "join":
        games[cid]["players"].append(uid)
        games[cid]["names"][uid] = call.from_user.first_name
        update_reg_menu(cid, call.message.message_id)
    elif call.data == "start":
        games[cid]["status"] = "play"
        bot.edit_message_text(f"بازی شروع شد! (سازنده: {games[cid]['creator_name']})\nنوبت: {games[cid]['names'][games[cid]['players'][0]]}", cid, call.message.message_id)
    elif call.data == "back_to_menu":
        # هدایت مجدد به انتخاب بازی
        handle_newgame(call.message)

@bot.message_handler(content_types=['dice'])
def handle_dice(m):
    cid = m.chat.id
    if cid in games and games[cid]["status"] == "play":
        g = games[cid]
        if m.from_user.id == g["players"][g["turn_index"]]:
            if m.dice.value in g["win_values"]:
                g["winners"].append(g["names"][m.from_user.id])
                bot.reply_to(m, f"{g['names'][m.from_user.id]} برنده شد!")
                g["players"].remove(m.from_user.id)
                if not g["players"]:
                    res = "پایان بازی! رتبه‌بندی:\n" + "\n".join([f"{i+1}. {w}" for i, w in enumerate(g['winners'])])
                    bot.send_message(cid, res)
                    games.pop(cid)
                    return
            g["turn_index"] = g["turn_index"] % len(g["players"])
            bot.send_message(cid, f"نوبت بعدی: {g['names'][g['players'][g['turn_index']]]}")

bot.infinity_polling()
