"""
SQLite Forensic Database Connection & Lifecycle Manager.
100% Offline & Air-Gapped Compliant. Uses WAL Mode for High Concurrency.
"""
import sqlite3
import logging
from pathlib import Path
from typing import Generator
from contextlib import contextmanager
from backend.app.core.config import APP_DATA_DIR, REPORTS_DIR

logger = logging.getLogger(__name__)

# Database path: <APP_DATA_DIR>/bitkaun_forensics.db
DB_DIR = APP_DATA_DIR
DB_PATH = DB_DIR / "bitkaun_forensics.db"

def init_db() -> None:
    """Initializes the SQLite database directory and sets WAL journal mode."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        conn.commit()
    logger.info(f"Forensic SQLite Database initialized at: {DB_PATH} (WAL mode active)")

@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Provides a thread-safe context-managed SQLite connection."""
    conn = sqlite3.connect(
        str(DB_PATH),
        timeout=30.0,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
