# eBay US 関税・送料 概算ツール

日本→米国向けの eBay 販売で、**生産国 × 商品カテゴリ × サイズ・重量** から
関税(2025年の相互関税対応) と 送料(EMS / eパケット / 船便) を概算する Next.js アプリ。

## 起動

```bash
npm install
npm run dev
# http://localhost:3000
```

## 機能

- 18 ヶ国 (日本/中国/韓国/ベトナム/EU/英国/メキシコ/カナダ 他) の **相互関税 (Reciprocal Tariff)** 代表値
- 16 カテゴリ (衣料品/靴/バッグ/時計/電子機器/カメラ/ジュエリー/楽器 他) の **MFN 関税** 代表値
- **送料**: 日本郵便 EMS / 国際eパケット / 船便小包 を同時比較
  - **実重量 vs 容積重量** (EMS は L×W×H/6000)
  - サイズ規制 (EMS: 1辺 1.5m / 周長 3m / 30kg) の自動チェック
- **MPF** (Merchandise Processing Fee, 0.3464%, $32.71〜$634.62) を加算
- **Landed Cost** (= 商品代金 + 関税 + 送料 + MPF) を一括表示

## ファイル構成

```
app/
  page.tsx                  # トップ
  layout.tsx
  api/calculate/route.ts    # JSON POST API
components/
  CalculatorForm.tsx        # 入力フォーム
  ResultDisplay.tsx         # 結果表示
lib/
  tariff.ts                 # 国別税率 / カテゴリ別税率テーブル
  shipping.ts               # 送料テーブル + 容積重量計算
  calculate.ts              # 関税・送料統合計算
scripts/
  sanity-check.ts           # 動作確認用スクリプト
```

## API 例

```bash
curl -X POST http://localhost:3000/api/calculate \
  -H "content-type: application/json" \
  -d '{
    "itemPriceUsd": 100,
    "originCountry": "JP",
    "category": "general",
    "actualWeightKg": 1.0,
    "lengthCm": 30, "widthCm": 20, "heightCm": 10,
    "jpyToUsd": 155,
    "includeShippingInDutyBase": true
  }'
```

## 注意事項

- 2025年 8月29日で **de minimis ($800 免税枠) が全世界で廃止**。すべての貨物が関税対象。
- 相互関税は 2025年中も頻繁に変動。本ツールの値は **2025年後半時点の代表値**。
- 正確な税率は **HTS コード** と最新の **Executive Order**、送料は日本郵便公式の最新料金表をご確認ください。
- USMCA 適合品 (メキシコ/カナダ原産) は通常無税。
