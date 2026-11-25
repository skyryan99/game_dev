# Client side of the connection. A background thread reads messages into a queue so the
# pygame loop never blocks: call poll() once per frame to collect whatever has arrived.
#
#   net = Network("192.168.1.100", 5555)       # or Network() to use CONQUEST_HOST / localhost
#   net.send({"type": "ready", "loadout": loadout.to_dict()})
#   for msg in net.poll(): ...
import os
import queue
import socket
import threading

import protocol


class Network:
    def __init__(self, host=None, port=None, timeout=5.0):
        self.host = host or os.environ.get("CONQUEST_HOST", "127.0.0.1")
        self.port = int(port or os.environ.get("CONQUEST_PORT", 5555))
        self.incoming = queue.Queue()
        self.connected = False
        self.player = None                      # 0 or 1 once the server says welcome
        self.sock = socket.create_connection((self.host, self.port), timeout=timeout)
        self.sock.settimeout(None)
        self.connected = True
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        try:
            while True:
                self.incoming.put(protocol.recv_msg(self.sock))
        except (ConnectionError, OSError, protocol.ProtocolError):
            pass
        finally:
            self.connected = False
            self.incoming.put({"type": "disconnected"})

    def send(self, msg):
        try:
            protocol.send_msg(self.sock, msg)
        except OSError:
            self.connected = False

    def poll(self):
        """Return every message received since the last call (never blocks)."""
        messages = []
        while True:
            try:
                msg = self.incoming.get_nowait()
            except queue.Empty:
                return messages
            if msg.get("type") == "welcome":
                self.player = msg["player"]
            messages.append(msg)

    def close(self):
        self.connected = False
        try:
            # shutdown() first: close() alone does not wake the reader thread blocked in recv(),
            # so the server would never see us leave.
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass
