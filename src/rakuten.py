from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable

import requests

RANKING_URL = "https://app.rakuten.co.jp/services/api/IchibaItem/Ranking/20220601"
SEARCH_URL = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601"
GENRE_URL = "https://app.rakuten.co.jp/services/api/IchibaGenre/Search/20140222"

PERIODS = ("realtime", "daily", "weekly", "monthly")

HOT_GENRES = {
    0: "全ジャンル",
    101240: "おもちゃ",
    101205: "本・雑誌・コミック",
    101164: "ゲーム",
    566382: "ホビー",
    100938: "スイーツ・お菓子",
    100533: "食品",
    100371: "家電",
    100939: "ダイエット・健康",
}


@dataclass
class RakutenItem:
    rank: int
    name: str
    item_code: str
    price: int
    shop_name: str
    url: str
    image_url: str
    review_count: int
    review_average: float
    genre_id: str

    def to_dict(self) -> dict:
        return {
            "source": "rakuten",
            "rank": self.rank,
            "name": self.name,
            "item_code": self.item_code,
            "price": self.price,
            "shop_name": self.shop_name,
            "url": self.url,
            "image_url": self.image_url,
            "review_count": self.review_count,
            "review_average": self.review_average,
            "genre_id": self.genre_id,
        }


class RakutenClient:
    def __init__(self, app_id: str, *, request_interval: float = 1.0):
        if not app_id:
            raise ValueError("RAKUTEN_APP_ID is not set")
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
        params = {**params, "applicationId": self.app_id, "format": "json"}
        resp = self._session.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def ranking(
        self,
        genre_id: int = 0,
        period: str = "realtime",
        page: int = 1,
    ) -> list[RakutenItem]:
        if period not in PERIODS:
            raise ValueError(f"period must be one of {PERIODS}")
        data = self._get(
            RANKING_URL,
            {"genreId": genre_id, "period": period, "page": page},
        )
        return [_parse_item(entry) for entry in data.get("Items", [])]

    def ranking_multi(
        self,
        genre_ids: Iterable[int],
        period: str = "realtime",
    ) -> dict[int, list[RakutenItem]]:
        return {gid: self.ranking(gid, period=period) for gid in genre_ids}

    def search(self, keyword: str, *, hits: int = 30, sort: str = "-reviewCount") -> list[RakutenItem]:
        data = self._get(
            SEARCH_URL,
            {"keyword": keyword, "hits": hits, "sort": sort},
        )
        return [_parse_item(entry) for entry in data.get("Items", [])]

    def genre_tree(self, genre_id: int = 0) -> dict:
        return self._get(GENRE_URL, {"genreId": genre_id})


def _parse_item(entry: dict) -> RakutenItem:
    item = entry.get("Item", entry)
    return RakutenItem(
        rank=int(item.get("rank", 0)),
        name=item.get("itemName", ""),
        item_code=item.get("itemCode", ""),
        price=int(item.get("itemPrice", 0) or 0),
        shop_name=item.get("shopName", ""),
        url=item.get("itemUrl", ""),
        image_url=(item.get("mediumImageUrls") or [{}])[0].get("imageUrl", "")
        if item.get("mediumImageUrls")
        else "",
        review_count=int(item.get("reviewCount", 0) or 0),
        review_average=float(item.get("reviewAverage", 0.0) or 0.0),
        genre_id=str(item.get("genreId", "")),
    )
