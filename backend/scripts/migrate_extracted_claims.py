import sqlite3

def migrate_db(db_path):
    print(f"Migrating {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(extracted_claims)")
    cols = {row[1] for row in cursor.fetchall()}

    columns_to_add = [
        ("sentence", "TEXT"),
        ("claim_category", "VARCHAR(50)"),
        ("analysis_version", "INTEGER DEFAULT 1"),
        ("analyzed_at", "DATETIME"),
    ]

    for col_name, col_type in columns_to_add:
        if col_name not in cols:
            print(f"  Adding column {col_name} ({col_type})")
            cursor.execute(f"ALTER TABLE extracted_claims ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()
    print(f"Done migrating {db_path}.")

if __name__ == "__main__":
    migrate_db("backend/contentguard.db")
    migrate_db("contentguard.db")
