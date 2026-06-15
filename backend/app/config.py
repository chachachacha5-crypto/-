"""アプリ設定。環境変数 (.env) から読み込む。

eBay の認証情報が無い場合でもアプリは起動し、サンプルデータで動作する。
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- eBay Developer 認証情報 (Browse API / OAuth client credentials) ---
    # https://developer.ebay.com/ で取得した App ID(Client ID) / Cert ID(Client Secret)
    ebay_client_id: str = ""
    ebay_client_secret: str = ""
    # "PRODUCTION" or "SANDBOX"
    ebay_environment: str = "PRODUCTION"
    # 米国マーケットプレイスを既定にする (販売先が米国のため)
    ebay_marketplace_id: str = "EBAY_US"

    # --- せどり利益計算の既定値 ---
    # 1 USD = ? JPY。実運用では為替レートを都度更新する。
    default_usd_jpy: float = 155.0
    # eBay 落札手数料 (Final Value Fee) の目安 %。トイ&ホビーは ~13.25%。
    default_ebay_fvf_percent: float = 13.25
    # 注文ごとの固定手数料 (USD)
    default_ebay_fixed_fee_usd: float = 0.40
    # 国際取引手数料の目安 %
    default_intl_fee_percent: float = 1.65
    # 売上を円転する際の通貨換算手数料の目安 %
    default_payout_fx_percent: float = 3.0
    # Promoted Listings(広告)手数料の目安 %（使わない場合は 0）
    default_ad_fee_percent: float = 0.0

    @property
    def ebay_oauth_url(self) -> str:
        if self.ebay_environment.upper() == "SANDBOX":
            return "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
        return "https://api.ebay.com/identity/v1/oauth2/token"

    @property
    def ebay_browse_url(self) -> str:
        if self.ebay_environment.upper() == "SANDBOX":
            return "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"
        return "https://api.ebay.com/buy/browse/v1/item_summary/search"

    @property
    def ebay_configured(self) -> bool:
        return bool(self.ebay_client_id and self.ebay_client_secret)


@lru_cache
def get_settings() -> Settings:
    return Settings()
