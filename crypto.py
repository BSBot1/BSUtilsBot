"""
Brawl Stars Pepper Crypto Implementation
Based on the NaCl cryptography library
"""
import os
import struct
import hashlib
import secrets
from nacl import bindings
from nacl.public import PrivateKey
from config import SERVER_PUBLIC_KEY

class Nonce:
    """Nonce generator for Brawl Stars protocol"""

    def __init__(self, nonce_bytes=None, keys=None):
        self.bytes_array = bytearray(24)

        if nonce_bytes is not None:
            self.bytes_array[:] = nonce_bytes[:24]
        elif keys is not None:
            self._generate_from_keys(keys)

    def _generate_from_keys(self, keys):
        """Generate nonce from client and server public keys"""
        combined = b''.join(k if isinstance(k, bytes) else bytes(k) for k in keys)
        h = hashlib.blake2b(combined, digest_size=24)
        self.bytes_array[:] = h.digest()[:24]

    def increment(self):
        """Increment the nonce counter"""
        for i in range(23, -1, -1):
            if self.bytes_array[i] < 255:
                self.bytes_array[i] += 1
                break
            self.bytes_array[i] = 0

    def get_bytes(self):
        return bytes(self.bytes_array)

class PepperCrypto:
    """Pepper crypto for Brawl Stars protocol"""

    def __init__(self):
        # Server public key (32 bytes)
        self.server_public_key = SERVER_PUBLIC_KEY

        # Generate client keypair using nacl.public.PrivateKey
        private_key_obj = PrivateKey.generate()
        self.client_secret_key = bytes(private_key_obj)
        self.client_public_key = bytes(private_key_obj.public_key)

        # Compute shared key using the raw bytes
        self.key = bindings.crypto_box_beforenm(self.server_public_key, self.client_secret_key)

        # Initialize nonces
        self.nonce = Nonce(keys=[self.client_public_key, self.server_public_key])
        self.client_nonce = Nonce()
        self.server_nonce = None
        self.session_key = None

    def encrypt(self, msg_type, payload):
        """Encrypt payload for given message type"""
        if msg_type == 10100:  # ClientHello - no encryption
            return payload

        if msg_type == 10101:  # Login
            data = self.session_key + self.client_nonce.get_bytes() + payload
            encrypted = bindings.crypto_box_afternm(data, self.nonce.get_bytes(), self.key)
            return self.client_public_key + encrypted

        # Other messages
        self.client_nonce.increment()
        return bindings.crypto_box_afternm(payload, self.client_nonce.get_bytes(), self.key)

    def decrypt(self, msg_type, payload):
        """Decrypt payload from given message type"""
        if msg_type == 20100:  # ServerHello
            self.session_key = payload[4:28]
            return payload

        if msg_type in (20103, 20104):  # Login responses
            if not self.session_key:
                return payload

            nonce = Nonce(nonce_bytes=self.client_nonce.get_bytes(),
                         keys=[self.client_public_key, self.server_public_key])

            decrypted = bindings.crypto_box_open_afternm(payload, nonce.get_bytes(), self.key)
            self.server_nonce = Nonce(nonce_bytes=decrypted[:24])
            self.key = decrypted[24:56]
            return decrypted[56:]

        # Other messages
        if self.server_nonce:
            self.server_nonce.increment()
            return bindings.crypto_box_open_afternm(payload, self.server_nonce.get_bytes(), self.key)
        return payload
