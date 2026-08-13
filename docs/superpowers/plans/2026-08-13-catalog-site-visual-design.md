# カタログサイト ビジュアルデザイン実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `site/` にTailwind CSSを導入し、`docs/superpowers/specs/2026-08-13-catalog-site-visual-design.md` で決めたビジュアル方針(ミニマル・モダン、ジャンル別カラー、拡張されたゲームカード、詳細ページのギャラリー)を実装する。

**Architecture:** Next.js App Router(static export)上にTailwind CSS v4をCSSファースト設定で導入。ジャンル→色のマッピングを`site/lib/genres.ts`に一元化し、バッジ・サムネイル・ギャラリーの各コンポーネントがそこから色情報を参照する。データモデル(`Game`型)にジャンル・対象年齢・プレイ人数・難易度・複数画像を追加する。

**Tech Stack:** Next.js 16 / React 19 / TypeScript / Tailwind CSS 4.3.3

## Global Constraints

- CSS実装はTailwind CSS(v4系、CSSファースト設定)を使う。`tailwind.config.js`は作成せず、`app/globals.css`内の`@theme`でテーマ拡張する。
- フォントはOS標準のシステムフォントのみ。Webフォントは読み込まない。
- 一覧カードに横スワイプカルーセルは含めない。カルーセル(ギャラリー)は個別詳細ページのみ。
- ギャラリーの操作方法を説明するテキスト(「スワイプで切り替え」等)はUIに表示しない。
- UI基調(共通ボタン等)はニュートラルな1色(neutral系)。ジャンルごとの色分けはバッジ・サムネイル・ギャラリーのプレースホルダーにのみ適用する。
- 画像データは今回追加しない。`images`が空/未設定の場合はプレースホルダー表示(ジャンルカラー背景+タイトル頭文字)にフォールバックする。
- 自動テストは導入しない。各タスクの完了確認は `npm run build`(型チェック+static export)の成功をもって行う。
- ジャンルと色の割り当ては仮決定(spec記載の7ジャンル)。`site/lib/genres.ts`に一元化し、後から調整しやすくする。

---

## ファイル構成

**新規作成:**
- `site/postcss.config.mjs` — Tailwind CSSのPostCSSプラグイン設定
- `site/app/globals.css` — Tailwind読み込み + ジャンルカラーのテーマ拡張 + bodyベーススタイル
- `site/lib/genres.ts` — `GenreKey`型とジャンル→表示情報(ラベル・色クラス)のマッピング
- `site/components/GenreBadge.tsx` — ジャンルタグ表示
- `site/components/MetaBadges.tsx` — 対象年齢・プレイ人数・難易度のバッジ表示
- `site/components/GameThumbnail.tsx` — 一覧カード用サムネイル(画像 or プレースホルダー)
- `site/components/GameCard.tsx` — 一覧ページのゲームカード
- `site/components/GameGallery.tsx` — 詳細ページのメイン画像+サムネイル切り替え(クライアントコンポーネント)

**修正:**
- `site/package.json` — `tailwindcss` / `@tailwindcss/postcss` を devDependencies に追加
- `site/app/layout.tsx` — `globals.css` の読み込み、bodyへのベースクラス付与
- `site/lib/games.ts` — `Game`型に `genre` / `ageRange` / `players` / `difficulty` / `images?` を追加
- `site/content/games/rungame-sample.json` — 新規フィールドの値を追加
- `site/app/games/page.tsx` — `GameCard` を使った一覧レイアウトに変更
- `site/app/games/[slug]/page.tsx` — `GameGallery` 等を使った詳細レイアウトに変更
- `site/app/page.tsx` — トップページをTailwindでスタイリング

---

### Task 1: Tailwind CSS v4 導入とグローバルスタイル基盤

**Files:**
- Modify: `site/package.json`
- Create: `site/postcss.config.mjs`
- Create: `site/app/globals.css`
- Modify: `site/app/layout.tsx`

