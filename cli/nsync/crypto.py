"""AES-256-GCM encryption with a symmetric cloud key."""
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_key() -> str:
    """Generate a new 256-bit key, returned as hex string."""
    return os.urandom(32).hex()


def encrypt(data: bytes, key_hex: str) -> bytes:
    """Encrypt data with AES-256-GCM. Returns nonce(12) + ciphertext."""
    nonce = os.urandom(12)
    ct = AESGCM(bytes.fromhex(key_hex)).encrypt(nonce, data, None)
    return nonce + ct


def decrypt(blob: bytes, key_hex: str) -> bytes:
    """Decrypt nonce(12) + ciphertext with AES-256-GCM."""
    return AESGCM(bytes.fromhex(key_hex)).decrypt(blob[:12], blob[12:], None)
