import { CalculatorForm } from "@/components/CalculatorForm";

export default function Page() {
  return (
    <main className="min-h-screen px-4 py-8 md:py-12">
      <div className="max-w-6xl mx-auto space-y-6">
        <header className="space-y-2">
          <h1 className="text-2xl md:text-3xl font-bold text-slate-100">
            eBay US 関税・送料 概算ツール
          </h1>
          <p className="text-sm text-slate-400">
            日本→米国向けの販売で、<span className="text-blue-300">生産国 × 商品カテゴリ × サイズ・重量</span>
            から関税と送料(EMS / eパケット / 船便)を概算します。
            2025年の相互関税 (Reciprocal Tariff) と de minimis 廃止に対応。
          </p>
        </header>
        <CalculatorForm />
        <footer className="text-xs text-slate-500 pt-4 border-t border-slate-800">
          税率データは 2025年後半時点の代表値です。実務では USTR / CBP の最新告示と日本郵便の料金表を必ずご確認ください。
        </footer>
      </div>
    </main>
  );
}
