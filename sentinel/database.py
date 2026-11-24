from pathlib import Path
import sqlite3
import pandas as pd

DB_PATH = Path("data") / "sentinel.sqlite3"

def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def initialize_database():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alert_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                reviewer_decision TEXT NOT NULL,
                notes TEXT DEFAULT '',
                reviewed_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS detection_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_at TEXT DEFAULT CURRENT_TIMESTAMP,
                input_events INTEGER,
                flagged_events INTEGER,
                algorithm TEXT
            )
        """)

def save_alerts(alerts, input_events=None):
    with _connect() as conn:
        conn.execute(
            "INSERT INTO detection_runs(input_events, flagged_events, algorithm) VALUES (?, ?, ?)",
            (int(input_events) if input_events is not None else None, int(len(alerts)), "IsolationForest")
        )

def save_feedback(event_id, decision, notes=""):
    with _connect() as conn:
        conn.execute(
            "INSERT INTO alert_reviews(event_id, reviewer_decision, notes) VALUES (?, ?, ?)",
            (str(event_id), str(decision), str(notes))
        )

def load_feedback():
    with _connect() as conn:
        return pd.read_sql_query("SELECT * FROM alert_reviews ORDER BY reviewed_at DESC", conn)
