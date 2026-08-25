# 共通ヘッダー/フッターとブランドアセット 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** カタログサイトに共通ヘッダー/フッター、ブランドアセット（ナマズのシンボル、ワードマーク、ファビコン）、`/about` ページ、ページ別のタイトルを追加し、全ページからトップへ戻れるようにする。

**Architecture:** `app/layout.tsx` に `SiteHeader` / `SiteFooter` を組み込む。リンク定義は `lib/nav.ts` に集約し、`lib/genres.ts` / `lib/devices.ts` と同じ「データを1箇所に置く」既存パターンに従う。シンボルは `components/CatfishMark.tsx` の SVG コンポーネント1点で、色は `currentColor` にして呼び出し側で決める。モバイルのメニューだけがサイト初のクライアントコンポーネント（`MobileNav`）になり、ここにのみテストを書く。

**Tech Stack:** Next.js 16（`output: "export"`）、React 19、TypeScript（`strict: false`）、Tailwind CSS 4、Vitest 4（`jsdom` と `@testing-library/react` を本計画で追加）

**Spec:** `docs/superpowers/specs/2026-08-25-site-header-footer-and-brand-design.md`

## Global Constraints

- 作業ディレクトリは `site/`。npm コマンドはすべて `site/` で実行する
- `site/tsconfig.json` は `"strict": false`。既存設定を変更しない
- Webフォントは読み込まない。テキストはシステムフォントのみ
- ブランド色は藍 `#1f3a5f`。`app/globals.css` の `@theme` に `--color-brand` として定義し、Tailwind のユーティリティ（`text-brand` / `bg-brand`）で使う
- 既存ボタンの `bg-neutral-900` は変更しない（spec の「未決事項」）
- モバイルとPCの切り替えは 640px（Tailwind の `sm`）
- テストでは `describe` / `it` / `expect` を `vitest` から明示的に import する。`globals: true` は使わない
- テストファイルはテスト対象と同じディレクトリに置く（`components/MobileNav.test.tsx`）
- 表示のみのコンポーネントにはテストを書かない。`MobileNav` だけが例外
- 表示ラベル中の括弧は全角（`（横向き）`）を使う
- コミットは Conventional Commits 形式（`feat:` / `fix:` / `test:` / `docs:` / `chore:`）
- 問い合わせフォーム: `https://docs.google.com/forms/d/e/1FAIpQLScr21ghCZcOtjrM7LM7QvcnM7hYjWjGE45Gu1TroNXlrFqFPg/viewform`
- 運営者の GitHub: `https://github.com/akabee0161`
- 各タスクの検証コマンドは `npm test` と `npm run build` の2つ

---

## File Structure

| ファイル | 責務 | 変更種別 |
|---|---|---|
| `site/components/CatfishMark.tsx` | ナマズのシンボル（SVG、`currentColor`） | 新規 |
| `site/app/globals.css` | ブランド色 `--color-brand` の定義 | 変更 |
| `site/app/icon.svg` | ファビコン（白地の角丸四角＋藍のナマズ） | 新規 |
| `site/app/apple-icon.png` | iOS ホーム画面用アイコン 180×180 | 新規（条件付き） |
| `site/lib/nav.ts` | ヘッダー/フッターのリンク定義 | 新規 |
| `site/components/SiteHeader.tsx` | 共通ヘッダー | 新規 |
| `site/components/MobileNav.tsx` | 640px未満のハンバーガーと全画面メニュー | 新規 |
| `site/components/MobileNav.test.tsx` | `MobileNav` の振る舞いのテスト | 新規 |
| `site/components/SiteFooter.tsx` | 共通フッター | 新規 |
| `site/app/layout.tsx` | ヘッダー/フッターの組み込み、タイトルの template | 変更 |
| `site/app/about/page.tsx` | 「このサイトについて」ページ | 新規 |
| `site/app/games/page.tsx` | ページタイトルの追加 | 変更 |
| `site/app/games/[slug]/page.tsx` | `generateMetadata` の追加 | 変更 |
| `site/app/not-found.tsx` | ページタイトルの追加 | 変更 |
| `site/package.json` | `jsdom` / `@testing-library/react` の追加 | 変更 |
| `README.md` | 正典の更新 | 変更 |

