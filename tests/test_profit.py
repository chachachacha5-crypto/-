"""利益計算エンジンのテスト。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.models import FeeProfile, ProfitInput
from backend.app.profit import breakeven_ebay_price_usd, calculate_profit


def _fees() -> FeeProfile:
    return FeeProfile(
        usd_jpy=155.0,
        ebay_fvf_percent=13.25,
        ebay_fixed_fee_usd=0.40,
        intl_fee_percent=1.65,
        payout_fx_percent=3.0,
        ad_fee_percent=0.0,
    )


def test_profitable_case():
    data = ProfitInput(
        title="test",
        ebay_price_usd=100.0,
        mercari_price_jpy=4500,
        intl_shipping_jpy=2000,
        fees=_fees(),
    )
    r = calculate_profit(data)
    # 売上 100USD -> 手数料控除 ~85USD -> *155 -> 円転3%控除
    assert r.gross_revenue_jpy == 15500
    assert r.total_cost_jpy == 6500
    assert r.is_profitable
    assert r.profit_jpy > 0
    # ざっくり妥当域（純売上は約 12,700 円前後）
    assert 12000 < r.net_revenue_jpy < 13500


def test_loss_case():
    data = ProfitInput(
        title="loss",
        ebay_price_usd=20.0,
        mercari_price_jpy=4000,
        intl_shipping_jpy=2000,
        fees=_fees(),
    )
    r = calculate_profit(data)
    assert not r.is_profitable
    assert r.profit_jpy < 0


def test_breakeven_roundtrip():
    fees = _fees()
    cost = 6500.0
    # 損益分岐の販売価格を逆算し、その価格で利益≒0 になることを確認
    price = breakeven_ebay_price_usd(cost, fees, target_roi_percent=0.0)
    data = ProfitInput(
        title="be",
        ebay_price_usd=price,
        mercari_price_jpy=cost,
        fees=fees,
    )
    r = calculate_profit(data)
    assert abs(r.profit_jpy) <= 2  # 端数誤差のみ


def test_breakeven_target_roi():
    fees = _fees()
    cost = 5000.0
    price = breakeven_ebay_price_usd(cost, fees, target_roi_percent=30.0)
    data = ProfitInput(
        title="roi", ebay_price_usd=price, mercari_price_jpy=cost, fees=fees
    )
    r = calculate_profit(data)
    assert abs(r.roi_percent - 30.0) < 1.0
