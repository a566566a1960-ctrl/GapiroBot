import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
import threading
import json
import os
import random
import time
from datetime import datetime, timedelta
from collections import defaultdict

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8750954453:AAEJwaDyw9prIK51txIBQuvt2uBm0ITXpZ4")
bot = telebot.TeleBot(BOT_TOKEN)

bot.delete_my_commands()
bot.set_my_commands([
    BotCommand("newgame", "🎮 شروع بازی جدید"),
    BotCommand("top", "🏆 جدول برترین ها"),
    BotCommand("me", "👤 پروفایل من"),
    BotCommand("stats", "📊 آمار ربات"),
    BotCommand("leave", "🚪 خروج از بازی"),
    BotCommand("daily", "🎁 جایزه روزانه"),
    BotCommand("help", "📜 راهنمای بازی"),
    BotCommand("about", "ℹ️ درباره ربات")
])

SCORE_FILE = "scores.json"
STATS_FILE = "stats.json"
DAILY_FILE = "daily.json"
PROFILE_FILE = "profiles.json"
games = {}
active_timers = {}
wrong_stickers = defaultdict(int)
lock = threading.Lock()
file_lock = threading.Lock()
timer_lock = threading.Lock()

GAME_CONFIG = {
    "تاس": {
        "emoji": "🎲",
        "desc": "تاس بنداز و شانست رو امتحان کن!",
        "targets": {
            "شیش آوردن": [6],
            "زوج": [2, 4, 6],
            "فرد": [1, 3, 5],
            "یک یا شیش": [1, 6],
            "سه یا چهار": [3, 4]
        }
    },
    "فوتبال": {
        "emoji": "⚽",
        "desc": "شوت بزن و گل کن!",
        "targets": {
            "گل": [5],
            "تیرک دروازه": [4],
            "آفساید": [3]
        }
    },
    "بسکتبال": {
        "emoji": "🏀",
        "desc": "شوت بزن و امتیاز بگیر!",
        "targets": {
            "پرتاب ۳ امتیازی": [5],
            "نزدیک حلقه": [2, 3, 4],
            "هوا خورد": [1]
        }
    },
    "دارت": {
        "emoji": "🎯",
        "desc": "نشونه بگیر و پرتاب کن!",
        "targets": {
            "مرکز کامل": [6],
            "نزدیک مرکز": [4, 5],
            "حاشیه": [1, 2, 3]
        }
    },
    "بولینگ": {
        "emoji": "🎳",
        "desc": "توپ رو بنداز و استرایک کن!",
        "targets": {
            "استرایک کامل": [6],
            "نیمه استرایک": [4, 5],
            "گاتر": [1]
        }
    },
    "کازینو": {
        "emoji": "🎰",
        "desc": "اسلات ماشین - شانس بزرگ!",
        "targets": {
            "💎 جکپات": [64],
            "🍇 سه تا انگور": [43],
            "🍋 سه تا لیمو": [22],
            "🔔 سه تا BAR": [1]
        }
    }
}

MEDALS = ["🥇", "🥈", "🥉"]
OWNER_NAME = "𝙃𝘼𝙈𝙄𝘿"
OWNER_ID = 8095326779
OWNER_SCORE = 100000
TOHID_NAME = "TOHID"
JOAD_NAME = "Aras Zandi"

RANKS = [
    (0, "🆕 تازه وارد"),
    (50, "🌱 ماجراجو"),
    (150, "📗 جوینده"),
    (350, "📘 کاوشگر"),
    (700, "📙 مبارز"),
    (1200, "⭐ جنگجو"),
    (2000, "🌟 شوالیه"),
    (3200, "🔮 جادوگر"),
    (4800, "🔮 جادوگر اعظم"),
    (6800, "👑 فرمانده"),
    (9200, "👑 سردار"),
    (12000, "⚡ قهرمان"),
    (15500, "⚡ قهرمان افسانه ای"),
    (19500, "💎 محافظ"),
    (24000, "💎 محافظ اعظم"),
    (29000, "🏆 سلطان"),
    (34500, "🏆 سلطان بزرگ"),
    (40500, "🌟 جاودانه"),
    (47000, "🌟 جاودانه طلایی"),
    (54000, "👑 خالق"),
    (61500, "👑 خالق برتر"),
    (69500, "🔥 فرمانروا"),
    (78000, "🔥 فرمانروای کل"),
    (87000, "💫 ابرقهرمان"),
    (100000, "💫 ایزدی")
]

WIN_MSG = [
    "🎉 ایول! برنده شدی!", "🔥 داغونشون کردی!", "👑 شاه شدی!",
    "💪 قهرمانی!", "⭐ ستاره شدی!", "💎 افسانه ای!", "🚀 موشکی!", "🌟 درخشیدی!"
]
WIN_MSG_TOHID = [
    "👑 توحید خودشه! بازم برد!", "💎 توحید عزیز، این برد تقدیم به تو!",
    "🌟 توحید جان، همیشه برنده ای!", "🔥 توحید داغون میکنه همیشه!", "🏆 توحید سلطان بازی!"
]
WIN_MSG_JOAD = [
    "😈 ارس این بار خوش شانس بود!", "🍑 ارس برنده شد، باور نکردنیه!",
    "🤡 ارس رو ببین، برنده شده!", "💀 ارس شانس آورد!",
    "🍆 ارس برنده شد، دنیا به آخر رسید!"
]
WIN_MSG_OWNER = [
    "👑 سازنده خودش برد!", "💎 حمید جان، این برد تقدیم به تو!",
    "🌟 استاد بزرگ همیشه برنده ست!", "🔥 حمید داغون میکنه همیشه!",
    "🏆 خدای بازی ها!", "⚡ حمید غیرقابل توقف!", "🎯 حمید شاه شده!"
]

