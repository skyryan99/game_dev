# Authoritative game server: clients send *intentions* ("move here"), the server runs them
# through engine.Game and broadcasts the resulting state. A client can never put the game into
# a state the rules do not allow, because it never gets to write the state.
#
#   python server.py                  # listens on 0.0.0.0:5555
#   python server.py --port 6000
#   python server.py --turn-limit 30      # seconds per turn: 10, 30, 60, 180 or inf
#
# Messages (see protocol.py for framing):
#   server -> client  {"type": "welcome", "player": 0 or 1}
#   client -> server  {"type": "ready", "loadout": {"troops": [...], "commands": [...]}}
#   server -> client  {"type": "state", "state": <Game.to_dict()>}      (sent after every change)
#   client -> server  {"type": "action", "action": {...}}               (see Game.apply_action)
#   server -> client  {"type": "error", "message": "..."}               (only to the sender)
import argparse
import socketserver
import threading

import protocol
from engine import DEFAULT_TURN_LIMIT, Game, IllegalAction, Loadout

TICK_SECONDS = 0.1                  # how often the server checks whether a turn has run out of time


class Room:
    """One match: two player slots and, once both are ready, the Game."""

    def __init__(self, turn_limit=DEFAULT_TURN_LIMIT):
        self.lock = threading.Lock()
        self.turn_limit = turn_limit
        self.reset()

    def reset(self):
        self.conns = [None, None]
        self.loadouts = [None, None]
        self.game = None

    def join(self, conn):
        with self.lock:
            for slot in (0, 1):
                if self.conns[slot] is None:
                    self.conns[slot] = conn
                    self.loadouts[slot] = None
                    return slot
        return None

    def leave(self, slot):
        with self.lock:
            self.conns[slot] = None
            if self.game is not None and self.game.winner is None:
                self.game.resign(slot)
                self._broadcast_state()
            if self.conns == [None, None]:
                self.reset()

    def handle(self, slot, msg):
        """Process one client message. Returns an error string for the sender, or None."""
        with self.lock:
            kind = msg.get("type") if isinstance(msg, dict) else None
            if kind == "ready":
                if self.game is not None:
                    return "the game has already started"
                try:
                    loadout = Loadout.from_dict(msg.get("loadout") or {})
                    loadout.validate()
                except (IllegalAction, TypeError, AttributeError) as exc:
                    return "bad loadout: %s" % exc
                self.loadouts[slot] = loadout
                if all(self.loadouts):
                    self.game = Game.new(self.loadouts, turn_limit=self.turn_limit)
                    self._broadcast_state()
                return None
            if kind == "action":
                if self.game is None:
                    return "the game has not started"
                try:
                    self.game.apply_action(slot, msg.get("action"))
                except IllegalAction as exc:
                    return str(exc)
                self._broadcast_state()
                return None
            return "unknown message type"

    def tick(self):
        """Called by the server's clock thread: end the turn if time has run out and tell both players."""
        with self.lock:
            if self.game is not None and self.game.tick():
                self._broadcast_state()

    def _broadcast_state(self):
        payload = {"type": "state", "state": self.game.to_dict()}
        for conn in self.conns:
            if conn is not None:
                try:
                    protocol.send_msg(conn, payload)
                except OSError:
                    pass        # that player's own handler thread will notice and call leave()


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        room = self.server.room
        slot = room.join(self.request)
        if slot is None:
            try:
                protocol.send_msg(self.request, {"type": "error", "message": "server is full"})
            except OSError:
                pass
            return
        try:
            protocol.send_msg(self.request, {"type": "welcome", "player": slot})
            while True:
                msg = protocol.recv_msg(self.request)
                error = room.handle(slot, msg)
                if error:
                    protocol.send_msg(self.request, {"type": "error", "message": error})
        except (ConnectionError, OSError, protocol.ProtocolError):
            pass
        finally:
            room.leave(slot)


class GameServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, host="0.0.0.0", port=5555, turn_limit=DEFAULT_TURN_LIMIT):
        super().__init__((host, port), Handler)
        self.room = Room(turn_limit)
        self._stop_clock = threading.Event()

    def serve_forever(self, poll_interval=0.5):
        threading.Thread(target=self._run_clock, daemon=True).start()
        super().serve_forever(poll_interval)

    def _run_clock(self):
        while not self._stop_clock.wait(TICK_SECONDS):
            self.room.tick()

    def shutdown(self):
        self._stop_clock.set()
        super().shutdown()

    @property
    def port(self):
        return self.server_address[1]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Conquest game server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5555)
    parser.add_argument("--turn-limit", default=str(DEFAULT_TURN_LIMIT), choices=["10", "30", "60", "180", "inf"],
                        help="seconds per turn, or inf for no limit")
    args = parser.parse_args()
    limit = None if args.turn_limit == "inf" else int(args.turn_limit)
    with GameServer(args.host, args.port, limit) as srv:
        print("Waiting for players on %s:%d" % (args.host, srv.port))
        srv.serve_forever()