**Interfaces:**
- Produces: `app/globals.css` に `@theme` で以下のCSSカスタムプロパティ(Tailwindユーティリティクラスとして `bg-genre-action` 等が使えるようになる)を定義する: `--color-genre-action`, `--color-genre-puzzle`, `--color-genre-adventure`, `--color-genre-rhythm`, `--color-genre-racing`, `--color-genre-shooting`, `--color-genre-simulation`。Task 2 の `site/lib/genres.ts` がこれらのクラス名を参照する。

- [ ] **Step 1: Tailwind CSSをインストール**

```bash
cd /home/ubuntu/workspace/ankardo/site
npm install -D tailwindcss@^4.3.3 @tailwindcss/postcss@^4.3.3
```

- [ ] **Step 2: PostCSS設定ファイルを作成**

`site/postcss.config.mjs`:

```js
const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};

export default config;
```

- [ ] **Step 3: グローバルCSSを作成**

`site/app/globals.css`:

```css
@import "tailwindcss";

@theme {
  --color-genre-action: #ff7a45;
  --color-genre-puzzle: #2f80ed;
  --color-genre-adventure: #43a047;
  --color-genre-rhythm: #ec407a;
  --color-genre-racing: #ffc107;
  --color-genre-shooting: #7c4dff;
  --color-genre-simulation: #26c6da;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Hiragino Kaku Gothic ProN",
    "Yu Gothic", sans-serif;
}
```

- [ ] **Step 4: layout.tsxでglobals.cssを読み込む**

`site/app/layout.tsx` の内容を以下に置き換える:

```tsx
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
```

- [ ] **Step 5: ビルドして確認**

```bash
cd /home/ubuntu/workspace/ankardo/site
npm run build
```

Expected: エラーなく成功し、`out/` が生成される。

- [ ] **Step 6: Commit**

```bash
cd /home/ubuntu/workspace/ankardo
git add site/package.json site/package-lock.json site/postcss.config.mjs site/app/globals.css site/app/layout.tsx
git commit -m "feat(site): Tailwind CSSを導入しジャンルカラーのテーマを定義"
```

---

### Task 2: ジャンル定義とゲームデータモデルの拡張

**Files:**
- Create: `site/lib/genres.ts`
- Modify: `site/lib/games.ts`
- Modify: `site/content/games/rungame-sample.json`

**Interfaces:**
- Consumes: Task 1 で定義した `bg-genre-*` 系のTailwindクラス名。
- Produces: `GenreKey`型(`"action" | "puzzle" | "adventure" | "rhythm" | "racing" | "shooting" | "simulation"`)と `GENRES: Record<GenreKey, { label: string; badgeClassName: string; placeholderClassName: string }>`。以降の全コンポーネントタスクがこれを `import { GENRES, type GenreKey } from "../lib/genres"` で利用する。`Game`型に `genre: GenreKey`, `ageRange: string`, `players: string`, `difficulty: string`, `images?: string[]` が追加される。

- [ ] **Step 1: ジャンル定義ファイルを作成**

`site/lib/genres.ts`:

```ts
export type GenreKey =
  | "action"
  | "puzzle"
  | "adventure"
  | "rhythm"
  | "racing"
  | "shooting"
  | "simulation";

export type GenreInfo = {
  label: string;
  badgeClassName: string;
  placeholderClassName: string;
};

export const GENRES: Record<GenreKey, GenreInfo> = {
  action: {
    label: "アクション",
    badgeClassName: "bg-genre-action",
    placeholderClassName: "bg-genre-action/15",
  },
  puzzle: {
    label: "パズル",
    badgeClassName: "bg-genre-puzzle",
    placeholderClassName: "bg-genre-puzzle/15",
  },
  adventure: {
    label: "アドベンチャー",
    badgeClassName: "bg-genre-adventure",
    placeholderClassName: "bg-genre-adventure/15",
  },
  rhythm: {
    label: "リズム/音楽",
    badgeClassName: "bg-genre-rhythm",
    placeholderClassName: "bg-genre-rhythm/15",
  },
  racing: {
    label: "レース",
    badgeClassName: "bg-genre-racing",
    placeholderClassName: "bg-genre-racing/15",
  },
  shooting: {
    label: "シューティング",
    badgeClassName: "bg-genre-shooting",
    placeholderClassName: "bg-genre-shooting/15",
  },
  simulation: {
    label: "育成/シミュレーション",
    badgeClassName: "bg-genre-simulation",
    placeholderClassName: "bg-genre-simulation/15",
  },
};
```

