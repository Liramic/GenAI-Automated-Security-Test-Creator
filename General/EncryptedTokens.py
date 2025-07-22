import os
import base64
import hashlib
from Crypto.Cipher import AES


irius_token = b'irius_token_encrypted'
azure_keys = [b'azure_key_1_encrypted', b'azure_key_2_encrypted']
jira_token = b'jira_token_encrypted'

def create_cipher():
    password = os.environ["PYTHON_SECRET"].encode()
    nonce = os.environ["PYTHON_NONCE"].encode()

    key = hashlib.sha256(password).digest()
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)

    return cipher

def encrypt_to_b64(string_data):
    cipher = create_cipher()
    ciphertext, tag = cipher.encrypt_and_digest(string_data.encode())
    return base64.b64encode(ciphertext)

def decrypt(b64_data):
    cipher = create_cipher()
    ciphet_text = base64.b64decode(b64_data)
    plaintext = cipher.decrypt(ciphet_text)
    return plaintext.decode()

def get_irius_token():
    return decrypt(irius_token)

def get_azure_key():
    #maybe better to select randomly?
    return decrypt(azure_keys[1])

def get_jira_token():
    return decrypt(jira_token)


## guide :
"""
1. Install the required library using 'pip install pycryptodome'.
2. Set the environment variables:
   - PYTHON_SECRET: Set this to your secret passphrase for key derivation.
   - PYTHON_NONCE: Set this to a unique nonce value (number used once) for encryption.
3. Replace 'irius_token' and 'azure_key' with your own tokens in bytes format ('b'...').
4. Use the 'encrypt_to_b64(string_data)' function to encrypt data and obtain a base64-encoded ciphertext.
5. Use the 'decrypt(b64_data)' function to decrypt base64-encoded data and obtain the plaintext.
6. Example usage (replace placeholders with your data):
   - Encrypt: encrypted_data = encrypt_to_b64("your_data_to_encrypt")
   - Decrypt: decrypted_data = decrypt("your_base64_encoded_data")
"""
