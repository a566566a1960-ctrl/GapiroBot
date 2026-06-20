import telebot, json, re, logging, uuid
from abc import ABC, abstractmethod

# 1. State Machine صریح
class GameState:
    REG = "reg"
    PLAY = "play"
    FINISHED = "finished"
    CANCELLED = "cancelled"

# 2. انتزاع Engine (هیچ خبری از SQLite نیست)
class GameEngine:
    @staticmethod
    def process_turn(state, uid, dice_value, win_targets):
        """Pure Logic: فقط ورودی می‌گیرد و خروجی می‌دهد."""
        players = state['players']
        turn_idx = state['turn_index']
        
        if str(players[turn_idx]) != str(uid):
            return "NOT_YOUR_TURN", state
        
        if dice_value in win_targets:
            players.pop(turn_idx)
            if not players: return "GAME_OVER", state
            state['turn_index'] = turn_idx % max(1, len(players))
            return "WIN", state
        
        state['turn_index'] = (turn_idx + 1) % max(1, len(players))
        return "NEXT_TURN", state

# 3. Persistence Layer (این تنها جایی است که DB را می‌شناسد)
class Repository:
    def get_game(self, cid): pass
    def save_game(self, cid, state): pass
    def acquire_lock(self, cid): pass # قابلیت جایگزینی با Redis
    def release_lock(self, cid): pass

# 4. Callback Router با State Machine Validation
class AppRouter:
    def dispatch(self, call):
        cid = call.message.chat.id
        game = repo.get_game(cid)
        
        # Validation بر اساس State Machine
        if game['status'] == GameState.PLAY and call.data == "join":
            return bot.answer_callback_query(call.id, "⚠️ بازی شروع شده!")
        
        # منطق توزیع
        ...
        
