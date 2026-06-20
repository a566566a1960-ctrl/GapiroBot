import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading

BOT_TOKEN = "8750954453:AAFWL7XzhN27MXVLP4JAdGmyvNFYUkeJEuo"
bot = telebot.TeleBot(BOT_TOKEN)

games = {}
GAME_CONFIG = {
    "🎲 تاس": {"emoji": "🎲", "targets": {"تاس ۶": [6], "زوج": [2, 4, 6], "فرد": [1, 3, 5]}},
    "🎰 کازینو": {"emoji": "🎰", "targets": {"۳ تا ۷": [64], "۳ تا انگور": [43], "۳ تا لیمو": [22], "۳ تا BAR": [1]}},
    "🏀 بسکتبال": {"emoji": "🏀", "targets": {"گل قطعی (۵)": [5]}},
    "🎯 دارت": {"emoji": "🎯", "targets": {"مرکز (۶)": [6]}}
}

def delete_later(cid, mid):
    def delete():
        try: bot.delete_message(cid, mid)
        except: pass
    threading.Timer(120, delete).start()

# راهنمای پی‌وی (دقیق مطابق عکس)
@bot.message_handler(commands=['start'])
def send_welcome(m):
    if m.chat.type == 'private':
        text = ("🎮 به ربات گپیرو (Gapiro) خوش آمدید!\n\n"
                "راهنمای جامع بازی:\n"
                "۱. ایجاد بازی: در گروه دستور /newgame را بزنید.\n"
                "۲. تنظیمات: نوع استیکر و شرط پیروزی را انتخاب کنید.\n"
                "۳. ثبت‌نام: اعضا با دکمه پیوست به بازی اضافه می‌شوند (۲ تا ۵ نفر).\n"
                "۴. شروع: سازنده دکمه شروع را می‌زند.\n"
                "۵. قوانین حرکت: هر بازیکن فقط در نوبت خود باید استیکر مربوطه را بفرستد.\n"
                "۶. پیروزی: اولین کسی که به هدف بزند برنده است. بازی تا مشخص شدن تمام رتبه‌ها ادامه می‌یابد.\n\n"
                "پشتیبانی: برای ارتباط با ادمین از دکمه زیر استفاده کنید.")
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("پشتیبانی: Hamid_18", url="https://t.me/Hamid_18"))
        bot.send_message(m.chat.id, text, reply_markup=markup)

@bot.message_handler(commands=['help', 'help@Hamid_18bot'])
def send_help(m):
    msg = bot.reply_to(m, "راهنمای بازی: /newgame را در گروه بزنید.")
    delete_later(m.chat.id, msg.message_id)

@bot.message_handler(commands=['newgame'])
def handle_newgame(m):
    if m.chat.type == 'private': return
    cid = m.chat.id
    games[cid] = {"creator": m.from_user.id, "game": None, "target": None, "win_values": [], 
                  "players": [m.from_user.id], "player_names": {m.from_user.id: m.from_user.first_name}, 
                  "status": "select_game", "turn_index": 0, "winners": []}
    markup = InlineKeyboardMarkup(row_width=1)
    for g in GAME_CONFIG: markup.add(InlineKeyboardButton(g, callback_data=f"type_{g}"))
    bot.send_message(cid, "🎮 نوع استیکر را انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    cid, uid = call.message.chat.id, call.from_user.id
    data = call.data
    if cid not in games: return
    g = games[cid]
    
    # محدودیت سازنده فقط در گروه
    if call.message.chat.type != 'private' and data in ["back_main", "back_target", "type_", "tgt_"] and uid != g["creator"]:
        bot.answer_callback_query(call.id, "❌ فقط سازنده!")
        return

    if data == "back_main":
        m = InlineKeyboardMarkup(row_width=1)
        for gn in GAME_CONFIG: m.add(InlineKeyboardButton(gn, callback_data=f"type_{gn}"))
        bot.edit_message_text("🎮 نوع استیکر را انتخاب کنید:", cid, call.message.message_id, reply_markup=m)
    elif data == "back_target":
        m = InlineKeyboardMarkup(row_width=1)
        for t in GAME_CONFIG[g["game"]]["targets"]: m.add(InlineKeyboardButton(t, callback_data=f"tgt_{t}"))
        m.add(InlineKeyboardButton("🔙 بازگشت به لیست", callback_data="back_main"))
        bot.edit_message_text("🎯 هدف را انتخاب کنید:", cid, call.message.message_id, reply_markup=m)
    elif data.startswith("type_"):
        g["game"] = data.split("_")[1]
        m = InlineKeyboardMarkup(row_width=1)
        for t in GAME_CONFIG[g["game"]]["targets"]: m.add(InlineKeyboardButton(t, callback_data=f"tgt_{t}"))
        m.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
        bot.edit_message_text("🎯 هدف را انتخاب کنید:", cid, call.message.message_id, reply_markup=m)
    elif data.startswith("tgt_"):
        g["target"] = data.split("_")[1]; g["win_values"] = GAME_CONFIG[g["game"]]["targets"][g["target"]]; g["status"] = "reg"
        update_reg(cid, call.message.message_id)
    elif data == "join" and g["status"] == "reg" and len(g["players"]) < 5:
        if uid not in g["players"]: g["players"].append(uid); g["player_names"][uid] = call.from_user.first_name
        update_reg(cid, call.message.message_id)
    elif data == "start" and g["status"] == "reg":
        if uid != g["creator"]: bot.answer_callback_query(call.id, "❌ فقط سازنده!")
        elif len(g["players"]) < 2: bot.answer_callback_query(call.id, "حداقل ۲ نفر!")
        else: g["status"] = "play"; bot.edit_message_text(f"🚀 شروع!\nنوبت: {g['player_names'][g['players'][0]]}", cid, call.message.message_id)

def update_reg(cid, mid):
    g = games[cid]
    text = f"📝 لیست:\nبازی: {g['game']}\nهدف: {g['target']}\n\nبازیکنان:\n" + "\n".join([f"👤 {n}" for n in g['player_names'].values()])
    m = InlineKeyboardMarkup(row_width=1)
    m.add(InlineKeyboardButton("➕ ورود", callback_data="join"), InlineKeyboardButton("🚀 شروع", callback_data="start"), InlineKeyboardButton("🔙 بازگشت", callback_data="back_target"))
    bot.edit_message_text(text, cid, mid, reply_markup=m)

@bot.message_handler(content_types=['dice'])
def handle_dice(m):
    cid = m.chat.id
    if cid not in games or games[cid]["status"] != "play": return
    g = games[cid]
    if m.from_user.id != g["players"][g["turn_index"]] or m.dice.emoji != GAME_CONFIG[g["game"]]["emoji"]: return
    if m.dice.value in g["win_values"]:
        g["winners"].append(g["player_names"][m.from_user.id])
        bot.reply_to(m, "🎉 تبریک! منتظر بمانید.")
        g["players"].remove(m.from_user.id)
        if not g["players"]:
            res = "🏁 پایان بازی! رتبه‌بندی:\n" + "\n".join([f"مقام {i+1}: {g['winners'][i] if i<len(g['winners']) else '---'}" for i in range(5)])
            bot.send_message(cid, res); games.pop(cid, None); return
    else: g["turn_index"] = (g["turn_index"] + 1) % len(g["players"])
    msg = bot.send_message(cid, f"👉 نوبت: {g['player_names'][g['players'][g['turn_index']]]}")
    delete_later(cid, msg.message_id)

bot.infinity_polling()
        
