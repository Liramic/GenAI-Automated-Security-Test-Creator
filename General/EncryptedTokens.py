import os
import base64
import hashlib
from Crypto.Cipher import AES


irius_token = b'irius_token_encrypted'
azure_keys = [b'azure_key_1_encrypted', b'azure_key_2_encrypted']
jira_token = b'jira_token_encrypted'

# Optional clear-text overrides (useful for local/dev without env vars)
# Set these to non-empty strings to override environment variables.

CLEAR_PYTHON_SECRET = "dor_P:{'}"
CLEAR_PYTHON_NONCE = "thisIsMyPythonNonce123"

# Flag to detect placeholder data (unencrypted short tokens) and missing environment
def _is_placeholder(data: bytes) -> bool:
    # Heuristic: placeholder values not base64 length and contain underscore text
    try:
        base64.b64decode(data)
        return False
    except Exception:
        return True

def _env_configured() -> bool:
    return all(k in os.environ and os.environ[k] for k in ["PYTHON_SECRET", "PYTHON_NONCE"])

def _overrides_configured() -> bool:
    return bool(CLEAR_PYTHON_SECRET) and bool(CLEAR_PYTHON_NONCE)

def _derive_nonce(nonce_str: str) -> bytes:
    # GCM recommended 12-byte nonce; derive deterministically if provided string isn't 12 bytes
    nb = nonce_str.encode()
    if len(nb) == 12:
        return nb
    # Derive 12 bytes from SHA256 of the string
    return hashlib.sha256(nb).digest()[:12]

def _get_secret_and_nonce() -> tuple[bytes, bytes]:
    if _overrides_configured():
        password_bytes = CLEAR_PYTHON_SECRET.encode()
        nonce_bytes = _derive_nonce(CLEAR_PYTHON_NONCE)
        return password_bytes, nonce_bytes
    elif _env_configured():
        password_bytes = os.environ["PYTHON_SECRET"].encode()
        nonce_bytes = _derive_nonce(os.environ["PYTHON_NONCE"])
        return password_bytes, nonce_bytes
    else:
        return b"", b""

def create_cipher():
    password, nonce = _get_secret_and_nonce()
    if not password or not nonce:
        # Signal missing config; callers should handle gracefully
        raise ValueError("Missing PYTHON_SECRET/PYTHON_NONCE (env or clear-text overrides)")

    key = hashlib.sha256(password).digest()
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher

def encrypt_to_b64(string_data):
    cipher = create_cipher()
    ciphertext, tag = cipher.encrypt_and_digest(string_data.encode())
    return base64.b64encode(ciphertext)

def decrypt(b64_data):
    # If data is a placeholder (not base64) simply indicate placeholder
    if _is_placeholder(b64_data):
        return "CONFIG_PLACEHOLDER"
    try:
        cipher = create_cipher()
        cipher_text = base64.b64decode(b64_data)
        plaintext = cipher.decrypt(cipher_text)
        return plaintext.decode()
    except Exception:
        return "CONFIG_DECRYPT_ERROR"

def get_irius_token():
    return decrypt(irius_token)

def get_azure_key():
    #maybe better to select randomly?
    if len(azure_keys) == 0:
        return "CONFIG_PLACEHOLDER"
    return decrypt(azure_keys[1 if len(azure_keys) > 1 else 0])

def get_jira_token():
    return decrypt(jira_token)


## guide :
"""
1. Install the required library using 'pip install pycryptodome'.
2. Configure secrets either via ENV or clear-text overrides:
    Option A (recommended): Set environment variables
    - PYTHON_SECRET: Your secret passphrase for key derivation.
    - PYTHON_NONCE: A unique nonce string (will be deterministically mapped to 12 bytes).
    Option B (dev/local): Set module-level variables
    - CLEAR_PYTHON_SECRET = "your-secret"
    - CLEAR_PYTHON_NONCE = "your-nonce"
    Note: CLEAR_* takes precedence over ENV when both provided.
3. Replace 'irius_token' and 'azure_key' with your own tokens in bytes format ('b'...').
4. Use the 'encrypt_to_b64(string_data)' function to encrypt data and obtain a base64-encoded ciphertext.
5. Use the 'decrypt(b64_data)' function to decrypt base64-encoded data and obtain the plaintext.
6. Example usage (replace placeholders with your data):
   - Encrypt: encrypted_data = encrypt_to_b64("your_data_to_encrypt")
   - Decrypt: decrypted_data = decrypt("your_base64_encoded_data")
"""
