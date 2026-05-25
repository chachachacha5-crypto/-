# trend-research

楽天 / Yahoo!ショッピングの**公式API**を使ったトレンド商品リサーチ用CLIツール。

ランキング・キーワード頻度・価格帯・両プラットフォーム横断のクロス分析を取得して、CSV/JSONに出力します。

## 用途（想定）

- 自社プロダクトの市場リサーチ
- 仕入れジャンル選定の材料
- カテゴリごとの価格帯把握
- 検索トレンドのモニタリング

> ⚠️ 本ツールは**市場調査用**です。各プラットフォームの利用規約・転売関連法令（古物営業法等）を遵守してください。

## セットアップ

### 1. 依存インストール

```bash
pip install -r requirements.txt
```

### 2. APIキーの取得

**楽天ウェブサービス** (必須):
1. https://webservice.rakuten.co.jp/ にアクセス
2. 楽天会員でログインしてアプリ登録
3. 発行された `applicationId` を控える

**Yahoo!ショッピングAPI** (任意):
1. https://e.developer.yahoo.co.jp/ にアクセス
2. アプリケーション登録 (Client ID = appid)
3. 発行された `Client ID` を控える

### 3. `.env` ファイルを作成

```bash
cp .env.example .env
# エディタで開いてキーを記入
```

```ini
RAKUTEN_APP_ID=xxxxxxxxxxxxxxxxxxxx
YAHOO_APP_ID=dj00aiZpPXxxxxxxxxxxxx
```

## 使い方

### 主要ジャンルID一覧を確認

```bash
python -m src.main genres
```

### 楽天ランキング取得

```bash
# 全ジャンル・リアルタイム
python -m src.main rakuten

# おもちゃジャンル・日次・CSV出力
python -m src.main rakuten --genre 101240 --period daily --format csv

# 期間: realtime | daily | weekly | monthly
```

### Yahoo!ショッピング検索

```bash
# キーワード検索 (人気順)
python -m src.main yahoo --keyword "ポケモン"

# カテゴリ指定 + JSON出力
python -m src.main yahoo --category 2502 --sort popular --format json

# ソート: popular | review | price_asc | price_desc | sold
```

### トレンド分析（横断）

```bash
# デフォルト: おもちゃ/本/ゲーム/ホビーをまとめて
python -m src.main trends

# ジャンル + キーワード指定
python -m src.main trends \
  --genres 101240 100371 \
  --keywords "新商品" "予約" \
  --period daily \
  --format both
```

出力されるもの:
- 各プラットフォームの価格統計 (min/max/median/avg)
- 商品名から抽出した頻出キーワードTOP15
- 楽天 ⇔ Yahoo のクロスマッチ (同一商品候補と価格差)
- `data/trends_YYYYMMDD_HHMMSS.{csv,json}` への出力

## ディレクトリ構成

```
.
├── src/
│   ├── main.py        # CLIエントリ
│   ├── rakuten.py     # 楽天APIクライアント
│   ├── yahoo.py       # Yahoo APIクライアント
│   ├── analyzer.py    # 価格統計/キーワード抽出/クロスマッチ
│   └── exporter.py    # CSV/JSON出力
├── data/              # 出力先 (gitignore)
├── requirements.txt
├── .env.example
└── README.md
```

## API レート制限の目安

- 楽天: 1リクエスト/秒程度 (本ツールは1秒間隔で自動スロットル)
- Yahoo: 同上

短時間に大量リクエストするとブロックされるので、`--genres` を絞るか実行頻度を調整してください。
