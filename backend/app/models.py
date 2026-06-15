"""API の入出力スキーマ。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class FeeProfile(BaseModel):
    """利益計算に使う各種レート・手数料。UI から上書きできる。"""

    usd_jpy: float = Field(155.0, gt=0, description="1 USD あたりの円")
    ebay_fvf_percent: float = Field(13.25, ge=0, description="eBay 落札手数料 %")
    ebay_fixed_fee_usd: float = Field(0.40, ge=0, description="注文ごと固定手数料 USD")
    intl_fee_percent: float = Field(1.65, ge=0, description="国際取引手数料 %")
    payout_fx_percent: float = Field(3.0, ge=0, description="円転時の通貨換算手数料 %")
    ad_fee_percent: float = Field(0.0, ge=0, description="Promoted Listings 手数料 %")


class ProfitInput(BaseModel):
    """1 商品ぶんの利益計算入力。"""

    title: str = ""
    ebay_price_usd: float = Field(..., ge=0, description="eBay 想定販売価格 (USD)")
    mercari_price_jpy: float = Field(..., ge=0, description="メルカリ仕入れ価格 (JPY)")
    mercari_shipping_jpy: float = Field(0, ge=0, description="国内送料 (JPY)")
    intl_shipping_jpy: float = Field(0, ge=0, description="国際送料 日本→米国 (JPY)")
    packaging_jpy: float = Field(0, ge=0, description="梱包資材費 (JPY)")
    fees: FeeProfile = Field(default_factory=FeeProfile)


class ProfitResult(BaseModel):
    """利益計算の結果。すべて JPY 換算 (手数料内訳のみ USD も保持)。"""

    title: str
    ebay_price_usd: float
    gross_revenue_jpy: float
    ebay_fee_usd: float
    fx_fee_jpy: float
    net_revenue_jpy: float
    total_cost_jpy: float
    profit_jpy: float
    profit_margin_percent: float
    roi_percent: float
    is_profitable: bool


class EbayItem(BaseModel):
    """eBay 検索結果 1 件 (利益計算前の素データ)。"""

    item_id: str
    title: str
    price_usd: float | None
    currency: str = "USD"
    condition: str | None = None
    seller: str | None = None
    url: str | None = None
    image: str | None = None
    is_sample: bool = False


class SearchResponse(BaseModel):
    query: str
    category_id: str
    count: int
    source: str  # "ebay_api" or "sample"
    items: list[EbayItem]
