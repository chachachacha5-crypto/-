import {
  findCountry,
  findCategory,
  MPF_RATE,
  MPF_MIN_USD,
  MPF_MAX_USD,
  type CountryCode,
  type CategoryCode,
} from "./tariff";
import { SHIPPING_OPTIONS, calculateShipping, type ShippingCalc } from "./shipping";

export interface CalcInput {
  // 商品代金 (eBay販売価格、USD)
  itemPriceUsd: number;
  // 生産国(原産国)
  originCountry: CountryCode;
  // カテゴリ
  category: CategoryCode;
  // 実重量 (kg)
  actualWeightKg: number;
  // 寸法 (cm)
  lengthCm: number;
  widthCm: number;
  heightCm: number;
  // 為替 (1USD = X JPY)
  jpyToUsd: number;
  // 関税の課税ベースに送料を含めるか (海上輸送 CIF / 航空輸送 では含むのが原則)
  includeShippingInDutyBase: boolean;
}

export interface DutyBreakdown {
  itemPriceUsd: number;
  shippingForDutyUsd: number;
  dutyBaseUsd: number;
  mfnRate: number; // %
  reciprocalRate: number; // %
  totalRate: number; // %
  mfnDutyUsd: number;
  reciprocalDutyUsd: number;
  totalDutyUsd: number;
  mpfUsd: number;
  totalImportFeeUsd: number;
  countryName: string;
  categoryName: string;
  notes: string[];
}

export interface CalcResult {
  input: CalcInput;
  shipping: ShippingCalc[];
  duty: DutyBreakdown;
  // 推奨送料(EMSベース)で総コスト
  recommended: {
    service: string;
    shippingJpy: number;
    shippingUsd: number;
    landedCostUsd: number; // = 商品代金 + 関税 + 送料 + MPF
  } | null;
}

export function calculate(input: CalcInput): CalcResult {
  const country = findCountry(input.originCountry);
  const category = findCategory(input.category);

  // 送料計算 (全サービス)
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

  // 推奨はEMS(あれば)
  const ems = shipping.find((s) => s.service === "EMS" && !s.oversize && s.feeUsd !== null);
  const shippingForDutyUsd =
    input.includeShippingInDutyBase && ems?.feeUsd ? ems.feeUsd : 0;

  const dutyBase = input.itemPriceUsd + shippingForDutyUsd;
  const mfnDuty = dutyBase * (category.mfnRate / 100);
  const reciprocalDuty = dutyBase * (country.reciprocalRate / 100);
  const totalDuty = mfnDuty + reciprocalDuty;

  // MPF
  let mpf = dutyBase * MPF_RATE;
  if (mpf < MPF_MIN_USD) mpf = MPF_MIN_USD;
  if (mpf > MPF_MAX_USD) mpf = MPF_MAX_USD;
  // 国際郵便 (EMS) は通常 MPF 加算なし。FedEx/DHL等の正式申告で課される
  // ここではユーザに見えるように郵便向けは「目安(非課税の場合あり)」と注釈
  // 簡易化: 通常MPFは表示はするがTotal上は加算する(慎重側)

  const notes: string[] = [];
  notes.push(
    "2025年8月29日でde minimis ($800免税枠) が全世界で廃止 → 全ての貨物が関税対象",
  );
  notes.push(
    `相互関税は2025年中も頻繁に変動しています (現在の代表値: ${country.name}=${country.reciprocalRate}%)`,
  );
  if (country.code === "MX" || country.code === "CA") {
    notes.push("USMCA原産品は通常無税。原産地証明があれば相互関税0%扱いになるケースあり");
  }
  if (category.code === "electronics" || category.code === "cameras") {
    notes.push("MFN税率は無税/低率だが、相互関税は別途課税される");
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
      mfnRate: category.mfnRate,
      reciprocalRate: country.reciprocalRate,
      totalRate: category.mfnRate + country.reciprocalRate,
      mfnDutyUsd: mfnDuty,
      reciprocalDutyUsd: reciprocalDuty,
      totalDutyUsd: totalDuty,
      mpfUsd: mpf,
      totalImportFeeUsd: totalDuty + mpf,
      countryName: country.name,
      categoryName: category.name,
      notes,
    },
    recommended,
  };
}
