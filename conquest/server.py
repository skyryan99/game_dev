# Authoritative game server: clients send *intentions* ("move here"), the server runs them
# through engine.Game and broadcasts the resulting state. A client can never put the game into
# a state the rules do not allow, because it never gets to write the state.
#
#   python server.py                  # listens on 0.0.0.0:5555
#   python server.py --port 6000
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
from engine import Game, IllegalAction, Loadout


class Room:
    """One match: two player slots and, once both are ready, the Game."""

    def __init__(self):
        self.lock = threading.Lock()
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
                    self.game = Game.new(self.loadouts)
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

    def __init__(self, host="0.0.0.0", port=5555):
        super().__init__((host, port), Handler)
        self.room = Room()

    @property
    def port(self):
        return self.server_address[1]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Conquest game server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5555)
    args = parser.parse_args()
    with GameServer(args.host, args.port) as srv:
        print("Waiting for players on %s:%d" % (args.host, srv.port))
        srv.serve_forever()
