import sqlite3
from pathlib import Path
from .models import UserAnswers

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    answers_json TEXT
);
"""

class Storage:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute(SCHEMA)
        self.conn.commit()

    def save(self, telegram_id: int, answers: UserAnswers):
        import json
        payload = answers.__dict__.copy()
        self.conn.execute(
            "INSERT INTO users(telegram_id, updated_at, answers_json) VALUES(?, CURRENT_TIMESTAMP, ?) "
            "ON CONFLICT(telegram_id) DO UPDATE SET updated_at=CURRENT_TIMESTAMP, answers_json=excluded.answers_json",
            (telegram_id, json.dumps(payload, ensure_ascii=False))
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
