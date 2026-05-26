// 2025-2026年 米国輸入関税の代表値テーブル
// 注: トランプ政権下の "Reciprocal Tariff" (相互関税) と通常MFN関税を合算した概算
// 実務では HTS コードと最新の Executive Order を必ず確認すること

export type CountryCode =
  | "JP"
  | "CN"
  | "KR"
  | "TW"
  | "VN"
  | "TH"
  | "ID"
  | "PH"
  | "MY"
  | "IN"
  | "BD"
  | "KH"
  | "MX"
  | "CA"
  | "EU"
  | "GB"
  | "BR"
  | "OTHER";

export type CategoryCode =
  | "apparel"
  | "footwear"
  | "bags_leather"
  | "bags_textile"
  | "watches"
  | "jewelry"
  | "electronics"
  | "cameras"
  | "toys_games"
  | "hobby_collectibles"
  | "books_paper"
  | "kitchenware"
  | "cosmetics"
  | "sporting_goods"
  | "musical_instruments"
  | "general";

export interface CountryInfo {
  code: CountryCode;
  name: string;
  // 2025 相互関税(追加関税)の代表税率 [%]
  reciprocalRate: number;
  note?: string;
}

export interface CategoryInfo {
  code: CategoryCode;
  name: string;
  // MFN 通常関税の代表税率 [%] (HTSの典型値)
  mfnRate: number;
  exampleHts?: string;
}

// 出典: USTR / Executive Orders 2025 (相互関税), 2025年後半時点の代表値
// 国別の追加関税は今後も変動するため "rough estimate" 表記とする
export const COUNTRIES: CountryInfo[] = [
  { code: "JP", name: "日本", reciprocalRate: 15, note: "2025年7月の日米合意以降の代表値" },
  { code: "CN", name: "中国", reciprocalRate: 30, note: "2025年5月以降の引下げ後 (品目により更に高い場合あり)" },
  { code: "KR", name: "韓国", reciprocalRate: 15 },
  { code: "TW", name: "台湾", reciprocalRate: 20 },
  { code: "VN", name: "ベトナム", reciprocalRate: 20 },
  { code: "TH", name: "タイ", reciprocalRate: 19 },
  { code: "ID", name: "インドネシア", reciprocalRate: 19 },
  { code: "PH", name: "フィリピン", reciprocalRate: 19 },
  { code: "MY", name: "マレーシア", reciprocalRate: 19 },
  { code: "IN", name: "インド", reciprocalRate: 25 },
  { code: "BD", name: "バングラデシュ", reciprocalRate: 20 },
  { code: "KH", name: "カンボジア", reciprocalRate: 19 },
  { code: "MX", name: "メキシコ", reciprocalRate: 25, note: "USMCA適合品は通常無税" },
  { code: "CA", name: "カナダ", reciprocalRate: 35, note: "USMCA適合品は通常無税" },
  { code: "EU", name: "EU加盟国", reciprocalRate: 15 },
  { code: "GB", name: "イギリス", reciprocalRate: 10 },
  { code: "BR", name: "ブラジル", reciprocalRate: 50 },
  { code: "OTHER", name: "その他 (10%ベースライン)", reciprocalRate: 10 },
];

// 米国 HTS の主要カテゴリの代表MFN税率
export const CATEGORIES: CategoryInfo[] = [
  { code: "apparel", name: "衣料品 (服全般)", mfnRate: 15, exampleHts: "6109/6204 等" },
  { code: "footwear", name: "靴・スニーカー", mfnRate: 12, exampleHts: "6403/6404" },
  { code: "bags_leather", name: "バッグ (革製)", mfnRate: 8, exampleHts: "4202.21" },
  { code: "bags_textile", name: "バッグ (布・合皮)", mfnRate: 17.6, exampleHts: "4202.92" },
  { code: "watches", name: "時計", mfnRate: 4, exampleHts: "9102 (構造により変動大)" },
  { code: "jewelry", name: "ジュエリー・アクセサリー", mfnRate: 6.5, exampleHts: "7113/7117" },
  { code: "electronics", name: "電子機器 (PC周辺・スマホ等)", mfnRate: 0, exampleHts: "8471/8517 (多くが無税)" },
  { code: "cameras", name: "カメラ・レンズ", mfnRate: 2.1, exampleHts: "9006/9002" },
  { code: "toys_games", name: "おもちゃ・ゲーム", mfnRate: 0, exampleHts: "9503 (多くが無税)" },
  { code: "hobby_collectibles", name: "ホビー・フィギュア・コレクター品", mfnRate: 0, exampleHts: "9503/9705" },
  { code: "books_paper", name: "書籍・紙製品", mfnRate: 0, exampleHts: "4901 (書籍は無税)" },
  { code: "kitchenware", name: "食器・キッチン用品", mfnRate: 7, exampleHts: "6911/7323" },
  { code: "cosmetics", name: "化粧品", mfnRate: 0, exampleHts: "3304 (多くが無税)" },
  { code: "sporting_goods", name: "スポーツ用品", mfnRate: 4, exampleHts: "9506" },
  { code: "musical_instruments", name: "楽器", mfnRate: 4.5, exampleHts: "9202/9205" },
  { code: "general", name: "その他 / 一般雑貨", mfnRate: 5 },
];

// 米国輸入時の処理手数料 (Merchandise Processing Fee) 2025年率
// 正式申告: ad valorem 0.3464%、min $32.71, max $634.62
// 非公式申告 (Informal Entry, $2,500未満): 固定 $2.62 (manual) / $2.18 (auto) ※郵便は通常加算なし
export const MPF_RATE = 0.003464;
export const MPF_MIN_USD = 32.71;
export const MPF_MAX_USD = 634.62;
export const INFORMAL_ENTRY_THRESHOLD_USD = 2500;
export const INFORMAL_ENTRY_FEE_USD = 2.62;

export function findCountry(code: CountryCode): CountryInfo {
  const c = COUNTRIES.find((c) => c.code === code);
  if (!c) throw new Error(`Unknown country: ${code}`);
  return c;
}

export function findCategory(code: CategoryCode): CategoryInfo {
  const c = CATEGORIES.find((c) => c.code === code);
  if (!c) throw new Error(`Unknown category: ${code}`);
  return c;
}