FAIL_MSG = [
    "💀 ایندفعه نشد، دوباره تلاش کن!", "😅 شانست یاری نکرد!", "🎲 بازی ادامه داره!",
    "🤞 شانس بیار!", "💪 تسلیم نشو!"
]
FAIL_MSG_JOAD = [
    "💀 ارس بمیره برات که باختی", "🍆 ارس با ۲۷ تا بخوابه",
    "🍑 ارس سر چهارراه کون بده", "👯 ارس فمبوی بشه",
    "🍽 ارس بهت کون میده", "🤡 ارس میخنده", "🪦 ارس سر قبرت"
]
FAIL_MSG_OWNER = [
    "😅 حمید جان، دفعه بعد جبران کن!", "💪 حمید، تو که کم نمیاری!",
    "🎲 شانس یاری نکرد استاد!"
]

KICK_MSG_STICKER = "برگرد تو کص ننت حرومزاده 🖕"
KICK_MSG_TIMER = "به دلیل عدم حرکت اخراج شدی 🖕"

def get_rank(score):
    rank_name = RANKS[0][1] if RANKS else "تازه وارد"
    for min_score, name in RANKS:
        if score >= min_score:
            rank_name = name
    return rank_name

def jload(f, d=None):
    if d is None:
        d = {}
    try:
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as ff:
                return json.load(ff)
    except:
        pass
    return d

def jsave(f, d):
    try:
        with open(f, "w", encoding="utf-8") as ff:
            json.dump(d, ff, ensure_ascii=False, indent=2)
    except:
        pass

def gstats():
    return jload(STATS_FILE, {"tg": 0, "tp": 0, "td": 0})

def ugame():
    with file_lock:
        s = gstats()
        s["tg"] = s.get("tg", 0) + 1
        jsave(STATS_FILE, s)

def uplays(c):
    with file_lock:
        s = gstats()
        s["tp"] = s.get("tp", 0) + c
        jsave(STATS_FILE, s)

def udice():
    with file_lock:
        s = gstats()
        s["td"] = s.get("td", 0) + 1
        jsave(STATS_FILE, s)

def calc_points(rank, total):
    if total == 2:
        return [2, 1][rank - 1]
    if total == 3:
        return [4, 2, 1][rank - 1]
    if total == 4:
        return [5, 3, 1, 0][rank - 1]
    return [5, 3, 1, 0, 0][rank - 1]

def sscore(winners):
    with file_lock:
        sc = jload(SCORE_FILE, {})
        total = len(winners)
        for i, name in enumerate(winners, 1):
            sc[name] = sc.get(name, 0) + calc_points(i, total)
        jsave(SCORE_FILE, sc)

def update_profile(name, won=False, lost=False):
    if not name or name == "?":
        return
    with file_lock:
        profiles = jload(PROFILE_FILE, {})
        if name not in profiles:
            profiles[name] = {"games": 0, "wins": 0, "losses": 0}
        profiles[name]["games"] = profiles[name].get("games", 0) + 1
        if won:
            profiles[name]["wins"] = profiles[name].get("wins", 0) + 1
        if lost:
            profiles[name]["losses"] = profiles[name].get("losses", 0) + 1
        jsave(PROFILE_FILE, profiles)

def gtop():
    sc = jload(SCORE_FILE, {})
    sc[OWNER_NAME] = OWNER_SCORE
    sorted_scores = sorted(sc.items(), key=lambda x: x[1], reverse=True)
    result = []
    for name, score in sorted_scores[:15]:
        result.append((name, score, get_rank(score)))
    return result

def myrank(name):
    sc = jload(SCORE_FILE, {})
    sc[OWNER_NAME] = OWNER_SCORE
    sorted_scores = sorted(sc.items(), key=lambda x: x[1], reverse=True)
    for i, (n, s) in enumerate(sorted_scores, 1):
        if n == name:
            return i, s, get_rank(s)
    return None, 0, "🆕 تازه وارد"

def bres(winners, dc=0):
    t = "🏁 بازی تموم شد!\n\n"
    t += "══════════════\n\n"
    t += "📊 رتبه بندی نهایی:\n\n"
    for i, n in enumerate(winners, 1):
        medal = MEDALS[i-1] if i <= 3 else "🏅"
        t += f"{medal} مقام {i}: {n} (+{calc_points(i, len(winners))} امتیاز)\n"
    if dc:
        t += f"\n🎲 پرتاب ها: {dc}"
    t += "\n✅ امتیازات ذخیره شد!"
    return t

def main_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("📜 راهنمای کامل بازی", callback_data="menu_help"),
        InlineKeyboardButton("🏆 جدول برترین ها", callback_data="menu_top"),
        InlineKeyboardButton("🎮 بازی های موجود", callback_data="menu_games"),
        InlineKeyboardButton("🏅 رتبه ها", callback_data="menu_ranks"),
        InlineKeyboardButton("❓ سوالات متداول", callback_data="menu_faq"),
        InlineKeyboardButton("📊 آمار ربات", callback_data="menu_stats"),
        InlineKeyboardButton("📞 ارتباط با ادمین", url="https://t.me/Hamid_18")
    )
    return kb

def get_win_msg(name, uid=None):
    if uid and uid == OWNER_ID:
        return random.choice(WIN_MSG_OWNER)
    if name == TOHID_NAME:
        return random.choice(WIN_MSG_TOHID)
    if name == JOAD_NAME:
        return random.choice(WIN_MSG_JOAD)
    return random.choice(WIN_MSG)

def cancel_timer(cid, gid):
    timer_id_prefix = f"{cid}_{gid}"
    with timer_lock:
        for tid in list(active_timers.keys()):
            if tid.startswith(timer_id_prefix):
                active_timers[tid] = False

