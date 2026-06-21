import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
import threading
import json
import os
import random

BOT_TOKEN = "8750954453:AAE6fj3Zpo7d2BKWq8WyDROMxOwHIql6H64"
bot = telebot.TeleBot(BOT_TOKEN)

bot.set_my_commands([
    BotCommand("newgame", "🎮 شروع بازی جدید"),
    BotCommand("help", "📜 راهنمای بازی"),
    BotCommand("top", "🏆 جدول برترین‌ها"),
    BotCommand("leave", "🚪 خروج از بازی"),
    BotCommand("stats", "📊 آمار ربات"),
    BotCommand("about", "ℹ️ درباره ربات")
])

SCORE_FILE = "scores.json"
STATS_FILE = "stats.json"
games = {}
lock = threading.Lock()
file_lock = threading.Lock()

GAME_CONFIG = {
    "🎲 تاس": {"emoji": "🎲", "targets": ["🎯 شیش آوردن", "🎲 زوج", "🎲 فرد", "💫 یک یا شیش", "⭐ سه یا چهار"], "values": [[6], [2,4,6], [1,3,5], [1,6], [3,4]]},
    "⚽ فوتبال": {"emoji": "⚽", "targets": ["⚽ گل", "🥅 تیرک دروازه", "🚩 آفساید", "🟥 کارت قرمز", "🟨 کارت زرد"], "values": [[5], [4], [3], [2], [1]]},
    "🏀 بسکتبال": {"emoji": "🏀", "targets": ["🏀 گل", "💫 حلقه", "💨 هوا"], "values": [[5], [2,3,4], [1]]},
    "🎯 دارت": {"emoji": "🎯", "targets": ["🎯 مرکز", "🎯 نزدیک مرکز", "🎯 حاشیه"], "values": [[6], [4,5], [1,2,3]]},
    "🎳 بولینگ": {"emoji": "🎳", "targets": ["💥 استرایک", "🎳 نیمه استرایک", "😅 گاتر"], "values": [[6], [4,5], [1]]}
}

MEDALS = ["🥇", "🥈", "🥉"]
POINTS = [5, 3, 1, 0, -1]
FAIL_MSG = [
    "💀 جواد بمیره برات که نتونستی ببری",
    "🍆 جواد با ۲۷ تا سیاه پوست بخوابه باخت ترو نبینم",
    "🍑 جواد سر چهار راه کون بده شکستتو نبینم",
    "👯 جواد فمبوی بشه زمین خوردنتو نبینم",
    "🍽 قصه نخور باختی ولی عوضش جواد بهت کون میده"
]
OWNER_NAME = "𝙃𝘼𝙈𝙄𝘿"
OWNER_SCORE = 10000

def load_json(filename, default):
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return default

def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

def get_stats():
    return load_json(STATS_FILE, {"total_games": 0, "total_players": 0, "total_dice_rolls": 0})

def update_stats(game_type=None, players_count=0):
    with file_lock:
        s = get_stats()
        s["total_games"] = s.get("total_games", 0) + 1
        s["total_players"] = s.get("total_players", 0) + players_count
        save_json(STATS_FILE, s)

def increment_dice_rolls():
    with file_lock:
        s = get_stats()
        s["total_dice_rolls"] = s.get("total_dice_rolls", 0) + 1
        save_json(STATS_FILE, s)

def save_rank_scores(winners_list):
    with file_lock:
        scores = load_json(SCORE_FILE, {})
        for i, name in enumerate(winners_list):
            if i < len(POINTS):
                scores[name] = scores.get(name, 0) + POINTS[i]
        save_json(SCORE_FILE, scores)

def get_top_scores():
    scores = load_json(SCORE_FILE, {})
    scores[OWNER_NAME] = OWNER_SCORE
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]

def build_results(winners, dice_count=0):
    t = "🏁 **بازی تموم شد!**\n\n▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n\n📊 **رتبه‌بندی نهایی:**\n\n"
    for i, name in enumerate(winners, 1):
        m = MEDALS[i-1] if i <= 3 else "🏅"
        p = POINTS[i-1] if i < len(POINTS) else 0
        t += m + " **مقام " + str(i) + ":** " + name + " _(+" + str(p) + " امتیاز)_\n"
    if dice_count > 0:
        t += "\n🎲 پرتاب‌ها: **" + str(dice_count) + "**"
    t += "\n\n✅ **امتیازات ثبت شد!** 🎉"
    return t

