import os
import sys
import threading
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import protocol
from network import Network
from server import GameServer


def wait_for(net, kind, timeout=3.0):
    end = time.time() + timeout
    seen = []
    while time.time() < end:
        for msg in net.poll():
            seen.append(msg)
            if msg.get("type") == kind:
                return msg
        time.sleep(0.01)
    raise AssertionError("never got %r, saw %r" % (kind, seen))


class ServerTestCase(unittest.TestCase):
    turn_limit = 60

    def setUp(self):
        self.server = GameServer("127.0.0.1", 0, self.turn_limit)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.clients = []

    def tearDown(self):
        for c in self.clients:
            c.close()
        self.server.shutdown()
        self.server.server_close()

    def connect(self):
        c = Network("127.0.0.1", self.server.port)
        self.clients.append(c)
        return c

    def start_match(self):
        a, b = self.connect(), self.connect()
        self.assertEqual(wait_for(a, "welcome")["player"], 0)
        self.assertEqual(wait_for(b, "welcome")["player"], 1)
        loadout = {"troops": ["scout", "knight"], "commands": ["charge"]}
        a.send({"type": "ready", "loadout": loadout})
        b.send({"type": "ready", "loadout": loadout})
        return a, b, wait_for(a, "state")["state"], wait_for(b, "state")["state"]



class NetworkTests(ServerTestCase):
    def test_match_starts_and_both_players_see_the_same_board(self):
        a, b, sa, sb = self.start_match()
        self.assertEqual(sa, sb)
        self.assertEqual(len(sa["units"]), 4)

    def test_legal_move_is_broadcast_and_illegal_ones_only_error_the_sender(self):
        a, b, state, _ = self.start_match()
        mine = [u for u in state["units"] if u["owner"] == 0][0]
        a.send({"type": "action", "action": {"type": "select", "unit": mine["uid"]}})
        new_a = wait_for(a, "state")["state"]
        new_b = wait_for(b, "state")["state"]
        self.assertEqual(new_a["selected"], mine["uid"])
        self.assertEqual(new_a, new_b)
        # Player 2 trying to act out of turn gets an error, and nobody gets a new state.
        theirs = [u for u in state["units"] if u["owner"] == 1][0]
        b.send({"type": "action", "action": {"type": "select", "unit": theirs["uid"]}})
        self.assertIn("turn", wait_for(b, "error")["message"])

    def test_garbage_does_not_crash_the_server(self):
        a, b, state, _ = self.start_match()
        a.send({"type": "action", "action": {"type": "move", "row": "x", "col": [1]}})
        wait_for(a, "error")
        a.send({"type": "nonsense"})
        wait_for(a, "error")
        a.send({"type": "ready", "loadout": {"troops": ["dragon"]}})
        wait_for(a, "error")
        a.send({"type": "action", "action": {"type": "end_turn"}})
        self.assertEqual(wait_for(a, "state")["state"]["current"], 1)

    def test_bad_loadout_rejected(self):
        a = self.connect()
        wait_for(a, "welcome")
        a.send({"type": "ready", "loadout": {"troops": ["champion"] * 6}})
        self.assertIn("loadout", wait_for(a, "error")["message"])

    def test_third_player_is_turned_away(self):
        self.connect(); self.connect()
        c = self.connect()
        self.assertIn("full", wait_for(c, "error")["message"])

    def test_disconnect_forfeits(self):
        a, b, _, _ = self.start_match()
        a.close()
        self.assertEqual(wait_for(b, "state")["state"]["winner"], 1)


class TurnTimerNetworkTests(ServerTestCase):
    turn_limit = 0.4                    # the server accepts any positive limit; the menu offers 10/30/60/180/inf

    def test_server_ends_a_turn_that_runs_out_of_time(self):
        a, b, state, _ = self.start_match()
        self.assertEqual((state["current"], state["turn_limit"]), (0, 0.4))
        for client in (a, b):                                   # nobody touches anything
            new = wait_for(client, "state", timeout=3)["state"]
            self.assertEqual(new["current"], 1)
            self.assertTrue(any("Time is up" in line for line in new["log"]))

    def test_no_limit_means_the_server_never_ends_the_turn(self):
        self.server.room.turn_limit = None
        a, b, state, _ = self.start_match()
        self.assertIsNone(state["turn_limit"])
        time.sleep(0.6)
        self.assertEqual(a.poll(), [])                          # no new state arrived: the turn is still player 1's


class ProtocolTests(unittest.TestCase):
    def test_round_trip_larger_than_old_recv_buffer(self):
        import socket
        left, right = socket.socketpair()
        big = {"blob": "x" * 50000}
        threading.Thread(target=protocol.send_msg, args=(left, big), daemon=True).start()
        self.assertEqual(protocol.recv_msg(right), big)
        left.close(); right.close()


if __name__ == "__main__":
    unittest.main()