---

### Task 1: ブランドアセット（シンボルとファビコン）

**Files:**
- Create: `site/components/CatfishMark.tsx`
- Create: `site/app/icon.svg`
- Create: `site/app/apple-icon.png`（条件付き。Step 6 参照）
- Modify: `site/app/globals.css`

**Interfaces:**
- Consumes: なし
- Produces: `CatfishMark({ className }: { className?: string })` — `viewBox="0 0 64 64"` の `<svg>` を返す。塗りは `currentColor`。サイズは呼び出し側が `className`（例: `h-7 w-7`）で決める

- [ ] **Step 1: ブランド色を定義する**

`site/app/globals.css` の `@theme` ブロックに1行足す。既存のジャンルカラーの下に置く。

```css
@theme {
  --color-genre-action: #ff7a45;
  --color-genre-puzzle: #2f80ed;
  --color-genre-adventure: #43a047;
  --color-genre-rhythm: #ec407a;
  --color-genre-racing: #ffc107;
  --color-genre-shooting: #7c4dff;
  --color-genre-simulation: #26c6da;
  --color-brand: #1f3a5f;
}
```

- [ ] **Step 2: シンボルのコンポーネントを作る**

`site/components/CatfishMark.tsx` を新規作成する。パスの数値は spec で確定したもの。**変更しないこと。**

```tsx
export function CatfishMark({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" className={className} aria-hidden="true" focusable="false">
      <g fill="none" stroke="currentColor" strokeWidth="3.2" strokeLinecap="round">
        <path d="M23 45 Q16 55 9 55" />
        <path d="M41 45 Q48 55 55 55" />
      </g>
      <path
        d="M37 28.5 C45.2 25.2 48.1 22.6 50.5 17 L51.8 19.2 C52.4 24.8 49.9 28.7 45.5 33 Z"
        fill="currentColor"
      />
      <ellipse
        cx="53.3"
        cy="13"
        rx="7"
        ry="4.6"
        transform="rotate(-66.8 53.3 13)"
        fill="currentColor"
      />
      <path d="M15 39 C 8 40 4 46 5 53 C 11 51 16 47 19 43 Z" fill="currentColor" />
      <path d="M49 39 C 56 40 60 46 59 53 C 53 51 48 47 45 43 Z" fill="currentColor" />
      <ellipse cx="32" cy="34" rx="20" ry="14" fill="currentColor" />
      <path
        d="M23.5 40.5 Q32 37 40.5 40.5"
        fill="none"
        stroke="#fff"
        strokeWidth="2.8"
        strokeLinecap="round"
      />
      <circle cx="24" cy="29" r="3.4" fill="#fff" />
      <circle cx="40" cy="29" r="3.4" fill="#fff" />
      <circle cx="24" cy="29" r="1.7" fill="currentColor" />
      <circle cx="40" cy="29" r="1.7" fill="currentColor" />
    </svg>
  );
}
```

`aria-hidden="true"` にするのは、この SVG が常にワードマークのテキスト「Ankardo」と並んで置かれ、リンクの読み上げ名はテキスト側が担うため。

- [ ] **Step 3: ファビコンを作る**

