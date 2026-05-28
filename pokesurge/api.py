"""Minimal client for the pokemontcg.io v2 API."""
from __future__ import annotations

import os
import time
import requests

API_BASE = "https://api.pokemontcg.io/v2"
PAGE_SIZE = 250
POLITE_DELAY_SEC = 0.2


def _headers() -> dict[str, str]:
    key = os.environ.get("POKEMONTCG_API_KEY")
    return {"X-Api-Key": key} if key else {}


def get_sets() -> list[dict]:
    resp = requests.get(f"{API_BASE}/sets", headers=_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()["data"]


def get_cards_in_set(set_id: str) -> list[dict]:
    cards: list[dict] = []
    page = 1
    while True:
        resp = requests.get(
            f"{API_BASE}/cards",
            params={"q": f"set.id:{set_id}", "page": page, "pageSize": PAGE_SIZE},
            headers=_headers(),
            timeout=60,
        )
        resp.raise_for_status()
        chunk = resp.json()["data"]
        cards.extend(chunk)
        if len(chunk) < PAGE_SIZE:
            return cards
        page += 1
        time.sleep(POLITE_DELAY_SEC)
