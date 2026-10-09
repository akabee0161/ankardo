import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";
import { SITE_URL } from "../lib/site";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Ankardo",
    template: "%s | Ankardo",
  },
  description: "子供向けインディーゲームカタログ Ankardo",
  appleWebApp: {
    title: "Ankardo",
    statusBarStyle: "default",
  },
};

export const viewport: Viewport = {
  themeColor: "#1f3a5f",
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
