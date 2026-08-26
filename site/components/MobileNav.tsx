"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { NAV_LINKS } from "../lib/nav";

const MENU_ID = "mobile-menu";

export function MobileNav() {
  const [open, setOpen] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const wasOpenRef = useRef(false);
  // 画面幅が sm 以上になったことでメニューを自動で閉じた場合は true。
  // このときボタン自体が sm:hidden で非表示になるため、フォーカスを
  // ボタンへ戻す代わりに、表示されているデスクトップナビ（SiteHeader.tsx
  // の #desktop-nav）の最初のリンクへフォーカスを移す。
  const closedByResizeRef = useRef(false);

  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  useEffect(() => {
    if (wasOpenRef.current && !open) {
      if (closedByResizeRef.current) {
        const firstDesktopLink = document.querySelector<HTMLAnchorElement>(
          "#desktop-nav a"
        );
        firstDesktopLink?.focus();
      } else {
        buttonRef.current?.focus();
      }
      closedByResizeRef.current = false;
    }
    wasOpenRef.current = open;
  }, [open]);

  useEffect(() => {
    if (!open) return;

    // 640px は Tailwind の sm ブレークポイント（SiteHeader.tsx / このファイルの
    // sm:hidden・sm:flex）と一致させる必要がある。ここを変更する場合は
    // クラス名側も合わせて更新すること。
    const mql = window.matchMedia("(min-width: 640px)");
    const closeIfDesktop = () => {
      if (mql.matches) {
        closedByResizeRef.current = true;
        setOpen(false);
      }
    };

    closeIfDesktop();
    mql.addEventListener("change", closeIfDesktop);

    return () => mql.removeEventListener("change", closeIfDesktop);
  }, [open]);

  return (
    <div className="ml-auto sm:hidden">
      <button
        ref={buttonRef}
        type="button"
        aria-expanded={open}
        aria-controls={MENU_ID}
        onClick={() => setOpen((current) => !current)}
        className="relative z-50 flex h-10 w-10 flex-col items-center justify-center gap-1.5"
      >
        <span className="sr-only">{open ? "メニューを閉じる" : "メニューを開く"}</span>
        <span
          aria-hidden="true"
          className={`block h-0.5 w-5 bg-neutral-800 transition ${
            open ? "translate-y-2 rotate-45" : ""
          }`}
        />
        <span
          aria-hidden="true"
          className={`block h-0.5 w-5 bg-neutral-800 transition ${open ? "opacity-0" : ""}`}
        />
        <span
          aria-hidden="true"
          className={`block h-0.5 w-5 bg-neutral-800 transition ${
            open ? "-translate-y-2 -rotate-45" : ""
          }`}
        />
      </button>

      {open && (
        <div
          id={MENU_ID}
          className="fixed inset-x-0 bottom-0 top-14 z-40 bg-white px-6 py-8"
        >
          <nav className="flex flex-col gap-7" aria-label="メインメニュー">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                className="text-xl font-bold text-neutral-900"
              >
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
      )}
    </div>
  );
}
