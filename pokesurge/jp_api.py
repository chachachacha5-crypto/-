"""Minimal client for the TCGdex v2 API (Japanese locale)."""
from __future__ import annotations

import requests

API_BASE = "https://api.tcgdex.net/v2"
POLITE_DELAY_SEC = 0.2


def get_sets(lang: str = "ja") -> list[dict]:
    resp = requests.get(f"{API_BASE}/{lang}/sets", timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_set(set_id: str, lang: str = "ja") -> dict:
    """Returns the set object including a ``cards`` array of brief card refs."""
    resp = requests.get(f"{API_BASE}/{lang}/sets/{set_id}", timeout=60)
    resp.raise_for_status()
    return resp.json()


def get_card(card_id: str, lang: str = "ja") -> dict:
    """Full card details (rarity, category, dexId, etc.)."""
    resp = requests.get(f"{API_BASE}/{lang}/cards/{card_id}", timeout=60)
    resp.raise_for_status()
    return resp.json()
