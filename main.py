import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8750954453:AAFWL7XzhN27MXVLP4JAdGmyvNFYUkeJEuo"
bot = telebot.TeleBot(BOT_TOKEN)

# دیتابیسِ موقتِ بازی‌ها
games = {}

GAME_CONFIG = {
    "🎲 تاس معمولی": {"emoji": "🎲", "targets": {"تاس (فقط ۶)": [6], "زوج": [2, 4, 6], "فرد": [1, 3, 5]}},
    "🎰 ماشین اسلات": {"emoji": "🎰", "targets": {"۳ تا ۷": [64], "۳ تا انگور": [43], "۳ تا لیمو": [22], "۳ تا BAR": [1]}},
    "🏀 بسکتبال": {"emoji": "🏀", "targets": {"گل شدن قطعی (امتیاز ۵)": [5]}},
    "🎯 دارت": {"emoji": "🎯", "targets": {"مرکز (۶)": [6]}}
}

# --- هندلر دستور شروع بازی در گروه ---
@bot.message_handler(commands=['newgame'])
def handle_newgame(message):
    if message.chat.type == 'private': return
    
    chat_id = message.chat.id
    games[chat_id] = {
        "creator": message.from_user.id,
        "creator_name": message.from_user.first_name,
        "step": "select_game",
        "game": None,
        "target": None,
        "win_values": [],
        "players": {message.from_user.id: message.from_user.first_name},
        "status": "setting"
    }
    
    markup = InlineKeyboardMarkup(row_width=1)
    for g_name in GAME_CONFIG.keys():
        markup.add(InlineKeyboardButton(g_name, callback_data=f"type_{g_name}"))
    
    bot.send_message(chat_id, f"🎮 بازی جدید توسط {message.from_user.first_name} ایجاد شد!\n👇 نوع استیکر را انتخاب کنید:", reply_markup=markup)

# --- هندلر دکمه‌ها (برای جلوگیری از باگ، هر مرحله چک می‌شود) ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    uid = call.from_user.id
    data = call.data
    
    if chat_id not in games: return

    # انتخاب نوع بازی
    if data.startswith("type_"):
        g_name = data.replace("type_", "")
        games[chat_id]["game"] = g_name
        games[chat_id]["step"] = "select_target"
        
        markup = InlineKeyboardMarkup(row_width=1)
        for t in GAME_CONFIG[g_name]["targets"]:
            markup.add(InlineKeyboardButton(t, callback_data=f"tgt_{t}"))
        markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu"))
        bot.edit_message_text(f"استیکر انتخاب شده: {g_name}\n👇 هدف برد را انتخاب کنید:", chat_id, call.message.message_id, reply_markup=markup)

    # انتخاب هدف و ورود به لیست ثبت‌نام
    elif data.startswith("tgt_"):
        t_name = data.replace("tgt_", "")
        games[chat_id]["target"] = t_name
        games[chat_id]["win_values"] = GAME_CONFIG[games[chat_id]["game"]]["targets"][t_name]
        update_registration(chat_id, call.message.message_id)

    # دکمه پیوست و شروع
    elif data == "join":
        games[chat_id]["players"][uid] = call.from_user.first_name
        update_registration(chat_id, call.message.message_id)
        
    elif data == "start_game":
        if uid != games[chat_id]["creator"]:
            bot.answer_callback_query(call.id, "❌ فقط سازنده بازی می‌تواند شروع کند!", show_alert=True)
        elif len(games[chat_id]["players"]) < 2:
            bot.answer_callback_query(call.id, "❌ حداقل ۲ نفر برای شروع لازم است!", show_alert=True)
        else:
            games[chat_id]["status"] = "playing"
            games[chat_id]["turn_list"] = list(games[chat_id]["players"].keys())
            games[chat_id]["turn_idx"] = 0
            bot.edit_message_text(f"🚀 بازی شروع شد!\nنوبت: {games[chat_id]['players'][games[chat_id]['turn_list'][0]]}", chat_id, call.message.message_id)

    elif data == "back_to_menu":
        handle_newgame(call.message)

# --- نمایش لیست ثبت‌نام ---
def update_registration(chat_id, message_id):
    g = games[chat_id]
    text = (f"📝 لیست ثبت‌نام رقابت بزرگ گروه\n\n"
            f"♦️ نوع بازی: {g['game']}\n🎯 هدف برد: {g['target']}\n\n"
            f"بازیکنان حاضر:\n" + "\n".join([f"👤 {n}" for n in g['players'].values()]))
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("➕ موافق (ورود)", callback_data="join"))
    markup.add(InlineKeyboardButton("🚀 شروع و اجرای بازی", callback_data="start_game"))
    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu"))
    bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)

bot.infinity_polling()
            
