import os, subprocess, base64, struct
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from PySide6.QtWidgets import(QApplication, QMainWindow, QTextEdit)
from argon2.low_level import hash_secret_raw, Type

RED = "\033[31m" # ERRORS & REPORT
GREEN = "\033[32m" # SUCCESS & NEW RECORDS
YELLOW = "\033[33m" # FRESH Keys, INTEGERS & OLD RECORDS 
BLUE = "\033[34m" # EXISTING Keys
RESET = "\033[0m"

if not os.path.exists("vault.salt"):
    salt = os.urandom(16)
    with open("vault.salt", "wb") as k:
        k.write(salt)
else:
    with open("vault.salt", "rb") as k:
        salt = k.read()
         
masterpasswd = input("Enter your masterpasswd: ")

key = hash_secret_raw(
    secret=masterpasswd.encode(),
    salt=salt, # Random values
    time_cost=3, # No. of iterations
    memory_cost=65536, # 64MB Argon memory hardness
    parallelism=4, # No. of system threads/lanes
    hash_len=32, # Output size, in bytes 32bytes = 256bits
    type=Type.ID # I : Designed against side-channel attacks, D : Designed against GPU attacks for passwords
)

def encrypt_vault(vault_lines):

    # Encrypt raw bytes
    enc_cipher = AESGCM(key) # outputs masterkey for encryption/decryption

    with open("passwords.bin", "wb") as encrypt_bin:
        for i, line in enumerate(vault_lines):
            line = line.strip()

            nonce = os.urandom(12)
            encrypt_enc_d = enc_cipher.encrypt(nonce, line.encode(), None) # Encrypt string to bytes
            record_enc_d = nonce + encrypt_enc_d
            length = len(record_enc_d)

            encrypt_bin.write(struct.pack(">I", length)) # store encrypted raw bytes length
            encrypt_bin.write(record_enc_d) # store encrypted raw bytes record with nonce
            # print(f"ENCRYPTED: {YELLOW}{length}{RESET}:{GREEN}{record_enc_d}{RESET}")

    print("Saved.!\n")

def decrypt_vault():
    enc_cipher = AESGCM(key) # outputs masterkey for encryption/decryption
    vault_lines = []
    file_bin = "passwords.bin"
    try:
        if not os.path.exists(file_bin) and salt:
            print(f"{RED}Vault exists but salt-key or passwords blob is missing.\nThe vault cannot be decrypted.{RESET}")

        else:
            print(f"{GREEN}File in working directory: {RESET}",file_bin.capitalize(), "\n")

            with open(file_bin, "rb") as decrypt_bin:
                while True:
                    read_len_data = decrypt_bin.read(4) # Read 4 byte length
                    if not read_len_data:
                        print(f"{RED}End Of Line, EOF.!{RESET}")
                        break

                    length = struct.unpack(">I", read_len_data)[0] # Unpack lenght integer bytes
                    record_enc_d = decrypt_bin.read(length) # Read full byte record
                    nonce, cipher_text = record_enc_d[:12], record_enc_d[12:] # Extract nonce and Cipher text
                    try:
                        decrypt_enc_d = enc_cipher.decrypt(nonce, cipher_text, None) # Decrypt raw bytes to string

                    except InvalidTag:
                        print(f"{RED}Wrong master password or corrupted vault.{RESET}\n")

                    vault_lines.append(decrypt_enc_d.decode())
                
    except FileNotFoundError as e1:
        print(f"{RED}Error: {RESET}", e1)
    
    return vault_lines

def user_edit():
    app = QApplication([])
    window = QMainWindow()
    window.setWindowTitle(f"PassCore: {os.getcwd()}")
    window.setFixedSize(900, 700)
    editor = QTextEdit()

    window.setCentralWidget(editor)
    
    vault_lines = decrypt_vault()
    editor.setPlainText("\n".join(vault_lines))

    window.show()
    app.exec()
    new_lines = editor.toPlainText().splitlines()

    encrypt_vault(new_lines)

user_edit()
