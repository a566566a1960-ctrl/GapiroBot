import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8750954453:AAFWL7XzhN27MXVLP4JAdGmyvNFYUkeJEuo"
SUPPORT_ID = "@Hamid_18"
bot = telebot.TeleBot(BOT_TOKEN)

games = {}
GAME_CONFIG = {
    "🎲 تاس": {"emoji": "🎲", "custom_targets": {"تاس (فقط ۶)": [6], "زوج": [2, 4, 6], "فرد": [1, 3, 5]}},
    "🎰 کازینو": {"emoji": "🎰", "custom_targets": {"۳ تا ۷": [64], "۳ تا انگور": [43], "۳ تا لیمو": [22], "۳ تا BAR": [1]}},
    "🏀 بسکتبال": {"emoji": "🏀", "custom_targets": {"گل قطعی (۵)": [5]}},
    "🎯 دارت": {"emoji": "🎯", "custom_targets": {"مرکز (۶)": [6]}}
}

# --- بخش پی‌وی و پشتیبانی ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type != 'private': return
    text = (f"سلام! به ربات گپیرو خوش آمدید.\n\n"
            f"پشتیبانی فنی: {SUPPORT_ID}\n"
            "من را به گروه اضافه کنید و دستور /newgame را بزنید.")
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("راهنمای بازی", callback_data="show_help"))
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "show_help")
def show_help(call):
    text = (f"راهنمای بازی گپیرو:\n\n1. دستور /newgame را بزنید.\n2. انتخاب نوع و هدف بازی.\n3. پیوستن و شروع توسط سازنده.\n4. ارسال استیکر در نوبت.\n\nپشتیبانی: {SUPPORT_ID}")
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("بازگشت", callback_data="back_to_start"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_start")
def back_to_start(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_welcome(call.message)

# --- مدیریت بازی در گروه ---
@bot.message_handler(commands=['newgame'])
def handle_newgame(message):
    if message.chat.type == 'private': return
    games[message.chat.id] = {"creator": message.from_user.id, "creator_name": message.from_user.first_name, "game_type": None, "players": [], "player_names": {}, "status": "setting", "turn_index": 0, "winners": []}
    send_main_menu(message.chat.id, message.message_id)

def send_main_menu(chat_id, message_id=None):
    markup = InlineKeyboardMarkup()
    for g_name in GAME_CONFIG.keys(): markup.add(InlineKeyboardButton(g_name, callback_data=f"type_{g_name}"))
    text = "بازی جدید ایجاد شد. نوع بازی را انتخاب کنید:"
    if message_id: bot.send_message(chat_id, text, reply_markup=markup)
    else: bot.send_message(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("type_"))
def handle_type(call):
    chat_id, g_name = call.message.chat.id, call.data.replace("type_", "")
    games[chat_id]["game_type"] = g_name
    markup = InlineKeyboardMarkup()
    for t in GAME_CONFIG[g_name]["custom_targets"]: markup.add(InlineKeyboardButton(t, callback_data=f"tgt_{t}"))
    markup.add(InlineKeyboardButton("بازگشت", callback_data="back_to_main"))
    bot.edit_message_text("هدف برد را انتخاب کنید:", chat_id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def handle_back(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_main_menu(call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("tgt_"))
def handle_target(call):
    chat_id, t_name = call.message.chat.id, call.data.replace("tgt_", "")
    g = games[chat_id]
    g["target_name"] = t_name
    g["win_values"] = GAME_CONFIG[g["game_type"]]["custom_targets"][t_name]
    g["status"] = "reg"
    if g["creator"] not in g["players"]:
        g["players"].append(g["creator"]); g["player_names"][g["creator"]] = g["creator_name"]
    show_reg(chat_id, call.message.message_id)

def show_reg(chat_id, mid):
    g = games[chat_id]
    text = (f"ثبت‌نام گپیرو\nسازنده: {g['creator_name']}\nنوع: {g['game_type']}\nهدف: {g['target_name']}\n\n"
            f"تعداد شرکت‌کنندگان: {len(g['players'])}\nلیست بازیکنان: {', '.join(g['player_names'].values())}")
    m = InlineKeyboardMarkup()
    m.add(InlineKeyboardButton("پیوست", callback_data="join"), InlineKeyboardButton("شروع", callback_data="start"))
    bot.edit_message_text(text, chat_id, mid, reply_markup=m)

@bot.callback_query_handler(func=lambda call: call.data in ["join", "start"])
def handle_reg_actions(call):
    chat_id, uid = call.message.chat.id, call.from_user.id
    if call.data == "join" and uid not in games[chat_id]["players"]:
        games[chat_id]["players"].append(uid)
        games[chat_id]["player_names"][uid] = call.from_user.first_name
        show_reg(chat_id, call.message.message_id)
    elif call.data == "start" and uid == games[chat_id]["creator"]:
        games[chat_id]["status"] = "play"
        bot.edit_message_text(f"بازی شروع شد! (سازنده: {games[chat_id]['creator_name']})\nنوبت: {games[chat_id]['player_names'][games[chat_id]['players'][0]]}", chat_id, call.message.message_id)

@bot.message_handler(content_types=['dice'])
def handle_dice(m):
    cid = m.chat.id
    if cid in games and games[cid]["status"] == "play":
        g = games[cid]
        if m.from_user.id == g["players"][g["turn_index"]] and m.dice.emoji == GAME_CONFIG[g["game_type"]]["emoji"]:
            if m.dice.value in g["win_values"]:
                g["winners"].append(g["player_names"][m.from_user.id])
                bot.reply_to(m, f"{g['player_names'][m.from_user.id]} برنده شد!")
                g["players"].remove(m.from_user.id)
                if not g["players"]:
                    res = "پایان بازی! رتبه‌بندی نهایی:\n" + "\n".join([f"{i+1}. {w}" for i, w in enumerate(g['winners'])])
                    bot.send_message(cid, res)
                    games.pop(cid)
            else:
                g["turn_index"] = (g["turn_index"] + 1) % len(g["players"])
                bot.send_message(cid, f"نوبت بعدی: {g['player_names'][g['players'][g['turn_index']]]}")

bot.infinity_polling()
    
