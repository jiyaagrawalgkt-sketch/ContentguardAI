import sqlite3
import os

db_paths = [
    os.path.abspath("contentguard.db"),
    os.path.abspath("backend/contentguard.db")
]

new_columns = [
    ("corrected_file_id", "TEXT"),
    ("corrected_image_path", "TEXT"),
    ("corrected_image_url", "TEXT"),
    ("review_status", "TEXT DEFAULT 'draft'"),
    ("accepted_corrections", "TEXT DEFAULT '[]'"),
    ("rejected_corrections", "TEXT DEFAULT '[]'"),
    ("creator_notes", "TEXT"),
    ("reviewer_comments", "TEXT"),
    ("reviewed_at", "TIMESTAMP"),
    ("reviewed_by_user_id", "TEXT"),
    ("is_published", "BOOLEAN DEFAULT 0"),
    ("published_at", "TIMESTAMP"),
]

for p in db_paths:
    if os.path.exists(p):
        conn = sqlite3.connect(p)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(visual_analysis_reports)")
        existing = {r[1] for r in cur.fetchall()}
        
        for col_name, col_type in new_columns:
            if col_name not in existing:
                try:
                    cur.execute(f"ALTER TABLE visual_analysis_reports ADD COLUMN {col_name} {col_type}")
                    print(f"Added {col_name} to {p}")
                except Exception as e:
                    print(f"Failed {col_name} on {p}: {e}")
        conn.commit()
        conn.close()
