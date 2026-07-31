"""
Score Store — Persistence layer for NOW Scores.

Supports SQLite (default) and provides an interface for PostgreSQL/other adapters.
"""

from __future__ import annotations

import abc
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


class ScoreStore(abc.ABC):
    """Abstract persistence layer for NOW scores."""

    @abc.abstractmethod
    def save_snapshot(self, scores: list[dict[str, Any]]) -> int:
        """Save a snapshot of all scores. Returns count."""
        ...

    @abc.abstractmethod
    def get_latest_snapshot(self) -> list[dict[str, Any]]:
        """Get the most recent score snapshot."""
        ...

    @abc.abstractmethod
    def get_history(self, asset_id: str, days: int = 365) -> list[dict[str, Any]]:
        """Get historical scores for an asset."""
        ...

    @abc.abstractmethod
    def get_score_at(self, asset_id: str, timestamp: datetime) -> float | None:
        """Get score for an asset at a specific time."""
        ...


class InMemoryStore(ScoreStore):
    """In-memory store for development/testing."""

    def __init__(self) -> None:
        self._snapshots: list[dict[str, Any]] = []

    def save_snapshot(self, scores: list[dict[str, Any]]) -> int:
        snapshot = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scores": scores,
        }
        self._snapshots.append(snapshot)
        return len(scores)

    def get_latest_snapshot(self) -> list[dict[str, Any]]:
        if not self._snapshots:
            return []
        return self._snapshots[-1]["scores"]

    def get_history(self, asset_id: str, days: int = 365) -> list[dict[str, Any]]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        history = []
        for snap in self._snapshots:
            ts = datetime.fromisoformat(snap["timestamp"])
            if ts >= cutoff:
                for score in snap["scores"]:
                    if score["asset_id"] == asset_id:
                        history.append({
                            "timestamp": ts.isoformat(),
                            "score": score["score"],
                            "rank": score.get("rank"),
                        })
        return history

    def get_score_at(self, asset_id: str, timestamp: datetime) -> float | None:
        for snap in reversed(self._snapshots):
            ts = datetime.fromisoformat(snap["timestamp"])
            if ts <= timestamp:
                for score in snap["scores"]:
                    if score["asset_id"] == asset_id:
                        return score["score"]
        return None


class SQLiteStore(ScoreStore):
    """SQLite-backed persistence for NOW scores."""

    def __init__(self, db_path: str | Path = "data/now_index.db") -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(str(self._db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS score_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                snapshot_json TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS asset_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                score REAL NOT NULL,
                rank INTEGER,
                factors_json TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_asset_history_id
            ON asset_history(asset_id, timestamp)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS asset_metadata (
                asset_id TEXT PRIMARY KEY,
                ticker TEXT NOT NULL,
                name TEXT NOT NULL,
                asset_class TEXT NOT NULL,
                metadata_json TEXT
            )
        """)
        conn.commit()
        conn.close()

    def save_snapshot(self, scores: list[dict[str, Any]]) -> int:
        timestamp = datetime.now(timezone.utc).isoformat()
        snapshot_json = json.dumps(scores, default=str)

        conn = sqlite3.connect(str(self._db_path))
        conn.execute(
            "INSERT INTO score_snapshots (timestamp, snapshot_json) VALUES (?, ?)",
            (timestamp, snapshot_json),
        )

        for score in scores:
            conn.execute(
                """INSERT INTO asset_history
                   (asset_id, timestamp, score, rank, factors_json)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    score["asset_id"],
                    timestamp,
                    score["score"],
                    score.get("rank"),
                    json.dumps(score.get("factors", {}), default=str),
                ),
            )
            # Upsert metadata
            conn.execute("""
                INSERT OR REPLACE INTO asset_metadata
                (asset_id, ticker, name, asset_class, metadata_json)
                VALUES (?, ?, ?, ?, ?)
            """, (
                score["asset_id"],
                score["ticker"],
                score["name"],
                score["asset_class"],
                json.dumps({
                    "country": score.get("country", ""),
                    "sector": score.get("sector", ""),
                    "industry": score.get("industry", ""),
                    "market_cap": score.get("market_cap"),
                    "exchange": score.get("exchange", ""),
                    "currency": score.get("currency", "USD"),
                }),
            ))

        conn.commit()
        conn.close()
        return len(scores)

    def get_latest_snapshot(self) -> list[dict[str, Any]]:
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.execute(
            "SELECT snapshot_json FROM score_snapshots ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
        return []

    def get_history(self, asset_id: str, days: int = 365) -> list[dict[str, Any]]:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.execute(
            """SELECT timestamp, score, rank FROM asset_history
               WHERE asset_id = ? AND timestamp >= ?
               ORDER BY timestamp ASC""",
            (asset_id, cutoff),
        )
        rows = cursor.fetchall()
        conn.close()
        return [
            {"timestamp": row[0], "score": row[1], "rank": row[2]}
            for row in rows
        ]

    def get_score_at(self, asset_id: str, timestamp: datetime) -> float | None:
        ts = timestamp.isoformat()
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.execute(
            """SELECT score FROM asset_history
               WHERE asset_id = ? AND timestamp <= ?
               ORDER BY timestamp DESC LIMIT 1""",
            (asset_id, ts),
        )
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