def main_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("📜 راهنمای بازی", callback_data="pv_help"), InlineKeyboardButton("🏆 برترین‌ها", callback_data="pv_top"), InlineKeyboardButton("🎮 بازی‌ها", callback_data="pv_games"), InlineKeyboardButton("❓ سوالات", callback_data="pv_faq"), InlineKeyboardButton("📊 آمار", callback_data="pv_stats"), InlineKeyboardButton("📞 ادمین", url="https://t.me/Hamid_18"))
    return kb

def safe_edit(call, text, kb=None):
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
    except:
        try:
            bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="Markdown")
        except:
            pass

@bot.message_handler(commands=['start'])
def start_cmd(m):
    if m.chat.type == "private":
        bot.send_message(m.chat.id, "✨ سلام " + m.from_user.first_name + "!\n\n🎲 به گپیرو خوش اومدی!\n📌 تو گروه /newgame رو بزن.", reply_markup=main_menu(), parse_mode="Markdown")
    else:
        bot.send_message(m.chat.id, "👋 سلام!\n🎮 به پی‌وی من سر بزن: @GapiroBot")

@bot.message_handler(commands=['help'])
def help_cmd(m):
    if m.chat.type == "private":
        start_cmd(m)
    else:
        bot.reply_to(m, "📜 به پی‌وی ربات سر بزن!")

@bot.message_handler(commands=['stats'])
def stats_cmd(m):
    s = get_stats()
    bot.reply_to(m, "📊 بازی‌ها: " + str(s.get('total_games',0)) + " | بازیکنان: " + str(s.get('total_players',0)) + " | دایس‌ها: " + str(s.get('total_dice_rolls',0)), parse_mode="Markdown")

@bot.message_handler(commands=['about'])
def about_cmd(m):
    bot.reply_to(m, "🤖 گپیرو نسخه ۲\n🎮 ربات بازی‌های گروهی\n👨‍💻 @Hamid_18")

@bot.message_handler(commands=['top'])
def show_top(m):
    ss = get_top_scores()
    t = "🏆 **برترین‌ها**\n\n"
    for i, (name, score) in enumerate(ss, 1):
        t += (MEDALS[i-1] if i<=3 else "🏅") + " **" + name + "**: " + str(score) + " امتیاز\n"
    bot.reply_to(m, t, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "pv_help")
def pv_help(call):
    t = "📜 **راهنما**\n\n🎯 /newgame تو گروه\n🎲 استیکر مخصوص بفرست\n🏆 اول:۵ دوم:۳ سوم:۱"
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 منو", callback_data="pv_menu"))
    safe_edit(call, t, kb)

@bot.callback_query_handler(func=lambda call: call.data == "pv_games")
def pv_games(call):
    t = "🎮 **بازی‌ها:**\n\n🎲 تاس\n⚽ فوتبال\n🏀 بسکتبال\n🎯 دارت\n🎳 بولینگ"
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 منو", callback_data="pv_menu"))
    safe_edit(call, t, kb)

@bot.callback_query_handler(func=lambda call: call.data == "pv_faq")
def pv_faq(call):
    t = "❓ **سوالات**\n\n• دایس کار نکرد؟ نوبتت نیست\n• /leave برای خروج"
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 منو", callback_data="pv_menu"))
    safe_edit(call, t, kb)

@bot.callback_query_handler(func=lambda call: call.data == "pv_top")
def pv_top(call):
    ss = get_top_scores()
    t = "🏆 **برترین‌ها**\n\n"
    for i, (name, score) in enumerate(ss, 1):
        t += (MEDALS[i-1] if i<=3 else "🏅") + " " + name + ": " + str(score) + "\n"
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 منو", callback_data="pv_menu"))
    safe_edit(call, t, kb)

@bot.callback_query_handler(func=lambda call: call.data == "pv_stats")
def pv_stats(call):
    s = get_stats()
    t = "📊 بازی‌ها: " + str(s.get('total_games',0)) + " | بازیکنان: " + str(s.get('total_players',0)) + " | دایس‌ها: " + str(s.get('total_dice_rolls',0))
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 منو", callback_data="pv_menu"))
    safe_edit(call, t, kb)

@bot.callback_query_handler(func=lambda call: call.data == "pv_menu")
def pv_menu(call):
    safe_edit(call, "✨ سلام " + call.from_user.first_name + "!\n\n🎲 به گپیرو خوش اومدی!\n📌 تو گروه /newgame رو بزن.", main_menu())

