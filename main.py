import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
import threading
import json
import os
import time
import random

BOT_TOKEN = "8750954453:AAFWL7XzhN27MXVLP4JAdGmyvNFYUkeJEuo"
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
    "🎲 تاس": {
        "emoji": "🎲",
        "desc": "تاس بنداز و شانست رو امتحان کن",
        "targets": {
            "🎯 شیش آوردن": [6],
            "🎲 زوج": [2, 4, 6],
            "🎲 فرد": [1, 3, 5],
            "💫 یک یا شیش": [1, 6],
            "⭐ سه یا چهار": [3, 4]
        },
        "auto_roll": False
    },
    "⚽ فوتبال": {
        "emoji": "⚽",
        "desc": "شوت بزن و گل کن",
        "targets": {
            "⚽ گل": [5],
            "🥅 تیرک دروازه": [4],
            "🚩 آفساید": [3],
            "🟥 کارت قرمز": [2],
            "🟨 کارت زرد": [1]
        },
        "auto_roll": False
    },
    "🏀 بسکتبال": {
        "emoji": "🏀",
        "desc": "شوت بزن و امتیاز بگیر",
        "targets": {
            "🏀 گل": [5],
            "💫 حلقه": [2, 3, 4],
            "💨 هوا": [1]
        },
        "auto_roll": False
    },
    "🎯 دارت": {
        "emoji": "🎯",
        "desc": "نشونه بگیر و پرتاب کن",
        "targets": {
            "🎯 مرکز": [6],
            "🎯 نزدیک مرکز": [4, 5],
            "🎯 حاشیه": [1, 2, 3]
        },
        "auto_roll": False
    },
    "🎳 بولینگ": {
        "emoji": "🎳",
        "desc": "توپ رو بنداز و استرایک کن",
        "targets": {
            "💥 استرایک": [6],
            "🎳 نیمه استرایک": [4, 5],
            "😅 گاتر": [1]
        },
        "auto_roll": False
    },
    "🎰 کازینو": {
        "emoji": "🎰",
        "desc": "اسلات ماشین - ربات دایس میندازه",
        "targets": {
            "💎 جکپات ۷۷۷": [64],
            "🍇 سه تا انگور": [43],
            "🍋 سه تا لیمو": [22],
            "🔔 سه تا BAR": [1]
        },
        "auto_roll": True
    }
}

MEDALS = ["🥇", "🥈", "🥉"]
POINTS = [5, 3, 1, 0, -1]
FAIL_MESSAGES = [
    "😅 ای بابا! این دفعه نشد...",
    "🎲 شانس نیاوردی! دفعه بعد جبران کن 💪",
    "😬 خیلی نزدیک بود! یه بار دیگه تلاش کن...",
    "💫 بخت باهات یار نبود! ادامه بده...",
    "🎯 هدف رو نزدی، ولی تسلیم نشو!",
    "🌟 شاید دفعه بعد... قول میدم!",
    "😤 آخی! خیلی نزدیک بودی..."
]

# ─── توابع کمکی ──────────────────────────────────

def get_stats():
    if not os.path.exists(STATS_FILE):
        return {"total_games": 0, "total_players": 0, "total_dice_rolls": 0}
    try:
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    except:
        return {"total_games": 0, "total_players": 0, "total_dice_rolls": 0}

def update_stats(game_type=None, players_count=0):
    with file_lock:
        s = get_stats()
        s["total_games"] += 1
        s["total_players"] += players_count
        with open(STATS_FILE, "w") as f:
            json.dump(s, f)

def increment_dice_rolls():
    with file_lock:
        s = get_stats()
        s["total_dice_rolls"] += 1
        with open(STATS_FILE, "w") as f:
            json.dump(s, f)

def save_rank_scores(winners_list):
    with file_lock:
        scores = {}
        if os.path.exists(SCORE_FILE):
            try:
                with open(SCORE_FILE, "r") as f:
                    scores = json.load(f)
            except:
                pass
        for i, name in enumerate(winners_list):
            if i < len(POINTS):
                scores[name] = scores.get(name, 0) + POINTS[i]
        with open(SCORE_FILE, "w") as f:
            json.dump(scores, f, ensure_ascii=False, indent=2)

