from __future__ import annotations

import re
from collections import Counter
from typing import Iterable


_TOKEN_RE = re.compile(r"[A-Za-z0-9]+|[一-鿿぀-ゟ゠-ヿ]+")
_STOPWORDS = {
    "送料無料",
    "正規品",
    "新品",
    "公式",
    "あす楽",
    "セール",
    "ポイント",
    "限定",
    "予約",
    "特価",
}


def tokenize(name: str) -> list[str]:
    tokens = _TOKEN_RE.findall(name or "")
    return [t for t in tokens if len(t) >= 2 and t not in _STOPWORDS]


def trending_keywords(items: Iterable[dict], top_n: int = 20) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for item in items:
        counter.update(set(tokenize(item.get("name", ""))))
    return counter.most_common(top_n)


def price_stats(items: Iterable[dict]) -> dict:
    prices = [int(it["price"]) for it in items if it.get("price")]
    if not prices:
        return {"count": 0}
    prices.sort()
    n = len(prices)
    median = prices[n // 2] if n % 2 else (prices[n // 2 - 1] + prices[n // 2]) // 2
    return {
        "count": n,
        "min": prices[0],
        "max": prices[-1],
        "median": median,
        "average": sum(prices) // n,
    }


def cross_platform_overlap(
    rakuten_items: list[dict],
    yahoo_items: list[dict],
    *,
    min_token_len: int = 2,
) -> list[dict]:
    rakuten_index: dict[str, list[dict]] = {}
    for item in rakuten_items:
        for token in set(tokenize(item.get("name", ""))):
            if len(token) >= min_token_len:
                rakuten_index.setdefault(token, []).append(item)

    matches: list[dict] = []
    for y_item in yahoo_items:
        y_tokens = set(tokenize(y_item.get("name", "")))
        candidates: Counter[int] = Counter()
        token_hits: dict[int, list[str]] = {}
        for token in y_tokens:
            if len(token) < min_token_len:
                continue
            for r_item in rakuten_index.get(token, []):
                key = id(r_item)
                candidates[key] += 1
                token_hits.setdefault(key, []).append(token)
        if not candidates:
            continue
        best_key, score = candidates.most_common(1)[0]
        if score < 2:
            continue
        r_item = next(it for it in rakuten_items if id(it) == best_key)
        matches.append(
            {
                "shared_tokens": sorted(set(token_hits[best_key])),
                "match_score": score,
                "rakuten_name": r_item.get("name"),
                "rakuten_price": r_item.get("price"),
                "rakuten_url": r_item.get("url"),
                "yahoo_name": y_item.get("name"),
                "yahoo_price": y_item.get("price"),
                "yahoo_url": y_item.get("url"),
                "price_diff": (y_item.get("price") or 0) - (r_item.get("price") or 0),
            }
        )
    matches.sort(key=lambda m: m["match_score"], reverse=True)
    return matches


def summarize(items: list[dict]) -> dict:
    return {
        "items_count": len(items),
        "price": price_stats(items),
        "top_keywords": trending_keywords(items, top_n=15),
        "top_shops": Counter(it.get("shop_name", "") for it in items if it.get("shop_name")).most_common(10),
    }
