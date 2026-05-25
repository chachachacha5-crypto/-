from __future__ import annotations

import time
from dataclasses import dataclass

import requests

SEARCH_URL = "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch"
CATEGORY_RANKING_URL = "https://shopping.yahooapis.jp/ShoppingWebService/V1/json/categoryRanking"

SORT_OPTIONS = {
    "popular": "-score",
    "review": "-review_count",
    "price_asc": "+price",
    "price_desc": "-price",
    "sold": "-sold",
}

HOT_CATEGORIES = {
    1: "全カテゴリ",
    2502: "おもちゃ・ゲーム",
    10002: "本・雑誌・コミック",
    13457: "テレビゲーム",
    2501: "ホビー・コレクション",
    2498: "食品",
    2508: "家電",
    2506: "ダイエット・健康",
}


@dataclass
class YahooItem:
    rank: int
    name: str
    item_code: str
    price: int
    shop_name: str
    url: str
    image_url: str
    review_count: int
    review_rate: float
    category_id: str

    def to_dict(self) -> dict:
        return {
            "source": "yahoo",
            "rank": self.rank,
            "name": self.name,
            "item_code": self.item_code,
            "price": self.price,
            "shop_name": self.shop_name,
            "url": self.url,
            "image_url": self.image_url,
            "review_count": self.review_count,
            "review_average": self.review_rate,
            "category_id": self.category_id,
        }


class YahooClient:
    def __init__(self, app_id: str, *, request_interval: float = 1.0):
        if not app_id:
            raise ValueError("YAHOO_APP_ID is not set")
        self.app_id = app_id
        self.request_interval = request_interval
        self._last_request_at = 0.0
        self._session = requests.Session()

    def _throttle(self):
        wait = self.request_interval - (time.monotonic() - self._last_request_at)
        if wait > 0:
            time.sleep(wait)
        self._last_request_at = time.monotonic()

    def _get(self, url: str, params: dict) -> dict:
        self._throttle()
        params = {**params, "appid": self.app_id}
        resp = self._session.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def search(
        self,
        *,
        keyword: str | None = None,
        category_id: int | None = None,
        sort: str = "popular",
        results: int = 30,
    ) -> list[YahooItem]:
        sort_key = SORT_OPTIONS.get(sort, sort)
        params: dict = {"sort": sort_key, "results": min(results, 50)}
        if keyword:
            params["query"] = keyword
        if category_id is not None:
            params["genre_category_id"] = category_id
        data = self._get(SEARCH_URL, params)
        items = data.get("hits", []) or []
        return [_parse_item(idx + 1, entry) for idx, entry in enumerate(items)]

    def category_ranking(self, category_id: int = 1) -> list[YahooItem]:
        params = {"category_id": category_id}
        data = self._get(CATEGORY_RANKING_URL, params)
        ranking = data.get("ResultSet", {}).get("0", {}).get("Result", {})
        items: list[YahooItem] = []
        for key in sorted(k for k in ranking.keys() if k.isdigit()):
            entry = ranking[key]
            items.append(
                YahooItem(
                    rank=int(key) + 1,
                    name=entry.get("Name", ""),
                    item_code=entry.get("Code", ""),
                    price=int(entry.get("Price", 0) or 0),
                    shop_name=entry.get("Store", {}).get("Name", "")
                    if isinstance(entry.get("Store"), dict)
                    else "",
                    url=entry.get("Url", ""),
                    image_url=entry.get("Image", {}).get("Medium", "")
                    if isinstance(entry.get("Image"), dict)
                    else "",
                    review_count=0,
                    review_rate=0.0,
                    category_id=str(category_id),
                )
            )
        return items


def _parse_item(rank: int, entry: dict) -> YahooItem:
    seller = entry.get("seller") or {}
    image = entry.get("image") or {}
    review = entry.get("review") or {}
    return YahooItem(
        rank=rank,
        name=entry.get("name", ""),
        item_code=entry.get("code", ""),
        price=int(entry.get("price", 0) or 0),
        shop_name=seller.get("name", ""),
        url=entry.get("url", ""),
        image_url=image.get("medium", "") or image.get("small", ""),
        review_count=int(review.get("count", 0) or 0),
        review_rate=float(review.get("rate", 0.0) or 0.0),
        category_id=str((entry.get("genreCategory") or {}).get("id", "")),
    )
