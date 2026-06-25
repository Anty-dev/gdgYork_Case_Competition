"""
sample_vulnerable.py
────────────────────
Intentionally bad code for testing the review system.
DO NOT USE IN PRODUCTION.
"""

import sqlite3
import subprocess
import pickle
import os

# Hardcoded secret (bad!)
DB_PASSWORD = "supersecret123"
API_KEY = "sk-prod-abc123xyz"


def get_user(username):
    # SQL injection vulnerability
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
    return cursor.fetchone()
    # BUG: connection never closed


def run_command(user_input):
    # Command injection vulnerability
    result = subprocess.run("ls " + user_input, shell=True, capture_output=True)
    return result.stdout


def load_data(data_bytes):
    # Unsafe deserialization
    return pickle.loads(data_bytes)


def divide(a, b):
    # No zero-division guard
    return a / b


def process_items(items):
    total = 0
    # Off-by-one: should be range(len(items))
    for i in range(len(items) - 1):
        total += items[i]
    return total


def find_user_by_id(user_id, users):
    # Will throw IndexError if user_id >= len(users)
    return users[user_id]


class DataProcessor:
    def __init__(self):
        self.d = {}  # terrible variable name

    def proc(self, x):  # terrible method name
        # magic number
        if x > 42:
            return x * 2
        else:
            return x


def read_file(filename):
    # Path traversal vulnerability
    base_dir = "/var/app/data/"
    full_path = base_dir + filename  # no validation
    with open(full_path, "r") as f:
        return f.read()


def authenticate(u, p):
    # Timing attack vulnerability; also terrible naming
    stored = get_user(u)
    if stored and stored[1] == p:
        return True
    return False
