// 米国輸入関税 — 2026年5月時点の構造
// 2026年2月20日 最高裁判決 (Learning Resources, Inc. v. Trump, 6-3) により
// IEEPA に基づく国別「相互関税」は違憲と判断され、2026年2月24日 0:00 EST に失効。
// 代替として Section 122 (Trade Act of 1974) による全世界一律 10% が暫定発動中
// (150日上限 = 2026年7月頃失効予定。継続には議会立法が必要)。
// 加えて Section 301 (中国製品のみ) と Section 232 (鉄鋼/アルミ/自動車) は継続。

export type CountryCode =
  | "JP" | "CN" | "KR" | "TW" | "VN" | "TH" | "ID" | "PH" | "MY"
  | "IN" | "BD" | "KH" | "MX" | "CA" | "EU" | "GB" | "BR" | "OTHER";

export type CategoryCode =
  | "apparel" | "footwear" | "bags_leather" | "bags_textile"
  | "watches" | "jewelry" | "electronics" | "cameras"
  | "toys_games" | "hobby_collectibles" | "books_paper"
  | "kitchenware" | "cosmetics" | "sporting_goods"
  | "musical_instruments" | "general";

export interface CountryInfo {
  code: CountryCode;
  name: string;
  note?: string;
}

export interface CategoryInfo {
  code: CategoryCode;
  name: string;
  // MFN 通常関税の代表税率 [%]
  mfnRate: number;
  // 中国製の場合の Section 301 代表追加率 [%]
  section301Rate: number;
  exampleHts?: string;
}

// 原産国 (eBay出品時の必須情報)。関税計算上は「中国かどうか」のみが効く
export const COUNTRIES: CountryInfo[] = [
  { code: "JP", name: "日本" },
  { code: "CN", name: "中国", note: "Section 301 追加関税の対象" },
  { code: "KR", name: "韓国" },
  { code: "TW", name: "台湾" },
  { code: "VN", name: "ベトナム" },
  { code: "TH", name: "タイ" },
  { code: "ID", name: "インドネシア" },
  { code: "PH", name: "フィリピン" },
  { code: "MY", name: "マレーシア" },
  { code: "IN", name: "インド" },
  { code: "BD", name: "バングラデシュ" },
  { code: "KH", name: "カンボジア" },
  { code: "MX", name: "メキシコ", note: "USMCA適合品は通常無税" },
  { code: "CA", name: "カナダ", note: "USMCA適合品は通常無税" },
  { code: "EU", name: "EU加盟国" },
  { code: "GB", name: "イギリス" },
  { code: "BR", name: "ブラジル" },
  { code: "OTHER", name: "その他" },
];

export const CATEGORIES: CategoryInfo[] = [
  { code: "apparel",             name: "衣料品 (服全般)",                mfnRate: 15.0, section301Rate: 7.5,  exampleHts: "6109/6204" },
  { code: "footwear",            name: "靴・スニーカー",                 mfnRate: 12.0, section301Rate: 15.0, exampleHts: "6403/6404" },
  { code: "bags_leather",        name: "バッグ (革製)",                  mfnRate: 8.0,  section301Rate: 7.5,  exampleHts: "4202.21" },
  { code: "bags_textile",        name: "バッグ (布・合皮)",              mfnRate: 17.6, section301Rate: 7.5,  exampleHts: "4202.92" },
  { code: "watches",             name: "時計",                           mfnRate: 4.0,  section301Rate: 25.0, exampleHts: "9102" },
  { code: "jewelry",             name: "ジュエリー・アクセサリー",       mfnRate: 6.5,  section301Rate: 7.5,  exampleHts: "7113/7117" },
  { code: "electronics",         name: "電子機器 (PC周辺・スマホ等)",    mfnRate: 0.0,  section301Rate: 25.0, exampleHts: "8471/8517" },
  { code: "cameras",             name: "カメラ・レンズ",                 mfnRate: 2.1,  section301Rate: 25.0, exampleHts: "9006/9002" },
  { code: "toys_games",          name: "おもちゃ・ゲーム",               mfnRate: 0.0,  section301Rate: 7.5,  exampleHts: "9503" },
  { code: "hobby_collectibles",  name: "ホビー・フィギュア・コレクター品", mfnRate: 0.0,  section301Rate: 7.5,  exampleHts: "9503/9705" },
  { code: "books_paper",         name: "書籍・紙製品",                   mfnRate: 0.0,  section301Rate: 0.0,  exampleHts: "4901" },
  { code: "kitchenware",         name: "食器・キッチン用品",             mfnRate: 7.0,  section301Rate: 25.0, exampleHts: "6911/7323" },
  { code: "cosmetics",           name: "化粧品",                         mfnRate: 0.0,  section301Rate: 7.5,  exampleHts: "3304" },
  { code: "sporting_goods",      name: "スポーツ用品",                   mfnRate: 4.0,  section301Rate: 25.0, exampleHts: "9506" },
  { code: "musical_instruments", name: "楽器",                           mfnRate: 4.5,  section301Rate: 7.5,  exampleHts: "9202/9205" },
  { code: "general",             name: "その他 / 一般雑貨",              mfnRate: 5.0,  section301Rate: 15.0 },
];

// 現行関税レート (2026年5月時点)
export const SECTION_122_RATE = 10.0;   // 全世界一律 (2026/2/24発効, 150日上限のため7月頃失効予定)
export const SECTION_232_RATE = 25.0;   // 鉄鋼/アルミ/自動車・関連部品 (国に依存しない)

// MPF (Merchandise Processing Fee) 2026年率
export const MPF_RATE = 0.003464;
export const MPF_MIN_USD = 32.71;
export const MPF_MAX_USD = 634.62;

export function findCountry(code: CountryCode): CountryInfo {
  const c = COUNTRIES.find((x) => x.code === code);
  if (!c) throw new Error(`Unknown country: ${code}`);
  return c;
}

export function findCategory(code: CategoryCode): CategoryInfo {
  const c = CATEGORIES.find((x) => x.code === code);
  if (!c) throw new Error(`Unknown category: ${code}`);
  return c;
}
