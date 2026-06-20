import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading

TOKEN = "8750954453:AAFWL7XzhN27MXVLP4JAdGmyvNFYUkeJEuo"
bot = telebot.TeleBot(TOKEN)

# دیتابیسِ حافظه برای بازی‌های فعال
games = {}

# تنظیمات بازی
GAME_CONFIG = {
    "🎲 تاس": {"emoji": "🎲", "targets": {"۶": [6]}},
    "🏀 بسکتبال": {"emoji": "🏀", "targets": {"گل": [5]}}
}

def delete_later(cid, mid):
    def delete():
        try: bot.delete_message(cid, mid)
        except: pass
    threading.Timer(60, delete).start()

@bot.message_handler(func=lambda m: True)
def handle_all_messages(m):
    cid = m.chat.id
    if not m.text: return
    
    if m.text.startswith('/newgame'):
        games[cid] = {
            "creator": m.from_user.id, "game": "🎲 تاس", "win_values": [6],
            "players": [m.from_user.id], "player_names": {m.from_user.id: m.from_user.first_name}, 
            "status": "reg", "turn_index": 0, "winners": [], "initial_count": 0
        }
        bot.reply_to(m, "✅ بازی جدید ساخته شد. اعضا وارد شوند و /startgame را بزنند.")
    
    elif m.text.startswith('/startgame') and cid in games:
        games[cid]["status"] = "play"
        games[cid]["initial_count"] = len(games[cid]["players"])
        bot.reply_to(m, "🚀 بازی شروع شد! تاس بریزید.")

    elif m.text.startswith('/join') and cid in games and games[cid]["status"] == "reg":
        if m.from_user.id not in games[cid]["players"]:
            games[cid]["players"].append(m.from_user.id)
            games[cid]["player_names"][m.from_user.id] = m.from_user.first_name
            bot.reply_to(m, f"👤 {m.from_user.first_name} وارد شد.")

@bot.message_handler(content_types=['dice'])
def handle_dice(m):
    cid = m.chat.id
    if cid not in games or games[cid]["status"] != "play": return
    g = games[cid]
    
    # بررسی نوبت
    if m.from_user.id != g["players"][g["turn_index"]]: return
    
    # بررسی برد
    if m.dice.value in g["win_values"]:
        winner_name = g["player_names"][m.from_user.id]
        g["winners"].append(winner_name)
        g["players"].remove(m.from_user.id)
        
        # ریپلای تبریک به برنده
        bot.reply_to(m, "🎉 تبریک! شما بردید.")
        
        # اگر بازی تمام شد
        if not g["players"]:
            res = "🏁 پایان بازی! رتبه‌بندی:\n" + "\n".join([f"مقام {i+1}: {name}" for i, name in enumerate(g['winners'])])
            bot.send_message(cid, res)
            del games[cid]
            return
        
        # اگر بازی ادامه دارد
        g["turn_index"] %= len(g["players"])
    else:
        # نوبت بعدی
        g["turn_index"] = (g["turn_index"] + 1) % len(g["players"])
    
    # اعلام نوبت
    msg = bot.send_message(cid, f"👉 نوبت: {g['player_names'][g['players'][g['turn_index']]]}")
    delete_later(cid, msg.message_id)

print("Bot is ready...")
bot.infinity_polling()
