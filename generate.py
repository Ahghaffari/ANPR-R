import socket
import time
import getmac
import uuid
import random
from cryptography.fernet import Fernet


def generate_key():
    """
    Generates a key and save it into a file
    """
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)


def encrypt_message(message):
    """
    Encrypts a message
    """
    key = 'CaM0fyXCyTkGp30mrRIzWPKVroOYFNh8_0IqtZTCTyA='

    encoded_message = message.encode()
    f = Fernet(key)

    return f.encrypt(encoded_message)


def decrypt_message(encrypted_message):
    """
    Decrypts an encrypted message
    """
    key = 'CaM0fyXCyTkGp30mrRIzWPKVroOYFNh8_0IqtZTCTyA='
    f = Fernet(key)
    decrypted_message = f.decrypt(encrypted_message)

    return decrypted_message.decode()


system_id = '9c8e9951c8ff'
encrypted_message = encrypt_message(system_id)
print(encrypted_message.decode())
print(decrypt_message(encrypted_message))
