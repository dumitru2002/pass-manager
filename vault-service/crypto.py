from Crypto.Cipher import AES
from base64 import b64encode, b64decode

# FIXED KEY - 32 bytes - NEVER CHANGES
KEY = b"12345678901234567890123456789012"

def encrypt(text: str) -> str:
    cipher = AES.new(KEY, AES.MODE_EAX)
    nonce = cipher.nonce
    ciphertext, tag = cipher.encrypt_and_digest(text.encode("utf-8"))
    return b64encode(nonce + tag + ciphertext).decode("utf-8")

def decrypt(enc: str) -> str:
    try:
        raw = b64decode(enc)
        nonce = raw[:16]
        tag = raw[16:32]
        ciphertext = raw[32:]
        cipher = AES.new(KEY, AES.MODE_EAX, nonce=nonce)
        plaintext = cipher.decrypt(ciphertext)   # first decrypt
        cipher.verify(tag)   # then verify tag
        return plaintext.decode("utf-8")
    except Exception as e:
        return f"!!!DECRYPT FAILED!!!"