@bot.message_handler(commands=['newgame'])
def newgame(m):
    if m.chat.type == "private":
        bot.reply_to(m, "🎮 فقط تو گروه!"); return
    cid = m.chat.id
    uid = m.from_user.id
    with lock:
        if cid in games and games[cid]["status"] == "play":
            bot.reply_to(m, "⛔ یه بازی در حال انجامه!"); return
        games.pop(cid, None)
        games[cid] = {"creator": uid, "game": None, "target": None, "win_values": [], "players": [uid], "player_names": {uid: m.from_user.first_name}, "status": "reg", "turn_index": 0, "winners": [], "menu_msg_id": None, "dice_count": 0, "finished": False}
    kb = InlineKeyboardMarkup(row_width=2)
    for g in GAME_CONFIG:
        kb.add(InlineKeyboardButton(g, callback_data="g_type_" + g))
    msg = bot.send_message(cid, "🎮 **بازی جدید**\n\n🎯 نوع بازی:", reply_markup=kb, parse_mode="Markdown")
    games[cid]["menu_msg_id"] = msg.message_id

@bot.message_handler(commands=['leave'])
def leave_game(m):
    if m.chat.type == "private":
        return
    cid = m.chat.id
    uid = m.from_user.id
    with lock:
        g = games.get(cid)
        if not g or uid not in g["players"]:
            bot.reply_to(m, "❌ تو بازی نیستی!"); return
        name = g["player_names"].get(uid, "ناشناس")
        if g["status"] == "play":
            oi = g["turn_index"]
            oid = g["players"][oi] if oi < len(g["players"]) else None
            g["players"].remove(uid)
            g["player_names"].pop(uid, None)
            if len(g["players"]) <= 1:
                if len(g["players"]) == 1:
                    g["winners"].append(g["player_names"][g["players"][0]])
                g["winners"].append(name)
                save_rank_scores(g["winners"])
                update_stats(g.get("game"), len(g["winners"]))
                bot.send_message(cid, build_results(g["winners"], g.get("dice_count", 0)), parse_mode="Markdown")
                games.pop(cid, None)
            else:
                if oid and oid != uid:
                    try:
                        g["turn_index"] = g["players"].index(oid)
                    except:
                        g["turn_index"] = 0
                else:
                    g["turn_index"] = min(oi, len(g["players"]) - 1)
                if g["turn_index"] >= len(g["players"]):
                    g["turn_index"] = 0
                nn = g['player_names'][g['players'][g['turn_index']]]
                bot.send_message(cid, "👋 " + name + " خارج شد.\n👉 نوبت: " + nn, parse_mode="Markdown")
        else:
            g["players"].remove(uid)
            g["player_names"].pop(uid, None)
            if len(g["players"]) == 0:
                games.pop(cid, None)
                bot.send_message(cid, "🚫 بازی کنسل شد.")
            else:
                update_reg(cid, g["menu_msg_id"])

@bot.callback_query_handler(func=lambda call: call.data.startswith("g_"))
def game_cb(call):
    cid = call.message.chat.id
    uid = call.from_user.id
    data = call.data
    g = games.get(cid)
    if not g or g.get("finished"):
        bot.answer_callback_query(call.id, "⏰ تموم شد!", show_alert=True); return
    if uid in g["player_names"]:
        g["player_names"][uid] = call.from_user.first_name

    if data == "g_back":
        if uid != g["creator"] or g["status"] == "play":
            return
        g["game"] = None
        g["target"] = None
        g["win_values"] = []
        g["players"] = [uid]
        g["player_names"] = {uid: call.from_user.first_name}
        kb = InlineKeyboardMarkup(row_width=2)
        for n in GAME_CONFIG:
            kb.add(InlineKeyboardButton(n, callback_data="g_type_" + n))
        bot.edit_message_text("🎮 نوع بازی:", cid, g["menu_msg_id"], reply_markup=kb, parse_mode="Markdown")

    elif data.startswith("g_type_"):
        if uid != g["creator"]:
            return
        gn = data.replace("g_type_", "")
        if gn not in GAME_CONFIG:
            return
        g["game"] = gn
        kb = InlineKeyboardMarkup(row_width=1)
        for i, tg in enumerate(GAME_CONFIG[gn]["targets"]):
            kb.add(InlineKeyboardButton(tg, callback_data="g_tgt_" + str(i)))
        kb.add(InlineKeyboardButton("🔙 بازگشت", callback_data="g_back"))
        bot.edit_message_text("🎯 هدف:", cid, g["menu_msg_id"], reply_markup=kb, parse_mode="Markdown")

    elif data.startswith("g_tgt_"):
        if uid != g["creator"]:
            return
        try:
            idx = int(data.replace("g_tgt_", ""))
            g["target"] = GAME_CONFIG[g["game"]]["targets"][idx]
            g["win_values"] = GAME_CONFIG[g["game"]]["values"][idx]
            update_reg(cid, g["menu_msg_id"])
        except:
            pass

    elif data == "g_join":
        if g["status"] != "reg":
            return
        if uid in g["players"] or len(g["players"]) >= 5:
            return
        g["players"].append(uid)
        g["player_names"][uid] = call.from_user.first_name
        bot.answer_callback_query(call.id, "✅ پیوستی!", show_alert=True)
        update_reg(cid, g["menu_msg_id"])

    elif data == "g_start":
        if uid != g["creator"] or len(g["players"]) < 2:
            return
        g["status"] = "play"
        fp = g['player_names'][g['players'][0]]
        em = GAME_CONFIG[g['game']]['emoji']
        t = "🚀 شروع!\n👉 نوبت: " + fp + "\n🎲 استیکر " + em + " رو بفرست!"
        bot.edit_message_text(t, cid, g["menu_msg_id"], parse_mode="Markdown")

