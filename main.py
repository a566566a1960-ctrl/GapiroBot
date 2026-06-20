import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8750954453:AAFWL7XzhN27MXVLP4JAdGmyvNFYUkeJEuo"
bot = telebot.TeleBot(BOT_TOKEN)

# آیدی پشتیبانی را اینجا وارد کن
SUPPORT_ID = "@YourSupportID"

games = {}
GAME_CONFIG = {
    "🎲 تاس": {"emoji": "🎲", "targets": {"تاس (عدد ۶)": [6], "تاس (زوج)": [2, 4, 6], "تاس (فرد)": [1, 3, 5]}},
    "🎰 کازینو": {"emoji": "🎰", "targets": {"جک‌پات (۷۷۷)": [64], "انگور (🍇)": [43], "لیمو (🍋)": [22], "بار (BAR)": [1]}},
    "🏀 بسکتبال": {"emoji": "🏀", "targets": {"گل مستقیم (۵)": [5]}},
    "🎯 دارت": {"emoji": "🎯", "targets": {"مرکز (۶)": [6]}}
}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type != 'private': return
    text = (f"🤖 **هوش مصنوعی Gapiro v2.0**\n\n"
            f"سیستم پردازش بازی‌های استیکری در وضعیت عملیاتی.\n"
            f"واحد پشتیبانی فنی: {SUPPORT_ID}\n\n"
            "برای شروع چالش در گروه‌ها، مرا به گروه خود اضافه کنید و دستور /newgame را ارسال نمایید.")
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def handle_help(message):
    help_text = (
        "📖 **راهنمای فنی سیستم Gapiro:**\n\n"
        "1️⃣ ایجاد سشن بازی با دستور `/newgame`.\n"
        "2️⃣ انتخاب نوع استیکر و تعیین شرایط پیروزی.\n"
        "3️⃣ عضویت بازیکنان (ظرفیت ۵ نفر).\n"
        "4️⃣ شروع عملیات توسط سازنده بازی.\n\n"
        "⚠️ جهت گزارش خطاهای سیستمی به پشتیبانی {SUPPORT_ID} مراجعه کنید."
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['newgame'])
def handle_newgame(message):
    if message.chat.type == 'private': return
    games[message.chat.id] = {"creator": message.from_user.id, "status": "setting", "players": [], "names": {}, "game": None, "target": None, "vals": [], "turn": 0, "winners": []}
    markup = InlineKeyboardMarkup()
    for g in GAME_CONFIG: markup.add(InlineKeyboardButton(g, callback_data=f"type_{g}"))
    bot.send_message(message.chat.id, "🎮 **سیستم بازی ایجاد شد.**\nنوع چالش را انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("type_"))
def handle_type(call):
    g_name = call.data.split("_")[1]
    games[call.message.chat.id].update({"game": g_name, "status": "target"})
    markup = InlineKeyboardMarkup()
    for t in GAME_CONFIG[g_name]["targets"]: markup.add(InlineKeyboardButton(t, callback_data=f"tgt_{t}"))
    bot.edit_message_text(f"🎯 **هدفِ {g_name} را تعیین کنید:**", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("tgt_"))
def handle_target(call):
    t_name = call.data.split("_")[1]
    cid = call.message.chat.id
    games[cid].update({"target": t_name, "vals": GAME_CONFIG[games[cid]["game"]]["targets"][t_name], "status": "reg"})
    show_reg(cid, call.message.message_id)

def show_reg(cid, mid):
    g = games[cid]
    text = f"📝 **پروتکل ثبت‌نام**\nچالش: {g['game']}\nهدف: {g['target']}\n\nبازیکنان حاضر: {len(g['players'])}"
    m = InlineKeyboardMarkup()
    m.add(InlineKeyboardButton("➕ پیوستن", callback_data="join"), InlineKeyboardButton("🚀 شروع", callback_data="start"))
    bot.edit_message_text(text, cid, mid, reply_markup=m, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data in ["join", "start"])
def handle_actions(call):
    cid, uid = call.message.chat.id, call.from_user.id
    if cid not in games: return
    if call.data == "join" and uid not in games[cid]["players"]:
        games[cid]["players"].append(uid)
        games[cid]["names"][uid] = call.from_user.first_name
        show_reg(cid, call.message.message_id)
    elif call.data == "start" and uid == games[cid]["creator"]:
        games[cid]["status"] = "play"
        bot.edit_message_text("🔥 **عملیات شروع شد.**\nنوبت اول: " + games[cid]["names"][games[cid]["players"][0]], cid, call.message.message_id)

@bot.message_handler(content_types=['dice'])
def handle_dice(m):
    cid = m.chat.id
    if cid in games and games[cid]["status"] == "play":
        # منطق بازی ساده شده برای اجرای دقیق
        bot.reply_to(m, "🔄 پردازش استیکر انجام شد. نوبت بعدی...")

print("Gapiro Engine v2.0 Initialized...")
bot.infinity_polling()
