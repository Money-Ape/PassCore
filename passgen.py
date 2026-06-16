import secrets, string
from PySide6.QtWidgets import QMessageBox

def generate_password(length=19, upper=True, lower=True, digits=True, symbols=True):
        chars = ""
        if upper:
            chars += string.ascii_uppercase
        if lower:
            chars += string.ascii_lowercase
        if digits:
            chars += string.digits
        if symbols:
            chars += "!@#$%^&*()-_=+[]{}"
        if not chars:
            QMessageBox.information(None, "Password Generator", "Not character set selected.! :(")

        passwd = "".join(secrets.choice(chars)
            for _ in range(length))
        
        return passwd
