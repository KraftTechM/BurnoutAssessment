import sqlite3
from . import config

def connect() -> sqlite3.Connection:
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    with connect() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team TEXT NOT NULL,
                role TEXT,
                consent INTEGER NOT NULL DEFAULT 0,
                submitted_at TEXT NOT NULL,
                answers TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS scores (
                response_id INTEGER PRIMARY KEY,
                demand_index REAL,
                resource_index REAL,
                strain_index REAL,
                risk_score REAL,
                FOREIGN KEY (response_id) REFERENCES responses(id)
            );
            """
        )
