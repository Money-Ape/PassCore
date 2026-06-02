import os, subprocess, base64, struct
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from datetime import datetime
from PySide6.QtWidgets import(QApplication, QMainWindow, QTextEdit)

RED = "\033[31m" # ERRORS & REPORT
GREEN = "\033[32m" # SUCCESS & NEW RECORDS
YELLOW = "\033[33m" # FRESH Keys, INTEGERS & OLD RECORDS 
BLUE = "\033[34m" # EXISTING Keys
RESET = "\033[0m"

if not os.path.exists("masterkey.key"):
    key = AESGCM.generate_key(bit_length=256) # Encryption AESGCM key
    with open("masterkey.key", "wb") as k: # Stores the masterkey
        k.write(key)
    print(f"NEW_KEY_GENERATED: {YELLOW}{key}{RESET}") # Output as YELLOW if new KEY generated
else:
    with open("masterkey.key", "rb") as k:
        key = k.read()
        print(f"EXISTIGNG_KEY: {BLUE}{key}{RESET}") # Output as BLUE if KEY exists

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
            print(f"ENCRYPTED: {YELLOW}{length}{RESET}:{GREEN}{record_enc_d}{RESET}")

    print("Saved.!\n")

def decrypt_vault():
    enc_cipher = AESGCM(key) # outputs masterkey for encryption/decryption
    vault_lines = []
    file_bin = "passwords.bin"
    try:
        if os.path.exists(file_bin):
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
                    decrypt_enc_d = enc_cipher.decrypt(nonce, cipher_text, None) # Decrypt raw bytes to string

                    vault_lines.append(decrypt_enc_d.decode())
                
    except FileNotFoundError as e1:
        print(f"{RED}Error: {RESET}", e1)
    
    return vault_lines

def user_edit():
    app = QApplication([])
    window = QMainWindow()
    window.setWindowTitle(f"PassCore: {os.getcwd()}")
    window.setFixedSize(900, 800)
    editor = QTextEdit()

    window.setCentralWidget(editor)
    
    vault_lines = decrypt_vault()
    editor.setPlainText("\n".join(vault_lines))
    print(vault_lines)

    window.show()
    app.exec()
    new_lines = editor.toPlainText().splitlines()

    encrypt_vault(new_lines)
    print("NEW_LINE: ", new_lines)

user_edit()