def build_results_text(winners_list, dice_count=0):
    text = "🏁 **بازی تموم شد!**\n\n"
    text += "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n\n"
    text += "📊 **رتبه‌بندی نهایی:**\n\n"
    for i, name in enumerate(winners_list, 1):
        medal = MEDALS[i-1] if i <= 3 else "🏅"
        pts = POINTS[i-1] if i <= len(POINTS) else 0
        text += medal + " **مقام " + str(i) + ":** " + name + " _(+" + str(pts) + " امتیاز)_\n"
    if dice_count > 0:
        text += "\n🎲 تعداد پرتاب‌ها: **" + str(dice_count) + "**"
    text += "\n\n✅ **امتیازات با موفقیت ثبت شد!** 🎉"
    return text

def get_main_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("📜 راهنمای کامل بازی", callback_data="pv_help"),
        InlineKeyboardButton("🏆 جدول برترین‌ها", callback_data="pv_top"),
        InlineKeyboardButton("🎮 بازی‌های موجود", callback_data="pv_games"),
        InlineKeyboardButton("❓ سوالات متداول", callback_data="pv_faq"),
        InlineKeyboardButton("📊 آمار ربات", callback_data="pv_stats"),
        InlineKeyboardButton("📞 ارتباط با ادمین", url="https://t.me/Hamid_18")
    )
    return kb

def safe_edit(call, text, kb=None, parse="Markdown"):
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode=parse)
    except:
        try:
            bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode=parse)
        except:
            pass

# ─── دستورات اصلی ──────────────────────────────────

@bot.message_handler(commands=['start'])
def start_cmd(m):
    if m.chat.type == "private":
        text = (
            "✨ **سلام " + m.from_user.first_name + " عزیز!** ✨\n\n"
            "🎲 به **گپیرو (Gapiro)** خوش اومدی!\n"
            "من ربات بازی‌های گروهی تلگرام هستم.\n\n"
            "🎯 **با من میتونی:**\n"
            "🔹 بازی‌های متنوع گروهی انجام بدی\n"
            "🔹 با دوستات رقابت کنی\n"
            "🔹 امتیاز جمع کنی و **برترین** باشی\n"
            "🔹 کلی سرگرم بشی و بخندی! 😄\n\n"
            "📌 **برای شروع:**\n"
            "توی یه گروه دستور `/newgame` رو بزن\n\n"
            "🎪 **۶ بازی** متنوع منتظرتن!"
        )
        bot.send_message(m.chat.id, text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
    else:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🤖 رفتن به پی‌وی ربات", url="https://t.me/GapiroBot"))
        bot.send_message(m.chat.id, "👋 سلام!\n\n🎮 برای استفاده از ربات و دیدن راهنما، لطفاً به پی‌وی من سر بزن.\n⚡ @GapiroBot", reply_markup=kb)

@bot.message_handler(commands=['help'])
def help_cmd(m):
    if m.chat.type == "private":
        start_cmd(m)
    else:
        bot.reply_to(m, "📜 برای دیدن راهنمای کامل، به پی‌وی ربات سر بزن!\n🔗 @GapiroBot")

@bot.message_handler(commands=['stats'])
def stats_cmd(m):
    s = get_stats()
    text = (
        "📊 **آمار گپیرو**\n\n"
        "▫️ کل بازی‌ها: **" + str(s['total_games']) + "** بازی\n"
        "▫️ کل بازیکنان: **" + str(s['total_players']) + "** نفر\n"
        "▫️ کل دایس‌ها: **" + str(s['total_dice_rolls']) + "** پرتاب\n\n"
        "🎯 به جمع ما بپیوند و آمار رو بالاتر ببر!"
    )
    bot.reply_to(m, text, parse_mode="Markdown")

@bot.message_handler(commands=['about'])
def about_cmd(m):
    text = (
        "╭━━━━━━━━━━━━━━━━━╮\n"
        "  ℹ️  **درباره گپیرو**\n"
        "╰━━━━━━━━━━━━━━━━━╯\n\n"
        "🤖 **نام:** گپیرو (Gapiro)\n"
        "📊 **نسخه:** ۲.۰\n"
        "🎮 **تعداد بازی‌ها:** ۶ بازی\n\n"
        "👨‍💻 **سازنده:** @Hamid_18\n\n"
        "✨ **ویژگی‌ها:**\n"
        "🔹 ۶ بازی متنوع گروهی\n"
        "🔹 سیستم امتیازدهی پیشرفته\n"
        "🔹 جدول برترین‌ها\n"
        "🔹 پشتیبانی از کازینو (خودکار)\n\n"
        "🌟 **با گپیرو، بازی کن و برنده شو!**"
    )
    bot.reply_to(m, text, parse_mode="Markdown")

@bot.message_handler(commands=['top'])
def show_top(m):
    if not os.path.exists(SCORE_FILE):
        bot.reply_to(m, "📭 هنوز هیچ امتیازی ثبت نشده!\n🎮 برو بازی کن و اولین امتیاز رو بگیر!")
        return
    with open(SCORE_FILE, "r") as f:
        scores = json.load(f)
    if not scores:
        bot.reply_to(m, "📭 هنوز هیچ امتیازی ثبت نشده!")
        return
    ss = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]
    text = "🏆 **جدول برترین بازیکنان** 🏆\n\n"
    text += "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n\n"
    for i, (name, score) in enumerate(ss, 1):
        medal = MEDALS[i-1] if i <= 3 else "🏅"
        crown = " 👑" if i == 1 else ""
        text += medal + " **" + name + "**" + crown + "\n      `" + str(score) + "` امتیاز\n\n"
    text += "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
    bot.reply_to(m, text, parse_mode="Markdown")

