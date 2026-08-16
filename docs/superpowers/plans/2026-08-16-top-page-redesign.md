# トップページ再設計 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `docs/superpowers/specs/2026-08-16-top-page-redesign-design.md` で決めた方針(ジャンルカラー主導のブランドヒーロー型)に沿って、`site/app/page.tsx` を単なる中継ページから「サイトの顔」として機能するトップページに書き換える。

**Architecture:** 既存の`Game`型・`GENRES`定義・`GameCard`コンポーネントを再利用する。新規コンポーネントは作成せず、`app/page.tsx`内にヒーロー・ピックアップ・ジャンルナビゲーション・保護者向け一文の4セクションを直接実装する(このページでしか使わない構成のため、抽出は将来必要になった時点で検討する)。ピックアップ表示用に`site/lib/games.ts`へ`getFeaturedGames()`ヘルパーを追加する。

**Tech Stack:** Next.js 16 / React 19 / TypeScript / Tailwind CSS 4.3.3(既存構成のまま、追加ライブラリなし)

## Global Constraints

- 新規ビジュアルアセット(ロゴ・アイコン・イラスト等)は使わない。ヒーロー背景は既存のジャンルカラー(`app/globals.css`の`@theme`で定義済みのCSS変数)を使ったCSSグラデーションで表現する。
- ジャンルタイルのクリック先は `/games` への単純遷移とする。ジャンル別フィルタ(`/games?genre=xxx`)は実装しない(spec記載の通り今回のスコープ外)。
- 保護者向けの一文は「対象年齢・ジャンルで選べる」という既存機能(`MetaBadges`/`GenreBadge`)のみを根拠にする。広告有無など未確認の主張は書かない。
- `featured`は必須フィールドにしない。未設定のゲームは`getFeaturedGames()`が自動的にフォールバック対象にする。
- 自動テストは導入しない(既存方針を踏襲)。各タスクの完了確認は `npm run build` の成功をもって行う。
- 新規コンポーネントファイルは作成しない。既存の`GameCard`をピックアップセクションに再利用する。

---

## ファイル構成

**修正:**
- `site/lib/games.ts` — `Game`型に`featured?: boolean`を追加、バリデーション拡張、`getFeaturedGames()`ヘルパーを追加
- `site/content/games/rungame-sample.json` — `featured: true`を設定(現状唯一のゲームをピックアップ表示するため)
- `site/app/page.tsx` — ヒーロー/ピックアップ/ジャンルナビゲーション/保護者向け一文で構成するトップページに書き換え

---

### Task 1: `Game`型へのfeaturedフィールド追加とgetFeaturedGamesヘルパー

**Files:**
- Modify: `site/lib/games.ts`

**Interfaces:**
- Produces: `Game`型に`featured?: boolean`。`getFeaturedGames(limit?: number): Game[]` — `featured: true`のゲームを返し、0件の場合は`getAllGames()`の先頭からフォールバックする。デフォルト`limit`は3。Task 3(トップページ)がこれを利用する。

- [ ] **Step 1: Game型にfeaturedを追加**

`site/lib/games.ts`の`Game`型定義に`featured?: boolean;`を追加する(`images?: string[];`の下に追加):

```ts
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
  featured?: boolean;
};
```

- [ ] **Step 2: バリデーションを拡張**

`validateGame`関数内、`images`のバリデーションブロックの後に以下を追加する:

```ts
  const featured = record.featured;
  if (featured !== undefined && typeof featured !== "boolean") {
    throw new Error(
      `content/games/${file}: "featured" はboolean型である必要があります`
    );
  }
```

- [ ] **Step 3: getFeaturedGamesを追加**

`getGame`関数の後に以下を追加する:

```ts
export function getFeaturedGames(limit = 3): Game[] {
  const games = getAllGames();
  const featured = games.filter((game) => game.featured);
  return (featured.length > 0 ? featured : games).slice(0, limit);
}
```

- [ ] **Step 4: ビルドして確認**

```bash
cd /home/ubuntu/workspace/ankardo/site
npm run build
```

Expected: エラーなく成功する(この時点ではどこからも使われていないため、未使用エラーが出ないことを確認する程度)。

- [ ] **Step 5: Commit**

```bash
cd /home/ubuntu/workspace/ankardo
git add site/lib/games.ts
git commit -m "feat(site): Game型にfeaturedフィールドとgetFeaturedGamesヘルパーを追加"
```

---

### Task 2: 既存ゲームデータにfeaturedを設定

