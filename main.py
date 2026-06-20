Import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading

TOKEN = "8750954453:AAFWL7XzhN27MXVLP4JAdGmyvNFYUkeJEuo"
bot = telebot.TeleBot(TOKEN)

games = {}
GAME_CONFIG = {
    "🎲 تاس": {"emoji": "🎲", "targets": {"۶": [6]}},
    "🏀 بسکتبال": {"emoji": "🏀", "targets": {"گل": [5]}}
}

# این هندلر برای تمام پیام‌هاست تا بفهمیم مشکل کجاست
@bot.message_handler(func=lambda m: True)
def debug_all(m):
    # لاگ کردن پیام‌ها برای اینکه بفهمیم ربات اصلاً پیام گروه را می‌بیند یا نه
    print(f"Message in {m.chat.id}: {m.text}")
    
    # اجرای دستورات
    if m.text and m.text.startswith('/newgame'):
        handle_newgame(m)
    elif m.text and m.text.startswith('/startgame'):
        handle_start(m)

def handle_newgame(m):
    cid = m.chat.id
    games[cid] = {
        "creator": m.from_user.id, "game": "🎲 تاس", "win_values": [6],
        "players": [m.from_user.id], "player_names": {m.from_user.id: m.from_user.first_name}, 
        "status": "reg", "turn_index": 0, "winners": [], "initial_count": 0
    }
    bot.reply_to(m, "✅ بازی جدید ساخته شد. اعضا وارد شوند و /startgame را بزنند.")

def handle_start(m):
    cid = m.chat.id
    if cid in games:
        games[cid]["status"] = "play"
        games[cid]["initial_count"] = len(games[cid]["players"])
        bot.reply_to(m, "🚀 بازی شروع شد! تاس بریزید.")

@bot.message_handler(content_types=['dice'])
def handle_dice(m):
    cid = m.chat.id
    if cid not in games or games[cid]["status"] != "play": return
    g = games[cid]
    if m.from_user.id != g["players"][g["turn_index"]]: return
    
    if m.dice.value in g["win_values"]:
        name = g["player_names"][m.from_user.id]
        g["winners"].append(name)
        g["players"].remove(m.from_user.id)
        
        # پیام ۳ نفر به بالا
        if g["initial_count"] >= 3 and len(g["players"]) > 0:
            bot.reply_to(m, f"🎉 {name} بردی! بقیه منتظر بمانید.")
        else:
            bot.reply_to(m, f"🎉 {name} بردی!")
            
        if not g["players"]:
            res = "🏁 پایان: " + ", ".join(g['winners'])
            bot.send_message(cid, res)
            del games[cid]
            return
        g["turn_index"] %= len(g["players"])
    else:
        g["turn_index"] = (g["turn_index"] + 1) % len(g["players"])
    
    bot.send_message(cid, f"👉 نوبت: {g['player_names'][g['players'][g['turn_index']]]}")

print("Bot is running...")
bot.infinity_polling()
