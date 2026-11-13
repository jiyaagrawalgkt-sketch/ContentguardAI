import sqlite3
import shutil
import json

root_db = "contentguard.db"
back_db = "backend/contentguard.db"

# 1. Read all approved facts from root_db
c_root = sqlite3.connect(root_db)
c_back = sqlite3.connect(back_db)

facts_root = c_root.execute("SELECT id, organization_id, topic, statement, verified_numbers, expiry_date, reference_url_or_doc, is_active FROM approved_facts").fetchall()
existing_back_statements = {row[0] for row in c_back.execute("SELECT statement FROM approved_facts").fetchall()}

for f in facts_root:
    if f[3] not in existing_back_statements:
        print(f"Adding fact to backend db: {f[2]} - {f[3]}")
        c_back.execute(
            "INSERT INTO approved_facts (id, organization_id, topic, statement, verified_numbers, expiry_date, reference_url_or_doc, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))",
            (f[0], f[1], f[2], f[3], json.dumps(f[4]) if isinstance(f[4], dict) else f[4], f[5], f[6], f[7])
        )
c_back.commit()

c_root.close()
c_back.close()

# 2. Overwrite root_db with back_db so both are 100% in sync
shutil.copy2(back_db, root_db)
print("Successfully synced backend/contentguard.db and contentguard.db!")
