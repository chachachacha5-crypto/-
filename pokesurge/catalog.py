"""Sync set & card catalog from pokemontcg.io into SQLite."""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from . import api
from .db import connect


def _cutoff_date(years_back: int) -> str:
    # pokemontcg.io uses "YYYY/MM/DD" string ordering, which is lexicographically safe.
    cutoff = datetime.now(timezone.utc) - timedelta(days=365 * years_back)
    return cutoff.strftime("%Y/%m/%d")


def sync(db_path: str, years_back: int = 5, verbose: bool = True) -> None:
    cutoff = _cutoff_date(years_back)
    all_sets = api.get_sets()
    sets = [s for s in all_sets if (s.get("releaseDate") or "") >= cutoff]
    sets.sort(key=lambda s: s.get("releaseDate") or "", reverse=True)

    if verbose:
        print(f"Syncing {len(sets)} sets released since {cutoff} "
              f"(out of {len(all_sets)} total)")

    now_iso = datetime.now(timezone.utc).isoformat()
    with connect(db_path) as conn:
        for s in sets:
            conn.execute(
                """INSERT OR REPLACE INTO sets
                   (id, name, series, release_date, total, printed_total, source_updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    s["id"], s.get("name"), s.get("series"), s.get("releaseDate"),
                    s.get("total"), s.get("printedTotal"), s.get("updatedAt"),
                ),
            )
            cards = api.get_cards_in_set(s["id"])
            for c in cards:
                images = c.get("images") or {}
                conn.execute(
                    """INSERT OR REPLACE INTO cards
                       (id, set_id, name, number, rarity, supertype, subtypes,
                        image_small, image_large, tcgplayer_url, cardmarket_url, synced_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        c["id"], s["id"], c.get("name"), c.get("number"),
                        c.get("rarity"), c.get("supertype"),
                        ",".join(c.get("subtypes") or []),
                        images.get("small"), images.get("large"),
                        (c.get("tcgplayer") or {}).get("url"),
                        (c.get("cardmarket") or {}).get("url"),
                        now_iso,
                    ),
                )
            conn.commit()
            if verbose:
                print(f"  {s['id']:<10} {s.get('releaseDate','?'):<10} "
                      f"{s.get('name','?')[:40]:<40} {len(cards)} cards")
            time.sleep(api.POLITE_DELAY_SEC)
