import os, struct
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from PySide6.QtWidgets import(QWidget ,QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QTextEdit, QInputDialog, QLineEdit, QPushButton, QMessageBox)
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

def encrypt_vault(new_lines, key):

    # Encrypt raw bytes
    enc_cipher = AESGCM(key) # outputs masterkey for encryption/decryption

    with open("passwords.bin", "wb") as encrypt_bin:
        for i, line in enumerate(new_lines):
            line = line.strip()

            nonce = os.urandom(12)
            encrypt_enc_d = enc_cipher.encrypt(nonce, line.encode(), None) # Encrypt string to bytes
            record_enc_d = nonce + encrypt_enc_d
            length = len(record_enc_d)

            encrypt_bin.write(struct.pack(">I", length)) # store encrypted raw bytes length
            encrypt_bin.write(record_enc_d) # store encrypted raw bytes record with nonce
            # print(f"ENCRYPTED: {YELLOW}{length}{RESET}:{GREEN}{record_enc_d}{RESET}")

    print("Saved.!\n")

def decrypt_vault(window, key):
    enc_cipher = AESGCM(key) # outputs masterkey for encryption/decryption
    vault_lines = []
    file_bin = "passwords.bin"
    try:
        if not os.path.exists(file_bin):
            print(f"{RED}Vault exists but salt-key or passwords blob is missing.\nThe vault cannot be decrypted.!{RESET}")
            QMessageBox.information(None, "PassCore", "No vault found.!\nCreating a new vault.!")
            return []

        else:
            print(f"{GREEN}File in working directory: {RESET}",file_bin.capitalize(), "\n")

            with open(file_bin, "rb") as decrypt_bin:
                while True:
                    read_len_data = decrypt_bin.read(4) # Read 4 byte length
                    if not read_len_data:
                        break

                    length = struct.unpack(">I", read_len_data)[0] # Unpack lenght integer bytes
                    record_enc_d = decrypt_bin.read(length) # Read full byte record
                    nonce, cipher_text = record_enc_d[:12], record_enc_d[12:] # Extract nonce and Cipher text
                    decrypt_enc_d = enc_cipher.decrypt(nonce, cipher_text, None) # Decrypt raw bytes to string
                    vault_lines.append(decrypt_enc_d.decode())
                
    except FileNotFoundError as e1:
        print(f"{RED}Error: {RESET}", e1)
    
    return vault_lines

def vault_lock(window, editor, save_btn, close_btn, unlock_btn, lock_btn):
    reply = QMessageBox.question(
        window, "PassCore", "Lock the vault.?", QMessageBox.Yes | QMessageBox.No
    )
    if reply == QMessageBox.Yes:
        editor.clear()
        editor.hide()
        save_btn.hide()
        close_btn.hide()
        lock_btn.hide()
        QMessageBox.information(window, "PassCore", "Vault Locked.!")

        unlock_btn.show()
        window.key = None 
        
    elif reply == QMessageBox.No:
        return

def unlock_vault(window, editor, save_btn, close_btn, unlock_btn, lock_btn):
    while True:
        masterpasswd, ok = QInputDialog.getText(
            window, "Unlock Vault",
            f"Master Passwd: ", QLineEdit.Password
        )
        if not ok:
            window.close()
            return
        
        key = hash_secret_raw(
            secret=masterpasswd.encode(),
            salt=salt, # Random values
            time_cost=3, # No. of iterations
            memory_cost=65536, # 64MB Argon memory hardness
            parallelism=4, # No. of system threads/lanes
            hash_len=32, # Output size, in bytes 32bytes = 256bits
            type=Type.ID # I : Designed against side-channel attacks, D : Designed against GPU attacks for passwords
        )    
        try:
            vault_lines = decrypt_vault(window, key)
            window.key = key
            unlock_btn.hide()
            
            editor.show()
            save_btn.show()
            close_btn.show()
            lock_btn.show()
            editor.setPlainText("\n".join(vault_lines))
            return
        
        except InvalidTag:
            QMessageBox.information(window, "PassCore", "wrong master password.!")


def save_vault(editor, key):
    new_lines = editor.toPlainText().splitlines()
    encrypt_vault(new_lines, key)
    QMessageBox.information(None, "PassCore", "Vault saved successfully.!")

def vault_close(window, editor, key):
    reply = QMessageBox.question(
        window, "PassCore", "Save changes before closing the Vault.?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
    )
    if reply == QMessageBox.Yes:
        new_lines = editor.toPlainText().splitlines()
        encrypt_vault(new_lines, key)
        window.close()
        print(f"{YELLOW}bye.!{RESET}")
    
    elif reply == QMessageBox.No:
        window.close()
        print(f"{YELLOW}bye.!{RESET}")
    
    elif reply == QMessageBox.Cancel:
        return


def user_edit():
    app = QApplication([])
    window = QMainWindow()
    window.setWindowTitle(f"PassCore: {os.getcwd()}")
    window.setFixedSize(900, 700)
    editor = QTextEdit()
    container = QWidget() # QWidget container
    layout = QVBoxLayout(container) # Vertical layout
    btn_layout = QHBoxLayout() # Horizontal layout
    
    save_btn = QPushButton("Save") # save 
    close_btn = QPushButton("Close") # close
    lock_btn = QPushButton("Lock Vault") # lock vault again
    unlock_btn = QPushButton("Unlock Vault") # unlock vault again
    unlock_btn.hide()

    btn_layout.addWidget(save_btn)
    btn_layout.addWidget(close_btn)
    btn_layout.addWidget(lock_btn)
    btn_layout.addWidget(unlock_btn)

    layout.addWidget(editor)
    layout.addLayout(btn_layout)
    window.setCentralWidget(container)
    
    unlock_vault(window, editor, save_btn, close_btn, unlock_btn, lock_btn)

    save_btn.clicked.connect(
        lambda: save_vault(editor, window.key)
    )

    close_btn.clicked.connect(
        lambda: vault_close(window, editor, window.key))
    
    lock_btn.clicked.connect(
        lambda: vault_lock(window, editor, save_btn, close_btn, unlock_btn, lock_btn)
    )
    unlock_btn.clicked.connect(
        lambda: unlock_vault(window, editor, save_btn, close_btn, unlock_btn, lock_btn)
    )
    
    window.show()
    app.exec()

user_edit()
