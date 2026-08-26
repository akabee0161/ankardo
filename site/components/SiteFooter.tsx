import Link from "next/link";
import { FOOTER_LINKS } from "../lib/nav";

export function SiteFooter() {
  return (
    <footer className="border-t border-neutral-200 bg-white">
      <div className="mx-auto max-w-5xl px-4 py-8">
        <nav className="flex flex-wrap gap-x-5 gap-y-2" aria-label="フッターメニュー">
          {FOOTER_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-bold text-neutral-700 hover:text-brand"
            >
              {link.label}
            </Link>
          ))}
        </nav>
        <p className="mt-4 text-xs leading-relaxed text-neutral-500">
          年齢・ジャンルで選べる、子供向けインディーゲームカタログ。広告・課金・アカウント登録はありません。
        </p>
        <p className="mt-2 text-xs text-neutral-500">© 2026 Ankardo</p>
      </div>
    </footer>
  );
}
