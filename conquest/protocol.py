# Wire format shared by the client and the server: a 4-byte big-endian length, then UTF-8 JSON.
# (Replaces pickle, which lets whoever you are talking to run code on your machine, and the
# fixed recv(2048), which silently truncates anything bigger.)
import json
import struct

MAX_MESSAGE_BYTES = 1 << 20


class ProtocolError(Exception):
    pass


def send_msg(sock, obj):
    payload = json.dumps(obj, separators=(",", ":")).encode("utf-8")
    if len(payload) > MAX_MESSAGE_BYTES:
        raise ProtocolError("message too large")
    sock.sendall(struct.pack(">I", len(payload)) + payload)


def _recv_exact(sock, count):
    chunks = []
    while count:
        chunk = sock.recv(count)
        if not chunk:
            raise ConnectionError("connection closed")
        chunks.append(chunk)
        count -= len(chunk)
    return b"".join(chunks)


def recv_msg(sock):
    """Block until one whole message arrives. Raises ConnectionError if the peer hangs up."""
    (length,) = struct.unpack(">I", _recv_exact(sock, 4))
    if length > MAX_MESSAGE_BYTES:
        raise ProtocolError("message too large")
    try:
        return json.loads(_recv_exact(sock, length).decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ProtocolError("bad message") from exc