**Files:**
- Modify: `site/content/games/rungame-sample.json`

- [ ] **Step 1: featured: trueを追加**

`site/content/games/rungame-sample.json`の末尾に`"featured": true`を追加する:

```json
{
  "slug": "rungame-sample",
  "title": "Space Runner",
  "description": "5〜8歳向け宇宙テーマのエンドレスランナーゲーム。",
  "playUrl": "/play/rungame-sample/",
  "genre": "action",
  "ageRange": "5〜8歳",
  "players": "ひとり用",
  "difficulty": "やさしめ",
  "featured": true
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
git add site/content/games/rungame-sample.json
git commit -m "feat(site): rungame-sampleをピックアップ表示対象に設定"
```

---

### Task 3: トップページの書き換え

**Files:**
- Modify: `site/app/page.tsx`

**Interfaces:**
- Consumes: `getFeaturedGames()`(Task 1)、`GameCard`(既存、`site/components/GameCard.tsx`)、`GENRES`/`GenreKey`(既存、`site/lib/genres.ts`)。

- [ ] **Step 1: page.tsxを書き換え**

`site/app/page.tsx`を以下に置き換える:

```tsx
import Link from "next/link";
import { getFeaturedGames } from "../lib/games";
import { GameCard } from "../components/GameCard";
import { GENRES, type GenreKey } from "../lib/genres";

export default function Home() {
  const featuredGames = getFeaturedGames();

  return (
    <main>
      <section
        className="px-4 py-16 text-center text-white"
        style={{
          background:
            "linear-gradient(120deg, var(--color-genre-action), var(--color-genre-puzzle), var(--color-genre-adventure), var(--color-genre-rhythm), var(--color-genre-racing), var(--color-genre-shooting), var(--color-genre-simulation))",
        }}
      >
        <h1 className="text-3xl font-extrabold drop-shadow-sm sm:text-4xl">
          見つけよう、きみだけのすきなゲーム
        </h1>
        <p className="mt-3 text-sm font-medium drop-shadow-sm sm:text-base">
          年齢・ジャンルで選べる、子供向けインディーゲームカタログ
        </p>
      </section>

      {featuredGames.length > 0 && (
        <section className="mx-auto max-w-5xl px-4 py-10">
          <h2 className="mb-4 text-xl font-bold text-neutral-900">ピックアップゲーム</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {featuredGames.map((game) => (
              <GameCard key={game.slug} game={game} />
            ))}
          </div>
        </section>
      )}

      <section className="mx-auto max-w-5xl px-4 py-10">
        <h2 className="mb-4 text-xl font-bold text-neutral-900">ジャンルから探す</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {(Object.keys(GENRES) as GenreKey[]).map((key) => {
            const info = GENRES[key];
            return (
              <Link
                key={key}
                href="/games"
                className={`flex h-16 items-center justify-center rounded-lg text-sm font-bold ${info.textClassName} ${info.badgeClassName}`}
              >
                {info.label}
              </Link>
            );
          })}
        </div>
      </section>

      <section className="mx-auto max-w-3xl px-4 pb-16 text-center">
        <p className="text-sm text-neutral-600">
          対象年齢やジャンルでゲームを選べるので、お子さまに合った一本を見つけやすくしています。
        </p>
        <Link
          href="/games"
          className="mt-6 inline-block rounded-lg bg-neutral-900 px-6 py-3 text-sm font-bold text-white"
        >
          ゲーム一覧を見る
        </Link>
      </section>
    </main>
  );
}
```

- [ ] **Step 2: ビルドして最終確認**

```bash
cd /home/ubuntu/workspace/ankardo/site
npm run build
```

Expected: エラーなく成功する。`npm run dev` を起動し、`/` を目視確認する(SSHポートフォワード経由でブラウザから確認)。

- [ ] **Step 3: Commit**

```bash
cd /home/ubuntu/workspace/ankardo
git add site/app/page.tsx
git commit -m "feat(site): トップページをブランドヒーロー型に再設計"
```

---

## この計画のスコープ外

- ジャンル別フィルタ(`/games?genre=xxx`)を含む一覧ページ側の改修
- ロゴ・ファビコン・ジャンルアイコン・マスコットイラスト等のビジュアルアセット制作(長期バックログ、`HANDOVER.md`参照)
- 「新着ゲーム」等のデータ駆動ダッシュボード要素(spec記載の案2、ゲーム数が増えた段階で再検討)
- ヒーローのキャッチコピー文言のユーザーテスト・A/Bテスト
- 自動テストの導入