`site/app/icon.svg` を新規作成する。白地の角丸四角に藍のナマズを載せる。`currentColor` は使えないので色を直接書く。中央で 0.84 倍に縮めて、角丸に対する余白を作る。

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <rect width="64" height="64" rx="14" fill="#ffffff"/>
  <g transform="translate(32 32) scale(0.84) translate(-32 -32)">
    <g fill="none" stroke="#1f3a5f" stroke-width="3.2" stroke-linecap="round">
      <path d="M23 45 Q16 55 9 55"/>
      <path d="M41 45 Q48 55 55 55"/>
    </g>
    <path d="M37 28.5 C45.2 25.2 48.1 22.6 50.5 17 L51.8 19.2 C52.4 24.8 49.9 28.7 45.5 33 Z" fill="#1f3a5f"/>
    <ellipse cx="53.3" cy="13" rx="7" ry="4.6" transform="rotate(-66.8 53.3 13)" fill="#1f3a5f"/>
    <path d="M15 39 C 8 40 4 46 5 53 C 11 51 16 47 19 43 Z" fill="#1f3a5f"/>
    <path d="M49 39 C 56 40 60 46 59 53 C 53 51 48 47 45 43 Z" fill="#1f3a5f"/>
    <ellipse cx="32" cy="34" rx="20" ry="14" fill="#1f3a5f"/>
    <path d="M23.5 40.5 Q32 37 40.5 40.5" fill="none" stroke="#ffffff" stroke-width="2.8" stroke-linecap="round"/>
    <circle cx="24" cy="29" r="3.4" fill="#ffffff"/>
    <circle cx="40" cy="29" r="3.4" fill="#ffffff"/>
    <circle cx="24" cy="29" r="1.7" fill="#1f3a5f"/>
    <circle cx="40" cy="29" r="1.7" fill="#1f3a5f"/>
  </g>
</svg>
```

- [ ] **Step 4: ビルドしてファビコンが出力されることを確認する**

```bash
npm run build
grep -o 'rel="icon"[^>]*' out/index.html
ls out/icon.svg
```

期待: `rel="icon"` を含む `<link>` が出力され、`out/icon.svg` が存在する。出力されない場合は `app/icon.svg` の配置場所（`app/` 直下であること）を確認する。

- [ ] **Step 5: iOS 用 PNG のラスタライズを試す**

```bash
convert -background none app/icon.svg -resize 180x180 app/apple-icon.png
```

- [ ] **Step 6: PNG の描画を目視で確認し、採否を決める**

生成した `site/app/apple-icon.png` を画像として開いて確認する。判断基準は次の1点のみ。

- **尾ビレ（`rotate(-66.8 …)` を掛けた楕円）が正しい角度・位置で描かれているか。**

正しく描けていれば採用してそのまま次へ進む。崩れていた場合（ImageMagick の内蔵 SVG レンダラーは `transform` の解釈が不完全なことがある）は、**`app/apple-icon.png` を削除して次へ進む。** 追加のラスタライズ手段（ヘッドレスブラウザの導入など）は本計画では行わない。iOS のホーム画面追加時にアイコンがページのスクリーンショットになるだけで、サイトの利用には影響しないため。この場合は Step 8 のコミットメッセージから `apple-icon.png` を外し、`README.md` にも記載しない。

```bash
rm -f app/apple-icon.png   # 崩れていた場合のみ
```

- [ ] **Step 7: テストとビルドが通ることを確認する**

```bash
npm test
npm run build
```

期待: テスト19件がパス、ビルド成功。

- [ ] **Step 8: コミット**

```bash
git add site/components/CatfishMark.tsx site/app/icon.svg site/app/globals.css
git add site/app/apple-icon.png   # Step 6 で採用した場合のみ
git commit -m "feat(site): ブランドのシンボルとファビコンを追加"
```

---

### Task 2: リンク定義と共通ヘッダー

**Files:**
- Create: `site/lib/nav.ts`
- Create: `site/components/SiteHeader.tsx`
- Modify: `site/app/layout.tsx`

**Interfaces:**
- Consumes: `CatfishMark({ className })`（Task 1）
- Produces:
  - `type NavLink = { href: string; label: string }`
  - `NAV_LINKS: NavLink[]` — ヘッダーに出すリンク（`/games`、`/about`）
  - `FOOTER_LINKS: NavLink[]` — フッターに出すリンク（`/` と `NAV_LINKS`）
  - `SiteHeader()` — 引数なし

- [ ] **Step 1: リンク定義を作る**

`site/lib/nav.ts` を新規作成する。

```ts
export type NavLink = {
  href: string;
  label: string;
};

export const NAV_LINKS: NavLink[] = [
  { href: "/games", label: "ゲーム一覧" },
  { href: "/about", label: "このサイトについて" },
];

