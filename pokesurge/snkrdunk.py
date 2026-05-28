"""Snkrdunk price fetcher (low-volume, opt-in).

Snkrdunk (snkr-dunk.com / SODA Inc.) is a Japanese marketplace whose web
site shows lowest-ask / highest-bid / last-trade prices for each card.
There is no public API and the ToS restricts automated access, so this
module is intentionally minimal: it fetches ONE product page at a time,
caches aggressively, and assumes the user has populated
``snkrdunk_links(jp_card_id, url)`` mapping rows themselves.

Selectors and JSON shape on the live site change without notice. The
extraction logic below is best-effort; if it returns ``None`` for a price,
inspect the page HTML and update ``_extract_prices``. This is the part
that needs verification against the live site before it returns useful
data.
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone

import requests

from . import jp_prices
from .db import connect

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
DEFAULT_DELAY_SEC = 2.0  # be polite — this is not an API


def add_link(db_path: str, jp_card_id: str, url: str, note: str | None = None) -> None:
    with connect(db_path) as conn:
        conn.execute(
            """INSERT OR REPLACE INTO snkrdunk_links
               (jp_card_id, url, note, linked_at)
               VALUES (?, ?, ?, ?)""",
            (jp_card_id, url, note, datetime.now(timezone.utc).isoformat()),
        )


def _extract_prices(html: str) -> dict[str, float]:
    """Best-effort price extraction from a Snkrdunk product page.

    Snkrdunk renders product data into a Next.js __NEXT_DATA__ JSON blob.
    We try that first, then fall back to scanning visible HTML for known
    labels. Returns {metric: price} where metric is in
    {'lowest_ask', 'highest_bid', 'last_trade'}.
    """
    out: dict[str, float] = {}

    m = re.search(
        r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL,
    )
    if m:
        try:
            data = json.loads(m.group(1))
            # The shape under props.pageProps changes; walk and collect.
            stack = [data]
            while stack:
                node = stack.pop()
                if isinstance(node, dict):
                    for key, value in node.items():
                        lk = key.lower()
                        if isinstance(value, (int, float)) and not isinstance(value, bool):
                            if "lowestask" in lk or lk == "minprice":
                                out.setdefault("lowest_ask", float(value))
                            elif "highestbid" in lk or lk == "maxbidprice":
                                out.setdefault("highest_bid", float(value))
                            elif "lasttrade" in lk or "latestprice" in lk:
                                out.setdefault("last_trade", float(value))
                        elif isinstance(value, (dict, list)):
                            stack.append(value)
                elif isinstance(node, list):
                    stack.extend(node)
        except (ValueError, KeyError):
            pass

    return out


def fetch_one(url: str, session: requests.Session | None = None) -> dict[str, float]:
    session = session or requests.Session()
    resp = session.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    return _extract_prices(resp.text)


def fetch_all(
    db_path: str,
    delay: float = DEFAULT_DELAY_SEC,
    limit: int | None = None,
    verbose: bool = True,
) -> int:
    """Walk the snkrdunk_links table, fetch each product page, and record
    prices. Returns the number of (card, metric) snapshots written.
    """
    session = requests.Session()
    written = 0
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT jp_card_id, url FROM snkrdunk_links ORDER BY linked_at"
        ).fetchall()
    if limit:
        rows = rows[:limit]
    for row in rows:
        try:
            prices = fetch_one(row["url"], session=session)
        except requests.RequestException as exc:
            if verbose:
                print(f"  fail  {row['jp_card_id']:<20} {exc}")
            time.sleep(delay)
            continue
        if not prices:
            if verbose:
                print(f"  empty {row['jp_card_id']:<20} (selectors may need updating)")
            time.sleep(delay)
            continue
        for metric, price in prices.items():
            jp_prices.record(
                db_path, row["jp_card_id"], price,
                source="snkrdunk", metric=metric, source_url=row["url"],
            )
            written += 1
        if verbose:
            preview = ", ".join(f"{k}={v:.0f}" for k, v in prices.items())
            print(f"  ok    {row['jp_card_id']:<20} {preview}")
        time.sleep(delay)
    if verbose:
        print(f"Done: {written} price snapshots written")
    return written
