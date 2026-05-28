"use client";

import { useMemo, useState } from "react";
import { COUNTRIES, CATEGORIES, type CountryCode, type CategoryCode } from "@/lib/tariff";
import { calculate, type CalcInput, type ShippingMode } from "@/lib/calculate";
import { ResultDisplay } from "./ResultDisplay";

const DEFAULT_INPUT: CalcInput = {
  itemPriceUsd: 100,
  originCountry: "JP",
  category: "general",
  actualWeightKg: 1.0,
  lengthCm: 30,
  widthCm: 20,
  heightCm: 10,
  jpyToUsd: 155,
  includeShippingInDutyBase: true,
  section232: false,
  shippingMode: "DIRECT",
};

function NumberInput({
  label,
  value,
  onChange,
  step,
  min,
  suffix,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  step?: number;
  min?: number;
  suffix?: string;
}) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="text-slate-300">{label}</span>
      <div className="flex items-center gap-2">
        <input
          type="number"
          className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100 focus:border-blue-400 focus:outline-none"
          value={Number.isFinite(value) ? value : 0}
          step={step ?? 1}
          min={min ?? 0}
          onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        />
        {suffix && <span className="text-slate-400 text-xs whitespace-nowrap">{suffix}</span>}
      </div>
    </label>
  );
}

export function CalculatorForm() {
  const [input, setInput] = useState<CalcInput>(DEFAULT_INPUT);
  const update = <K extends keyof CalcInput>(key: K, value: CalcInput[K]) =>
    setInput((prev) => ({ ...prev, [key]: value }));

  const result = useMemo(() => calculate(input), [input]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <section className="rounded-xl border border-slate-700 bg-slate-900/50 p-5 space-y-4">
        <h2 className="text-lg font-semibold text-slate-100">入力</h2>

        <div className="grid grid-cols-2 gap-3">
          <label className="flex flex-col gap-1 text-sm col-span-2">
            <span className="text-slate-300">生産国 (原産国 / eBay出品時に必須)</span>
            <select
              className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
              value={input.originCountry}
              onChange={(e) => update("originCountry", e.target.value as CountryCode)}
            >
              {COUNTRIES.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.name}
                  {c.code === "CN" ? " (Section 301 対象)" : ""}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-sm col-span-2">
            <span className="text-slate-300">商品カテゴリ</span>
            <select
              className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
              value={input.category}
              onChange={(e) => update("category", e.target.value as CategoryCode)}
            >
              {CATEGORIES.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.name} (MFN {c.mfnRate}%)
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-sm col-span-2">
            <span className="text-slate-300">発送方法</span>
            <select
              className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
              value={input.shippingMode}
              onChange={(e) => update("shippingMode", e.target.value as ShippingMode)}
            >
              <option value="DIRECT">直接発送 (EMS / DHL / FedEx)</option>
              <option value="EIS">eBay International Shipping (eIS / GSP)</option>
            </select>
          </label>

          <NumberInput label="商品代金" value={input.itemPriceUsd} onChange={(v) => update("itemPriceUsd", v)} step={1} suffix="USD" />
          <NumberInput label="為替" value={input.jpyToUsd} onChange={(v) => update("jpyToUsd", v)} step={0.1} suffix="円/USD" />
          <NumberInput label="実重量" value={input.actualWeightKg} onChange={(v) => update("actualWeightKg", v)} step={0.1} suffix="kg" />
          <div />
          <NumberInput label="長さ (L)" value={input.lengthCm} onChange={(v) => update("lengthCm", v)} step={1} suffix="cm" />
          <NumberInput label="横 (W)" value={input.widthCm} onChange={(v) => update("widthCm", v)} step={1} suffix="cm" />
          <NumberInput label="高 (H)" value={input.heightCm} onChange={(v) => update("heightCm", v)} step={1} suffix="cm" />

          <label className="col-span-2 flex items-center gap-2 text-sm mt-2">
            <input
              type="checkbox"
              checked={input.includeShippingInDutyBase}
              onChange={(e) => update("includeShippingInDutyBase", e.target.checked)}
            />
            <span className="text-slate-300">関税の課税ベースに送料を含める (航空便CIFが原則)</span>
          </label>

          <label className="col-span-2 flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={input.section232}
              onChange={(e) => update("section232", e.target.checked)}
            />
            <span className="text-slate-300">鉄鋼・アルミ・自動車部品である (Section 232 +25%)</span>
          </label>
        </div>
      </section>

      <ResultDisplay result={result} />
    </div>
  );
}
