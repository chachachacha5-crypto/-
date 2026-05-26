// 日本→米国の国際郵便代表値テーブル (2025年改定後の概算)
// 出典: 日本郵便 国際郵便料金表 (米国: 第2地帯) の代表値
// 注: 正確な料金は日本郵便公式 (https://www.post.japanpost.jp/) を要確認

export type ShippingService = "EMS" | "EPACKET" | "SAL_PARCEL" | "SURFACE_PARCEL";

export interface ShippingOption {
  service: ShippingService;
  label: string;
  description: string;
  // [重量(kg), 料金(円)] の階段表 (重量超過分は計算で外挿)
  rateTable: Array<[number, number]>;
  maxWeightKg: number;
  // 容積重量を使うか (大型化対策)
  useVolumetric: boolean;
  // 容積重量の換算係数 (cm^3 / divisor = kg)
  volumetricDivisor: number;
  // 追跡・補償の有無 (UI表示用)
  trackable: boolean;
}

// EMS to USA (Zone 2) 2025年6月改定後の代表値
const EMS_US_RATES: Array<[number, number]> = [
  [0.5, 3900],
  [0.6, 4180],
  [0.7, 4460],
  [0.8, 4740],
  [0.9, 5020],
  [1.0, 5300],
  [1.25, 5975],
  [1.5, 6650],
  [1.75, 7325],
  [2.0, 8000],
  [2.5, 9350],
  [3.0, 10650],
  [3.5, 11925],
  [4.0, 13200],
  [4.5, 14450],
  [5.0, 15700],
  [5.5, 16975],
  [6.0, 18250],
  [7.0, 20800],
  [8.0, 23350],
  [9.0, 25900],
  [10.0, 28450],
  [12.0, 33550],
  [15.0, 41200],
  [17.5, 47475],
  [20.0, 53950],
  [22.5, 60325],
  [25.0, 66700],
  [27.5, 73075],
  [30.0, 79450],
];

// 国際eパケット 米国向け (2kgまで)
const EPACKET_US_RATES: Array<[number, number]> = [
  [0.1, 1880],
  [0.2, 2280],
  [0.3, 2680],
  [0.4, 3080],
  [0.5, 3480],
  [0.6, 3880],
  [0.7, 4280],
  [0.8, 4680],
  [0.9, 5080],
  [1.0, 5480],
  [1.25, 6480],
  [1.5, 7480],
  [1.75, 8480],
  [2.0, 9480],
];

// 船便小包 (SURFACE) 米国向け 概算
const SURFACE_US_RATES: Array<[number, number]> = [
  [1.0, 2400],
  [2.0, 3450],
  [3.0, 4500],
  [4.0, 5550],
  [5.0, 6600],
  [6.0, 7650],
  [7.0, 8700],
  [8.0, 9750],
  [9.0, 10800],
  [10.0, 11850],
  [15.0, 17100],
  [20.0, 22350],
];

export const SHIPPING_OPTIONS: ShippingOption[] = [
  {
    service: "EMS",
    label: "EMS (国際スピード郵便)",
    description: "追跡・補償あり / 3-7日。eBayでGSPなしで送る場合の標準",
    rateTable: EMS_US_RATES,
    maxWeightKg: 30,
    useVolumetric: true,
    volumetricDivisor: 6000,
    trackable: true,
  },
  {
    service: "EPACKET",
    label: "国際eパケット",
    description: "追跡あり / 7-14日 / 2kgまでの軽量品向け",
    rateTable: EPACKET_US_RATES,
    maxWeightKg: 2,
    useVolumetric: false,
    volumetricDivisor: 6000,
    trackable: true,
  },
  {
    service: "SURFACE_PARCEL",
    label: "船便小包",
    description: "追跡なし(オプション可) / 1-3ヶ月 / 重量物向け最安",
    rateTable: SURFACE_US_RATES,
    maxWeightKg: 30,
    useVolumetric: false,
    volumetricDivisor: 6000,
    trackable: false,
  },
];

// 容積重量 = L * W * H / divisor (cm基準)
export function volumetricWeightKg(
  lengthCm: number,
  widthCm: number,
  heightCm: number,
  divisor: number,
): number {
  return (lengthCm * widthCm * heightCm) / divisor;
}

// 階段料金表から該当料金を引く
// 表の中の最小重量以上 かつ <= 重量 の中で最大の段に該当
export function lookupRate(
  weightKg: number,
  rateTable: Array<[number, number]>,
): number | null {
  // 最後の段を超える場合は null (上限超過)
  const lastWeight = rateTable[rateTable.length - 1][0];
  if (weightKg > lastWeight) return null;
  for (const [w, fee] of rateTable) {
    if (weightKg <= w) return fee;
  }
  return null;
}

export interface ShippingCalc {
  service: ShippingService;
  label: string;
  description: string;
  actualWeightKg: number;
  volumetricWeightKg: number;
  chargeableWeightKg: number;
  feeJpy: number | null;
  feeUsd: number | null;
  oversize: boolean;
  reason?: string;
}

export function calculateShipping(
  opt: ShippingOption,
  actualWeightKg: number,
  lengthCm: number,
  widthCm: number,
  heightCm: number,
  jpyToUsd: number,
): ShippingCalc {
  const vol = volumetricWeightKg(lengthCm, widthCm, heightCm, opt.volumetricDivisor);
  const chargeable = opt.useVolumetric ? Math.max(actualWeightKg, vol) : actualWeightKg;
  const oversize = chargeable > opt.maxWeightKg;
  const fee = oversize ? null : lookupRate(chargeable, opt.rateTable);

  // EMSのサイズ規制: 1辺の最長 1.5m, 長さ + (横+高)*2 = 3m まで
  let reason: string | undefined;
  if (oversize) {
    reason = `${opt.label}の上限 ${opt.maxWeightKg}kg を超過 (請求重量 ${chargeable.toFixed(2)}kg)`;
  }
  if (opt.service === "EMS") {
    const longest = Math.max(lengthCm, widthCm, heightCm);
    const others = [lengthCm, widthCm, heightCm].sort((a, b) => b - a);
    const girth = others[0] + 2 * (others[1] + others[2]);
    if (longest > 150) reason = `1辺が150cmを超過 (${longest}cm)`;
    else if (girth > 300) reason = `長さ+(横+高)*2 が300cmを超過 (${girth.toFixed(0)}cm)`;
  }

  return {
    service: opt.service,
    label: opt.label,
    description: opt.description,
    actualWeightKg,
    volumetricWeightKg: vol,
    chargeableWeightKg: chargeable,
    feeJpy: fee,
    feeUsd: fee !== null ? fee / jpyToUsd : null,
    oversize: oversize || !!reason,
    reason,
  };
}
