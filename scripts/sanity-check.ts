// 計算ロジックの簡易チェック (tsx で実行: npx tsx scripts/sanity-check.ts)
import { calculate } from "../lib/calculate";

const cases = [
  {
    name: "日本産 / 一般雑貨 / 1kg / 30x20x10",
    input: {
      itemPriceUsd: 100,
      originCountry: "JP" as const,
      category: "general" as const,
      actualWeightKg: 1.0,
      lengthCm: 30,
      widthCm: 20,
      heightCm: 10,
      jpyToUsd: 155,
      includeShippingInDutyBase: true,
    },
  },
  {
    name: "中国産 / 衣料品 / 0.5kg / 25x18x5",
    input: {
      itemPriceUsd: 50,
      originCountry: "CN" as const,
      category: "apparel" as const,
      actualWeightKg: 0.5,
      lengthCm: 25,
      widthCm: 18,
      heightCm: 5,
      jpyToUsd: 155,
      includeShippingInDutyBase: true,
    },
  },
  {
    name: "日本産 / カメラ / 2kg / 35x25x20",
    input: {
      itemPriceUsd: 800,
      originCountry: "JP" as const,
      category: "cameras" as const,
      actualWeightKg: 2.0,
      lengthCm: 35,
      widthCm: 25,
      heightCm: 20,
      jpyToUsd: 155,
      includeShippingInDutyBase: true,
    },
  },
  {
    name: "EMS上限超過テスト (35kg)",
    input: {
      itemPriceUsd: 200,
      originCountry: "JP" as const,
      category: "general" as const,
      actualWeightKg: 35.0,
      lengthCm: 60,
      widthCm: 40,
      heightCm: 40,
      jpyToUsd: 155,
      includeShippingInDutyBase: true,
    },
  },
];

for (const c of cases) {
  const r = calculate(c.input);
  console.log("\n=== " + c.name + " ===");
  console.log(
    `  関税: ${r.duty.totalRate.toFixed(1)}% = $${r.duty.totalDutyUsd.toFixed(2)} (MFN ${r.duty.mfnRate}% + 相互 ${r.duty.reciprocalRate}%)`,
  );
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
