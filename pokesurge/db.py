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

-- Pokedex name dictionary (from PokeAPI). Bridges English and Japanese cards
-- via the National Pokedex number, since card names differ across locales.
CREATE TABLE IF NOT EXISTS pokemon_names (
    pokedex_number  INTEGER PRIMARY KEY,
    name_en         TEXT,
    name_ja         TEXT,         -- katakana form (ja-Hrkt)
    name_roomaji    TEXT,
    synced_at       TEXT
);
CREATE INDEX IF NOT EXISTS idx_dex_name_ja ON pokemon_names(name_ja);
CREATE INDEX IF NOT EXISTS idx_dex_name_en ON pokemon_names(name_en);

-- Japanese set catalog (from TCGdex /ja/).
CREATE TABLE IF NOT EXISTS jp_sets (
    id              TEXT PRIMARY KEY,
    name            TEXT,
    series          TEXT,
    release_date    TEXT,
    card_count      INTEGER,
    synced_at       TEXT
);

CREATE TABLE IF NOT EXISTS jp_cards (
    id              TEXT PRIMARY KEY,
    set_id          TEXT NOT NULL,
    name            TEXT,
    local_id        TEXT,
    rarity          TEXT,
    category        TEXT,         -- 'Pokemon' | 'Trainer' | 'Energy' (best effort)
    pokedex_numbers TEXT,         -- comma-separated; filled by linker via dex
    image_url       TEXT,
    synced_at       TEXT,
    FOREIGN KEY (set_id) REFERENCES jp_sets(id)
);
CREATE INDEX IF NOT EXISTS idx_jp_cards_set     ON jp_cards(set_id);
CREATE INDEX IF NOT EXISTS idx_jp_cards_name    ON jp_cards(name);
CREATE INDEX IF NOT EXISTS idx_jp_cards_pokedex ON jp_cards(pokedex_numbers);

-- One row per (English card, Japanese card) candidate, with a confidence
-- score and a human-readable reason string.
CREATE TABLE IF NOT EXISTS card_links (
    en_card_id  TEXT NOT NULL,
    jp_card_id  TEXT NOT NULL,
    score       REAL NOT NULL,
    reason      TEXT,
    linked_at   TEXT,
    PRIMARY KEY (en_card_id, jp_card_id),
    FOREIGN KEY (en_card_id) REFERENCES cards(id),
    FOREIGN KEY (jp_card_id) REFERENCES jp_cards(id)
);
CREATE INDEX IF NOT EXISTS idx_links_en ON card_links(en_card_id, score DESC);
CREATE INDEX IF NOT EXISTS idx_links_jp ON card_links(jp_card_id);

-- Time-series of Japanese-market prices, parallel to price_snapshots.
-- Sources: 'snkrdunk', 'mercari', 'surugaya', 'cardrush', 'manual', ...
CREATE TABLE IF NOT EXISTS jp_price_snapshots (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    jp_card_id    TEXT NOT NULL,
    source        TEXT NOT NULL,
    condition     TEXT,            -- 'raw' | 'PSA10' | 'PSA9' | 'NM' | NULL
    currency      TEXT NOT NULL DEFAULT 'JPY',
    price         REAL NOT NULL,
    metric        TEXT NOT NULL,   -- 'lowest_ask' | 'highest_bid' | 'last_trade' | 'mean'
    source_url    TEXT,
    snapshot_at   TEXT NOT NULL,
    FOREIGN KEY (jp_card_id) REFERENCES jp_cards(id)
);
CREATE INDEX IF NOT EXISTS idx_jp_snap_card   ON jp_price_snapshots(jp_card_id, snapshot_at);
CREATE INDEX IF NOT EXISTS idx_jp_snap_recent ON jp_price_snapshots(snapshot_at);
CREATE INDEX IF NOT EXISTS idx_jp_snap_lookup
    ON jp_price_snapshots(source, metric, jp_card_id, snapshot_at);

-- Optional manual mapping from a JP card to its SNKRDUNK product page.
-- The fetcher uses this table when present.
CREATE TABLE IF NOT EXISTS snkrdunk_links (
    jp_card_id  TEXT PRIMARY KEY,
    url         TEXT NOT NULL,
    note        TEXT,
    linked_at   TEXT,
    FOREIGN KEY (jp_card_id) REFERENCES jp_cards(id)
);
"""


def init_db(path: str = DEFAULT_DB) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)
        # Additive migration: pokedex_numbers was added to `cards` in v0.2.
        existing = {row[1] for row in conn.execute("PRAGMA table_info(cards)")}
        if "pokedex_numbers" not in existing:
            conn.execute("ALTER TABLE cards ADD COLUMN pokedex_numbers TEXT")


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
