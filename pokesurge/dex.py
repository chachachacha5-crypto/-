"""Build the Pokedex name dictionary from PokeAPI.

This is the bridge between English and Japanese card names: both sides
expose the National Pokedex number, so we cache (number, name_en, name_ja)
once and reuse it for matching.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

import requests

from .db import connect

POKEAPI_BASE = "https://pokeapi.co/api/v2"
POLITE_DELAY_SEC = 0.1


def _pick_name(names: list[dict], language: str) -> str | None:
    for entry in names or []:
        lang = (entry.get("language") or {}).get("name")
        if lang == language:
            return entry.get("name")
    return None


def sync(
    db_path: str,
    max_id: int = 1025,
    delay: float = POLITE_DELAY_SEC,
    verbose: bool = True,
) -> None:
    """Fetch species 1..max_id and store en / ja-Hrkt / roomaji names."""
    now_iso = datetime.now(timezone.utc).isoformat()
    inserted = 0
    skipped = 0
    with connect(db_path) as conn:
        for species_id in range(1, max_id + 1):
            try:
                resp = requests.get(
                    f"{POKEAPI_BASE}/pokemon-species/{species_id}", timeout=30,
                )
                resp.raise_for_status()
            except requests.HTTPError as exc:
                if exc.response is not None and exc.response.status_code == 404:
                    skipped += 1
                    continue
                raise
            data = resp.json()
            names = data.get("names") or []
            name_en = _pick_name(names, "en")
            name_ja = _pick_name(names, "ja-Hrkt") or _pick_name(names, "ja")
            name_rm = _pick_name(names, "roomaji")
            conn.execute(
                """INSERT OR REPLACE INTO pokemon_names
                   (pokedex_number, name_en, name_ja, name_roomaji, synced_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (species_id, name_en, name_ja, name_rm, now_iso),
            )
            inserted += 1
            if verbose and species_id % 50 == 0:
                conn.commit()
                print(f"  synced {species_id} / {max_id} ({name_en} / {name_ja})")
            time.sleep(delay)
        conn.commit()
    if verbose:
        print(f"Done: {inserted} species stored, {skipped} skipped (404)")
