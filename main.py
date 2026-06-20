import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8750954453:AAFWL7XzhN27MXVLP4JAdGmyvNFYUkeJEuo"
bot = telebot.TeleBot(BOT_TOKEN)

games = {}

# همان ساختار بازی که در تصاویر بود
GAME_CONFIG = {
    "🎲 تاس معمولی": {"emoji": "🎲", "targets": {"تاس (فقط ۶)": [6], "زوج": [2, 4, 6], "فرد": [1, 3, 5]}},
    "🎰 ماشین اسلات": {"emoji": "🎰", "targets": {"۳ تا ۷": [64], "۳ تا انگور": [43], "۳ تا لیمو": [22], "۳ تا BAR": [1]}},
    "🏀 بسکتبال": {"emoji": "🏀", "targets": {"گل شدن قطعی (امتیاز ۵)": [5], "برخورد به حلقه و گل (۴ و ۵)": [4, 5]}},
    "🎯 دارت": {"emoji": "🎯", "targets": {"مرکز (۶)": [6]}}
}

@bot.message_handler(commands=['newgame'])
def handle_newgame(message):
    if message.chat.type == 'private': return
    
    # ساختار لیستِ انتخاب بازی (شبیه به تصویر)
    markup = InlineKeyboardMarkup(row_width=1)
    for g_name in GAME_CONFIG.keys():
        markup.add(InlineKeyboardButton(g_name, callback_data=f"type_{g_name}"))
    
    text = f"🎮 یک بازی جدید توسط {message.from_user.first_name} ایجاد شد!\n\n👇 نوع استیکر مسابقه را انتخاب کنید:"
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("type_"))
def handle_type(call):
    g_name = call.data.replace("type_", "")
    chat_id = call.message.chat.id
    games[chat_id] = {"creator": call.from_user.id, "creator_name": call.from_user.first_name, "game": g_name, "players": [call.from_user.id], "names": {call.from_user.id: call.from_user.first_name}}
    
    # ساختار انتخاب هدف (شبیه به تصویر)
    markup = InlineKeyboardMarkup(row_width=1)
    for t in GAME_CONFIG[g_name]["targets"]:
        markup.add(InlineKeyboardButton(t, callback_data=f"tgt_{t}"))
    
    bot.edit_message_text(f"✨ استیکر انتخاب شده: {GAME_CONFIG[g_name]['emoji']} {g_name}\n\n👇 حالا هدف برد (شرط وین شدن) را مشخص کنید:", 
                          chat_id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("tgt_"))
def handle_target(call):
    t_name = call.data.replace("tgt_", "")
    chat_id = call.message.chat.id
    g = games[chat_id]
    g["target"] = t_name
    
    # لیست ثبت‌نام (دقیقاً همان ظاهر تصویر)
    text = (f"📝 لیست ثبت‌نام رقابت بزرگ گروه\n\n"
            f"♦️ نوع بازی: {GAME_CONFIG[g['game']]['emoji']} {g['game']}\n"
            f"🎯 هدف برد: {GAME_CONFIG[g['game']]['emoji']} {t_name}\n\n"
            f"بازیکنان حاضر:\n👤 {g['names'][g['creator']]}")
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("➕ موافق (ورود)", callback_data="join"))
    markup.add(InlineKeyboardButton("➖ مخالف (خروج)", callback_data="leave"))
    markup.add(InlineKeyboardButton("🚀 شروع و اجرای بازی", callback_data="start"))
    
    bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)

# [هندلرهای مربوط به join, leave و logic بازی را در ادامه به همین سبک اضافه کن]

bot.infinity_polling()
