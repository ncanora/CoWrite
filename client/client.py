import hashlib

class Client:
    def __init__(self, name, color):
        self.name = name
        self.cursor_mark_name = f"cursor_{name}"
        self.color = color
        self.locked_lines = set()

def hash_key(password):
    return hashlib.sha256(password.encode()).hexdigest()