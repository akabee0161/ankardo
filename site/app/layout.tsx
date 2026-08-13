import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ankardo",
  description: "子供向けインディーゲームカタログ Ankardo",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ja">
      <body className="bg-neutral-50 text-neutral-900">{children}</body>
    </html>
  );
}
