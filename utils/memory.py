# utils/memory.py
import json
import os
import time

FILE = "memory.json"

def load():
    if os.path.exists(FILE):
        with open(FILE) as f:
            return json.load(f)
    return []

def save(history):
    with open(FILE, "w") as f:
        json.dump(history[-5:], f)

def remember(message, reply):
    data = load()
    data.append({"t": int(time.time()), "u": message, "a": reply})
    save(data)
    return data
