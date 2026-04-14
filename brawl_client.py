"""
Brawl Stars TCP Client for Friend Requests and Spectate
"""
import socket
import struct
import threading
import time
from crypto import PepperCrypto
from config import BRAWL_STARS_HOST, BRAWL_STARS_PORT, MSG_CLIENT_HELLO, MSG_LOGIN, MSG_FRIEND, MSG_SPECTATE

# Tag encoding characters
TAG_CHARS = '0289PYLQGRJCUV'

def encode_tag(tag):
    """Encode player tag to high/low ID bytes"""
    tag = tag.lstrip('#').upper()
    player_id = 0

    for char in tag:
        index = TAG_CHARS.index(char)
        player_id *= len(TAG_CHARS)
        player_id += index

    high = player_id % 256
    low = (player_id - high) // 256
    return high, low

def create_header(msg_type, version, payload_length):
    """Create message header"""
    return struct.pack('>HhHH', msg_type, version, payload_length)

def encode_vint(value):
    """Encode variable-length integer"""
    result = []
    val = value

    while True:
        byte = val & 0x7F
        val >>= 7
        if val > 0:
            byte |= 0x80
        result.append(byte)
        if val == 0:
            break

    return bytes(result)

def decode_vint(data, offset=0):
    """Decode variable-length integer"""
    result = 0
    shift = 0

    while True:
        if offset >= len(data):
            return None, offset

        byte = data[offset]
        offset += 1
        result |= (byte & 0x7F) << shift

        if (byte & 0x80) == 0:
            break
        shift += 7

    return result, offset

class BrawlClient:
    """TCP client for Brawl Stars server"""

    def __init__(self, high_id, low_id, action='friend'):
        self.high_id = high_id
        self.low_id = low_id
        self.action = action  # 'friend' or 'spectate'
        self.crypto = PepperCrypto()
        self.socket = None
        self.connected = False
        self.done = False

    def connect(self):
        """Connect to Brawl Stars server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((BRAWL_STARS_HOST, BRAWL_STARS_PORT))
            self.connected = True

            # Send ClientHello
            self._send_client_hello()

            # Receive ServerHello
            if self._receive_and_process():
                # Send Login
                self._send_login()

                # Receive Login response
                self._receive_and_process()

                # Send Friend or Spectate
                if self.action == 'friend':
                    self._send_friend_request()
                else:
                    self._send_spectate()

            return True

        except Exception as e:
            print(f"Connection error: {e}")
            return False
        finally:
            self._close()

    def _send_client_hello(self):
        """Send ClientHello message"""
        # ClientHello payload (empty for now)
        payload = bytes([
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # padding
        ])

        encrypted = self.crypto.encrypt(MSG_CLIENT_HELLO, payload)
        self._send_packet(MSG_CLIENT_HELLO, 0, encrypted)

    def _send_login(self):
        """Send Login message"""
        # Login message structure
        major = 59
        minor = 219
        build = 1
        hash_id = bytes.fromhex("08dae21938f2f66e9a1dcc3d857b5fdf7f0e3eb8")

        content = bytearray()
        content.extend(hash_id)  # 20 bytes hash
        content.extend(struct.pack('>Hh', major, minor))  # 2 + 2 bytes
        content.extend(struct.pack('>I', build))  # 4 bytes
        content.extend(struct.pack('>I', 0))  # unknown
        content.extend(struct.pack('>I', 0))  # unknown
        content.extend(struct.pack('>I', 0))  # unknown

        payload = bytes(content)
        encrypted = self.crypto.encrypt(MSG_LOGIN, payload)
        self._send_packet(MSG_LOGIN, 0, encrypted)

    def _send_friend_request(self):
        """Send FriendRequest message"""
        payload = struct.pack('>BBHH',
            1,                    # Message version
            0,                    # Unknown
            self.high_id,         # High ID
            self.low_id           # Low ID
        )

        encrypted = self.crypto.encrypt(MSG_FRIEND, payload)
        self._send_packet(MSG_FRIEND, 0, encrypted)

    def _send_spectate(self):
        """Send Spectate message"""
        payload = struct.pack('>BBHH',
            0,                    # Message version
            1,                    # Unknown
            self.high_id,         # High ID
            self.low_id           # Low ID
        )

        encrypted = self.crypto.encrypt(MSG_SPECTATE, payload)
        self._send_packet(MSG_SPECTATE, 0, encrypted)

    def _send_packet(self, msg_type, version, payload):
        """Send encrypted packet to server"""
        header = create_header(msg_type, version, len(payload))
        packet = header + payload
        self.socket.sendall(packet)

    def _receive_and_process(self):
        """Receive and process server messages"""
        try:
            data = self.socket.recv(4096)
            if not data:
                return False

            # Parse packets
            offset = 0
            while offset < len(data):
                if offset + 7 > len(data):
                    break

                msg_type = struct.unpack('>H', data[offset:offset+2])[0]
                length = struct.unpack('>I', b'\x00' + data[offset+2:offset+5])[0]
                version = struct.unpack('>H', data[offset+5:offset+7])[0]

                if offset + 7 + length > len(data):
                    break

                payload = data[offset+7:offset+7+length]
                decrypted = self.crypto.decrypt(msg_type, payload)

                offset += 7 + length

                # Check for login success/failure
                if msg_type == 20103:
                    return True  # Login OK
                elif msg_type == 20104:
                    return True  # Login OK

            return True

        except socket.timeout:
            return True  # Timeout is okay, we might have sent our message
        except Exception as e:
            print(f"Receive error: {e}")
            return False

    def _close(self):
        """Close the connection"""
        try:
            if self.socket:
                self.socket.close()
        except:
            pass
        self.connected = False
        self.done = True

def send_friend_requests(tag, count=30):
    """Send multiple friend requests to a player"""
    try:
        high, low = encode_tag(tag)
    except (ValueError, KeyError):
        return False, "Invalid player tag"

    threads = []
    results = []

    for i in range(count):
        client = BrawlClient(high, low, 'friend')
        thread = threading.Thread(target=lambda c=client: results.append(c.connect()))
        thread.start()
        threads.append(thread)
        time.sleep(0.05)  # Small delay between connections

    for thread in threads:
        thread.join(timeout=10)

    success_count = sum(1 for r in results if r)
    return True, f"Sent {success_count}/{count} friend requests to {tag}"

def send_spectators(tag, count=1):
    """Send spectators to a player"""
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
        thread = threading.Thread(target=lambda c=client: results.append(c.connect()))
        thread.start()
        threads.append(thread)
        time.sleep(0.02)  # Small delay

    for thread in threads:
        thread.join(timeout=15)

    success_count = sum(1 for r in results if r)
    return True, f"Sent {success_count}/{count} spectators to {tag}"
