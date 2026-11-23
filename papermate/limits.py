"""Coarse shared limits for ONE Streamlit instance. Not authenticated/per-user.
SQLite is ephemeral on many free hosts and is not suitable for multi-instance scaling.
"""
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB = Path(os.getenv("PAPERMATE_LIMIT_DB", "/tmp/papermate_usage.sqlite3"))

class LimitReached(Exception):
    pass


def use_budget(max_calls: int) -> tuple[int, int]:
    if max_calls <= 0:
        raise LimitReached("서비스 사용량 한도가 설정되어 있지 않습니다.")
    DB.parent.mkdir(parents=True, exist_ok=True)
    day = datetime.now(timezone.utc).date().isoformat()
    with sqlite3.connect(DB, timeout=10) as con:
        con.execute("BEGIN IMMEDIATE")
        con.execute("CREATE TABLE IF NOT EXISTS usage (day TEXT PRIMARY KEY, calls INTEGER NOT NULL)")
        con.execute("DELETE FROM usage WHERE day < ?", (day,))
        con.execute("INSERT OR IGNORE INTO usage(day,calls) VALUES(?,0)", (day,))
        calls = con.execute("SELECT calls FROM usage WHERE day=?", (day,)).fetchone()[0]
        if calls >= max_calls:
            raise LimitReached("오늘의 무료 AI 처리 예산이 소진됐습니다. 내일(UTC 기준) 다시 이용해 주세요.")
        con.execute("UPDATE usage SET calls=calls+1 WHERE day=?", (day,))
        return calls + 1, max_calls
