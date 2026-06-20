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

# هندلرهای پی‌وی
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
    text = (f"راهنمای بازی گپیرو:\n\n"
            "1. دستور /newgame را در گروه بزنید.\n"
            "2. نوع بازی و هدف را انتخاب کنید.\n"
            "3. با دکمه پیوست عضو شوید.\n"
            "4. با دکمه شروع، بازی را استارت بزنید.\n"
            "5. در نوبت خود استیکر مخصوص را بفرستید.\n\n"
            f"پشتیبانی: {SUPPORT_ID}")
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("بازگشت", callback_data="back_to_start"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_start")
def back_to_start(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_welcome(call.message)

# هندلرهای گروه
@bot.message_handler(commands=['newgame'])
def handle_newgame(message):
    if message.chat.type == 'private': return
    send_main_menu(message.chat.id, message.from_user.id, message.from_user.first_name)

def send_main_menu(chat_id, user_id, user_name, message_id=None):
    games[chat_id] = {"creator": user_id, "game_type": None, "players": [], "status": "setting"}
    markup = InlineKeyboardMarkup()
    for g_name in GAME_CONFIG.keys(): markup.add(InlineKeyboardButton(g_name, callback_data=f"type_{g_name}"))
    text = "بازی جدید ایجاد شد. نوع بازی را انتخاب کنید:"
    if message_id: bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
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
    send_main_menu(call.message.chat.id, call.from_user.id, call.from_user.first_name, call.message.message_id)

print("Gapiro v2.0 - UI Optimized...")
bot.infinity_polling()
    