def start_turn_timer(cid, gid, uid):
    timer_id = f"{cid}_{gid}_{uid}"
    with timer_lock:
        active_timers[timer_id] = True
    
    def timer_job():
        time.sleep(60)
        with timer_lock:
            if not active_timers.get(timer_id):
                return
            active_timers[timer_id] = False
        
        with lock:
            if cid not in games or gid not in games[cid]:
                return
            g = games[cid][gid]
            if g.get("fin") or g["st"] != "play":
                return
            if uid not in g["pl"] or g["pl"][g["ti"]] != uid:
                return
            
            nm = g["pn"].get(uid, "?")
            g["pl"].remove(uid)
            g["pn"].pop(uid, None)
            update_profile(nm, lost=True)
            
            try:
                bot.send_message(cid, f"{KICK_MSG_TIMER}\n⏰ {nm} به دلیل عدم حرکت اخراج شد!")
            except:
                pass
            
            if len(g["pl"]) <= 1:
                if len(g["pl"]) == 1:
                    last_name = g["pn"][g["pl"][0]]
                    g["wn"].append(last_name)
                    update_profile(last_name, won=True)
                g["wn"].append(nm)
                g["fin"] = True
                sscore(g["wn"])
                ugame()
                uplays(len(g["wn"]))
                try:
                    bot.edit_message_text(bres(g["wn"], g.get("dc", 0)), cid, g["mid"])
                except:
                    pass
                if g.get("last_turn_msg"):
                    try:
                        bot.delete_message(cid, g["last_turn_msg"])
                    except:
                        pass
                games[cid].pop(gid, None)
                return
            
            if g["ti"] >= len(g["pl"]):
                g["ti"] = 0
            nn = g['pn'][g['pl'][g['ti']]]
            em = GAME_CONFIG[g['g']]['emoji']
            
            txt = f"🎯 هدف: {g['t']}\n🎮 بازی: {g['g']}\n\n👥 بازیکنان ({len(g['pl'])} نفر):\n"
            for i, u in enumerate(g["pl"]):
                n = g["pn"].get(u, "?")
                prefix = "👑 " if u == g['cr'] else "👤 "
                if i == g["ti"]:
                    txt += f"➡️ {prefix}{n} ⬅️\n"
                else:
                    txt += f"{prefix}{n}\n"
            
            if g.get("wn"):
                txt += "\n🏆 برنده ها:\n"
                for i, w in enumerate(g["wn"], 1):
                    txt += f"{MEDALS[i-1] if i <= 3 else '🏅'} {w}\n"
            
            txt += f"\n👉 نوبت {nn} هست\n🎲 استیکر {em} رو بفرست!"
            try:
                bot.edit_message_text(txt, cid, g["mid"])
            except:
                pass
            
            bot.send_message(cid, f"👤 نفر بعدی: {nn}")
            
            next_uid = g["pl"][g["ti"]]
            start_turn_timer(cid, gid, next_uid)
    
    t = threading.Thread(target=timer_job, daemon=True)
    t.start()

def handle_menu(call):
    cid = call.message.chat.id
    mid = call.message.message_id
    d = call.data
    
    if d == "menu_help":
        t = """📜 راهنمای کامل گپیرو

══════════════
🎯 شروع بازی:
1. ربات را به گروه اضافه کنید
2. /newgame را بزنید
3. بازی و هدف را انتخاب کنید
4. بازیکنان «پیوستن» را بزنند
5. سازنده «شروع» را بزند

🎲 نحوه بازی:
• استیکر مخصوص بازی را بفرستید
• ۳ بار استیکر اشتباه = اخراج
• ۶۰ ثانیه فرصت داری وگرنه حذف میشی!

🏆 امتیازدهی:
👥 2 نفر: 2-1 | 👥 3 نفر: 4-2-1
👥 4 نفر: 5-3-1-0 | 👥 5 نفر: 5-3-1-0-0"""
    elif d == "menu_games":
        t = "🎮 بازی های موجود\n\n══════════════\n\n"
        for gn, gc in GAME_CONFIG.items():
            t += f"{gc['emoji']} {gn}\n📝 {gc['desc']}\n🎯 اهداف:\n"
            for tgt in gc['targets']:
                t += f"  • {tgt}\n"
            t += "\n"
    elif d == "menu_ranks":
        t = """🏅 راهنمای رتبه ها

══════════════

🆕 تازه وارد - 0 تا 49
🌱 ماجراجو - 50 تا 149
📗 جوینده - 150 تا 349
📘 کاوشگر - 350 تا 699
📙 مبارز - 700 تا 1199
⭐ جنگجو - 1200 تا 1999
🌟 شوالیه - 2000 تا 3199
🔮 جادوگر - 3200 تا 4799
🔮 جادوگر اعظم - 4800 تا 6799
👑 فرمانده - 6800 تا 9199
👑 سردار - 9200 تا 11999
⚡ قهرمان - 12000 تا 15499
⚡ قهرمان افسانه ای - 15500 تا 19499
💎 محافظ - 19500 تا 23999
💎 محافظ اعظم - 24000 تا 28999
🏆 سلطان - 29000 تا 34499
🏆 سلطان بزرگ - 34500 تا 40499
🌟 جاودانه - 40500 تا 46999
🌟 جاودانه طلایی - 47000 تا 53999
👑 خالق - 54000 تا 61499
👑 خالق برتر - 61500 تا 69499
🔥 فرمانروا - 69500 تا 77999
🔥 فرمانروای کل - 78000 تا 86999
💫 ابرقهرمان - 87000 تا 99999
💫 ایزدی - 100000 به بالا

══════════════
🎯 هر برد 2 تا 5 امتیاز داره
🥇 با بردن توی بازی ها زودتر رتبه میگیری!

💫 ایزدی فقط برای 100 هزار امتیازه!"""
    elif d == "menu_faq":
        t = """❓ سوالات متداول

══════════════
🤔 چرا دایس من کار نکرد؟
• نوبت شما نیست
• استیکر اشتباه فرستاده اید
• ۳ بار اشتباه = اخراج

🚫 چرا نمی توانم پیوستن بزنم؟
• بازی شروع شده است
• ظرفیت پر (حداکثر 5 نفر)
• قبلاً پیوسته اید

🚪 چطور خارج شوم؟
• /leave را بزنید"""
    elif d == "menu_top":
        ss = gtop()
        if not ss:
            t = "🏆 جدول برترین ها\n\n══════════════\n\nهنوز هیچ بازی انجام نشده!"
        else:
            t = "🏆 جدول برترین ها\n\n══════════════\n\n"
            for i, (n, s, rank) in enumerate(ss, 1):
                md = MEDALS[i-1] if i <= 3 else "🏅"
                cr = " 👑" if n == OWNER_NAME else ""
                t += f"{md} {i}. {n}{cr}\n"
                t += f"   ⭐ {s:,} امتیاز | 🏅 {rank}\n"
    elif d == "menu_stats":
        s = gstats()
        sc = jload(SCORE_FILE, {})
        profiles = jload(PROFILE_FILE, {})
        t = f"""📊 آمار گپیرو

══════════════
🎮 کل بازی ها: {s.get('tg', 0):,}
👥 کل بازیکنان: {len(sc):,}
🎲 کل دایس ها: {s.get('td', 0):,}
📁 پروفایل ها: {len(profiles):,}
══════════════"""
    elif d == "menu_back":
        try:
            bot.edit_message_text(
                f"✨ سلام {call.from_user.first_name}!\n\n🎲 به گپیرو خوش اومدی!\n\n🎮 6 بازی متنوع\n🎁 /daily جایزه روزانه\n👤 /me پروفایل\n🏆 /top برترین ها",
                cid, mid,
                reply_markup=main_menu()
            )
        except:
            pass
        return
    else:
        return
    
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 بازگشت به منو", callback_data="menu_back"))
    try:
        bot.edit_message_text(t, cid, mid, reply_markup=kb)
    except:
        pass

