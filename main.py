import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8750954453:AAFWL7XzhN27MXVLP4JAdGmyvNFYUkeJEuo"
bot = telebot.TeleBot(BOT_TOKEN)

games = {}

GAME_CONFIG = {
    "🎲 تاس": {"emoji": "🎲", "custom_targets": {"🎲 تاس (فقط ۶)": [6], "🎲 زوج": [2, 4, 6], "🎲 فرد": [1, 3, 5]}},
    "🎰 کازینو": {"emoji": "🎰", "custom_targets": {"🎰 ۳ تا ۷": [64], "🍇 ۳ تا انگور": [43], "🍋 ۳ تا لیمو": [22], "🎰 ۳ تا BAR": [1]}},
    "🏀 بسکتبال": {"emoji": "🏀", "custom_targets": {"🗑 گل قطعی (۵)": [5]}},
    "🎯 دارت": {"emoji": "🎯", "custom_targets": {"🎯 مرکز (۶)": [6]}}
}

# 1. هندلر دستور شروع (فقط در پیوی)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type != 'private': return
    text = ("🎮 **به ربات گپیرو (Gapiro) خوش آمدید!**\n\n"
            "این ربات برای مسابقات استیکری در گروه‌ها طراحی شده است.\n"
            "برای شروع در گروه، دستور /newgame را بزنید.")
    bot.send_message(message.chat.id, text)

# 2. هندلر دستور راهنما (در گروه)
@bot.message_handler(commands=['help'])
def handle_help(message):
    help_text = (
        "📖 **راهنمای بازی گپیرو:**\n\n"
        "1️⃣ دستور `/newgame` را در گروه بزنید.\n"
        "2️⃣ نوع استیکر و هدف را انتخاب کنید.\n"
        "3️⃣ با دکمه «➕ پیوست» عضو شوید.\n"
        "4️⃣ سازنده بازی را «🚀 شروع» کند.\n"
        "5️⃣ در نوبت خود استیکر مخصوص را بفرستید."
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

# 3. هندلر دستور شروع بازی (در گروه)
@bot.message_handler(commands=['newgame'])
def handle_newgame(message):
    if message.chat.type == 'private': return
    send_main_menu(message.chat.id, message.from_user.id, message.from_user.first_name)

def send_main_menu(chat_id, user_id, user_name, message_id=None):
    games[chat_id] = {"creator": user_id, "creator_name": user_name, "status": "setting_type", 
                      "game_type": None, "target_name": None, "win_values": [], 
                      "players": [], "player_names": {}, "turn_index": 0, "winners": []}
    markup = InlineKeyboardMarkup()
    for g_name in GAME_CONFIG.keys(): markup.add(InlineKeyboardButton(g_name, callback_data=f"type_{g_name}"))
    markup.add(InlineKeyboardButton("📖 راهنما", callback_data="show_help"))
    text = f"🎮 بازی جدید توسط {user_name} ایجاد شد!\n\n👇 نوع استیکر را انتخاب کنید:"
    if message_id: bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
    else: bot.send_message(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "show_help")
def show_help_alert(call):
    bot.answer_callback_query(call.id, "راهنما: در نوبت خود استیکر مشخص شده را بفرستید تا به هدف برسید.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def handle_back(call):
    chat_id = call.message.chat.id
    if chat_id in games and games[chat_id]["creator"] == call.from_user.id:
        send_main_menu(chat_id, call.from_user.id, call.from_user.first_name, call.message.message_id)
        bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("type_"))
def handle_type(call):
    chat_id, g_name = call.message.chat.id, call.data.replace("type_", "")
    if chat_id not in games or games[chat_id]["creator"] != call.from_user.id: return
    games[chat_id]["game_type"] = g_name
    markup = InlineKeyboardMarkup()
    for t in GAME_CONFIG[g_name]["custom_targets"]: markup.add(InlineKeyboardButton(t, callback_data=f"tgt_{t}"))
    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main"))
    bot.edit_message_text("🎯 هدف برد را انتخاب کنید:", chat_id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("tgt_"))
def handle_target(call):
    chat_id, t_name = call.message.chat.id, call.data.replace("tgt_", "")
    if chat_id not in games: return
    g = games[chat_id]
    g["target_name"] = t_name
    g["win_values"] = GAME_CONFIG[g["game_type"]]["custom_targets"][t_name]
    g["status"] = "reg"
    if g["creator"] not in g["players"]:
        g["players"].append(g["creator"]); g["player_names"][g["creator"]] = g["creator_name"]
    show_reg(chat_id, call.message.message_id)

def show_reg(chat_id, mid):
    g = games[chat_id]
    pls = "\n".join([f"👤 {n}" for n in g["player_names"].values()])
    text = f"📝 **ثبت‌نام گپیرو**\nنوع: {g['game_type']}\nهدف: {g['target_name']}\n\nبازیکنان:\n{pls}"
    m = InlineKeyboardMarkup()
    if len(g["players"]) < 5: m.add(InlineKeyboardButton("➕ پیوست", callback_data="join"))
    m.add(InlineKeyboardButton("🚀 شروع", callback_data="start"), InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main"))
    bot.edit_message_text(text, chat_id, mid, reply_markup=m, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data in ["join", "start"])
def handle_reg_actions(call):
    chat_id, uid = call.message.chat.id, call.from_user.id
    if chat_id not in games: return
    g = games[chat_id]
    if call.data == "join":
        if uid not in g["players"] and len(g["players"]) < 5:
            g["players"].append(uid); g["player_names"][uid] = call.from_user.first_name
            show_reg(chat_id, call.message.message_id)
    elif call.data == "start" and uid == g["creator"]:
        if len(g["players"]) < 2: bot.answer_callback_query(call.id, "حداقل ۲ نفر!", show_alert=True)
        else:
            g["status"] = "play"
            bot.edit_message_text(f"🔥 بازی شروع شد!\nنوبت: {g['player_names'][g['players'][0]]}", chat_id, call.message.message_id)

@bot.message_handler(content_types=['dice'])
def handle_dice(m):
    cid, uid = m.chat.id, m.from_user.id
    if cid not in games or games[cid]["status"] != "play": return
    g = games[cid]
    if uid != g["players"][g["turn_index"]] or m.dice.emoji != GAME_CONFIG[g["game_type"]]["emoji"]: return
    if m.dice.value in g["win_values"]:
        g["winners"].append(uid)
        bot.reply_to(m, f"🎉 {g['player_names'][uid]} برنده شد!")
        g["players"].remove(uid)
        if not g["players"]: end_game(cid); return
        g["turn_index"] %= len(g["players"])
    else: g["turn_index"] = (g["turn_index"] + 1) % len(g["players"])
    bot.send_message(cid, f"👉 نوبت: {g['player_names'][g['players'][g['turn_index']]]}")

def end_game(cid):
    g = games[cid]
    res = "🏁 پایان گپیرو:\n" + "\n".join([f"رتبه {i+1}: {g['player_names'][w]}" for i, w in enumerate(g['winners'])])
    bot.send_message(cid, res); games.pop(cid, None)

print("گپیرو روشن شد...")
bot.infinity_polling()
    
