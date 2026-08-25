import Link from "next/link";
import { NAV_LINKS } from "../lib/nav";
import { CatfishMark } from "./CatfishMark";
import { MobileNav } from "./MobileNav";

export function SiteHeader() {
  return (
    <header className="border-b border-neutral-200 bg-white">
      <div className="mx-auto flex h-14 max-w-5xl items-center px-4">
        <Link href="/" className="flex items-center gap-2 text-brand">
          <CatfishMark className="h-7 w-7" />
          <span className="text-lg font-extrabold tracking-tight">Ankardo</span>
        </Link>
        <nav className="ml-auto hidden items-center gap-5 sm:flex">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-bold text-neutral-700 hover:text-brand"
            >
              {link.label}
            </Link>
          ))}
        </nav>
        <MobileNav />
      </div>
    </header>
  );
}