def handle_game_callback(call):
    cid = call.message.chat.id
    uid = call.from_user.id
    d = call.data
    
    if d.startswith("gjoin_"):
        action, gid = "gjoin", d[6:]
    elif d.startswith("gstart_"):
        action, gid = "gstart", d[7:]
    elif d.startswith("gback_"):
        action, gid = "gback", d[6:]
    elif d.startswith("game_"):
        parts = d.split("_", 2)
        action, gid = "game", parts[1] if len(parts) > 1 else ""
        gn = parts[2] if len(parts) > 2 else ""
    elif d.startswith("target_"):
        parts = d.split("_", 2)
        action, gid = "target", parts[1] if len(parts) > 1 else ""
        tgt = parts[2] if len(parts) > 2 else ""
    else:
        return
    
    if not gid or cid not in games or gid not in games[cid]:
        bot.answer_callback_query(call.id, "❌ بازی نامعتبر است!", show_alert=True)
        return
    
    g = games[cid][gid]
    
    if g.get("fin"):
        bot.answer_callback_query(call.id, "⏰ بازی تمام شده!", show_alert=True)
        return
    
    g["pn"][uid] = call.from_user.first_name

    if action == "game":
        if uid != g["cr"] or gn not in GAME_CONFIG:
            bot.answer_callback_query(call.id, "❌ فقط سازنده می تواند انتخاب کند!", show_alert=True)
            return
        g["g"] = gn
        kb = InlineKeyboardMarkup(row_width=1)
        for tgt_name in GAME_CONFIG[gn]["targets"]:
            kb.add(InlineKeyboardButton(tgt_name, callback_data=f"target_{gid}_{tgt_name}"))
        kb.add(InlineKeyboardButton("🔙 بازگشت", callback_data=f"gback_{gid}"))
        try:
            bot.edit_message_text(f"🎮 {gn}\n📝 {GAME_CONFIG[gn]['desc']}\n\n🎯 هدف را انتخاب کنید:", cid, g["mid"], reply_markup=kb)
        except:
            pass
    
    elif action == "target":
        if uid != g["cr"]:
            bot.answer_callback_query(call.id, "❌ فقط سازنده می تواند انتخاب کند!", show_alert=True)
            return
        if g["g"] and tgt in GAME_CONFIG[g["g"]]["targets"]:
            g["t"] = tgt
            g["wv"] = GAME_CONFIG[g["g"]]["targets"][tgt]
            txt = f"🎯 هدف: {g['t']}\n🎮 بازی: {g['g']}\n\n📝 بازیکنان ({len(g['pl'])}/5):\n"
            for u, n in g["pn"].items():
                txt += f"{'👑' if u == g['cr'] else '👤'} {n}\n"
            txt += "\n⏳ منتظر شروع..."
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("➕ پیوستن", callback_data=f"gjoin_{gid}"),
                InlineKeyboardButton("🚀 شروع", callback_data=f"gstart_{gid}"),
                InlineKeyboardButton("🔙 بازگشت", callback_data=f"gback_{gid}")
            )
            try:
                bot.edit_message_text(txt, cid, g["mid"], reply_markup=kb)
            except:
                pass
    
    elif action == "gjoin":
        if g["st"] != "reg":
            bot.answer_callback_query(call.id, "⏰ بازی شروع شده است!", show_alert=True)
            return
        if uid in g["pl"]:
            bot.answer_callback_query(call.id, "❌ شما قبلاً پیوسته اید!", show_alert=True)
            return
        if len(g["pl"]) >= 5:
            bot.answer_callback_query(call.id, "❌ ظرفیت پر است (حداکثر 5 نفر)!", show_alert=True)
            return
        g["pl"].append(uid)
        g["pn"][uid] = call.from_user.first_name
        bot.answer_callback_query(call.id, "✅ پیوستی!", show_alert=True)
        txt = f"🎯 هدف: {g.get('t', '?')}\n🎮 بازی: {g.get('g', '?')}\n\n📝 بازیکنان ({len(g['pl'])}/5):\n"
        for u, n in g["pn"].items():
            txt += f"{'👑' if u == g['cr'] else '👤'} {n}\n"
        txt += "\n⏳ منتظر شروع..."
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("➕ پیوستن", callback_data=f"gjoin_{gid}"),
            InlineKeyboardButton("🚀 شروع", callback_data=f"gstart_{gid}"),
            InlineKeyboardButton("🔙 بازگشت", callback_data=f"gback_{gid}")
        )
        try:
            bot.edit_message_text(txt, cid, g["mid"], reply_markup=kb)
        except:
            pass
    
    elif action == "gstart":
        if uid != g["cr"]:
            bot.answer_callback_query(call.id, "❌ فقط سازنده می تواند شروع کند!", show_alert=True)
            return
        if len(g["pl"]) < 2:
            bot.answer_callback_query(call.id, "❌ حداقل 2 بازیکن لازم است!", show_alert=True)
            return
        if not g.get("g") or not g.get("t"):
            bot.answer_callback_query(call.id, "❌ ابتدا بازی و هدف را انتخاب کنید!", show_alert=True)
            return
        g["st"] = "play"
        g["ti"] = 0
        fp = g['pn'][g['pl'][0]]
        em = GAME_CONFIG[g['g']]['emoji']
        txt = f"🎯 هدف: {g['t']}\n🎮 بازی: {g['g']}\n\n🚀 بازی شروع شد!\n\n👥 بازیکنان ({len(g['pl'])} نفر):\n"
        for i, u in enumerate(g["pl"]):
            n = g["pn"].get(u, "?")
            if i == 0:
                txt += f"➡️ {'👑' if u == g['cr'] else '👤'} {n} ⬅️\n"
            else:
                txt += f"{'👑' if u == g['cr'] else '👤'} {n}\n"
        txt += f"\n👉 نوبت {fp} هست\n🎲 استیکر {em} رو بفرست!"
        try:
            bot.edit_message_text(txt, cid, g["mid"])
        except:
            pass
        
        start_turn_timer(cid, gid, g["pl"][0])
    
    elif action == "gback":
        if uid != g["cr"]:
            bot.answer_callback_query(call.id, "❌ فقط سازنده!", show_alert=True)
            return
        if g["st"] == "play":
            bot.answer_callback_query(call.id, "❌ بازی شروع شده!", show_alert=True)
            return
        g["g"] = None
        g["t"] = None
        g["wv"] = []
        g["pl"] = [uid]
        g["pn"] = {uid: call.from_user.first_name}
        kb = InlineKeyboardMarkup(row_width=2)
        for gn in GAME_CONFIG:
            kb.add(InlineKeyboardButton(gn, callback_data=f"game_{gid}_{gn}"))
        try:
            bot.edit_message_text("🎮 نوع بازی:", cid, g["mid"], reply_markup=kb)
        except:
            pass