def update_reg(cid, mid):
    g = games[cid]
    gn = g.get('game', '؟')
    if not gn:
        gn = '؟'
    tn = g.get('target', '؟')
    if not tn:
        tn = '؟'
    pl = ""
    for u, n in g["player_names"].items():
        if u == g['creator']:
            pl += "👑 "
        else:
            pl += "👤 "
        pl += n + "\n"
    t = "🎮 " + str(gn) + "\n🎯 " + str(tn) + "\n\n📝 بازیکنان (" + str(len(g['players'])) + "/۵):\n" + pl
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("➕ پیوستن", callback_data="g_join"), InlineKeyboardButton("🚀 شروع", callback_data="g_start"))
    kb.add(InlineKeyboardButton("🔙 بازگشت", callback_data="g_back"))
    try:
        bot.edit_message_text(t, cid, mid, reply_markup=kb, parse_mode="Markdown")
    except:
        pass

@bot.message_handler(content_types=['dice'])
def dice_handler(m):
    cid = m.chat.id
    uid = m.from_user.id
    g = games.get(cid)
    if not g or g["status"] != "play" or g.get("finished"):
        return
    if len(g["players"]) == 0:
        return
    if g["turn_index"] >= len(g["players"]):
        g["turn_index"] = 0
    if uid != g["players"][g["turn_index"]]:
        cn = g['player_names'].get(g['players'][g['turn_index']], "?")
        bot.reply_to(m, "⏳ نوبت " + cn + " هست!"); return
    req = GAME_CONFIG[g["game"]]["emoji"]
    if m.dice.emoji != req:
        bot.reply_to(m, "❌ استیکر " + req + " رو بفرست!"); return
    with lock:
        if cid not in games or g["status"] != "play" or g.get("finished"):
            return
        if len(g["players"]) == 0 or uid != g["players"][g["turn_index"]]:
            return
        g["dice_count"] = g.get("dice_count", 0) + 1
        increment_dice_rolls()
        v = m.dice.value
        if v in g["win_values"]:
            wn = g["player_names"][uid]
            g["winners"].append(wn)
            oi = g["turn_index"]
            g["players"].remove(uid)
            if len(g["players"]) <= 1:
                if len(g["players"]) == 1:
                    g["winners"].append(g["player_names"][g["players"][0]])
                g["finished"] = True
                save_rank_scores(g["winners"])
                update_stats(g.get("game"), len(g["winners"]))
                bot.send_message(cid, build_results(g["winners"], g.get("dice_count", 0)), parse_mode="Markdown")
                games.pop(cid, None)
                bot.reply_to(m, "🎉 " + wn + " برنده شد!\n🏁 بازی تموم شد!", parse_mode="Markdown")
                return
            if oi >= len(g["players"]):
                g["turn_index"] = 0
            else:
                g["turn_index"] = oi
            if g["turn_index"] >= len(g["players"]):
                g["turn_index"] = 0
            nn = g['player_names'][g['players'][g['turn_index']]]
            r = "🎉 " + wn + " برنده شد! مقام " + str(len(g['winners'])) + "\n👉 نوبت: " + nn + "\n🎲 استیکر " + req + " رو بفرست!"
            bot.reply_to(m, r, parse_mode="Markdown")
        else:
            g["turn_index"] = (g["turn_index"] + 1) % len(g["players"])
            nn = g['player_names'][g['players'][g['turn_index']]]
            r = random.choice(FAIL_MSG) + "\n👉 نوبت: " + nn + "\n🎲 استیکر " + req + " رو بفرست!"
            bot.reply_to(m, r, parse_mode="Markdown")

print("✅ گپیرو آماده‌ست!")
bot.infinity_polling()
