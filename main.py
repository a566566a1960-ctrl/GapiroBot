import telebot

TOKEN = "8750954453:AAFWL7XzhN27MXVLP4JAdGmyvNFYUkeJEuo"
bot = telebot.TeleBot(TOKEN)

games = {}

@bot.message_handler(func=lambda m: m.text and m.text.startswith('/newgame'))
def handle_newgame(m):
    cid = m.chat.id
    games[cid] = {
        "creator": m.from_user.id, 
        "game": "🎲 تاس", 
        "win_values": [6],
        "players": [m.from_user.id], 
        "player_names": {m.from_user.id: m.from_user.first_name}, 
        "status": "reg", 
        "turn_index": 0, 
        "winners": []
    }
    bot.reply_to(m, "✅ بازی جدید ساخته شد.\nاعضا وارد شوند و /startgame را بزنند.")

@bot.message_handler(func=lambda m: m.text and m.text.startswith('/startgame'))
def handle_start(m):
    cid = m.chat.id
    if cid in games:
        games[cid]["status"] = "play"
        bot.reply_to(m, "🚀 بازی شروع شد! تاس بریزید.")
        # نمایش نوبت اولین نفر
        first_player = games[cid]["player_names"][games[cid]["players"][0]]
        bot.send_message(cid, f"👉 نوبت: {first_player}")

@bot.message_handler(content_types=['dice'])
def handle_dice(m):
    cid = m.chat.id
    if cid not in games or games[cid]["status"] != "play": return
    g = games[cid]
    
    # بررسی نوبت
    if m.from_user.id != g["players"][g["turn_index"]]: return
    
    if m.dice.value in g["win_values"]:
        name = g["player_names"][m.from_user.id]
        g["winners"].append(name)
        g["players"].remove(m.from_user.id)
        
        # اگر کسی باقی نمانده باشد (پایان بازی)
        if not g["players"]:
            bot.reply_to(m, "🎉 شما بردید!")
            res = "🏁 جدول رده‌بندی:\n" + "\n".join([f"{i+1}. {name}" for i, name in enumerate(g['winners'])])
            bot.send_message(cid, res)
            del games[cid]
            return
        else:
            bot.reply_to(m, f"🎉 {name} بردید! بقیه منتظر بمانید.")
            # چون بازیکن حذف شد، ایندکس نباید تغییر کند تا به نفر بعدی اشاره کند
            g["turn_index"] %= len(g["players"])
    else:
        # تغییر نوبت
        g["turn_index"] = (g["turn_index"] + 1) % len(g["players"])
    
    # ارسال نوبت بعدی
    bot.send_message(cid, f"👉 نوبت: {g['player_names'][g['players'][g['turn_index']]]}")

print("Bot is running...")
bot.infinity_polling()