@bot.callback_query_handler(func=lambda c: True)
def master_callback(call):
    if call.data.startswith("menu_"):
        handle_menu(call)
    else:
        handle_game_callback(call)

@bot.message_handler(commands=['start'])
def start(m):
    if m.chat.type == "private":
        w = f"""✨ سلام {m.from_user.first_name} عزیز!

🎲 من گپیرو هستم، ربات بازی های گروهی تلگرام!

🎯 با من میتونی:
• بازی های گروهی انجام بدی
• با دوستات رقابت کنی
• امتیاز جمع کنی و برترین باشی

📌 برای شروع:
• منو به گروه اضافه کن
• ادمینم کن
• تو گروه /newgame رو بزن

🎁 /daily - جایزه روزانه
👤 /me - پروفایل تو
🏆 /top - جدول برترین ها"""
        bot.send_message(m.chat.id, w, reply_markup=main_menu())
    else:
        bot.reply_to(m, "👋 سلام! برای بازی /newgame رو بزن.")

@bot.message_handler(commands=['help'])
def help_cmd(m):
    t = """📜 راهنمای گپیرو

🎯 شروع بازی:
1. ربات رو به گروه اضافه کن و ادمینش کن
2. تو گروه /newgame رو بزن
3. بازی و هدف رو انتخاب کن
4. بازیکنا با دکمه «➕ پیوستن» وارد شن
5. سازنده دکمه «🚀 شروع» رو بزنه

🎲 نحوه بازی:
• هر کی نوبتشه استیکر مخصوص بازی رو بفرسته
• ۳ بار استیکر اشتباه = اخراج
• ۶۰ ثانیه فرصت داری وگرنه حذف میشی!

🏆 امتیازدهی:
• 2 نفر: اول 2، دوم 1
• 3 نفر: اول 4، دوم 2، سوم 1
• 4 نفر: اول 5، دوم 3، سوم 1، چهارم 0
• 5 نفر: اول 5، دوم 3، سوم 1، چهارم 0، پنجم 0

🎁 /daily - جایزه روزانه (1 تا 10 امتیاز)
👤 /me - پروفایل و امتیازات
🏆 /top - جدول برترین ها
📊 /stats - آمار ربات"""
    bot.reply_to(m, t)

@bot.message_handler(commands=['daily'])
def daily_cmd(m):
    name = m.from_user.first_name
    now = datetime.now()
    
    dd = jload(DAILY_FILE, {})
    
    if name in dd and "last_time" in dd[name]:
        last_time_str = dd[name].get("last_time", "")
        if last_time_str:
            try:
                last_time = datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S")
                diff = now - last_time
                if diff.total_seconds() < 86400:
                    remaining = timedelta(seconds=86400) - diff
                    hours = remaining.seconds // 3600
                    minutes = (remaining.seconds % 3600) // 60
                    seconds = remaining.seconds % 60
                    bot.reply_to(m, f"⏰ شما قبلاً جایزه رو گرفتی!\n\n🕐 {hours} ساعت و {minutes} دقیقه و {seconds} ثانیه دیگه میتونی دوباره بگیری")
                    return
            except:
                pass
    
    bonus = random.randint(1, 10)
    dd[name] = {"last_time": now.strftime("%Y-%m-%d %H:%M:%S")}
    jsave(DAILY_FILE, dd)
    
    sc = jload(SCORE_FILE, {})
    sc[name] = sc.get(name, 0) + bonus
    jsave(SCORE_FILE, sc)
    
    msg = f"🎁 {bonus} امتیاز گرفتی! 🎉"
    msg += f"\n\n🕐 24 ساعت دیگه میتونی دوباره بگیری"
    bot.reply_to(m, msg)

