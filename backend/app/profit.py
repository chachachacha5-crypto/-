"""せどり利益計算エンジン（メルカリ仕入れ → eBay US 販売）。

計算の流れ:

  売上側 (USD → JPY)
    総売上(USD)        = eBay 販売価格
    eBay手数料(USD)    = 総売上 * (落札% + 広告% + 国際取引%) / 100 + 固定手数料
    純売上(USD)        = 総売上 - eBay手数料
    純売上(JPY 換算前) = 純売上(USD) * 為替レート
    円転手数料(JPY)    = 純売上(JPY換算前) * 円転手数料% / 100
    純売上(JPY)        = 純売上(JPY換算前) - 円転手数料

  仕入れ・経費側 (JPY)
    総コスト(JPY) = メルカリ価格 + 国内送料 + 国際送料 + 梱包資材費

  利益
    利益(JPY)   = 純売上(JPY) - 総コスト(JPY)
    利益率(%)   = 利益 / 総売上(JPY) * 100
    ROI(%)      = 利益 / 総コスト(JPY) * 100
"""

from __future__ import annotations

from .models import FeeProfile, ProfitInput, ProfitResult


def calculate_profit(data: ProfitInput) -> ProfitResult:
    f = data.fees

    gross_usd = data.ebay_price_usd
    variable_fee_percent = f.ebay_fvf_percent + f.ad_fee_percent + f.intl_fee_percent
    ebay_fee_usd = gross_usd * variable_fee_percent / 100 + f.ebay_fixed_fee_usd
    net_usd = gross_usd - ebay_fee_usd

    net_jpy_before_fx = net_usd * f.usd_jpy
    fx_fee_jpy = net_jpy_before_fx * f.payout_fx_percent / 100
    net_revenue_jpy = net_jpy_before_fx - fx_fee_jpy

    gross_revenue_jpy = gross_usd * f.usd_jpy

    total_cost_jpy = (
        data.mercari_price_jpy
        + data.mercari_shipping_jpy
        + data.intl_shipping_jpy
        + data.packaging_jpy
    )

    profit_jpy = net_revenue_jpy - total_cost_jpy

    margin = (profit_jpy / gross_revenue_jpy * 100) if gross_revenue_jpy else 0.0
    roi = (profit_jpy / total_cost_jpy * 100) if total_cost_jpy else 0.0

    return ProfitResult(
        title=data.title,
        ebay_price_usd=round(gross_usd, 2),
        gross_revenue_jpy=round(gross_revenue_jpy),
        ebay_fee_usd=round(ebay_fee_usd, 2),
        fx_fee_jpy=round(fx_fee_jpy),
        net_revenue_jpy=round(net_revenue_jpy),
        total_cost_jpy=round(total_cost_jpy),
        profit_jpy=round(profit_jpy),
        profit_margin_percent=round(margin, 1),
        roi_percent=round(roi, 1),
        is_profitable=profit_jpy > 0,
    )


def breakeven_ebay_price_usd(
    total_cost_jpy: float, fees: FeeProfile, target_roi_percent: float = 0.0
) -> float:
    """目標 ROI を満たすのに必要な eBay 販売価格 (USD) を逆算する。

    target_roi_percent=0 なら損益分岐点となる販売価格を返す。
    """
    # 必要な手取り(JPY) = コスト * (1 + 目標ROI/100)
    required_net_jpy = total_cost_jpy * (1 + target_roi_percent / 100)
    # required_net_jpy = (gross_usd*(1 - var%/100) - fixed) * usd_jpy * (1 - fx%/100)
    var = (fees.ebay_fvf_percent + fees.ad_fee_percent + fees.intl_fee_percent) / 100
    fx = fees.payout_fx_percent / 100

    if var >= 1 or fx >= 1 or fees.usd_jpy <= 0:
        return float("inf")
    gross_usd = (required_net_jpy / (fees.usd_jpy * (1 - fx)) + fees.ebay_fixed_fee_usd) / (1 - var)
    return round(gross_usd, 2)