- [ ] **Step 2: Game型を拡張**

`site/lib/games.ts` は現在以下の内容になっている:

```ts
import fs from "node:fs";
import path from "node:path";

export type Game = {
  slug: string;
  title: string;
  description: string;
  playUrl: string;
  screenshot?: string;
};

const GAMES_DIR = path.join(process.cwd(), "content", "games");

export function getAllGames(): Game[] {
  const files = fs.readdirSync(GAMES_DIR).filter((f) => f.endsWith(".json"));
  const games = files.map((file) => {
    const raw = fs.readFileSync(path.join(GAMES_DIR, file), "utf-8");
    return JSON.parse(raw) as Game;
  });
  return games.sort((a, b) => a.slug.localeCompare(b.slug));
}

export function getGame(slug: string): Game | undefined {
  return getAllGames().find((game) => game.slug === slug);
}
```

冒頭の `import` 2行と `Game` 型定義(4〜12行目)を以下に置き換える。`GAMES_DIR` / `getAllGames` / `getGame` の実装は変更しない:

```ts
import fs from "node:fs";
import path from "node:path";
import type { GenreKey } from "./genres";

export type Game = {
  slug: string;
  title: string;
  description: string;
  playUrl: string;
  genre: GenreKey;
  ageRange: string;
  players: string;
  difficulty: string;
  images?: string[];
};
```

- [ ] **Step 3: 既存ゲームデータに新規フィールドを追加**

`site/content/games/rungame-sample.json` を以下に置き換える:

```json
{
  "slug": "rungame-sample",
  "title": "Space Runner",
  "description": "5〜8歳向け宇宙テーマのエンドレスランナーゲーム。",
  "playUrl": "/play/rungame-sample/",
  "genre": "action",
  "ageRange": "5〜8歳",
  "players": "ひとり用",
  "difficulty": "やさしめ"
}
```

- [ ] **Step 4: 型チェックのためビルド**

```bash
cd /home/ubuntu/workspace/ankardo/site
npm run build
```

Expected: エラーなく成功する(`getAllGames()` が読むJSONの形は`Game`型と構造的に一致するため型エラーは出ないが、ビルドが通ることを確認する)。

- [ ] **Step 5: Commit**

```bash
cd /home/ubuntu/workspace/ankardo
git add site/lib/genres.ts site/lib/games.ts site/content/games/rungame-sample.json
git commit -m "feat(site): ジャンル定義とGame型のメタ情報フィールドを追加"
```

---

### Task 3: GenreBadge / MetaBadges コンポーネント

**Files:**
- Create: `site/components/GenreBadge.tsx`
- Create: `site/components/MetaBadges.tsx`

**Interfaces:**
- Consumes: `GENRES`, `GenreKey`(`site/lib/genres.ts`、Task 2)。
- Produces: `GenreBadge({ genre: GenreKey })`、`MetaBadges({ ageRange: string; players: string; difficulty: string })`。Task 5(GameCard)・Task 7(詳細ページ)が利用する。

- [ ] **Step 1: GenreBadgeを作成**

`site/components/GenreBadge.tsx`:

```tsx
import { GENRES, type GenreKey } from "../lib/genres";

export function GenreBadge({ genre }: { genre: GenreKey }) {
  const info = GENRES[genre];

  return (
    <span
      className={`inline-block rounded px-2 py-0.5 text-xs font-bold text-white ${info.badgeClassName}`}
    >
      {info.label}
    </span>
  );
}
```