@bot.message_handler(commands=['me'])
def me_cmd(m):
    name = m.from_user.first_name
    uid = m.from_user.id
    
    st = gstats()
    sc = jload(SCORE_FILE, {})
    profiles = jload(PROFILE_FILE, {})
    
    user_profile = profiles.get(name, {"games": 0, "wins": 0, "losses": 0})
    games_played = user_profile.get("games", 0)
    games_won = user_profile.get("wins", 0)
    games_lost = user_profile.get("losses", 0)
    win_rate = round((games_won / games_played * 100) if games_played > 0 else 0, 1)
    
    r, s, rank_name = myrank(name)
    user_score = sc.get(name, 0)
    
    total_games_all = st.get('tg', 0)
    total_players_all = len(sc)
    
    if uid == OWNER_ID:
        user_score = OWNER_SCORE
        rank_name = "💫 ایزدی"
    
    t = f"""👤 پروفایل {name}

══════════════
🆔 شناسه: {uid}
🏅 رتبه: {rank_name}
⭐ امتیاز: {user_score:,}
🏆 جایگاه: {r if r else 'نامشخص'} از {len(sc)} بازیکن

══════════════
📊 آمار شخصی:
🎮 کل بازی ها: {games_played}
🥇 برد: {games_won}
💀 باخت: {games_lost}
📈 درصد برد: {win_rate}%

══════════════
📈 آمار کلی ربات:
🎮 کل بازی ها: {total_games_all:,}
👥 کل بازیکنان: {total_players_all:,}
🎲 کل دایس ها: {st.get('td', 0):,}
══════════════"""
    
    if uid == OWNER_ID:
        t = f"👑 ایــــزدی - سازنده گپیرو\n\n{t}"
    
    bot.reply_to(m, t)

@bot.message_handler(commands=['stats'])
def stats_cmd(m):
    s = gstats()
    sc = jload(SCORE_FILE, {})
    profiles = jload(PROFILE_FILE, {})
    t = f"""📊 آمار گپیرو

══════════════
🎮 کل بازی ها: {s.get('tg', 0):,}
👥 کل بازیکنان: {len(sc):,}
🎲 کل دایس ها: {s.get('td', 0):,}
📁 پروفایل ها: {len(profiles):,}
══════════════

🎯 برای شروع /newgame رو بزن!"""
    bot.reply_to(m, t)

@bot.message_handler(commands=['about'])
def about_cmd(m):
    t = f"""🤖 گپیرو - ربات بازی گروهی تلگرام

══════════════
🎮 6 بازی متنوع:
🎲 تاس - شانس و احتمال
⚽ فوتبال - شوت و گل
🏀 بسکتبال - پرتاب و امتیاز
🎯 دارت - دقت و تمرکز
🎳 بولینگ - استرایک و قدرت
🎰 کازینو - جکپات و هیجان

🎁 جایزه روزانه (1 تا 10 امتیاز)
👑 جدول برترین ها با 25 رتبه
👥 پشتیبانی از بازی همزمان
📊 آمار دقیق بازیکنان
⏰ تایمر ۶۰ ثانیه
🚫 ۳ استیکر اشتباه = اخراج

👨‍💻 سازنده: @Hamid_18

برای شروع /newgame رو تو گروه بزن!"""
    bot.reply_to(m, t)

@bot.message_handler(commands=['top'])
def top_cmd(m):
    ss = gtop()
    t = "🏆 جدول برترین ها\n\n══════════════\n\n"
    for i, (n, s, rank) in enumerate(ss, 1):
        md = MEDALS[i-1] if i <= 3 else "🏅"
        cr = " 👑" if n == OWNER_NAME else ""
        t += f"{md} {i}. {n}{cr}\n"
        t += f"   ⭐ {s:,} امتیاز | 🏅 {rank}\n"
    bot.reply_to(m, t)

@bot.message_handler(commands=['newgame'])
def newgame(m):
    if m.chat.type == "private":
        bot.reply_to(m, "🎮 بازی ها فقط در گروه انجام می شوند!\n\n📌 ربات را به گروه اضافه کنید و /newgame را بزنید.")
        return
    cid = m.chat.id
    uid = m.from_user.id
    gid = str(int(datetime.now().timestamp() * 1000))
    with lock:
        if cid not in games:
            games[cid] = {}
        games[cid][gid] = {
            "cr": uid, "g": None, "t": None, "wv": [],
            "pl": [uid], "pn": {uid: m.from_user.first_name},
            "st": "reg", "ti": 0, "wn": [], "mid": None,
            "dc": 0, "fin": False, "last_turn_msg": None
        }
    kb = InlineKeyboardMarkup(row_width=2)
    for g in GAME_CONFIG:
        kb.add(InlineKeyboardButton(g, callback_data=f"game_{gid}_{g}"))
    msg = bot.send_message(cid, "🎮 بازی جدید\n\n🎯 نوع بازی را انتخاب کنید:", reply_markup=kb)
    games[cid][gid]["mid"] = msg.message_id

