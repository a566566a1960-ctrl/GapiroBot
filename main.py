import telebot
import threading

TOKEN = "8750954453:AAFWL7XzhN27MXVLP4JAdGmyvNFYUkeJEuo"
bot = telebot.TeleBot(TOKEN)

# دیتابیس حافظه
games = {}

def delete_later(cid, mid):
    def delete():
        try: bot.delete_message(cid, mid)
        except: pass
    threading.Timer(60, delete).start()

@bot.message_handler(func=lambda m: True)
def handle_all_messages(m):
    cid = m.chat.id
    text = m.text if m.text else ""
    
    # دستور ساخت بازی
    if text.startswith('/newgame'):
        games[cid] = {
            "players": [m.from_user.id], 
            "player_names": {m.from_user.id: m.from_user.first_name}, 
            "status": "reg", 
            "turn_index": 0, 
            "winners": []
        }
        bot.reply_to(m, "✅ بازی ساخته شد. برای ورود دیگران /join و برای شروع /startgame را بزنید.")
    
    # دستور ورود به بازی
    elif text.startswith('/join') and cid in games and games[cid]["status"] == "reg":
        if m.from_user.id not in games[cid]["players"]:
            games[cid]["players"].append(m.from_user.id)
            games[cid]["player_names"][m.from_user.id] = m.from_user.first_name
            bot.reply_to(m, f"👤 {m.from_user.first_name} وارد شد.")
            
    # دستور شروع بازی
    elif text.startswith('/startgame') and cid in games:
        games[cid]["status"] = "play"
        bot.reply_to(m, "🚀 بازی شروع شد! تاس بریزید.")

@bot.message_handler(content_types=['dice'])
def handle_dice(m):
    cid = m.chat.id
    if cid not in games or games[cid]["status"] != "play": return
    g = games[cid]
    
    # باگ‌گیری: فقط نوبتِ بازیکن
    if m.from_user.id != g["players"][g["turn_index"]]: return
    
    # باگ‌گیری: فقط تاس ۶ برنده است
    if m.dice.value == 6:
        winner_name = g["player_names"][m.from_user.id]
        g["winners"].append(winner_name)
        g["players"].remove(m.from_user.id)
        
        # تبریک فقط به برنده
        bot.reply_to(m, "🎉 تبریک! شما بردید.")
        
        # اگر بازی تمام شد
        if not g["players"]:
            res = "🏁 پایان بازی! رتبه‌بندی:\n" + "\n".join([f"مقام {i+1}: {name}" for i, name in enumerate(g['winners'])])
            bot.send_message(cid, res)
            del games[cid]
            return
        
        # تنظیم مجدد نوبت
        g["turn_index"] %= len(g["players"])
    else:
        # اگر ۶ نبود، نوبت بعدی
        g["turn_index"] = (g["turn_index"] + 1) % len(g["players"])
    
    # اعلام نوبت
    next_name = g["player_names"].get(g["players"][g["turn_index"]], "بازیکن")
    msg = bot.send_message(cid, f"👉 نوبت: {next_name}")
    delete_later(cid, msg.message_id)

print("Bot is ready...")
bot.infinity_polling()