# ─── پی‌وی ──────────────────────────────────

@bot.callback_query_handler(func=lambda call: call.data == "pv_help")
def pv_help(call):
    text = (
        "📜 **راهنمای کامل گپیرو**\n\n"
        "╭─────────────────────╮\n"
        "  🎯 **شروع بازی**\n"
        "╰─────────────────────╯\n"
        "۱. توی گروه `/newgame` رو بزن\n"
        "۲. نوع بازی و هدف رو انتخاب کن\n"
        "۳. دوستات با دکمه **«➕ پیوستن»** بیان\n"
        "۴. سازنده دکمه **«🚀 شروع»** رو بزنه\n\n"
        "╭─────────────────────╮\n"
        "  🎲 **نحوه بازی**\n"
        "╰─────────────────────╯\n"
        "🔸 هر کی نوبتشه، **استیکر مخصوص** رو بفرسته\n"
        "🔸 اگه هدف رو بزنه → **برنده میشه!**\n"
        "🔸 بازی ادامه داره تا همه رتبه‌بندی بشن\n\n"
        "╭─────────────────────╮\n"
        "  🏆 **امتیازدهی**\n"
        "╰─────────────────────╯\n"
        "🥇 اول: **۵** | 🥈 دوم: **۳** | 🥉 سوم: **۱**\n"
        "🏅 چهارم: **۰** | 💔 پنجم: **۱-**\n\n"
        "📋 `/newgame` • `/leave` • `/top` • `/stats` • `/about`\n\n"
        "💡 **نکته:** کازینو 🎰 توسط خود ربات انجام میشه!"
    )
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🎮 بازی‌ها", callback_data="pv_games"),
        InlineKeyboardButton("❓ سوالات", callback_data="pv_faq"),
        InlineKeyboardButton("🔙 منو اصلی", callback_data="pv_menu")
    )
    safe_edit(call, text, kb)

@bot.callback_query_handler(func=lambda call: call.data == "pv_games")
def pv_games(call):
    text = "🎮 **بازی‌های موجود در گپیرو**\n\n"
    text += "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n\n"
    for game_name, config in GAME_CONFIG.items():
        text += game_name + "\n"
        text += "📝 " + config['desc'] + "\n"
        text += "🎯 اهداف:\n"
        for target in config['targets']:
            text += "  ▫️ " + target + "\n"
        if config.get('auto_roll'):
            text += "\n🤖 **ربات دایس رو میندازه!**\n"
        text += "\n▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n\n"
    text += "💡 هر بازی با استیکر مخصوص خودش انجام میشه!"
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📜 راهنما", callback_data="pv_help"),
        InlineKeyboardButton("🔙 منو اصلی", callback_data="pv_menu")
    )
    safe_edit(call, text, kb)

