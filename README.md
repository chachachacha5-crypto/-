# eBay US 関税・送料 概算ツール (2026年版)

日本→米国向けの eBay 販売で、**原産国 × カテゴリ × サイズ・重量** から
関税(2026年2月SCOTUS判決後の構造)と送料(EMS / eパケット / 船便)を概算する Next.js アプリ。

スマホで使う場合: `docs/index.html` を GitHub Pages か htmlpreview で開けば
インストール不要・1ファイルで動きます。

## 2026年5月時点の関税構造

| 区分 | 内容 | 適用 |
|---|---|---|
| MFN 通常関税 | HTSコード別の通常税率 (カテゴリで決まる) | 常時 |
| **Section 122** | 全世界一律 **+10%** (2026/2/24発効, 150日上限) | 暫定 (2026年7月頃失効予定) |
| **Section 301** | 中国製品のみ追加 (品目別 7.5〜25%) | 中国製のみ |
| **Section 232** | 鉄鋼/アルミ/自動車・関連部品 +25% | 該当製品のみ |
| MPF 処理手数料 | 0.3464% (最低 $32.71, 上限 $634.62) | 常時 |
| ~~IEEPA 相互関税~~ | ~~国別 (日本15%, 中国30%, EU15% 等)~~ | **2026/2/24 失効** |
| de minimis ($800) | 2025/8/29 廃止以降 停止継続 | 全貨物が関税対象 |

最高裁判決: [Learning Resources, Inc. v. Trump (02/20/2026)](https://www.supremecourt.gov/opinions/25pdf/24-1287_4gcj.pdf) — 6-3 で IEEPA 関税を違憲と判断。

## 起動

```bash
npm install
npm run dev
# http://localhost:3000
```

## ファイル構成

```
app/
  page.tsx
  layout.tsx
  api/calculate/route.ts    # JSON POST API
components/
  CalculatorForm.tsx
  ResultDisplay.tsx
lib/
  tariff.ts                 # 国・カテゴリ・各Section税率テーブル
  shipping.ts               # 送料テーブル + 容積重量計算
  calculate.ts              # MFN/S122/S301/S232/MPF 統合計算
docs/
  index.html                # スマホ向け 1ファイル版 (サーバ不要)
scripts/
  sanity-check.ts           # 動作確認スクリプト
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
    "includeShippingInDutyBase": true,
    "section232": false,
    "shippingMode": "DIRECT"
  }'
```

## 注意事項

- Section 122 は 150日上限のため **2026年7月頃に失効予定**。継続には議会立法が必要。
- 正確な税率は **HTSコード** と CBP / USTR の最新告示を、送料は日本郵便公式料金表を必ずご確認ください。
- USMCA 原産品 (メキシコ/カナダ) は通常無税で扱われる場合があります。
