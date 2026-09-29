"""Local content-addressed numeric feature cache (never a prediction/label cache).

Keys cover raw feature inputs and the feature implementation/encoder/schema.
Only finite JSON numbers are stored; a missing/corrupt entry is recomputed.
"""
import json
import logging
import math
import sqlite3
from pathlib import Path
from threading import RLock

logger = logging.getLogger(__name__)


class FeatureCache:
    def __init__(self, path: Path | None):
        self.path = path
        self._connection = None
        self._disk_disabled = False
        self._pending = {}
        self._lock = RLock()
        self.hits = 0
        self.misses = 0

    def _db(self):
        if self._disk_disabled:
            return None
        if self._connection is None and self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.path), timeout=10, check_same_thread=False)
            try:
                conn.execute("CREATE TABLE IF NOT EXISTS features (cache_key TEXT PRIMARY KEY, values_json TEXT NOT NULL)")
            except sqlite3.Error:
                conn.close()
                raise
            self._connection = conn
        return self._connection

    def get(self, key, feature_names):
        with self._lock:
            try:
                encoded = self._pending.get(key)
                if encoded is None:
                    db = self._db()
                    row = db.execute("SELECT values_json FROM features WHERE cache_key = ?", (key,)).fetchone() if db else None
                    encoded = row[0] if row else None
                if encoded is not None:
                    values = json.loads(encoded)
                    if isinstance(values, list) and len(values) == len(feature_names) and all(type(v) in (int, float) and math.isfinite(v) for v in values):
                        self.hits += 1
                        return dict(zip(feature_names, values))
            except (OSError, sqlite3.Error, ValueError, TypeError):
                logger.warning("Feature cache read failed; recomputing from source records", exc_info=True)
                self._disk_disabled = True
            self.misses += 1
            return None

    def put(self, key, values):
        if self.path is None or self._disk_disabled or not all(math.isfinite(v) for v in values):
            return
        with self._lock:
            self._pending[key] = json.dumps(values, allow_nan=False)
            if len(self._pending) >= 128:
                self.flush()

    def flush(self):
        with self._lock:
            if not self._pending:
                return
            try:
                db = self._db()
                if db:
                    db.executemany("INSERT OR REPLACE INTO features(cache_key, values_json) VALUES (?, ?)", self._pending.items())
                    db.commit()
            except (OSError, sqlite3.Error):
                logger.warning("Feature cache write failed; serving computed values without disk cache", exc_info=True)
                self._disk_disabled = True
                if self._connection is not None:
                    try:
                        self._connection.rollback()
                    except sqlite3.Error:
                        pass
            finally:
                self._pending.clear()

    def close(self):
        with self._lock:
            self.flush()
            if self._connection is not None:
                self._connection.close()
                self._connection = None