@bot.callback_query_handler(func=lambda call: call.data == "pv_faq")
def pv_faq(call):
    text = (
        "❓ **سوالات متداول**\n\n"
        "╭─────────────────────────╮\n"
        "  🤔 **چرا دایس من کار نکرد؟**\n"
        "╰─────────────────────────╯\n"
        "🔸 نوبت تو نیست (صبور باش)\n"
        "🔸 استیکر اشتباه فرستادی\n"
        "🔸 بازی تموم شده\n\n"
        "╭─────────────────────────╮\n"
        "  🚫 **چرا نمیتونم join کنم؟**\n"
        "╰─────────────────────────╯\n"
        "🔸 بازی شروع شده\n"
        "🔸 ظرفیت پر (حداکثر ۵ نفر)\n"
        "🔸 قبلاً join کردی\n\n"
        "╭─────────────────────────╮\n"
        "  🚪 **چطور خارج بشم؟**\n"
        "╰─────────────────────────╯\n"
        "🔸 `/leave` رو بزن\n\n"
        "╭─────────────────────────╮\n"
        "  🎰 **کازینو چطور کار میکنه؟**\n"
        "╰─────────────────────────╯\n"
        "🔸 ربات خودش دایس رو میندازه\n"
        "🔸 نیازی نیست کاری بکنی!\n\n"
        "╭─────────────────────────╮\n"
        "  🔄 **بازی هنگ کرد، چیکار کنم؟**\n"
        "╰─────────────────────────╯\n"
        "🔸 `/leave` بزن\n"
        "🔸 `/newgame` جدید بساز"
    )
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📜 راهنما", callback_data="pv_help"),
        InlineKeyboardButton("📞 ادمین", url="https://t.me/Hamid_18"),
        InlineKeyboardButton("🔙 منو اصلی", callback_data="pv_menu")
    )
    safe_edit(call, text, kb)

@bot.callback_query_handler(func=lambda call: call.data == "pv_top")
def pv_top(call):
    if not os.path.exists(SCORE_FILE):
        text = "📭 **هنوز هیچ امتیازی ثبت نشده!**\n\n🎮 برو تو گروه بازی کن و اولین امتیاز رو بگیر!"
    else:
        with open(SCORE_FILE, "r") as f:
            scores = json.load(f)
        if not scores:
            text = "📭 **هنوز هیچ امتیازی ثبت نشده!**"
        else:
            ss = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]
            text = "🏆 **جدول برترین بازیکنان** 🏆\n\n"
            text += "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n\n"
            for i, (name, score) in enumerate(ss, 1):
                medal = MEDALS[i-1] if i <= 3 else "🏅"
                crown = " 👑" if i == 1 else ""
                text += medal + " **" + name + "**" + crown + "\n      `" + str(score) + "` امتیاز\n\n"
            text += "▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔"
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 منو اصلی", callback_data="pv_menu"))
    safe_edit(call, text, kb)

@bot.callback_query_handler(func=lambda call: call.data == "pv_stats")
def pv_stats(call):
    s = get_stats()
    text = (
        "📊 **آمار گپیرو**\n\n"
        "▫️ کل بازی‌ها: **" + str(s['total_games']) + "** 🎮\n"
        "▫️ کل بازیکنان: **" + str(s['total_players']) + "** 👥\n"
        "▫️ کل دایس‌ها: **" + str(s['total_dice_rolls']) + "** 🎲\n\n"
        "🎯 به جمع ما بپیوند!"
    )
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 منو اصلی", callback_data="pv_menu"))
    safe_edit(call, text, kb)

@bot.callback_query_handler(func=lambda call: call.data == "pv_menu")
def pv_menu(call):
    text = (
        "✨ **سلام " + call.from_user.first_name + " عزیز!** ✨\n\n"
        "🎲 به **گپیرو (Gapiro)** خوش اومدی!\n"
        "من ربات بازی‌های گروهی تلگرام هستم.\n\n"
        "📌 **برای شروع:**\n"
        "توی یه گروه دستور `/newgame` رو بزن\n\n"
        "🎪 **۶ بازی** متنوع منتظرتن!"
    )
    safe_edit(call, text, get_main_keyboard())

# ─── بازی ──────────────────────────────────

