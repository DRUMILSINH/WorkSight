import json
import sqlite3
import time
from pathlib import Path

from agent.ai.types import AIResultEnvelope


class AIQueueStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ai_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    payload TEXT NOT NULL,
                    attempt INTEGER NOT NULL DEFAULT 0,
                    queued_at TEXT NOT NULL,
                    next_retry_at REAL NOT NULL DEFAULT 0,
                    dead_letter INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_ai_queue_retry ON ai_queue(dead_letter, next_retry_at)"
            )

    def enqueue(self, envelope: AIResultEnvelope, idempotency_key: str) -> bool:
        body = envelope.to_dict()
        with self._connect() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO ai_queue (
                        idempotency_key, payload, attempt, queued_at, next_retry_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        idempotency_key,
                        json.dumps(body["metric"]),
                        body["attempt"],
                        body["queued_at"],
                        body["next_retry_at"],
                    ),
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def ready_items(self, limit: int) -> list[dict]:
        now_ts = time.time()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, idempotency_key, payload, attempt
                FROM ai_queue
                WHERE dead_letter = 0 AND next_retry_at <= ?
                ORDER BY id ASC
                LIMIT ?
                """,
                (now_ts, limit),
            ).fetchall()

        items = []
        for row in rows:
            items.append(
                {
                    "id": row[0],
                    "idempotency_key": row[1],
                    "metric": json.loads(row[2]),
                    "attempt": row[3],
                }
            )
        return items

    def mark_success(self, row_id: int):
        with self._connect() as conn:
            conn.execute("DELETE FROM ai_queue WHERE id = ?", (row_id,))

    def reschedule(self, row_id: int, attempt: int, next_retry_at: float, error: str):
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE ai_queue
                SET attempt = ?, next_retry_at = ?, last_error = ?
                WHERE id = ?
                """,
                (attempt, next_retry_at, error[:500], row_id),
            )

    def mark_dead_letter(self, row_id: int, error: str):
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE ai_queue
                SET dead_letter = 1, last_error = ?
                WHERE id = ?
                """,
                (error[:500], row_id),
            )

    def backlog_count(self) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM ai_queue WHERE dead_letter = 0"
            ).fetchone()
        return row[0] if row else 0