- [ ] **Step 2: MetaBadgesを作成**

`site/components/MetaBadges.tsx`:

```tsx
export function MetaBadges({
  ageRange,
  players,
  difficulty,
}: {
  ageRange: string;
  players: string;
  difficulty: string;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      <span className="rounded border border-neutral-200 bg-white px-2 py-0.5 text-xs text-neutral-600">
        👶 {ageRange}
      </span>
      <span className="rounded border border-neutral-200 bg-white px-2 py-0.5 text-xs text-neutral-600">
        🎮 {players}
      </span>
      <span className="rounded border border-neutral-200 bg-white px-2 py-0.5 text-xs text-neutral-600">
        ⭐ {difficulty}
      </span>
    </div>
  );
}
```

- [ ] **Step 3: ビルドして確認**

```bash
cd /home/ubuntu/workspace/ankardo/site
npm run build
```

Expected: エラーなく成功する(この時点ではどこからも使われていないため、未使用エラーが出ないことを確認する程度)。

- [ ] **Step 4: Commit**

```bash
cd /home/ubuntu/workspace/ankardo
git add site/components/GenreBadge.tsx site/components/MetaBadges.tsx
git commit -m "feat(site): ジャンルバッジとメタ情報バッジのコンポーネントを追加"
```

---

### Task 4: GameThumbnail コンポーネント(一覧用サムネイル)

**Files:**
- Create: `site/components/GameThumbnail.tsx`

**Interfaces:**
- Consumes: `GENRES`, `GenreKey`(`site/lib/genres.ts`)。
- Produces: `GameThumbnail({ genre: GenreKey; images?: string[]; title: string })`。Task 5(GameCard)が利用する。`images` が空/未設定の場合はプレースホルダー(ジャンルカラー背景+タイトル頭文字)を描画する。

- [ ] **Step 1: GameThumbnailを作成**

`site/components/GameThumbnail.tsx`:

```tsx
import { GENRES, type GenreKey } from "../lib/genres";

export function GameThumbnail({
  genre,
  images,
  title,
}: {
  genre: GenreKey;
  images?: string[];
  title: string;
}) {
  const firstImage = images?.[0];

  if (firstImage) {
    return <img src={firstImage} alt={title} className="h-full w-full object-cover" />;
  }

  return (
    <div
      className={`flex h-full w-full items-center justify-center text-4xl font-bold text-neutral-400 ${GENRES[genre].placeholderClassName}`}
    >
      {title.charAt(0)}
    </div>
  );
}
```

- [ ] **Step 2: ビルドして確認**

```bash
cd /home/ubuntu/workspace/ankardo/site
npm run build
```

Expected: エラーなく成功する。

- [ ] **Step 3: Commit**

```bash
cd /home/ubuntu/workspace/ankardo
git add site/components/GameThumbnail.tsx
git commit -m "feat(site): 一覧用サムネイル(画像/プレースホルダー)コンポーネントを追加"
```

---

### Task 5: GameCard コンポーネントと一覧ページの更新

**Files:**
- Create: `site/components/GameCard.tsx`
- Modify: `site/app/games/page.tsx`

**Interfaces:**
- Consumes: `Game`型(`site/lib/games.ts`)、`GenreBadge`(Task 3)、`MetaBadges`(Task 3)、`GameThumbnail`(Task 4)、`getAllGames()`(既存)。
- Produces: `GameCard({ game: Game })`。`site/app/games/page.tsx` がこれを一覧表示に使う。

- [ ] **Step 1: GameCardを作成**

`site/components/GameCard.tsx`:

```tsx
import Link from "next/link";
import type { Game } from "../lib/games";
import { GenreBadge } from "./GenreBadge";
import { MetaBadges } from "./MetaBadges";
import { GameThumbnail } from "./GameThumbnail";

export function GameCard({ game }: { game: Game }) {
  return (
    <Link
      href={`/games/${game.slug}`}
      className="block overflow-hidden rounded-lg border border-neutral-200 bg-white transition hover:shadow-md"
    >
      <div className="h-40 w-full">
        <GameThumbnail genre={game.genre} images={game.images} title={game.title} />
      </div>
      <div className="p-4">
        <div className="mb-2">
          <GenreBadge genre={game.genre} />
        </div>
        <h3 className="text-base font-bold text-neutral-900">{game.title}</h3>
        <p className="mt-1 line-clamp-2 text-sm text-neutral-600">{game.description}</p>
        <div className="mt-3">
          <MetaBadges
            ageRange={game.ageRange}
            players={game.players}
            difficulty={game.difficulty}
          />
        </div>
      </div>
    </Link>
  );
}
```

- [ ] **Step 2: 一覧ページをGameCardベースに書き換え**

`site/app/games/page.tsx` を以下に置き換える:

```tsx
import { getAllGames } from "../../lib/games";
import { GameCard } from "../../components/GameCard";

export default function GamesList() {
  const games = getAllGames();

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold text-neutral-900">ゲーム一覧</h1>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {games.map((game) => (
          <GameCard key={game.slug} game={game} />
        ))}
      </div>
    </main>
  );
}
```

- [ ] **Step 3: ビルドして確認**

```bash
cd /home/ubuntu/workspace/ankardo/site
npm run build
```

Expected: エラーなく成功する。

- [ ] **Step 4: Commit**

```bash
cd /home/ubuntu/workspace/ankardo
git add site/components/GameCard.tsx site/app/games/page.tsx
git commit -m "feat(site): 一覧ページのゲームカードを画像拡大+メタ情報表示に更新"
```

---

### Task 6: GameGallery コンポーネント(詳細ページ用)

**Files:**
- Create: `site/components/GameGallery.tsx`

**Interfaces:**
- Consumes: `GENRES`, `GenreKey`(`site/lib/genres.ts`)。
- Produces: `GameGallery({ genre: GenreKey; images?: string[]; title: string })`。クライアントコンポーネント(`"use client"`)。Task 7(詳細ページ)が利用する。`images`が空/未設定ならプレースホルダーを表示し、複数枚あればサムネイルクリックでメイン画像を切り替える。操作説明テキストは表示しない。

- [ ] **Step 1: GameGalleryを作成**

`site/components/GameGallery.tsx`:

```tsx
"use client";

import { useState } from "react";
import { GENRES, type GenreKey } from "../lib/genres";

export function GameGallery({
  genre,
  images,
  title,
}: {
  genre: GenreKey;
  images?: string[];
  title: string;
}) {
  const [selectedIndex, setSelectedIndex] = useState(0);

  if (!images || images.length === 0) {
    return (
      <div
        className={`flex h-48 w-full items-center justify-center rounded-lg text-6xl font-bold text-neutral-400 sm:h-72 ${GENRES[genre].placeholderClassName}`}
      >
        {title.charAt(0)}
      </div>
    );
  }

  return (
    <div>
      <div className="h-48 w-full overflow-hidden rounded-lg sm:h-72">
        <img src={images[selectedIndex]} alt={title} className="h-full w-full object-cover" />
      </div>
      {images.length > 1 && (
        <div className="mt-2 flex gap-2">
          {images.map((image, index) => (
            <button
              key={image}
              type="button"
              onClick={() => setSelectedIndex(index)}
              className={`h-16 w-16 overflow-hidden rounded-md border-2 ${
                index === selectedIndex ? "border-neutral-900" : "border-transparent opacity-60"
              }`}
            >
              <img src={image} alt="" className="h-full w-full object-cover" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: ビルドして確認**

```bash
cd /home/ubuntu/workspace/ankardo/site
npm run build
```

Expected: エラーなく成功する。

- [ ] **Step 3: Commit**

```bash
cd /home/ubuntu/workspace/ankardo
git add site/components/GameGallery.tsx
git commit -m "feat(site): 詳細ページ用の画像ギャラリーコンポーネントを追加"
```

---

### Task 7: 詳細ページの更新

**Files:**
- Modify: `site/app/games/[slug]/page.tsx`

**Interfaces:**
- Consumes: `getAllGames`, `getGame`(既存、`site/lib/games.ts`)、`GenreBadge`(Task 3)、`MetaBadges`(Task 3)、`GameGallery`(Task 6)。

- [ ] **Step 1: 詳細ページを書き換え**

`site/app/games/[slug]/page.tsx` を以下に置き換える:

```tsx
import { notFound } from "next/navigation";
import { getAllGames, getGame } from "../../../lib/games";
import { GenreBadge } from "../../../components/GenreBadge";
import { MetaBadges } from "../../../components/MetaBadges";
import { GameGallery } from "../../../components/GameGallery";

