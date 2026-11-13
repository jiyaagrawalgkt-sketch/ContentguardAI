import sqlite3
import os

db_paths = [
    os.path.abspath("contentguard.db"),
    os.path.abspath("backend/contentguard.db")
]

for p in db_paths:
    if os.path.exists(p):
        conn = sqlite3.connect(p)
        cur = conn.cursor()
        cur.execute("UPDATE users SET full_name = 'Namo Tripathi' WHERE email = 'admin@contentguard.demo'")
        cur.execute("UPDATE users SET full_name = 'Jiya Agrawal' WHERE email = 'reviewer@contentguard.demo'")
        cur.execute("UPDATE users SET full_name = 'Demo Creator' WHERE email = 'demo@contentguard.ai'")
        conn.commit()
        cur.execute("SELECT email, full_name, role FROM users WHERE email IN ('admin@contentguard.demo', 'reviewer@contentguard.demo', 'demo@contentguard.ai')")
        print(p, cur.fetchall())
        conn.close()
