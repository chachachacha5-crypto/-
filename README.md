# eBay × メルカリ 輸出せどりリサーチツール（トイ&ホビー）

メルカリで仕入れ、**eBay US で販売**する価格差せどりで、利益が取れる商品を
リサーチするための Web アプリ（MVP）です。ジャンルはトイ&ホビーを想定。

- eBay 側の相場は **eBay 公式 Browse API** から取得（規約に沿った正規利用）。
- メルカリ側は公開 API が無いため、**手動入力 / CSV 取込**で価格を与えます
  （スクレイピングは利用規約・安定性の問題があるため本ツールでは行いません）。
- eBay 手数料・国際送料・為替・円転手数料を差し引いた**手取り利益**を計算します。

## できること

1. **相場検索** — キーワード＋トイ&ホビーのカテゴリで eBay US の出品価格を取得。
2. **利益計算** — 各候補にメルカリ仕入れ価格・送料を入力すると、純売上・総コスト・
   利益・利益率・ROI を算出し、利益が出る順に並べ替え。
3. **CSV 取込** — 仕入れ候補リスト（タイトル / メルカリ価格 / eBay価格…）をまとめて計算。
4. **損益分岐価格の逆算** — `/api/breakeven` で目標 ROI に必要な eBay 販売価格を計算。

> eBay キー未設定でも**サンプルモード**で UI と計算ロジックを試せます。

## 利益計算ロジック

```
売上側(USD→JPY)
  総売上(USD)     = eBay 販売価格
  eBay手数料(USD) = 総売上 * (落札% + 広告% + 国際取引%) / 100 + 固定手数料
  純売上(USD)     = 総売上 - eBay手数料
  純売上(JPY)     = 純売上(USD) * 為替 - 円転手数料

仕入れ・経費側(JPY)
  総コスト = メルカリ価格 + 国内送料 + 国際送料 + 梱包資材費

利益(JPY) = 純売上(JPY) - 総コスト
利益率(%) = 利益 / 総売上(JPY) * 100
ROI(%)    = 利益 / 総コスト * 100
```

手数料の既定値（落札 13.25% / 円転 3% など）はあくまで一般的な目安です。
実際のカテゴリ・ストア契約・配送方法に合わせて UI または `.env` で調整してください。

## セットアップ

```bash
# 1. (任意) eBay 認証情報を設定
cp .env.example .env   # EBAY_CLIENT_ID / EBAY_CLIENT_SECRET を記入

# 2. 起動
./run.sh
#   または
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

ブラウザで http://localhost:8000 を開きます。

### eBay API キーの取得

1. https://developer.ebay.com/ でアカウント作成
2. Application Keys から **App ID (Client ID)** と **Cert ID (Client Secret)** を取得
3. `.env` に設定（Browse API は client credentials grant で利用）

## API エンドポイント

| メソッド | パス | 説明 |
|---|---|---|
| GET  | `/api/health` | 稼働状況・eBay 接続モード |
| GET  | `/api/categories` | トイ&ホビーのカテゴリ一覧 |
| GET  | `/api/fx-rate?force=` | USD/JPY を自動取得（失敗時は既定値）|
| GET  | `/api/defaults` | 手数料・レートの既定値 |
| GET  | `/api/search?q=&category_id=&limit=` | eBay 相場検索 |
| POST | `/api/profit` | 1 商品の利益計算 |
| POST | `/api/profit/batch` | 複数商品の一括計算 |
| POST | `/api/breakeven` | 目標 ROI に必要な販売価格を逆算 |
| POST | `/api/import/mercari-csv` | 仕入れ候補 CSV の取込 |

## テスト

```bash
source .venv/bin/activate
pip install pytest
pytest tests/ -q
```

## 構成

```
backend/app/
  config.py   設定（.env）
  models.py   入出力スキーマ
  profit.py   利益計算エンジン
  ebay.py     eBay Browse API クライアント（サンプルフォールバック付き）
  main.py     FastAPI ルート・フロント配信
frontend/     バニラ JS の SPA（ビルド不要）
tests/        利益計算のテスト
```

## 注意・今後の拡張

- 現状の相場は「出品中(active)」価格。実売価格(sold)は eBay の
  Marketplace Insights API（要申請）で取得すると精度が上がります。
- 為替レート(USD/JPY)は起動時に無料 API（`open.er-api.com` → `api.frankfurter.app`）
  から自動取得し、UI の ⟳ ボタンで更新できます。取得失敗時は `DEFAULT_USD_JPY` に
  フォールバックします。egress allowlist 制の環境では上記ホストの許可が必要です。
- 関税・輸入消費税・返品率などは未計上。運用に合わせて拡張してください。
