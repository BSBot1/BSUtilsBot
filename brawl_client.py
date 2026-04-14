"""
Brawl Stars TCP Client for Friend Requests and Spectate
"""
import socket
import struct
import threading
import time
from crypto import PepperCrypto
from config import BRAWL_STARS_HOST, BRAWL_STARS_PORT, MSG_CLIENT_HELLO, MSG_LOGIN, MSG_FRIEND, MSG_SPECTATE

TAG_CHARS = '0289PYLQGRJCUV'

def encode_tag(tag):
    tag = tag.lstrip('#').upper()
    player_id = 0
    for char in tag:
        index = TAG_CHARS.index(char)
        player_id *= len(TAG_CHARS)
        player_id += index
    high = player_id % 256
    low = (player_id - high) // 256
    return high, low

class BrawlClient:
    def __init__(self, high_id, low_id, action='friend'):
        self.high_id = high_id
        self.low_id = low_id
        self.action = action
        self.crypto = PepperCrypto()
        self.socket = None

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((BRAWL_STARS_HOST, BRAWL_STARS_PORT))
            self._send_client_hello()
            self._send_login()
            if self.action == 'friend':
                self._send_friend_request()
            else:
                self._send_spectate()
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
        finally:
            if self.socket:
                self.socket.close()

    def _send_packet(self, msg_type, version, payload):
        payload_len = len(payload)
        header = struct.pack('>HH', msg_type, version)
        header += bytes([(payload_len >> 16) & 0xFF, (payload_len >> 8) & 0xFF, payload_len & 0xFF])
        self.socket.sendall(header + payload)

    def _send_client_hello(self):
        payload = bytes([0x00] * 8)
        encrypted = self.crypto.encrypt(MSG_CLIENT_HELLO, payload)
        self._send_packet(MSG_CLIENT_HELLO, 0, encrypted)

    def _send_login(self):
        major, minor, build = 59, 219, 1
        hash_id = bytes.fromhex("08dae21938f2f66e9a1dcc3d857b5fdf7f0e3eb8")
        content = bytearray(hash_id)
        content.extend(struct.pack('>HhI', major, minor, build))
        content.extend(bytes(12))
        encrypted = self.crypto.encrypt(MSG_LOGIN, bytes(content))
        self._send_packet(MSG_LOGIN, 0, encrypted)

    def _send_friend_request(self):
        payload = bytes([1, 0]) + self.high_id.to_bytes(2, 'big') + self.low_id.to_bytes(2, 'big')
        encrypted = self.crypto.encrypt(MSG_FRIEND, payload)
        self._send_packet(MSG_FRIEND, 0, encrypted)

    def _send_spectate(self):
        payload = bytes([0, 1]) + self.high_id.to_bytes(2, 'big') + self.low_id.to_bytes(2, 'big')
        encrypted = self.crypto.encrypt(MSG_SPECTATE, payload)
        self._send_packet(MSG_SPECTATE, 0, encrypted)

def send_friend_requests(tag, count=30):
    try:
        high, low = encode_tag(tag)
    except (ValueError, KeyError):
        return False, "Invalid player tag"
    threads = []
    results = []
    for i in range(count):
        client = BrawlClient(high, low, 'friend')
        t = threading.Thread(target=lambda c=client: results.append(c.connect()))
        t.start()
        threads.append(t)
        time.sleep(0.05)
    for t in threads:
        t.join(timeout=10)
    success_count = sum(1 for r in results if r)
    return True, f"Sent {success_count}/{count} friend requests to {tag}"

def send_spectators(tag, count=1):
    try:
        high, low = encode_tag(tag)
    except (ValueError, KeyError):
        return False, "Invalid player tag"
    if count < 1 or count > 200:
        return False, "Count must be between 1 and 200"
    threads = []
    results = []
    for i in range(count):
        client = BrawlClient(high, low, 'spectate')
        t = threading.Thread(target=lambda c=client: results.append(c.connect()))
        t.start()
        threads.append(t)
        time.sleep(0.02)
    for t in threads:
        t.join(timeout=15)
    success_count = sum(1 for r in results if r)
    return True, f"Sent {success_count}/{count} spectators to {tag}"
