"""SQLite schema and connection helpers."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

DEFAULT_DB = "pokesurge.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS sets (
    id              TEXT PRIMARY KEY,
    name            TEXT,
    series          TEXT,
    release_date    TEXT,
    total           INTEGER,
    printed_total   INTEGER,
    source_updated_at TEXT
);

CREATE TABLE IF NOT EXISTS cards (
    id              TEXT PRIMARY KEY,
    set_id          TEXT NOT NULL,
    name            TEXT,
    number          TEXT,
    rarity          TEXT,
    supertype       TEXT,
    subtypes        TEXT,
    image_small     TEXT,
    image_large     TEXT,
    tcgplayer_url   TEXT,
    cardmarket_url  TEXT,
    synced_at       TEXT,
    FOREIGN KEY (set_id) REFERENCES sets(id)
);

CREATE INDEX IF NOT EXISTS idx_cards_set  ON cards(set_id);
CREATE INDEX IF NOT EXISTS idx_cards_name ON cards(name);

-- One row per (card, source, variant, metric, snapshot).
-- Variant covers TCGPlayer foil types ('normal','holofoil','reverseHolofoil',
-- '1stEditionHolofoil', ...). For Cardmarket we use 'default'.
CREATE TABLE IF NOT EXISTS price_snapshots (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id           TEXT NOT NULL,
    source            TEXT NOT NULL,
    variant           TEXT NOT NULL,
    metric            TEXT NOT NULL,
    price             REAL NOT NULL,
    snapshot_at       TEXT NOT NULL,
    source_updated_at TEXT,
    FOREIGN KEY (card_id) REFERENCES cards(id)
);

CREATE INDEX IF NOT EXISTS idx_snap_card    ON price_snapshots(card_id, snapshot_at);
CREATE INDEX IF NOT EXISTS idx_snap_recent  ON price_snapshots(snapshot_at);
CREATE INDEX IF NOT EXISTS idx_snap_lookup  ON price_snapshots(source, metric, card_id, snapshot_at);
"""


def init_db(path: str = DEFAULT_DB) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)


@contextmanager
def connect(path: str = DEFAULT_DB) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
