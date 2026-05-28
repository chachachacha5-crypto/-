"""Snapshot current TCGPlayer + Cardmarket prices into the time-series table."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Iterable

from . import api
from .db import connect


def _flatten_tcgplayer(prices: dict | None) -> Iterable[tuple[str, str, float]]:
    """Yield (variant, metric, price) for TCGPlayer's nested foil/metric dict."""
    if not prices:
        return
    for variant, fields in prices.items():
        if not isinstance(fields, dict):
            continue
        for metric, price in fields.items():
            if isinstance(price, (int, float)) and not isinstance(price, bool):
                yield variant, metric, float(price)


def _flatten_cardmarket(prices: dict | None) -> Iterable[tuple[str, str, float]]:
    """Yield ('default', metric, price) for Cardmarket's flat metric dict."""
    if not prices:
        return
    for metric, price in prices.items():
        if isinstance(price, (int, float)) and not isinstance(price, bool):
            yield "default", metric, float(price)


def snapshot(db_path: str, set_id: str | None = None, verbose: bool = True) -> None:
    now_iso = datetime.now(timezone.utc).isoformat()
    with connect(db_path) as conn:
        if set_id:
            sets = [(set_id,)]
        else:
            sets = [
                (row["id"],)
                for row in conn.execute(
                    "SELECT id FROM sets ORDER BY release_date DESC"
                ).fetchall()
            ]

        if not sets:
            print("No sets in DB. Run `pokesurge catalog` first.")
            return

        for (sid,) in sets:
            cards = api.get_cards_in_set(sid)
            rows = 0
            for c in cards:
                tcg = c.get("tcgplayer") or {}
                cm = c.get("cardmarket") or {}
                for variant, metric, price in _flatten_tcgplayer(tcg.get("prices")):
                    conn.execute(
                        """INSERT INTO price_snapshots
                           (card_id, source, variant, metric, price, snapshot_at, source_updated_at)
                           VALUES (?, 'tcgplayer', ?, ?, ?, ?, ?)""",
                        (c["id"], variant, metric, price, now_iso, tcg.get("updatedAt")),
                    )
                    rows += 1
                for variant, metric, price in _flatten_cardmarket(cm.get("prices")):
                    conn.execute(
                        """INSERT INTO price_snapshots
                           (card_id, source, variant, metric, price, snapshot_at, source_updated_at)
                           VALUES (?, 'cardmarket', ?, ?, ?, ?, ?)""",
                        (c["id"], variant, metric, price, now_iso, cm.get("updatedAt")),
                    )
                    rows += 1
            conn.commit()
            if verbose:
                print(f"  {sid:<10} {len(cards):>4} cards  {rows:>5} price rows")
            time.sleep(api.POLITE_DELAY_SEC)