export const FOOTER_LINKS: NavLink[] = [
  { href: "/", label: "トップ" },
  ...NAV_LINKS,
];
```

- [ ] **Step 2: ヘッダーを作る**

`site/components/SiteHeader.tsx` を新規作成する。この時点ではモバイル用メニューをまだ持たない（Task 3 で足す）。

```tsx
import Link from "next/link";
import { NAV_LINKS } from "../lib/nav";
import { CatfishMark } from "./CatfishMark";

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
      </div>
    </header>
  );
}
```

- [ ] **Step 3: レイアウトに組み込む**

`site/app/layout.tsx` を次の内容に置き換える。フッターは Task 4 で足すため、この時点ではヘッダーのみ。

```tsx
import type { Metadata } from "next";
import type { ReactNode } from "react";
import { SiteHeader } from "../components/SiteHeader";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ankardo",
  description: "子供向けインディーゲームカタログ Ankardo",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ja">
      <body className="bg-neutral-50 text-neutral-900">
        <SiteHeader />
        {children}
      </body>
    </html>
  );
}
```

- [ ] **Step 4: ビルドしてヘッダーが全ページに出ることを確認する**

```bash
npm run build
grep -c "Ankardo" out/games/index.html out/games/rungame-sample/index.html out/index.html
```

期待: 3ファイルとも1以上。ヘッダーのワードマークが各ページに入っている。

- [ ] **Step 5: 目視確認**

```bash
npm run dev
```

ブラウザで `http://localhost:3000/games` を開き、次を確認する。

- 左上にナマズのマークと「Ankardo」が藍色で表示される
- 右に「ゲーム一覧」「このサイトについて」が並ぶ（`/about` はまだ 404 でよい）
- ワードマークをクリックするとトップへ戻る
- ウィンドウ幅を 640px 未満にすると、リンクが消えてワードマークだけになる（Task 3 で解消する）

確認できたら `Ctrl+C` で開発サーバーを止める。

- [ ] **Step 6: コミット**

```bash
git add site/lib/nav.ts site/components/SiteHeader.tsx site/app/layout.tsx
git commit -m "feat(site): 共通ヘッダーを追加"
```

---

### Task 3: モバイルのメニュー

**Files:**
- Create: `site/components/MobileNav.tsx`
- Create: `site/components/MobileNav.test.tsx`
- Modify: `site/components/SiteHeader.tsx`
- Modify: `site/package.json`

**Interfaces:**
- Consumes: `NAV_LINKS`（Task 2）
- Produces: `MobileNav()` — 引数なし。640px未満でのみ表示される。開くボタンのアクセシブルネームは「メニューを開く」、開いている間は「メニューを閉じる」

- [ ] **Step 1: テスト用の依存を入れる**

```bash
npm install -D jsdom @testing-library/react @testing-library/dom
```

- [ ] **Step 2: 失敗するテストを書く**

`site/components/MobileNav.test.tsx` を新規作成する。1行目の docblock でこのファイルだけ `jsdom` 環境にする（他のテストは `node` のまま）。

