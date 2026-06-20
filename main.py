import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8750954453:AAFWL7XzhN27MXVLP4JAdGmyvNFYUkeJEuo"
SUPPORT_ID = "@Hamid_18"
bot = telebot.TeleBot(BOT_TOKEN)

games = {}
GAME_CONFIG = {
    "🏀 بسکتبال": {"emoji": "🏀", "targets": {"گل قطعی (۵)": [5]}},
    "🎯 دارت": {"emoji": "🎯", "targets": {"مرکز (۶)": [6]}},
    "🎲 تاس": {"emoji": "🎲", "targets": {"تاس ۶": [6], "زوج": [2, 4, 6]}}
}

# 1. ظاهر پی‌وی دقیق طبق عکس
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type != 'private': return
    text = ("🎮 به ربات گپیرو (Gapiro) خوش آمدید!\n\n"
            "راهنمای جامع بازی:\n"
            "۱. ایجاد بازی: در گروه دستور newgame/ را بزنید.\n"
            "۲. تنظیمات: نوع استیکر و شرط پیروزی را انتخاب کنید.\n"
            "۳. ثبت‌نام: اعضا با دکمه پیوست به بازی اضافه می‌شوند (۲ تا ۵ نفر).\n"
            "۴. شروع: سازنده دکمه شروع را می‌زند.\n"
            "۵. قوانین حرکت: هر بازیکن فقط در نوبت خود باید استیکر مربوطه را بفرستد.\n"
            "۶. پیروزی: اولین کسی که به هدف بزند برنده است. بازی تا مشخص شدن تمام رتبه‌ها ادامه می‌یابد.\n\n"
            "پشتیبانی: برای ارتباط با ادمین از دکمه زیر استفاده کنید.")
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("پشتیبانی: Hamid_18", url=f"https://t.me/{SUPPORT_ID.replace('@', '')}"))
    bot.send_message(message.chat.id, text, reply_markup=markup)

# 2. مدیریت بازی
@bot.message_handler(commands=['newgame'])
def handle_newgame(message):
    if message.chat.type == 'private': return
    games[message.chat.id] = {
        "creator": message.from_user.id, "creator_name": message.from_user.first_name,
        "game": None, "win_values": [], "players": [message.from_user.id],
        "names": {message.from_user.id: message.from_user.first_name},
        "status": "setting", "turn_index": 0, "winners": []
    }
    markup = InlineKeyboardMarkup()
    for g in GAME_CONFIG: markup.add(InlineKeyboardButton(g, callback_data=f"type_{g}"))
    bot.send_message(message.chat.id, "انتخاب نوع استیکر مسابقه:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("type_"))
def handle_type(call):
    cid = call.message.chat.id
    g = call.data.replace("type_", "")
    games[cid]["game"] = g
    markup = InlineKeyboardMarkup()
    for t in GAME_CONFIG[g]["targets"]: markup.add(InlineKeyboardButton(t, callback_data=f"tgt_{t}"))
    bot.edit_message_text(f"استیکر انتخاب شده: {g}\nهدف را انتخاب کنید:", cid, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("tgt_"))
def handle_target(call):
    cid = call.message.chat.id
    t = call.data.replace("tgt_", "")
    games[cid]["win_values"] = GAME_CONFIG[games[cid]["game"]]["targets"][t]
    update_reg(cid, call.message.message_id)

def update_reg(cid, mid):
    g = games[cid]
    text = f"لیست ثبت‌نام رقابت بزرگ\n\nبازیکنان حاضر ({len(g['players'])}/5):\n" + "\n".join([f"👤 {n}" for n in g['names'].values()])
    markup = InlineKeyboardMarkup()
    if len(g['players']) < 5: markup.add(InlineKeyboardButton("➕ پیوست", callback_data="join"))
    markup.add(InlineKeyboardButton("🚀 شروع بازی", callback_data="start"))
    bot.edit_message_text(text, cid, mid, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["join", "start"])
def handle_actions(call):
    cid, uid = call.message.chat.id, call.from_user.id
    if call.data == "join" and uid not in games[cid]["players"]:
        games[cid]["players"].append(uid)
        games[cid]["names"][uid] = call.from_user.first_name
        update_reg(cid, call.message.message_id)
    elif call.data == "start":
        if uid != games[cid]["creator"]:
            bot.answer_callback_query(call.id, "فقط سازنده بازی می‌تواند بازی را شروع کند!", show_alert=True)
        elif len(games[cid]["players"]) < 2:
            bot.answer_callback_query(call.id, "حداقل ۲ نفر برای شروع لازم است!", show_alert=True)
        else:
            games[cid]["status"] = "play"
            bot.edit_message_text(f"بازی شروع شد!\nنوبت: {games[cid]['names'][games[cid]['players'][0]]}", cid, call.message.message_id)

@bot.message_handler(content_types=['dice'])
def handle_dice(m):
    cid = m.chat.id
    if cid in games and games[cid]["status"] == "play":
        g = games[cid]
        if m.from_user.id == g["players"][g["turn_index"]] and m.dice.emoji == GAME_CONFIG[g["game"]]["emoji"]:
            if m.dice.value in g["win_values"]:
                g["winners"].append(g["names"][m.from_user.id])
                g["players"].remove(m.from_user.id)
                bot.reply_to(m, f"🎉 {g['names'][m.from_user.id]} برنده شد!")
                if not g["players"]:
                    bot.send_message(cid, "پایان بازی! رتبه‌بندی:\n" + "\n".join([f"{i+1}. {w}" for i, w in enumerate(g['winners'])]))
                    games.pop(cid); return
            g["turn_index"] = g["turn_index"] % len(g["players"])
            bot.send_message(cid, f"نوبت بعدی: {g['names'][g['players'][g['turn_index']]]}")

bot.infinity_polling()
