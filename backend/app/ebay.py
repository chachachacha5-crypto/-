"""eBay Browse API クライアント。

- OAuth2 (client credentials grant) でアプリトークンを取得しキャッシュする。
- item_summary/search で米国マーケットの出品を検索する。
- 認証情報が無い / API がエラーの場合はサンプルデータにフォールバックする
  ので、開発環境でも UI を確認できる。

注意: Browse API が返すのは「現在出品中(active)」の価格。実際の相場は
売れた価格(sold)を見るのが理想だが、それを返す Marketplace Insights API は
利用申請が必要なため、MVP では active を相場の目安として使う。
"""

from __future__ import annotations

import base64
import time

import httpx

from .config import Settings
from .models import EbayItem, SearchResponse

# eBay US の主要トイ&ホビー カテゴリ
# https://www.ebay.com/sch/220/  (Toys & Hobbies = 220)
TOYS_HOBBIES_CATEGORY = "220"

CATEGORIES: dict[str, str] = {
    "220": "Toys & Hobbies (全般)",
    "246": "Action Figures & Accessories",
    "2536": "Models & Kits (プラモデル等)",
    "19169": "Trading Card Games",
    "238": "Diecast & Toy Vehicles",
    "1188": "Stuffed Animals (ぬいぐるみ)",
}


class _TokenCache:
    token: str | None = None
    expires_at: float = 0.0


_token_cache = _TokenCache()


async def _get_app_token(settings: Settings, client: httpx.AsyncClient) -> str:
    """client credentials grant でアプリトークンを取得（簡易キャッシュ付き）。"""
    now = time.time()
    if _token_cache.token and now < _token_cache.expires_at - 60:
        return _token_cache.token

    basic = base64.b64encode(
        f"{settings.ebay_client_id}:{settings.ebay_client_secret}".encode()
    ).decode()
    resp = await client.post(
        settings.ebay_oauth_url,
        headers={
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope",
        },
    )
    resp.raise_for_status()
    payload = resp.json()
    _token_cache.token = payload["access_token"]
    _token_cache.expires_at = now + float(payload.get("expires_in", 7200))
    return _token_cache.token


def _parse_items(payload: dict) -> list[EbayItem]:
    items: list[EbayItem] = []
    for it in payload.get("itemSummaries", []) or []:
        price = it.get("price", {}) or {}
        try:
            value = float(price.get("value")) if price.get("value") is not None else None
        except (TypeError, ValueError):
            value = None
        items.append(
            EbayItem(
                item_id=it.get("itemId", ""),
                title=it.get("title", ""),
                price_usd=value,
                currency=price.get("currency", "USD"),
                condition=it.get("condition"),
                seller=(it.get("seller") or {}).get("username"),
                url=it.get("itemWebUrl"),
                image=(it.get("image") or {}).get("imageUrl"),
            )
        )
    return items


async def search_items(
    settings: Settings,
    query: str,
    category_id: str = TOYS_HOBBIES_CATEGORY,
    limit: int = 25,
) -> SearchResponse:
    if not settings.ebay_configured:
        return _sample_response(query, category_id, limit)

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            token = await _get_app_token(settings, client)
            resp = await client.get(
                settings.ebay_browse_url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-EBAY-C-MARKETPLACE-ID": settings.ebay_marketplace_id,
                    "Content-Type": "application/json",
                },
                params={
                    "q": query,
                    "category_ids": category_id,
                    "limit": min(limit, 200),
                    "filter": "buyingOptions:{FIXED_PRICE}",
                    "sort": "price",
                },
            )
            resp.raise_for_status()
            items = _parse_items(resp.json())
        return SearchResponse(
            query=query,
            category_id=category_id,
            count=len(items),
            source="ebay_api",
            items=items,
        )
    except (httpx.HTTPError, KeyError, ValueError):
        # 認証/通信エラー時はサンプルにフォールバックして UI を壊さない
        return _sample_response(query, category_id, limit)


def _sample_response(query: str, category_id: str, limit: int) -> SearchResponse:
    base = [
        ("Bandai Gundam RG 1/144 Nu Gundam Model Kit", 58.99, "New"),
        ("Pokemon TCG Charizard ex Booster Box Japanese", 129.50, "New"),
        ("Tamiya 1/24 Toyota Supra Plastic Model Kit", 41.00, "New"),
        ("Good Smile Nendoroid Figure Anime Japan Import", 74.99, "New"),
        ("Takara Tomy Transformers Masterpiece MP-44", 189.00, "Used"),
        ("Kotobukiya Frame Arms Girl Plastic Kit", 52.25, "New"),
        ("Square Enix Final Fantasy Bring Arts Figure", 99.99, "New"),
        ("Bandai Super Robot Chogokin Diecast Figure", 145.00, "Used"),
    ]
    items = [
        EbayItem(
            item_id=f"sample-{i}",
            title=f"{title}",
            price_usd=price,
            currency="USD",
            condition=cond,
            seller="sample_seller",
            url="https://www.ebay.com/",
            image=None,
            is_sample=True,
        )
        for i, (title, price, cond) in enumerate(base[:limit])
    ]
    return SearchResponse(
        query=query,
        category_id=category_id,
        count=len(items),
        source="sample",
        items=items,
    )