```tsx
/**
 * @vitest-environment jsdom
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MobileNav } from "./MobileNav";

// next/link はクリック時に App Router のコンテキストを要求する。
// テストでは素の <a> に差し替えて、コンテキストなしでもクリックできるようにする。
vi.mock("next/link", () => ({
  default: ({ children, ...props }) => <a {...props}>{children}</a>,
}));

afterEach(() => {
  cleanup();
  document.body.style.overflow = "";
});

describe("MobileNav", () => {
  it("初期状態ではメニューが閉じている", () => {
    render(<MobileNav />);

    const button = screen.getByRole("button", { name: "メニューを開く" });
    expect(button.getAttribute("aria-expanded")).toBe("false");
    expect(screen.queryByRole("link", { name: "ゲーム一覧" })).toBeNull();
  });

  it("ボタンを押すとメニューが開く", () => {
    render(<MobileNav />);

    fireEvent.click(screen.getByRole("button", { name: "メニューを開く" }));

    expect(screen.getByRole("link", { name: "ゲーム一覧" })).not.toBeNull();
    expect(screen.getByRole("link", { name: "このサイトについて" })).not.toBeNull();
    expect(
      screen.getByRole("button", { name: "メニューを閉じる" }).getAttribute("aria-expanded")
    ).toBe("true");
  });

  it("開いている間は背後のスクロールを止める", () => {
    render(<MobileNav />);

    fireEvent.click(screen.getByRole("button", { name: "メニューを開く" }));
    expect(document.body.style.overflow).toBe("hidden");

    fireEvent.click(screen.getByRole("button", { name: "メニューを閉じる" }));
    expect(document.body.style.overflow).toBe("");
  });

  it("Escキーで閉じる", () => {
    render(<MobileNav />);

    fireEvent.click(screen.getByRole("button", { name: "メニューを開く" }));
    fireEvent.keyDown(document, { key: "Escape" });

    expect(screen.queryByRole("link", { name: "ゲーム一覧" })).toBeNull();
  });

  it("閉じたときフォーカスがボタンに戻る", () => {
    render(<MobileNav />);

    const button = screen.getByRole("button", { name: "メニューを開く" });
    fireEvent.click(button);
    fireEvent.keyDown(document, { key: "Escape" });

    expect(document.activeElement).toBe(
      screen.getByRole("button", { name: "メニューを開く" })
    );
  });

  it("メニュー内のリンクを押すと閉じる", () => {
    render(<MobileNav />);

    fireEvent.click(screen.getByRole("button", { name: "メニューを開く" }));
    fireEvent.click(screen.getByRole("link", { name: "ゲーム一覧" }));

    expect(screen.queryByRole("link", { name: "ゲーム一覧" })).toBeNull();
  });

  it("aria-controls がメニューの id と一致する", () => {
    render(<MobileNav />);

    const button = screen.getByRole("button", { name: "メニューを開く" });
    const controls = button.getAttribute("aria-controls");
    fireEvent.click(button);

    expect(document.getElementById(controls)).not.toBeNull();
  });
});
```

- [ ] **Step 3: テストを実行して失敗することを確認する**

```bash
npm test
```

期待: `MobileNav.test.tsx` が `Failed to resolve import "./MobileNav"` で失敗する。既存の `games.test.ts` 19件はパスしたまま。

**JSX のトランスパイルでエラーが出た場合**（`Unexpected token <` など）は、`@vitejs/plugin-react` を追加して `site/vitest.config.ts` を作る。

```bash
npm install -D @vitejs/plugin-react
```

```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
});
```

- [ ] **Step 4: `MobileNav` を実装する**

`site/components/MobileNav.tsx` を新規作成する。

```tsx
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
```

- [ ] **Step 5: テストを実行して通ることを確認する**

```bash
npm test
```

期待: 26件すべてパス（既存19件＋新規7件）。

jsdom が `Not implemented: navigation` を警告することがあるが、リンクのクリックに対する jsdom の既知の制限で、テストの成否には影響しない。無視してよい。

- [ ] **Step 6: ヘッダーに組み込む**

`site/components/SiteHeader.tsx` を次の内容に置き換える。`MobileNav` の import と、`<nav>` の後ろへの配置を足しただけ。

```tsx
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
```

- [ ] **Step 7: ビルドと目視確認**

```bash
npm run build
npm run dev
```

ブラウザの開発者ツールで幅を 375px にし、`http://localhost:3000/games` で次を確認する。

- 右上にハンバーガーが出る
- 押すとヘッダー下から画面下端までが白く覆われ、リンクが縦に大きく並ぶ
- 開いている間、背後のページをスクロールできない
- Esc キーで閉じ、ハンバーガーにフォーカスが戻る
- 幅を 640px 以上にするとハンバーガーが消え、リンクが横に並ぶ

確認できたら `Ctrl+C` で止める。

- [ ] **Step 8: コミット**

```bash
git add site/components/MobileNav.tsx site/components/MobileNav.test.tsx site/components/SiteHeader.tsx site/package.json site/package-lock.json
git add site/vitest.config.ts   # Step 3 で作った場合のみ
git commit -m "feat(site): モバイル用のメニューを追加"
```

---

### Task 4: 共通フッター

**Files:**
- Create: `site/components/SiteFooter.tsx`
- Modify: `site/app/layout.tsx`

