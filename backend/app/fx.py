"""為替レート(USD/JPY)の自動取得。

無料・APIキー不要の為替 API から取得する。失敗時（ネットワーク制限・
API 障害など）は設定の既定値にフォールバックするため、アプリは止まらない。

注意: この実行環境が egress allowlist 制の場合、為替 API のホストを
ネットワーク許可設定に追加する必要がある（未許可だと 403 でフォールバック）。
"""

from __future__ import annotations

import time

import httpx

from .config import Settings

# (URL, レスポンスJSONから JPY レートを取り出す関数)
_PROVIDERS: list[tuple[str, str]] = [
    ("open.er-api.com", "https://open.er-api.com/v6/latest/USD"),
    ("frankfurter.app", "https://api.frankfurter.app/latest?from=USD&to=JPY"),
]


def _extract_jpy(host: str, data: dict) -> float | None:
    rates = data.get("rates") or {}
    value = rates.get("JPY")
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


class _RateCache:
    rate: float | None = None
    source: str = ""
    fetched_at: float = 0.0


_cache = _RateCache()
_TTL_SECONDS = 3600  # 1 時間キャッシュして API への過剰アクセスを避ける


async def get_usd_jpy(settings: Settings, force: bool = False) -> dict:
    """USD/JPY を返す。

    戻り値: {rate, source, is_live, fetched_at, note}
    - is_live=True なら為替 API から取得した値
    - is_live=False なら設定の既定値（取得失敗時のフォールバック）
    """
    now = time.time()
    if (
        not force
        and _cache.rate is not None
        and now - _cache.fetched_at < _TTL_SECONDS
    ):
        return {
            "rate": _cache.rate,
            "source": _cache.source,
            "is_live": True,
            "fetched_at": _cache.fetched_at,
            "note": "cached",
        }

    last_error = ""
    async with httpx.AsyncClient(timeout=8) as client:
        for host, url in _PROVIDERS:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                rate = _extract_jpy(host, resp.json())
                if rate and rate > 0:
                    _cache.rate = rate
                    _cache.source = host
                    _cache.fetched_at = now
                    return {
                        "rate": round(rate, 3),
                        "source": host,
                        "is_live": True,
                        "fetched_at": now,
                        "note": "live",
                    }
                last_error = f"{host}: JPY レートを取得できませんでした"
            except httpx.HTTPStatusError as e:
                last_error = f"{host}: HTTP {e.response.status_code}"
            except (httpx.HTTPError, ValueError) as e:
                last_error = f"{host}: {type(e).__name__}"

    # 全プロバイダ失敗 → 既定値にフォールバック
    return {
        "rate": settings.default_usd_jpy,
        "source": "default",
        "is_live": False,
        "fetched_at": now,
        "note": f"為替APIに接続できないため既定値を使用 ({last_error})",
    }
