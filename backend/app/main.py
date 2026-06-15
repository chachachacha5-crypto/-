"""FastAPI アプリ本体。API ルートとフロントエンド配信。"""

from __future__ import annotations

import csv
import io
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import ebay, fx
from .config import get_settings
from .models import FeeProfile, ProfitInput, ProfitResult, SearchResponse
from .profit import breakeven_ebay_price_usd, calculate_profit

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

app = FastAPI(
    title="eBay × Mercari 輸出せどりリサーチツール",
    description="メルカリ仕入れ → eBay US 販売の価格差から利益商品をリサーチする",
    version="0.1.0",
)


@app.get("/api/health")
async def health() -> dict:
    s = get_settings()
    return {
        "status": "ok",
        "ebay_configured": s.ebay_configured,
        "ebay_environment": s.ebay_environment,
        "mode": "ebay_api" if s.ebay_configured else "sample",
    }


@app.get("/api/categories")
async def categories() -> dict:
    return {"categories": ebay.CATEGORIES}


@app.get("/api/fx-rate")
async def fx_rate(force: bool = False) -> dict:
    """USD/JPY の為替レートを自動取得する（失敗時は既定値にフォールバック）。"""
    return await fx.get_usd_jpy(get_settings(), force=force)


@app.get("/api/defaults", response_model=FeeProfile)
async def defaults() -> FeeProfile:
    """UI のフォーム初期値（設定 .env の既定値から）。"""
    s = get_settings()
    return FeeProfile(
        usd_jpy=s.default_usd_jpy,
        ebay_fvf_percent=s.default_ebay_fvf_percent,
        ebay_fixed_fee_usd=s.default_ebay_fixed_fee_usd,
        intl_fee_percent=s.default_intl_fee_percent,
        payout_fx_percent=s.default_payout_fx_percent,
        ad_fee_percent=s.default_ad_fee_percent,
    )


@app.get("/api/search", response_model=SearchResponse)
async def search(q: str, category_id: str = ebay.TOYS_HOBBIES_CATEGORY, limit: int = 25):
    s = get_settings()
    return await ebay.search_items(s, query=q, category_id=category_id, limit=limit)


@app.post("/api/profit", response_model=ProfitResult)
async def profit(data: ProfitInput) -> ProfitResult:
    return calculate_profit(data)


class ProfitBatch(BaseModel):
    items: list[ProfitInput]


@app.post("/api/profit/batch", response_model=list[ProfitResult])
async def profit_batch(batch: ProfitBatch) -> list[ProfitResult]:
    return [calculate_profit(i) for i in batch.items]


class BreakevenInput(BaseModel):
    total_cost_jpy: float
    target_roi_percent: float = 0.0
    fees: FeeProfile = FeeProfile()


@app.post("/api/breakeven")
async def breakeven(data: BreakevenInput) -> dict:
    price = breakeven_ebay_price_usd(
        data.total_cost_jpy, data.fees, data.target_roi_percent
    )
    return {
        "total_cost_jpy": data.total_cost_jpy,
        "target_roi_percent": data.target_roi_percent,
        "required_ebay_price_usd": price,
    }


@app.post("/api/import/mercari-csv")
async def import_mercari_csv(file: UploadFile = File(...)) -> dict:
    """メルカリ仕入れ候補の CSV を取り込む。

    想定ヘッダ: title, mercari_price_jpy, ebay_price_usd (任意),
                mercari_shipping_jpy (任意), intl_shipping_jpy (任意)
    """
    raw = await file.read()
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows: list[dict] = []
    for row in reader:
        rows.append(
            {
                "title": (row.get("title") or "").strip(),
                "mercari_price_jpy": _num(row.get("mercari_price_jpy")),
                "ebay_price_usd": _num(row.get("ebay_price_usd")),
                "mercari_shipping_jpy": _num(row.get("mercari_shipping_jpy")),
                "intl_shipping_jpy": _num(row.get("intl_shipping_jpy")),
            }
        )
    return {"count": len(rows), "rows": rows}


def _num(value: str | None) -> float:
    if value is None:
        return 0.0
    value = value.strip().replace(",", "").replace("¥", "").replace("$", "")
    try:
        return float(value)
    except ValueError:
        return 0.0


# --- フロントエンド配信（API ルートの後に登録する）---
if FRONTEND_DIR.exists():

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "index.html")

    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