**Interfaces:**
- Consumes: `FOOTER_LINKS`（Task 2）
- Produces: `SiteFooter()` — 引数なし

- [ ] **Step 1: フッターを作る**

`site/components/SiteFooter.tsx` を新規作成する。

```tsx
import Link from "next/link";
import { FOOTER_LINKS } from "../lib/nav";

export function SiteFooter() {
  return (
    <footer className="border-t border-neutral-200 bg-white">
      <div className="mx-auto max-w-5xl px-4 py-8">
        <nav className="flex flex-wrap gap-x-5 gap-y-2">
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
```

- [ ] **Step 2: レイアウトに組み込み、フッターを最下部へ送る**

`site/app/layout.tsx` を次の内容に置き換える。

```tsx
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
```

`flex-1` を持つ `<div>` で children を包むのは、内容が短いページ（404 など）でもフッターが画面下に張り付くようにするため。

- [ ] **Step 3: ビルドと目視確認**

```bash
npm run build
npm run dev
```

`http://localhost:3000/` と、内容の短い `http://localhost:3000/存在しないページ/` を開き、次を確認する。

- フッターにリンク3本、説明1行、コピーライトが出る
- 内容が短いページでもフッターが画面の下端に位置し、途中で浮かない

確認できたら `Ctrl+C` で止める。

- [ ] **Step 4: テストとビルドが通ることを確認する**

```bash
npm test
npm run build
```

期待: 26件パス、ビルド成功。

- [ ] **Step 5: コミット**

```bash
git add site/components/SiteFooter.tsx site/app/layout.tsx
git commit -m "feat(site): 共通フッターを追加"
```

---

### Task 5: 「このサイトについて」ページ

**Files:**
- Create: `site/app/about/page.tsx`

**Interfaces:**
- Consumes: なし
- Produces: `/about` ルート（`NAV_LINKS` と `FOOTER_LINKS` の参照先）

- [ ] **Step 1: about ページを作る**

`site/app/about/page.tsx` を新規作成する。本文は spec の4ブロック構成に対応する。

```tsx
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "このサイトについて",
  description:
    "Ankardo の目的、安全性の方針、掲載しているゲーム、運営者と連絡先について。",
};

const CONTACT_FORM_URL =
  "https://docs.google.com/forms/d/e/1FAIpQLScr21ghCZcOtjrM7LM7QvcnM7hYjWjGE45Gu1TroNXlrFqFPg/viewform";
const GITHUB_URL = "https://github.com/akabee0161";

export default function About() {
  return (
    <main className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="text-2xl font-extrabold text-neutral-900">このサイトについて</h1>

      <section className="mt-8">
        <h2 className="text-base font-bold text-neutral-900">Ankardo とは</h2>
        <p className="mt-2 text-sm leading-relaxed text-neutral-600">
          Ankardo は、小さな子供が安心して遊べるゲームを集めたカタログサイトです。ブラウザですぐに遊べるゲームだけを掲載しています。
        </p>
        <p className="mt-3 text-sm leading-relaxed text-neutral-600">
          ゲームは対象年齢・ジャンル・対応デバイスを添えて紹介しています。対象年齢は目安で、遊べる下限を示すものではありません。対応デバイスは、そのゲームが快適に遊べる環境（PC、スマートフォンの縦向き・横向き）を表します。
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-base font-bold text-neutral-900">安全性について</h2>
        <ul className="mt-2 list-disc pl-5 text-sm leading-relaxed text-neutral-600">
          <li>広告・課金・アカウント登録はありません。</li>
          <li>
            ゲームの記録（ハイスコアなど）は、お使いの端末の中にのみ保存されます。サーバーへは送信されません。
          </li>
          <li>
            アクセス解析を行う場合も、個人を特定しない集計のみで、Cookie は使いません。
          </li>
        </ul>
      </section>

      <section className="mt-8">
        <h2 className="text-base font-bold text-neutral-900">掲載しているゲームについて</h2>
        <p className="mt-2 text-sm leading-relaxed text-neutral-600">
          掲載しているゲームは、すべて運営者本人が制作しています。第三者から募集した作品は掲載していません。
        </p>
      </section>

      <section className="mt-8">
        <h2 className="text-base font-bold text-neutral-900">運営者と連絡先</h2>
        <p className="mt-2 text-sm leading-relaxed text-neutral-600">
          個人で制作・運営しています。ソースコードは{" "}
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noreferrer"
            className="font-bold text-brand underline"
          >
            GitHub
          </a>
          で公開しています。
        </p>
        <p className="mt-3 text-sm leading-relaxed text-neutral-600">
          ご意見・ご質問・不具合の報告は、
          <a
            href={CONTACT_FORM_URL}
            target="_blank"
            rel="noreferrer"
            className="font-bold text-brand underline"
          >
            お問い合わせフォーム
          </a>
          からお寄せください。
        </p>
      </section>
    </main>
  );
}
```

