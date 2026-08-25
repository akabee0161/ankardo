import type { Metadata } from "next";
import type { ReactNode } from "react";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ankardo",
  description: "子供向けインディーゲームカタログ Ankardo",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ja">
      <body className="flex min-h-screen flex-col bg-neutral-50 text-neutral-900">
        <SiteHeader />
        <div className="flex-1">{children}</div>
        <SiteFooter />
      </body>
    </html>
  );
}
