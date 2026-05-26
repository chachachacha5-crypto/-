import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "eBay US 関税・送料 簡易計算 (日本→米国)",
  description:
    "生産国とサイズ・重量から、米国向けeBay販売時の関税(2025年相互関税対応)と送料(EMS他)を概算します。",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