- [ ] **Step 2: ビルドしてページが生成されることを確認する**

```bash
npm run build
ls out/about/index.html
grep -o "docs.google.com/forms[^\"]*" out/about/index.html | head -1
```

期待: `out/about/index.html` が存在し、フォームの URL が含まれる。

- [ ] **Step 3: 目視確認**

```bash
npm run dev
```

`http://localhost:3000/about` を開き、次を確認する。

- 4つの見出しと本文が表示される
- ヘッダーの「このサイトについて」から遷移できる
- フォームのリンクを押すと Google フォームが別タブで開く（フォームが実際に開けることをここで確認する）
- GitHub のリンクが `https://github.com/akabee0161` を開く

確認できたら `Ctrl+C` で止める。

- [ ] **Step 4: コミット**

```bash
git add site/app/about/page.tsx
git commit -m "feat(site): このサイトについてのページを追加"
```

---

### Task 6: ページ別のタイトル

**Files:**
- Modify: `site/app/layout.tsx`
- Modify: `site/app/games/page.tsx`
- Modify: `site/app/games/[slug]/page.tsx`
- Modify: `site/app/not-found.tsx`

**Interfaces:**
- Consumes: `getGame(slug)`（既存の `lib/games.ts`）
- Produces: なし

- [ ] **Step 1: タイトルの template を設定する**

`site/app/layout.tsx` の `metadata` を次に置き換える（他の部分は Task 4 のまま）。

```tsx
export const metadata: Metadata = {
  title: {
    default: "Ankardo",
    template: "%s | Ankardo",
  },
  description: "子供向けインディーゲームカタログ Ankardo",
};
```

- [ ] **Step 2: 一覧ページにタイトルを足す**

`site/app/games/page.tsx` の先頭に import と `metadata` を足す。既存の `GamesList` 関数は変更しない。

```tsx
import type { Metadata } from "next";
import { getAllGames } from "../../lib/games";
import { GameCard } from "../../components/GameCard";

export const metadata: Metadata = {
  title: "ゲーム一覧",
  description: "Ankardo に掲載しているゲームの一覧。",
};
```

- [ ] **Step 3: 詳細ページにタイトルを足す**

`site/app/games/[slug]/page.tsx` の `generateStaticParams` の下に `generateMetadata` を足す。

```tsx
export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const game = getGame(slug);

  if (!game) {
    return { title: "ページが見つかりません" };
  }

  return { title: game.title, description: game.description };
}
```

- [ ] **Step 4: 404 ページにタイトルを足す**

`site/app/not-found.tsx` の先頭に import と `metadata` を足す。既存の `NotFound` 関数は変更しない。

```tsx
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "ページが見つかりません",
};
```

- [ ] **Step 5: ビルドしてタイトルを確認する**

```bash
npm run build
grep -o "<title>[^<]*</title>" out/index.html out/games/index.html out/games/rungame-sample/index.html out/about/index.html
```

期待:

- `out/index.html` → `<title>Ankardo</title>`
- `out/games/index.html` → `<title>ゲーム一覧 | Ankardo</title>`
- `out/games/rungame-sample/index.html` → `<title>Space Runner | Ankardo</title>`
- `out/about/index.html` → `<title>このサイトについて | Ankardo</title>`

- [ ] **Step 6: テストとビルドが通ることを確認する**

```bash
npm test
npm run build
```

期待: 26件パス、ビルド成功。

