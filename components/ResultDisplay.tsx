import type { CalcResult } from "@/lib/calculate";

function usd(v: number | null | undefined): string {
  if (v == null || !Number.isFinite(v)) return "—";
  return `$${v.toFixed(2)}`;
}

function jpy(v: number | null | undefined): string {
  if (v == null || !Number.isFinite(v)) return "—";
  return `¥${Math.round(v).toLocaleString("ja-JP")}`;
}

export function ResultDisplay({ result }: { result: CalcResult }) {
  const { duty, shipping, recommended, input } = result;

  return (
    <section className="rounded-xl border border-slate-700 bg-slate-900/50 p-5 space-y-5">
      <h2 className="text-lg font-semibold text-slate-100">計算結果</h2>

      <div className="rounded-lg border border-slate-700 bg-slate-950/40 p-4 space-y-2">
        <h3 className="text-sm font-semibold text-blue-400">関税 (米国輸入時 / 2026年5月構造)</h3>
        <div className="text-xs text-slate-400 flex flex-wrap gap-1">
          <span className="px-2 py-0.5 rounded-full bg-slate-800">{duty.countryName}</span>
          <span className="px-2 py-0.5 rounded-full bg-slate-800">{duty.categoryName}</span>
          {duty.isChinaOrigin && (
            <span className="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-200">Section 301</span>
          )}
          {duty.section232Rate > 0 && (
            <span className="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-200">Section 232</span>
          )}
        </div>
        <table className="w-full text-sm">
          <tbody>
            <Row label="商品代金" value={usd(duty.itemPriceUsd)} />
            <Row
              label={`課税対象送料 (${input.includeShippingInDutyBase ? "含む" : "含まない"})`}
              value={usd(duty.shippingForDutyUsd)}
            />
            <Row label="課税ベース (CIF)" value={usd(duty.dutyBaseUsd)} bold />
            <Row label={`① MFN通常関税 (${duty.mfnRate}%)`} value={usd(duty.mfnDutyUsd)} />
            <Row
              label={`② Section 122 一律 (${duty.section122Rate}%) ※7月頃失効予定`}
              value={usd(duty.section122Usd)}
            />
            <Row
              label={`③ Section 301 中国製のみ (${duty.section301Rate}%)`}
              value={usd(duty.section301Usd)}
              dim={duty.section301Rate === 0}
            />
            <Row
              label={`④ Section 232 鉄鋼/アルミ/自動車 (${duty.section232Rate}%)`}
              value={usd(duty.section232Usd)}
              dim={duty.section232Rate === 0}
            />
            <Row
              label={`関税合計 (実効 ${duty.totalRate.toFixed(1)}%)`}
              value={usd(duty.totalDutyUsd)}
              accent
            />
            <Row label="MPF 処理手数料 (目安)" value={usd(duty.mpfUsd)} />
            <Row label="輸入諸経費合計" value={usd(duty.totalImportFeeUsd)} bold />
          </tbody>
        </table>
      </div>

      <div className="rounded-lg border border-slate-700 bg-slate-950/40 p-4 space-y-2">
        <h3 className="text-sm font-semibold text-blue-400">送料 (日本→米国)</h3>
        <table className="w-full text-sm">
          <thead className="text-xs text-slate-400">
            <tr className="border-b border-slate-700">
              <th className="text-left py-1">サービス</th>
              <th className="text-right py-1">請求重量</th>
              <th className="text-right py-1">JPY</th>
              <th className="text-right py-1">USD</th>
            </tr>
          </thead>
          <tbody>
            {shipping.map((s) => (
              <tr key={s.service} className="border-b border-slate-800 last:border-0">
                <td className="py-2 pr-2">
                  <div className="text-slate-100">{s.label}</div>
                  <div className="text-xs text-slate-400">{s.description}</div>
                  {s.reason && (
                    <div className="text-xs text-amber-400 mt-1">⚠ {s.reason}</div>
                  )}
                </td>
                <td className="text-right text-slate-300">
                  {s.chargeableWeightKg.toFixed(2)} kg
                  <div className="text-xs text-slate-500">
                    実{s.actualWeightKg.toFixed(2)} / 容積{s.volumetricWeightKg.toFixed(2)}
                  </div>
                </td>
                <td className="text-right text-slate-200">{jpy(s.feeJpy)}</td>
                <td className="text-right text-slate-200">{usd(s.feeUsd)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {recommended ? (
        <div className="rounded-lg border border-blue-500/40 bg-blue-500/10 p-4 space-y-1">
          <h3 className="text-sm font-semibold text-blue-300">
            推奨: {recommended.service} で発送した場合の総コスト
          </h3>
          <div className="text-xs text-slate-300">
            送料 {jpy(recommended.shippingJpy)} ({usd(recommended.shippingUsd)})
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-2">
            Landed Cost: {usd(recommended.landedCostUsd)}
          </div>
          <div className="text-xs text-slate-400">
            = 商品代金 + 関税 + 送料 + MPF (買い手が支払う総額の目安)
          </div>
        </div>
      ) : (
        <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-4 text-sm text-amber-200">
          EMSで発送できないサイズ・重量です。FedEx / DHL等の他キャリアを検討してください。
        </div>
      )}

      <div className="rounded-lg border border-slate-700 bg-slate-950/40 p-4 space-y-1">
        <h3 className="text-xs font-semibold text-slate-400">⚠ 注意事項 / 最新情報</h3>
        <ul className="text-xs text-slate-400 list-disc pl-5 space-y-1">
          {duty.notes.map((n, i) => (
            <li key={i}>{n}</li>
          ))}
          <li>
            本ツールは概算です。正確な関税は HTS コードと CBP / USTR の最新告示、送料は日本郵便公式の最新料金表を必ずご確認ください。
          </li>
        </ul>
      </div>
    </section>
  );
}

function Row({
  label,
  value,
  bold,
  accent,
  dim,
}: {
  label: string;
  value: string;
  bold?: boolean;
  accent?: boolean;
  dim?: boolean;
}) {
  return (
    <tr className="border-b border-slate-800 last:border-0">
      <td
        className={`py-1 ${
          dim ? "text-slate-600" : bold ? "font-semibold text-slate-100" : "text-slate-300"
        }`}
      >
        {label}
      </td>
      <td
        className={`py-1 text-right tabular-nums ${
          dim
            ? "text-slate-600"
            : accent
              ? "text-blue-300 font-semibold"
              : bold
                ? "text-slate-100 font-semibold"
                : "text-slate-200"
        }`}
      >
        {value}
      </td>
    </tr>
  );
}
