"""Ingest Japanese-market prices into jp_price_snapshots.

Two modes:

- ``import_csv`` reads a CSV file. Header columns: ``jp_card_id``, ``price``,
  ``metric``, ``source``, ``condition``, ``currency``, ``source_url``.
  Only ``jp_card_id`` and ``price`` are required. Sensible defaults are
  applied for the rest.
- ``record`` is the programmatic helper used by scrapers.

The CSV path is the immediately useful one — paste prices from any source
(Snkrdunk, Mercari, Suruga-ya) into a spreadsheet, export, import.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone

from .db import connect

DEFAULT_METRIC = "lowest_ask"
DEFAULT_SOURCE = "manual"
DEFAULT_CURRENCY = "JPY"
DEFAULT_CONDITION = "raw"


def record(
    db_path: str,
    jp_card_id: str,
    price: float,
    *,
    source: str = DEFAULT_SOURCE,
    metric: str = DEFAULT_METRIC,
    condition: str | None = DEFAULT_CONDITION,
    currency: str = DEFAULT_CURRENCY,
    source_url: str | None = None,
    snapshot_at: str | None = None,
) -> None:
    snapshot_at = snapshot_at or datetime.now(timezone.utc).isoformat()
    with connect(db_path) as conn:
        conn.execute(
            """INSERT INTO jp_price_snapshots
               (jp_card_id, source, condition, currency, price, metric, source_url, snapshot_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (jp_card_id, source, condition, currency, float(price),
             metric, source_url, snapshot_at),
        )


def import_csv(db_path: str, csv_path: str, verbose: bool = True) -> int:
    """Returns number of rows inserted."""
    now_iso = datetime.now(timezone.utc).isoformat()
    inserted = 0
    skipped = 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        with connect(db_path) as conn:
            for row in reader:
                jp_card_id = (row.get("jp_card_id") or "").strip()
                raw_price = (row.get("price") or "").strip()
                if not jp_card_id or not raw_price:
                    skipped += 1
                    continue
                try:
                    price = float(raw_price)
                except ValueError:
                    skipped += 1
                    continue
                conn.execute(
                    """INSERT INTO jp_price_snapshots
                       (jp_card_id, source, condition, currency, price, metric, source_url, snapshot_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        jp_card_id,
                        (row.get("source") or DEFAULT_SOURCE).strip(),
                        (row.get("condition") or DEFAULT_CONDITION).strip() or None,
                        (row.get("currency") or DEFAULT_CURRENCY).strip(),
                        price,
                        (row.get("metric") or DEFAULT_METRIC).strip(),
                        (row.get("source_url") or "").strip() or None,
                        (row.get("snapshot_at") or now_iso).strip(),
                    ),
                )
                inserted += 1
    if verbose:
        print(f"Imported {inserted} rows ({skipped} skipped) from {csv_path}")
    return inserted
