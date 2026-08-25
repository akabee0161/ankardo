"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { NAV_LINKS } from "../lib/nav";

const MENU_ID = "mobile-menu";

export function MobileNav() {
  const [open, setOpen] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const wasOpenRef = useRef(false);

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
      buttonRef.current?.focus();
    }
    wasOpenRef.current = open;
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
          <nav className="flex flex-col gap-7">
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
