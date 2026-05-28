"""Sync Japanese sets & cards from TCGdex into SQLite."""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from . import jp_api
from .db import connect


def _cutoff_date(years_back: int) -> str:
    # TCGdex returns ISO dates like "2023-01-20"; lexicographic compare works.
    cutoff = datetime.now(timezone.utc) - timedelta(days=365 * years_back)
    return cutoff.strftime("%Y-%m-%d")


def _card_count(raw: dict | int | None) -> int | None:
    """TCGdex's cardCount is sometimes a dict, sometimes an int — normalize."""
    if isinstance(raw, dict):
        for key in ("total", "official"):
            value = raw.get(key)
            if isinstance(value, int):
                return value
        return None
    if isinstance(raw, int):
        return raw
    return None


def _enrich_card(card_id: str) -> dict | None:
    """Fetch full card details; return None if unavailable."""
    try:
        return jp_api.get_card(card_id)
    except Exception:
        return None


def sync(
    db_path: str,
    years_back: int = 5,
    deep: bool = False,
    verbose: bool = True,
) -> None:
    """Sync JP sets+cards. ``deep=True`` fetches full card details for each
    card (rarity, category, dexId) at the cost of many extra requests."""
    cutoff = _cutoff_date(years_back)
    all_sets = jp_api.get_sets()
    sets = [s for s in all_sets if (s.get("releaseDate") or "") >= cutoff]
    sets.sort(key=lambda s: s.get("releaseDate") or "", reverse=True)

    if verbose:
        print(f"Syncing {len(sets)} JP sets released since {cutoff} "
              f"(out of {len(all_sets)} total){' [deep]' if deep else ''}")

    now_iso = datetime.now(timezone.utc).isoformat()
    with connect(db_path) as conn:
        for s in sets:
            full = jp_api.get_set(s["id"])
            serie = full.get("serie") or {}
            conn.execute(
                """INSERT OR REPLACE INTO jp_sets
                   (id, name, series, release_date, card_count, synced_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    s["id"], full.get("name") or s.get("name"),
                    serie.get("name") if isinstance(serie, dict) else None,
                    full.get("releaseDate") or s.get("releaseDate"),
                    _card_count(full.get("cardCount") or s.get("cardCount")),
                    now_iso,
                ),
            )
            cards = full.get("cards") or []
            for c in cards:
                rarity = c.get("rarity")
                category = c.get("category")
                pokedex = ""
                if deep:
                    detail = _enrich_card(c["id"])
                    if detail:
                        rarity = detail.get("rarity") or rarity
                        category = detail.get("category") or category
                        dex_ids = detail.get("dexId") or []
                        pokedex = ",".join(str(n) for n in dex_ids)
                    time.sleep(jp_api.POLITE_DELAY_SEC)
                conn.execute(
                    """INSERT OR REPLACE INTO jp_cards
                       (id, set_id, name, local_id, rarity, category,
                        pokedex_numbers, image_url, synced_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        c["id"], s["id"], c.get("name"), c.get("localId"),
                        rarity, category, pokedex, c.get("image"), now_iso,
                    ),
                )
            conn.commit()
            if verbose:
                print(f"  {s['id']:<14} {full.get('releaseDate','?'):<12} "
                      f"{(full.get('name') or '?')[:30]:<30} {len(cards)} cards")
            time.sleep(jp_api.POLITE_DELAY_SEC)