@bot.message_handler(commands=['leave'])
def leave_game(m):
    if m.chat.type == "private":
        return
    cid = m.chat.id
    uid = m.from_user.id
    with lock:
        if cid not in games:
            bot.reply_to(m, "❌ شما در هیچ بازی نیستید!")
            return
        found = None
        for gid, g in games[cid].items():
            if uid in g["pl"]:
                found = gid
                break
        if not found:
            bot.reply_to(m, "❌ شما در هیچ بازی نیستید!")
            return
        g = games[cid][found]
        nm = g["pn"].get(uid, "?")
        g["pl"].remove(uid)
        g["pn"].pop(uid, None)
        
        cancel_timer(cid, found)
        
        if not g["pl"]:
            if g["st"] == "play":
                for name in g.get("wn", []):
                    update_profile(name, won=True)
            try:
                bot.delete_message(cid, g["mid"])
            except:
                pass
            if g.get("last_turn_msg"):
                try:
                    bot.delete_message(cid, g["last_turn_msg"])
                except:
                    pass
            games[cid].pop(found, None)
            bot.send_message(cid, f"👋 {nm} خارج شد. بازی لغو شد.")
        elif g["st"] == "play":
            update_profile(nm, lost=True)
            if len(g["pl"]) == 1:
                last_name = g["pn"][g["pl"][0]]
                g["wn"].append(last_name)
                g["wn"].append(nm)
                g["fin"] = True
                sscore(g["wn"])
                ugame()
                uplays(len(g["wn"]))
                for name in g["wn"]:
                    update_profile(name, won=True)
                try:
                    bot.edit_message_text(bres(g["wn"], g.get("dc", 0)), cid, g["mid"])
                except:
                    pass
                if g.get("last_turn_msg"):
                    try:
                        bot.delete_message(cid, g["last_turn_msg"])
                    except:
                        pass
                games[cid].pop(found, None)
                bot.send_message(cid, bres(g["wn"], g.get("dc", 0)))
                return
            
            if g["ti"] >= len(g["pl"]):
                g["ti"] = 0
            nn = g['pn'][g['pl'][g['ti']]]
            em = GAME_CONFIG[g['g']]['emoji']
            txt = f"🎯 هدف: {g['t']}\n🎮 بازی: {g['g']}\n\n👋 {nm} خارج شد.\n👉 نوبت {nn} هست\n🎲 استیکر {em} رو بفرست!"
            try:
                bot.edit_message_text(txt, cid, g["mid"])
            except:
                pass
            bot.send_message(cid, f"👋 {nm} از بازی خارج شد.\n👤 نفر بعدی: {nn}")
            
            next_uid = g["pl"][g["ti"]]
            start_turn_timer(cid, found, next_uid)
        else:
            txt = f"🎯 هدف: {g.get('t', '?')}\n🎮 بازی: {g.get('g', '?')}\n\n📝 بازیکنان ({len(g['pl'])}/5):\n"
            for u, n in g["pn"].items():
                txt += f"{'👑' if u == g['cr'] else '👤'} {n}\n"
            txt += "\n⏳ منتظر شروع..."
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("➕ پیوستن", callback_data=f"gjoin_{found}"),
                InlineKeyboardButton("🚀 شروع", callback_data=f"gstart_{found}"),
                InlineKeyboardButton("🔙 بازگشت", callback_data=f"gback_{found}")
            )
            try:
                bot.edit_message_text(txt, cid, g["mid"], reply_markup=kb)
            except:
                pass
            bot.send_message(cid, f"👋 {nm} از بازی خارج شد.")