@bot.message_handler(commands=['newgame'])
def newgame(m):
    if m.chat.type == "private":
        bot.reply_to(m, "🎮 بازی‌ها فقط توی **گروه** انجام میشن!\n\n💡 منو به یه گروه اضافه کن و `/newgame` رو بزن.")
        return
    cid = m.chat.id
    uid = m.from_user.id
    with lock:
        if cid in games and games[cid]["status"] == "play":
            bot.reply_to(m, "⛔ **یه بازی در حال انجامه!**\n💡 صبر کن تموم بشه یا با `/leave` خارج شید.")
            return
        games.pop(cid, None)
        games[cid] = {
            "creator": uid,
            "creator_name": m.from_user.first_name,
            "game": None,
            "target": None,
            "win_values": [],
            "players": [uid],
            "player_names": {uid: m.from_user.first_name},
            "status": "reg",
            "turn_index": 0,
            "winners": [],
            "menu_msg_id": None,
            "auto_roll": False,
            "dice_count": 0
        }
    kb = InlineKeyboardMarkup(row_width=2)
    for g in GAME_CONFIG:
        kb.add(InlineKeyboardButton(g, callback_data="game_type_" + g))
    text = (
        "🎮 **بازی جدید**\n"
        "▔▔▔▔▔▔▔▔▔▔▔▔▔▔\n"
        "👤 **سازنده:** " + m.from_user.first_name + "\n"
        "👥 **بازیکنان:** ۱ نفر (حداقل ۲ نفر)\n\n"
        "🎯 لطفاً **نوع بازی** رو انتخاب کن:"
    )
    msg = bot.send_message(cid, text, reply_markup=kb, parse_mode="Markdown")
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
            bot.reply_to(m, "❌ شما توی بازی نیستید!")
            return
        name = g["player_names"].get(uid, "ناشناس")
        if g["status"] == "play":
            old_index = g["turn_index"]
            old_id = g["players"][old_index] if old_index < len(g["players"]) else None
            g["players"].remove(uid)
            g["player_names"].pop(uid, None)
            if len(g["players"]) <= 1:
                if g["players"]:
                    g["winners"].append(g["player_names"][g["players"][0]])
                g["winners"].append(name)
                save_rank_scores(g["winners"])
                update_stats(g.get("game"), len(g["winners"]))
                text = build_results_text(g["winners"], g.get("dice_count", 0))
                bot.send_message(cid, text, parse_mode="Markdown")
                games.pop(cid, None)
            else:
                if old_id and old_id != uid:
                    try:
                        g["turn_index"] = g["players"].index(old_id)
                    except ValueError:
                        g["turn_index"] = 0
                else:
                    g["turn_index"] = min(old_index, len(g["players"]) - 1)
                next_name = g['player_names'][g['players'][g['turn_index']]]
                text = (
                    "👋 **" + name + "** از بازی خارج شد.\n\n"
                    "👥 **" + str(len(g['players'])) + "** بازیکن باقی مونده\n"
                    "👉 نوبت: **" + next_name + "**"
                )
                bot.send_message(cid, text, parse_mode="Markdown")
        else:
            g["players"].remove(uid)
            g["player_names"].pop(uid, None)
            if len(g["players"]) == 0:
                games.pop(cid, None)
                try:
                    bot.delete_message(cid, g["menu_msg_id"])
                except:
                    pass
                bot.send_message(cid, "🚫 همه بازیکنا خارج شدن.\n**بازی کنسل شد.**")
            else:
                update_reg(cid, g["menu_msg_id"])

@bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
def game_cb(call):
    cid = call.message.chat.id
    uid = call.from_user.id
    data = call.data
    g = games.get(cid)
    if not g:
        bot.answer_callback_query(call.id, "⏰ این بازی تموم شده!", show_alert=True)
        return
    if uid in g["player_names"]:
        g["player_names"][uid] = call.from_user.first_name

    # بازگشت به انتخاب بازی
    if data == "game_back":
        if uid != g["creator"]:
            bot.answer_callback_query(call.id, "❌ فقط سازنده میتونه برگرده!", show_alert=True)
            return
        if g["status"] == "play":
            bot.answer_callback_query(call.id, "⛔ بازی در حال انجامه!", show_alert=True)
            return
        g["game"] = None
        g["target"] = None
        g["win_values"] = []
        g["auto_roll"] = False
        g["players"] = [uid]
        g["player_names"] = {uid: call.from_user.first_name}
        kb = InlineKeyboardMarkup(row_width=2)
        for name in GAME_CONFIG:
            kb.add(InlineKeyboardButton(name, callback_data="game_type_" + name))
        bot.edit_message_text("🎮 **نوع بازی رو انتخاب کن:**", cid, g["menu_msg_id"], reply_markup=kb, parse_mode="Markdown")

    # انتخاب نوع بازی
    elif data.startswith("game_type_"):
        if uid != g["creator"]:
            bot.answer_callback_query(call.id, "❌ فقط سازنده میتونه انتخاب کنه!", show_alert=True)
            return
        game_name = data[10:]
        g["game"] = game_name
        g["auto_roll"] = GAME_CONFIG[game_name].get("auto_roll", False)
        config = GAME_CONFIG[game_name]
        text = game_name + "\n📝 " + config['desc'] + "\n\n🎯 **هدف رو انتخاب کن:**"
        if g["auto_roll"]:
            text += "\n\n🤖 _ربات دایس رو میندازه!_"
        kb = InlineKeyboardMarkup(row_width=1)
        for t in config["targets"]:
            kb.add(InlineKeyboardButton(t, callback_data="game_tgt_" + t))
        kb.add(InlineKey
