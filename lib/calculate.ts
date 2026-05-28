import {
  findCountry,
  findCategory,
  SECTION_122_RATE,
  SECTION_232_RATE,
  MPF_RATE,
  MPF_MIN_USD,
  MPF_MAX_USD,
  type CountryCode,
  type CategoryCode,
} from "./tariff";
import { SHIPPING_OPTIONS, calculateShipping, type ShippingCalc } from "./shipping";

export type ShippingMode = "DIRECT" | "EIS";

export interface CalcInput {
  itemPriceUsd: number;
  originCountry: CountryCode;
  category: CategoryCode;
  actualWeightKg: number;
  lengthCm: number;
  widthCm: number;
  heightCm: number;
  jpyToUsd: number;
  includeShippingInDutyBase: boolean;
  // 鉄鋼/アルミ/自動車部品 (Section 232 対象)
  section232: boolean;
  // 発送方法 (eBay代行 or 直接発送)
  shippingMode: ShippingMode;
}

export interface DutyBreakdown {
  itemPriceUsd: number;
  shippingForDutyUsd: number;
  dutyBaseUsd: number;
  // 各レイヤーの料率と金額
  mfnRate: number;
  section122Rate: number;
  section301Rate: number;
  section232Rate: number;
  totalRate: number;
  mfnDutyUsd: number;
  section122Usd: number;
  section301Usd: number;
  section232Usd: number;
  totalDutyUsd: number;
  mpfUsd: number;
  totalImportFeeUsd: number;
  countryName: string;
  categoryName: string;
  isChinaOrigin: boolean;
  notes: string[];
}

export interface CalcResult {
  input: CalcInput;
  shipping: ShippingCalc[];
  duty: DutyBreakdown;
  recommended: {
    service: string;
    shippingJpy: number;
    shippingUsd: number;
    landedCostUsd: number;
  } | null;
}

export function calculate(input: CalcInput): CalcResult {
  const country = findCountry(input.originCountry);
  const category = findCategory(input.category);

  const shipping = SHIPPING_OPTIONS.map((opt) =>
    calculateShipping(
      opt,
      input.actualWeightKg,
      input.lengthCm,
      input.widthCm,
      input.heightCm,
      input.jpyToUsd,
    ),
  );

  const ems = shipping.find((s) => s.service === "EMS" && !s.oversize && s.feeUsd !== null);
  const shippingForDutyUsd =
    input.includeShippingInDutyBase && ems?.feeUsd ? ems.feeUsd : 0;
  const dutyBase = input.itemPriceUsd + shippingForDutyUsd;

  const mfnRate = category.mfnRate;
  const section122Rate = SECTION_122_RATE;
  const isChina = country.code === "CN";
  const section301Rate = isChina ? category.section301Rate : 0;
  const section232Rate = input.section232 ? SECTION_232_RATE : 0;

  const mfnDuty = dutyBase * (mfnRate / 100);
  const section122 = dutyBase * (section122Rate / 100);
  const section301 = dutyBase * (section301Rate / 100);
  const section232 = dutyBase * (section232Rate / 100);
  const totalDuty = mfnDuty + section122 + section301 + section232;
  const totalRate = mfnRate + section122Rate + section301Rate + section232Rate;

  let mpf = dutyBase * MPF_RATE;
  if (mpf < MPF_MIN_USD) mpf = MPF_MIN_USD;
  if (mpf > MPF_MAX_USD) mpf = MPF_MAX_USD;

  const notes: string[] = [];
  notes.push("2026年2月20日 最高裁判決で IEEPA 関税 (国別相互関税) は違憲・撤廃 (2026/2/24 失効)");
  notes.push("Section 122 (+10%) は 150日上限のため 2026年7月頃に失効予定。継続には議会立法が必要");
  if (isChina) {
    notes.push(`中国製品は Section 301 (+${category.section301Rate}% / カテゴリ代表値) が継続中`);
  }
  if (input.section232) {
    notes.push("Section 232 (+25%) は鉄鋼/アルミ/自動車・関連部品が対象");
  }
  if (country.code === "MX" || country.code === "CA") {
    notes.push("USMCA 原産品は通常無税。原産地証明があれば Section 122 等の扱いが変わる場合あり");
  }
  notes.push("de minimis ($800免税枠) は 2025/8/29 廃止以降、停止継続中 → 全貨物が関税対象");
  if (input.shippingMode === "EIS") {
    notes.push("eIS / GSP 利用時: チェックアウト時にeBayが関税徴収・代行。原産国とHTSコードはeBayが処理");
  } else {
    notes.push("直接発送時: 原産国・HTSコード・正確な商品価値を申告書に明記。買い手がCBPに直接支払い");
  }
  if (ems?.oversize) {
    notes.push("EMSが利用できないサイズ・重量です。FedEx/DHLでの送付を検討してください");
  }

  let recommended: CalcResult["recommended"] = null;
  if (ems && ems.feeJpy !== null && ems.feeUsd !== null) {
    recommended = {
      service: ems.label,
      shippingJpy: ems.feeJpy,
      shippingUsd: ems.feeUsd,
      landedCostUsd: input.itemPriceUsd + totalDuty + ems.feeUsd + mpf,
    };
  }

  return {
    input,
    shipping,
    duty: {
      itemPriceUsd: input.itemPriceUsd,
      shippingForDutyUsd,
      dutyBaseUsd: dutyBase,
      mfnRate,
      section122Rate,
      section301Rate,
      section232Rate,
      totalRate,
      mfnDutyUsd: mfnDuty,
      section122Usd: section122,
      section301Usd: section301,
      section232Usd: section232,
      totalDutyUsd: totalDuty,
      mpfUsd: mpf,
      totalImportFeeUsd: totalDuty + mpf,
      countryName: country.name,
      categoryName: category.name,
      isChinaOrigin: isChina,
      notes,
    },
    recommended,
  };
}