@bot.message_handler(content_types=['dice'])
def dice_handler(m):
    try:
        cid = m.chat.id
        uid = m.from_user.id
        
        if cid not in games:
            return
        
        found = None
        for gid, g in games[cid].items():
            if g["st"] == "play" and uid in g["pl"] and not g.get("fin"):
                found = gid
                break
        
        if not found:
            return
        
        g = games[cid][found]
        g["pn"][uid] = m.from_user.first_name
        
        if g["ti"] >= len(g["pl"]):
            g["ti"] = 0
        
        if uid != g["pl"][g["ti"]]:
            cn = g['pn'].get(g['pl'][g['ti']], "?")
            bot.reply_to(m, f"⏳ نوبت {cn} است!")
            return
        
        req = GAME_CONFIG[g["g"]]["emoji"]
        sticker_key = f"{cid}_{uid}"
        
        if m.dice.emoji != req:
            wrong_stickers[sticker_key] += 1
            if wrong_stickers[sticker_key] >= 3:
                nm = g["pn"].get(uid, "?")
                g["pl"].remove(uid)
                g["pn"].pop(uid, None)
                update_profile(nm, lost=True)
                wrong_stickers[sticker_key] = 0
                
                timer_id = f"{cid}_{found}_{uid}"
                with timer_lock:
                    active_timers[timer_id] = False
                
                try:
                    bot.send_message(cid, f"{KICK_MSG_STICKER}\n{nm} به دلیل ۳ بار استیکر اشتباه اخراج شد!")
                except:
                    pass
                
                if g.get("last_turn_msg"):
                    try:
                        bot.delete_message(cid, g["last_turn_msg"])
                    except:
                        pass
                    g["last_turn_msg"] = None
                
                if len(g["pl"]) <= 1:
                    if len(g["pl"]) == 1:
                        last_name = g["pn"][g["pl"][0]]
                        g["wn"].append(last_name)
                        update_profile(last_name, won=True)
                    g["wn"].append(nm)
                    g["fin"] = True
                    sscore(g["wn"])
                    ugame()
                    uplays(len(g["wn"]))
                    try:
                        bot.edit_message_text(bres(g["wn"], g.get("dc", 0)), cid, g["mid"])
                    except:
                        pass
                    games[cid].pop(found, None)
                    bot.send_message(cid, bres(g["wn"], g.get("dc", 0)))
                    return
                
                if g["ti"] >= len(g["pl"]):
                    g["ti"] = 0
                nn = g['pn'][g['pl'][g['ti']]]
                em = GAME_CONFIG[g['g']]['emoji']
                
                txt = f"🎯 هدف: {g['t']}\n🎮 بازی: {g['g']}\n\n👥 بازیکنان ({len(g['pl'])} نفر):\n"
                for i, u in enumerate(g["pl"]):
                    n = g["pn"].get(u, "?")
                    prefix = "👑 " if u == g['cr'] else "👤 "
                    if i == g["ti"]:
                        txt += f"➡️ {prefix}{n} ⬅️\n"
                    else:
                        txt += f"{prefix}{n}\n"
                
                if g.get("wn"):
                    txt += "\n🏆 برنده ها:\n"
                    for i, w in enumerate(g["wn"], 1):
                        txt += f"{MEDALS[i-1] if i <= 3 else '🏅'} {w}\n"
                
                txt += f"\n👉 نوبت {nn} هست\n🎲 استیکر {em} رو بفرست!"
                try:
                    bot.edit_message_text(txt, cid, g["mid"])
                except:
                    pass
                
                bot.send_message(cid, f"👤 نفر بعدی: {nn}")
                
                next_uid = g["pl"][g["ti"]]
                start_turn_timer(cid, found, next_uid)
            else:
                remaining = 3 - wrong_stickers[sticker_key]
                bot.reply_to(m, f"❌ استیکر {req} را بفرست!\n⚠️ {remaining} فرصت باقی مانده تا اخراج!")
            return
        
        wrong_stickers[sticker_key] = 0
        
        with lock:
            if cid not in games or found not in games[cid]:
                return
            
            g = games[cid][found]
            
            if g["st"] != "play" or g.get("fin") or not g["pl"] or uid != g["pl"][g["ti"]]:
                return
            
            g["dc"] = g.get("dc", 0) + 1
            udice()
            v = m.dice.value
            
            timer_id = f"{cid}_{found}_{uid}"
            with timer_lock:
                active_timers[timer_id] = False
            
            if g.get("last_turn_msg"):
                try:
                    bot.delete_message(cid, g["last_turn_msg"])
                except:
                    pass
                g["last_turn_msg"] = None
            
            if v in g["wv"]:
                wn = g["pn"][uid]
                g["wn"].append(wn)
                update_profile(wn, won=True)
                old_idx = g["ti"]
                g["pl"].remove(uid)
                
                if len(g["pl"]) <= 1:
                    if len(g["pl"]) == 1:
                        last_name = g["pn"][g["pl"][0]]
                        g["wn"].append(last_name)
                        update_profile(last_name, lost=True)
                    for uid_in_game in g.get("pl", []):
                        pname = g["pn"].get(uid_in_game, "?")
                        if pname not in g.get("wn", []) and pname != "?":
                            update_profile(pname, lost=True)
                    g["fin"] = True
                    sscore(g["wn"])
                    ugame()
                    uplays(len(g["wn"]))
                    try:
                        bot.edit_message_text(bres(g["wn"], g.get("dc", 0)), cid, g["mid"])
                    except:
                        pass
                    games[cid].pop(found, None)
                    bot.send_message(cid, bres(g["wn"], g.get("dc", 0)))
                    bot.reply_to(m, get_win_msg(wn, uid))
                    return
                
                if old_idx >= len(g["pl"]):
                    g["ti"] = 0
                else:
                    g["ti"] = old_idx
                
                if g["ti"] >= len(g["pl"]):
                    g["ti"] = 0
                
                nn = g['pn'][g['pl'][g['ti']]]
                em = GAME_CONFIG[g['g']]['emoji']
                
                txt = f"🎯 هدف: {g['t']}\n🎮 بازی: {g['g']}\n\n👥 بازیکنان ({len(g['pl'])} نفر):\n"
                for i, u in enumerate(g["pl"]):
                    n = g["pn"].get(u, "?")
                    prefix = "👑 " if u == g['cr'] else "👤 "
                    if i == g["ti"]:
                        txt += f"➡️ {prefix}{n} ⬅️\n"
                    else:
                        txt += f"{prefix}{n}\n"
                
                if g.get("wn"):
                    txt += "\n🏆 برنده ها:\n"
                    for i, w in enumerate(g["wn"], 1):
                        txt += f"{MEDALS[i-1] if i <= 3 else '🏅'} {w}\n"
                
                txt += f"\n👉 نوبت {nn} هست\n🎲 استیکر {em} رو بفرست!"
                try:
                    bot.edit_message_text(txt, cid, g["mid"])
                except:
                    pass
                
                msg = bot.reply_to(m, f"{get_win_msg(wn, uid)}\n\n👉 نوبت {nn} هست\n🎲 استیکر {em} رو بفرست!")
                g["last_turn_msg"] = msg.message_id
                
                next_uid = g["pl"][g["ti"]]
                start_turn_timer(cid, found, next_uid)
            else:
                update_profile(g['pn'].get(uid, "?"), lost=True)
                g["ti"] = (g["ti"] + 1) % len(g["pl"])
                nn = g['pn'][g['pl'][g['ti']]]
                em = GAME_CONFIG[g['g']]['emoji']
                
                txt = f"🎯 هدف: {g['t']}\n🎮 بازی: {g['g']}\n\n👥 بازیکنان ({len(g['pl'])} نفر):\n"
                for i, u in enumerate(g["pl"]):
                    n = g["pn"].get(u, "?")
                    prefix = "👑 " if u == g['cr'] else "👤 "
                    if i == g["ti"]:
                        txt += f"➡️ {prefix}{n} ⬅️\n"
                    else:
                        txt += f"{prefix}{n}\n"
                
                if g.get("wn"):
                    txt += "\n🏆 برنده ها:\n"
                    for i, w in enumerate(g["wn"], 1):
                        txt += f"{MEDALS[i-1] if i <= 3 else '🏅'} {w}\n"
                
                txt += f"\n👉 نوبت {nn} هست\n🎲 استیکر {em} رو بفرست!"
                try:
                    bot.edit_message_text(txt, cid, g["mid"])
                except:
                    pass
                
                current_player = g['pn'].get(uid, "?")
                if current_player == JOAD_NAME:
                    fail_msg = random.choice(FAIL_MSG_JOAD)
                elif uid == OWNER_ID:
                    fail_msg = random.choice(FAIL_MSG_OWNER)
                else:
                    fail_msg = random.choice(FAIL_MSG)
                
                msg = bot.reply_to(m, f"{fail_msg}\n\n👉 نوبت {nn} هست\n🎲 استیکر {em} رو بفرست!")
                g["last_turn_msg"] = msg.message_id
                
                next_uid = g["pl"][g["ti"]]
                start_turn_timer(cid, found, next_uid)
    except Exception as e:
        print(f"Error: {e}")

print("✅ گپیرو آماده است!")
bot.infinity_polling()