- [ ] **Step 7: コミット**

```bash
git add site/app/layout.tsx site/app/games/page.tsx "site/app/games/[slug]/page.tsx" site/app/not-found.tsx
git commit -m "feat(site): ページ別のタイトルを設定"
```

---

### Task 7: 正典ドキュメントの更新

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: なし
- Produces: なし

- [ ] **Step 1: ルーティングの表に `/about` を足す**

`README.md` の「ルーティング」の表に行を1つ足す。`ankardo.com/games` の行の下に置く。

```markdown
| `ankardo.com/about` | カタログ(`site/`) | このサイトについて(目的・安全性の方針・運営者と連絡先) |
```

- [ ] **Step 2: サイトの構成の説明を更新する**

`README.md` の「構成」のツリーにあるコメントを更新する。

変更前:

```text
└── site/      # Next.js カタログサイト(静的書き出し、トップ・一覧・個別詳細ページ)
```

変更後:

```text
└── site/      # Next.js カタログサイト(静的書き出し、トップ・一覧・個別詳細・このサイトについて)
```

- [ ] **Step 3: ブランドアセットの節を足す**

`README.md` の「### site/ (Next.js カタログサイト)」の節の末尾（`npm run build` のコードブロックとゲーム追加の説明の後）に、次を足す。

```markdown
#### ブランドアセット

- シンボルは `site/components/CatfishMark.tsx`（ナマズの正面顔、SVG 1点）。色は `currentColor` で、呼び出し側が決める
- ブランド色は藍 `#1f3a5f`。`site/app/globals.css` の `@theme` に `--color-brand` として定義し、`text-brand` / `bg-brand` で使う。既存ボタンの `bg-neutral-900` は据え置き
- ファビコンは `site/app/icon.svg`(白地の角丸四角＋藍のナマズ)。Next.js のファイル規約で `<link rel="icon">` が自動生成される
- ヘッダー/フッターのリンクは `site/lib/nav.ts` に集約する。リンクを増やすときはこのファイルだけを変更する
- Webフォントは読み込まない(表示速度優先の既存方針)
```

- [ ] **Step 4: テストの説明を更新する**

`README.md` の開発コマンドの `npm test` の行を更新する。

変更前:

```markdown
npm test       # Vitest でバリデーションのテストを実行
```

変更後:

```markdown
npm test       # Vitest でバリデーションと MobileNav のテストを実行
```

さらにコードブロックの下に1行足す。

```markdown
`MobileNav` のテストだけはファイル冒頭の docblock で `jsdom` 環境を指定している。他のテストは `node` 環境で動く。
```

- [ ] **Step 5: 記述が実装と一致していることを確認する**

```bash
grep -n "color-brand" site/app/globals.css
ls site/app/icon.svg site/lib/nav.ts site/components/CatfishMark.tsx
grep -n "vitest-environment" site/components/MobileNav.test.tsx
```

期待: すべて存在する。Task 1 Step 6 で `apple-icon.png` を見送った場合、README にその記載がないことを確認する。

- [ ] **Step 6: 最終確認**

```bash
cd site && npm test && npm run build
```

期待: 26件パス、ビルド成功。

- [ ] **Step 7: コミット**

```bash
git add README.md
git commit -m "docs: ヘッダー/フッターとブランドアセットを正典ドキュメントに反映"
```

---

## 実装完了後に残る手作業

計画の実行では完了しない。ユーザーが行う。

1. **PR の作成とマージ** — `Site (Next.js)` ワークフローの production environment 承認を含む
2. **問い合わせフォームの動作確認** — 実際に送信して回答が届くことを確認する（Task 5 Step 3 ではリンクが開くことまでしか確認しない）
3. **スマートフォン実機での確認** — ハンバーガーメニューの操作感、ヘッダーの高さ

## 本計画で扱わないもの（spec の未決事項）

- 既存ボタン（`bg-neutral-900`）をブランド色に寄せるかの判断
- アクセス解析の導入。about の「Cookie は使わない」という記述が制約になる
- OGP画像、SEO対策
- プレイページ（各ゲームリポジトリ）からカタログへ戻る導線
