// 計算ロジックの簡易チェック (npx tsx scripts/sanity-check.ts)
import { calculate } from "../lib/calculate";

const cases = [
  {
    name: "日本産 / 一般雑貨 / 1kg (相互関税撤廃後)",
    input: {
      itemPriceUsd: 100,
      originCountry: "JP" as const,
      category: "general" as const,
      actualWeightKg: 1.0,
      lengthCm: 30, widthCm: 20, heightCm: 10,
      jpyToUsd: 155,
      includeShippingInDutyBase: true,
      section232: false,
      shippingMode: "DIRECT" as const,
    },
  },
  {
    name: "中国産 / 電子機器 (Section 301対象)",
    input: {
      itemPriceUsd: 50,
      originCountry: "CN" as const,
      category: "electronics" as const,
      actualWeightKg: 0.5,
      lengthCm: 25, widthCm: 18, heightCm: 5,
      jpyToUsd: 155,
      includeShippingInDutyBase: true,
      section232: false,
      shippingMode: "DIRECT" as const,
    },
  },
  {
    name: "日本産 / カメラ / eIS発送",
    input: {
      itemPriceUsd: 800,
      originCountry: "JP" as const,
      category: "cameras" as const,
      actualWeightKg: 2.0,
      lengthCm: 35, widthCm: 25, heightCm: 20,
      jpyToUsd: 155,
      includeShippingInDutyBase: true,
      section232: false,
      shippingMode: "EIS" as const,
    },
  },
  {
    name: "日本産 / 自動車部品 (Section 232対象)",
    input: {
      itemPriceUsd: 200,
      originCountry: "JP" as const,
      category: "general" as const,
      actualWeightKg: 3.0,
      lengthCm: 40, widthCm: 30, heightCm: 20,
      jpyToUsd: 155,
      includeShippingInDutyBase: true,
      section232: true,
      shippingMode: "DIRECT" as const,
    },
  },
];

for (const c of cases) {
  const r = calculate(c.input);
  const d = r.duty;
  console.log("\n=== " + c.name + " ===");
  console.log(
    `  実効税率: ${d.totalRate.toFixed(1)}% = MFN ${d.mfnRate}% + S122 ${d.section122Rate}% + S301 ${d.section301Rate}% + S232 ${d.section232Rate}%`,
  );
  console.log(
    `  内訳: MFN $${d.mfnDutyUsd.toFixed(2)} / S122 $${d.section122Usd.toFixed(2)} / S301 $${d.section301Usd.toFixed(2)} / S232 $${d.section232Usd.toFixed(2)}`,
  );
  console.log(`  関税合計 $${d.totalDutyUsd.toFixed(2)} + MPF $${d.mpfUsd.toFixed(2)}`);
  for (const s of r.shipping) {
    console.log(
      `  ${s.service.padEnd(16)} 請求${s.chargeableWeightKg.toFixed(2)}kg → ${
        s.feeJpy != null ? "¥" + s.feeJpy.toLocaleString() : "(不可)"
      }${s.reason ? "  ⚠ " + s.reason : ""}`,
    );
  }
  if (r.recommended) {
    console.log(`  推奨: ${r.recommended.service} → Landed $${r.recommended.landedCostUsd.toFixed(2)}`);
  }
}
