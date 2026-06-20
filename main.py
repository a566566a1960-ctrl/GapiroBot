import sqlite3, json, threading, time
from collections import defaultdict, OrderedDict

# -----------------------------
# 1. IDENTITY + IDEMPOTENCY LAYER (SAFE + TTL + CLEANUP)
# -----------------------------
class Idempotency:
    def __init__(self, ttl=2, max_size=5000):
        self.ttl = ttl
        self.cache = OrderedDict()
        self.lock = threading.Lock()
        self.max_size = max_size

    def check(self, uid, cid, action):
        key = f"{uid}:{cid}:{action}"
        now = time.time()

        with self.lock:
            # cleanup expired
            expired = [k for k, t in self.cache.items() if now - t > self.ttl]
            for k in expired:
                del self.cache[k]

            # bounded memory
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)

            if key in self.cache:
                return False

            self.cache[key] = now
            return True


idempotency = Idempotency()

# -----------------------------
# 2. FSM (EVENT-DRIVEN, NOT JUST STATE MAP)
# -----------------------------
class FSM:
    REG, PLAY, PAUSED, FINISHED, CANCELLED = range(5)

    transitions = {
        REG: {"start": PLAY, "cancel": CANCELLED},
        PLAY: {"pause": PAUSED, "finish": FINISHED},
        PAUSED: {"resume": PLAY, "finish": FINISHED},
    }

    @staticmethod
    def can(current, event):
        return event in FSM.transitions.get(current, {})

    @staticmethod
    def next(current, event):
        return FSM.transitions[current][event]

# -----------------------------
# 3. REPOSITORY (ATOMIC + SAFE READ-MODIFY-WRITE)
# -----------------------------
class Repository:
    _lock = threading.Lock()
    DB = "gapiro.db"

    @classmethod
    def get(cls, cid):
        with sqlite3.connect(cls.DB, timeout=30) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(
                "SELECT * FROM games WHERE cid=?",
                (cid,)
            ).fetchone()

    @classmethod
    def save(cls, state):
        with cls._lock:
            with sqlite3.connect(cls.DB, timeout=30) as conn:
                conn.execute("PRAGMA journal_mode=WAL")

                conn.execute("""
                    INSERT INTO games (cid, status, players, player_names, turn_index, winners)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(cid) DO UPDATE SET
                        status=excluded.status,
                        players=excluded.players,
                        player_names=excluded.player_names,
                        turn_index=excluded.turn_index,
                        winners=excluded.winners
                """, (
                    state["cid"],
                    state["status"],
                    json.dumps(state["players"]),
                    json.dumps(state["names"]),
                    state["turn"],
                    json.dumps(state["winners"])
                ))

# -----------------------------
# 4. GAME ENGINE (FULL SAFE LOGIC)
# -----------------------------
class GameEngine:

    @staticmethod
    def process_turn(state, uid, dice, win_targets):
        players = state["players"]
        turn = state["turn"]

        # safety checks (anti-crash)
        if not players or turn >= len(players):
            state["turn"] = 0
            return "INVALID_STATE", state

        if players[turn] != uid:
            return "NOT_YOUR_TURN", state

        # WIN CONDITION
        if dice in win_targets:
            players.pop(turn)

            if not players:
                state["status"] = FSM.FINISHED
                return "GAME_OVER", state

            state["turn"] = turn % len(players)
            return "WIN", state

        # NEXT TURN
        state["turn"] = (turn + 1) % len(players)
        return "NEXT_TURN", state

# -----------------------------
# 5. DISPATCHER (FULL ENFORCEMENT LAYER)
# -----------------------------
def dispatch_action(uid, cid, action, payload):

    # 1. idempotency gate
    if not idempotency.check(uid, cid, action):
        return "TOO_FAST"

    # 2. load state
    row = Repository.get(cid)
    if not row:
        return "GAME_NOT_FOUND"

    state = {
        "cid": cid,
        "status": row["status"],
        "players": json.loads(row["players"]),
        "names": json.loads(row["player_names"]),
        "turn": row["turn_index"],
        "winners": json.loads(row["winners"])
    }

    # 3. FSM validation
    if action in FSM.transitions.get(state["status"], {}):
        new_status = FSM.next(state["status"], action)
        state["status"] = new_status
    elif action in ["dice"]:
        pass
    else:
        return "INVALID_TRANSITION"

    # 4. engine execution
    if action == "dice":
        result, state = GameEngine.process_turn(state, uid, payload["dice"])

    # 5. persist
    Repository.save(state)

    return result

# -----------------------------
# 6. CLEAN BOT READY (integration point)
# -----------------------------
# bot handlers فقط این رو صدا می‌زنن:
# dispatch_action(uid, cid, "dice", {"dice": value})