export function generateStaticParams() {
  return getAllGames().map((game) => ({ slug: game.slug }));
}

export default async function GameDetail({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const game = getGame(slug);

  if (!game) {
    notFound();
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      <GameGallery genre={game.genre} images={game.images} title={game.title} />
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <GenreBadge genre={game.genre} />
        <MetaBadges
          ageRange={game.ageRange}
          players={game.players}
          difficulty={game.difficulty}
        />
      </div>
      <h1 className="mt-3 text-2xl font-extrabold text-neutral-900">{game.title}</h1>
      <p className="mt-2 text-sm leading-relaxed text-neutral-600">{game.description}</p>
      <a
        href={game.playUrl}
        className="mt-6 inline-block rounded-lg bg-neutral-900 px-6 py-3 text-sm font-bold text-white"
      >
        ▶ プレイする
      </a>
    </main>
  );
}
```

- [ ] **Step 2: ビルドして確認**

```bash
cd /home/ubuntu/workspace/ankardo/site
npm run build
```

Expected: エラーなく成功し、`out/games/rungame-sample/index.html` が生成される。

- [ ] **Step 3: Commit**

```bash
cd /home/ubuntu/workspace/ankardo
git add site/app/games/\[slug\]/page.tsx
git commit -m "feat(site): 詳細ページをギャラリー+メタ情報表示に更新"
```

---

### Task 8: トップページのスタイリング

**Files:**
- Modify: `site/app/page.tsx`

- [ ] **Step 1: トップページを書き換え**

`site/app/page.tsx` を以下に置き換える:

```tsx
import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto flex max-w-3xl flex-col items-center px-4 py-16 text-center">
      <h1 className="text-3xl font-extrabold text-neutral-900">Ankardo</h1>
      <p className="mt-3 text-sm text-neutral-600">
        子供向けインディーゲームのカタログサイトです。
      </p>
      <Link
        href="/games"
        className="mt-8 inline-block rounded-lg bg-neutral-900 px-6 py-3 text-sm font-bold text-white"
      >
        ゲーム一覧を見る
      </Link>
    </main>
  );
}
```

- [ ] **Step 2: ビルドして最終確認**

```bash
cd /home/ubuntu/workspace/ankardo/site
npm run build
```

Expected: エラーなく成功する。`npm run dev` を起動し、`/`・`/games`・`/games/rungame-sample` を目視確認する(SSHポートフォワード経由でブラウザから確認)。

- [ ] **Step 3: Commit**

```bash
cd /home/ubuntu/workspace/ankardo
git add site/app/page.tsx
git commit -m "feat(site): トップページをミニマル・モダン方針でスタイリング"
```

---

## この計画のスコープ外

- 実際のゲームスクリーンショット画像の用意(今後のゲーム追加時に対応)
- ジャンル・色割り当ての最終確定(spec記載の通り仮決定、今後調整)
- 自動テストの導入
- ヘッダー/フッターなどサイト共通ナビゲーションの新規デザイン(spec・ブレインストーミングで議論していないため)
