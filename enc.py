import os, subprocess, base64, struct
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from datetime import datetime

RED = "\033[31m" # ERRORS & REPORT
GREEN = "\033[32m" # SUCCESS & NEW RECORDS
YELLOW = "\033[33m" # FRESH Keys, INTEGERS & OLD RECORDS 
BLUE = "\033[34m" # EXISTING Keys
RESET = "\033[0m"
     
# Decoded base64 bytes
existing_dec_line = []
if os.path.exists("b64b.bin"):
    with open("b64b.bin", "rb") as b64b:
        for line in b64b:
            line = line.strip()
    
            dec_records = base64.b64decode(line).decode()
            existing_dec_line.append(dec_records)
            print(f"OLD_RECORD: {YELLOW}{dec_records}{RESET}")

# Store from txt to Compare with
compare_lines = []
for src_txt_file in os.listdir():
    if src_txt_file.endswith(".txt"):
        with open(src_txt_file, "r") as src:
            src_line = src.read().splitlines()
            
            for line in src_line:
                line = line.strip()
                if not line:
                    continue
                if line:
                    compare_lines.append(line)
            break

# Compare with Decoded records
update_line = []
for i, new_line in enumerate(compare_lines):
    timestamp = datetime.now().strftime("[%d_%m_%Y:%H_%M]")

    if i < len(existing_dec_line): # Old exists
        old_rec = existing_dec_line[i].rsplit("[", 1)[0].strip()

        if old_rec == new_line: # Unchanged
            update_line.append(existing_dec_line[i])
        else:
            update_line.append(f"{new_line} {timestamp}") # Modified
    else:
        update_line.append(f"{new_line} {timestamp}") # New line added

# Encode to bin
with open("b64b.bin", "w") as b64b:
    for records in update_line:
        enc_records = base64.b64encode(records.encode()).decode()
        b64b.write(enc_records+"\n")

if not os.path.exists("masterkey.key"):
    key = AESGCM.generate_key(bit_length=256) # Encryption AESGCM key
    with open("masterkey.key", "wb") as k: # Stores the masterkey
        key = k.write(key)
        print(f"NEW_KEY_GENERATED: {YELLOW}{key}{RESET}") # Output as YELLOW if new KEY generated
else:
    with open("masterkey.key", "rb") as k:
        key = k.read()
        print(f"EXISTIGNG_KEY: {BLUE}{key}{RESET}") # Output as BLUE if KEY exists
enc_cipher = AESGCM(key) # outputs masterkey for encryption/decryption

def encrypted_bytes():
    
    # Encrypt raw bytes
    with open("passwords.bin", "wb") as encrypt_bin:
        for i, line in enumerate(update_line):
            line = line.strip()

            nonce = os.urandom(12)
            encrypt_enc_d = enc_cipher.encrypt(nonce, line.encode(), None) # Encrypt string to bytes
            record_enc_d = nonce + encrypt_enc_d
            length = len(record_enc_d)

            encrypt_bin.write(struct.pack(">I", length)) # store encrypted raw bytes length
            encrypt_bin.write(record_enc_d) # store encrypted raw bytes record with nonce
            print(f"ENCRYPTED: {YELLOW}{length}{RESET}:{GREEN}{record_enc_d}{RESET}")

    print("Saved.!\n")

    # Decrypt binary Data
    file_b = "passwords.bin"
    try:
        if os.path.exists(file_b):
            print(f"{GREEN}File in working directory: {RESET}",file_b, "\n")

            with open(file_b, "rb") as decrypt_bin:
                while True:
                    read_len_data = decrypt_bin.read(4) # Read 4 byte length
                    if not read_len_data:
                        print(f"{RED}End Of Line, EOF.!{RESET}")
                        break

                    length = struct.unpack(">I", read_len_data)[0] # Unpack lenght integer bytes
                    record_enc_d = decrypt_bin.read(length) # Read full byte record
                    nonce, cipher_text = record_enc_d[:12], record_enc_d[12:] # Extract nonce and Cipher text
                    decrypt_enc_d = enc_cipher.decrypt(nonce, cipher_text, None) # Decrypt raw bytes to string
                    print("DECRYPTED_NEW_BYTE_RECORD: ",decrypt_enc_d.decode())
            
    except FileNotFoundError as e1:
        print(f"{RED}Error: {RESET}", e1)

encrypted_bytes()