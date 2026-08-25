# カタログのアセット規約とメタデータ拡張 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** カタログのゲームデータに対応デバイスと操作方法を追加し、スクリーンショットの置き場所と比率の規約を確定させ、バリデーションをテストで保護する。

**Architecture:** `site/lib/genres.ts` の既存パターンに倣って `site/lib/devices.ts` を新設し、値と表示ラベルを1箇所に集約する。`site/lib/games.ts` の `validateGame` を拡張してビルド時に検証する。表示側は既存の `MetaBadges` にバッジを追加し、画像を表示する箇所の固定高さを `aspect-video` に置き換えて 16:9 に統一する。

**Tech Stack:** Next.js 16（`output: "export"`）、React 19、TypeScript（`strict: false`）、Tailwind CSS 4、Vitest（本計画で新規導入）

**Spec:** `docs/superpowers/specs/2026-08-25-catalog-assets-and-metadata-design.md`

## Global Constraints

- 作業ディレクトリは `site/`。npm コマンドはすべて `site/` で実行する
- `site/tsconfig.json` は `"strict": false`。既存設定を変更しない
- Vitest の実行環境は `node`（既定値）。DOM を触るテストは書かないため jsdom は導入しない
- テストでは `describe` / `it` / `expect` を `vitest` から明示的に `import` する。`globals: true` は使わない（`tsconfig.json` の `types` を変更せずに済むため）
- テストファイルはテスト対象と同じディレクトリに置く（`site/lib/games.test.ts`）。3つのゲームリポジトリと同じ配置
- コミットは Conventional Commits 形式（`feat:` / `fix:` / `test:` / `docs:` / `chore:`）
- 表示ラベル中の括弧は全角（`（横向き）`）を使う
- 検証コマンドは `npm test` と `npm run build` の2つ。`npm run build` は静的書き出しまで通ることを確認する

---

## File Structure

| ファイル | 責務 | 変更種別 |
|---|---|---|
| `site/lib/devices.ts` | 対応デバイスのキーと表示ラベルの定義 | 新規 |
| `site/lib/games.ts` | `Game` 型と JSON のビルド時バリデーション | 変更 |
| `site/lib/games.test.ts` | `validateGame` のテスト | 新規 |
| `site/components/MetaBadges.tsx` | 年齢・人数・難易度・対応デバイスのバッジ表示 | 変更 |
| `site/components/GameCard.tsx` | 一覧カード。サムネイル領域の比率 | 変更 |
| `site/components/GameGallery.tsx` | 詳細ページの画像ギャラリー。メイン画像の比率 | 変更 |
| `site/app/games/[slug]/page.tsx` | 詳細ページ。「あそびかた」セクションの追加 | 変更 |
| `site/content/games/*.json` | ゲームデータ | 変更 |
| `site/public/screenshots/.gitkeep` | スクリーンショットの置き場所 | 新規 |
| `site/package.json` | `test` script と Vitest 依存 | 変更 |
| `.github/workflows/site.yml` | CI にテスト実行を追加 | 変更 |
| `.claude/skills/new-game/SKILL.md` | ゲーム追加手順（正典） | 変更 |
| `README.md` | 必須フィールドの説明（正典） | 変更 |

---

### Task 1: Vitest の導入と既存バリデーションの回帰テスト

`devices` / `controls` を追加する前に、現在のバリデーション挙動をテストで固定する。以降のタスクでバリデーションを拡張しても既存の検証が壊れていないことを確認できるようにする。

**Files:**
- Modify: `site/package.json`
- Modify: `site/lib/games.ts`（`validateGame` に `export` を付ける。33行目付近）
- Create: `site/lib/games.test.ts`
- Modify: `.github/workflows/site.yml`

**Interfaces:**
- Consumes: なし（最初のタスク）
- Produces: `export function validateGame(data: unknown, file: string): Game` — 以降のタスクのテストがこの関数を直接呼ぶ

- [ ] **Step 1: Vitest をインストールする**

```bash
cd site
npm install -D vitest
```

- [ ] **Step 2: `package.json` に test script を追加する**

`site/package.json` の `scripts` を次にする（`dev` / `build` は既存のまま）。

```json
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "test": "vitest run",
    "test:watch": "vitest"
  },
```

- [ ] **Step 3: 失敗するテストを書く**

`site/lib/games.test.ts` を新規作成する。

```ts
import { describe, expect, it } from "vitest";
import { validateGame } from "./games";

const VALID_GAME = {
  slug: "sample",
  title: "サンプルゲーム",
  description: "テスト用のゲーム。",
  playUrl: "/play/sample/",
  genre: "action",
  ageRange: "5〜8歳",
  players: "ひとり用",
  difficulty: "やさしめ",
};

describe("validateGame", () => {
  it("必須フィールドが揃っていれば通る", () => {
    expect(validateGame(VALID_GAME, "sample.json")).toEqual(VALID_GAME);
  });

  it("JSONオブジェクトでなければエラーになる", () => {
    expect(() => validateGame(null, "sample.json")).toThrow(
      /JSONオブジェクトではありません/
    );
    expect(() => validateGame("文字列", "sample.json")).toThrow(
      /JSONオブジェクトではありません/
    );
  });

  it("必須の文字列フィールドが欠けていればエラーになる", () => {
    const { title, ...withoutTitle } = VALID_GAME;
    expect(() => validateGame(withoutTitle, "sample.json")).toThrow(/"title"/);
  });

  it("必須の文字列フィールドが空文字ならエラーになる", () => {
    expect(() =>
      validateGame({ ...VALID_GAME, description: "   " }, "sample.json")
    ).toThrow(/"description"/);
  });

  it("genre が GENRES に無い値ならエラーになる", () => {
    expect(() =>
      validateGame({ ...VALID_GAME, genre: "cooking" }, "sample.json")
    ).toThrow(/"genre"/);
  });

  it("images が配列でなければエラーになる", () => {
    expect(() =>
      validateGame({ ...VALID_GAME, images: "/a.png" }, "sample.json")
    ).toThrow(/"images"/);
  });

  it("images に空文字が含まれていればエラーになる", () => {
    expect(() =>
      validateGame({ ...VALID_GAME, images: ["/a.png", ""] }, "sample.json")
    ).toThrow(/"images"/);
  });

  it("images が未設定でも通る", () => {
    expect(validateGame(VALID_GAME, "sample.json")).toEqual(VALID_GAME);
  });
});
```

- [ ] **Step 4: テストを実行して失敗することを確認する**

Run: `cd site && npm test`
Expected: FAIL。`validateGame` が `games.ts` から export されていないため、インポートエラーになる。

- [ ] **Step 5: `validateGame` を export する**

`site/lib/games.ts` の関数宣言に `export` を付ける。他の変更はしない。

```ts
export function validateGame(data: unknown, file: string): Game {
```

- [ ] **Step 6: テストを実行して通ることを確認する**

Run: `cd site && npm test`
Expected: PASS（8件）

- [ ] **Step 7: ビルドが壊れていないことを確認する**

Run: `cd site && npm run build`
Expected: 成功。`out/` が生成される。

- [ ] **Step 8: CI にテスト実行を追加する**

`.github/workflows/site.yml` の `- run: npm ci` と `- run: npm run build` の間に1行追加する。

```yaml
      - run: npm ci
      - run: npm test
      - run: npm run build
```

- [ ] **Step 9: コミット**

```bash
git add site/package.json site/package-lock.json site/lib/games.ts site/lib/games.test.ts .github/workflows/site.yml
git commit -m "test: Vitest を導入しゲームデータのバリデーションにテストを追加"
```

---

### Task 2: `devices` フィールドの追加

対応デバイスを必須フィールドとして追加する。必須にするため、バリデーションの追加と既存3件の JSON 更新を同一タスクで行う。片方だけコミットすると `npm run build` が失敗するため、分割できない。

**Files:**
- Create: `site/lib/devices.ts`
- Modify: `site/lib/games.ts`
- Modify: `site/lib/games.test.ts`
- Modify: `site/content/games/rungame-sample.json`
- Modify: `site/content/games/shogi-vs-cpu.json`
- Modify: `site/content/games/character-tactics.json`

**Interfaces:**
- Consumes: `validateGame(data, file)`（Task 1）
- Produces:
  - `export type DeviceKey = "pc" | "mobile-landscape" | "mobile-portrait"`
  - `export type DeviceInfo = { label: string; icon: string }`
  - `export const DEVICES: Record<DeviceKey, DeviceInfo>`
  - `Game` 型に `devices: DeviceKey[]`（必須）が追加される

- [ ] **Step 1: 失敗するテストを書く**

`site/lib/games.test.ts` の `VALID_GAME` に `devices` を追加し、テストケースを追記する。

`VALID_GAME` を次に差し替える。

```ts
const VALID_GAME = {
  slug: "sample",
  title: "サンプルゲーム",
  description: "テスト用のゲーム。",
  playUrl: "/play/sample/",
  genre: "action",
  ageRange: "5〜8歳",
  players: "ひとり用",
  difficulty: "やさしめ",
  devices: ["pc"],
};
```

`describe("validateGame", ...)` の中に次のテストを追記する。

```ts
  it("devices が未設定ならエラーになる", () => {
    const { devices, ...withoutDevices } = VALID_GAME;
    expect(() => validateGame(withoutDevices, "sample.json")).toThrow(
      /"devices"/
    );
  });

  it("devices が空配列ならエラーになる", () => {
    expect(() =>
      validateGame({ ...VALID_GAME, devices: [] }, "sample.json")
    ).toThrow(/"devices"/);
  });

  it("devices が配列でなければエラーになる", () => {
    expect(() =>
      validateGame({ ...VALID_GAME, devices: "pc" }, "sample.json")
    ).toThrow(/"devices"/);
  });

  it("devices に DEVICES に無い値が含まれていればエラーになる", () => {
    expect(() =>
      validateGame({ ...VALID_GAME, devices: ["pc", "vr"] }, "sample.json")
    ).toThrow(/"devices"/);
  });

  it("devices に重複があればエラーになる", () => {
    expect(() =>
      validateGame({ ...VALID_GAME, devices: ["pc", "pc"] }, "sample.json")
    ).toThrow(/重複/);
  });

  it("devices に複数の有効な値を指定できる", () => {
    const game = { ...VALID_GAME, devices: ["pc", "mobile-landscape"] };
    expect(validateGame(game, "sample.json")).toEqual(game);
  });
```

- [ ] **Step 2: テストを実行して失敗することを確認する**

Run: `cd site && npm test`
Expected: FAIL。`devices` の検証が存在しないため、エラーを期待するテストが「例外が投げられなかった」として失敗する。

- [ ] **Step 3: `site/lib/devices.ts` を新規作成する**

```ts
export type DeviceKey = "pc" | "mobile-landscape" | "mobile-portrait";

export type DeviceInfo = {
  label: string;
  icon: string;
};

export const DEVICES: Record<DeviceKey, DeviceInfo> = {
  pc: { label: "PC", icon: "💻" },
  "mobile-landscape": { label: "スマホ・タブレット（横向き）", icon: "📱" },
  "mobile-portrait": { label: "スマホ・タブレット（縦向き）", icon: "📱" },
};
```

- [ ] **Step 4: `site/lib/games.ts` にバリデーションを追加する**

インポート行に `devices.ts` を追加する。

```ts
import { DEVICES, type DeviceKey } from "./devices";
```

`Game` 型に `devices` を追加する（`genre` の下）。

```ts
export type Game = {
  slug: string;
  title: string;
  description: string;
  playUrl: string;
  genre: GenreKey;
  devices: DeviceKey[];
  ageRange: string;
  players: string;
  difficulty: string;
  images?: string[];
  featured?: boolean;
};
```

`validateGame` の `genre` の検証ブロックの直後に、`devices` の検証を追加する。

```ts
  const devices = record.devices;
  if (!Array.isArray(devices) || devices.length === 0) {
    throw new Error(
      `content/games/${file}: "devices" は1つ以上の要素を持つ配列である必要があります`
    );
  }

  for (const device of devices) {
    if (
      typeof device !== "string" ||
      !Object.prototype.hasOwnProperty.call(DEVICES, device)
    ) {
      throw new Error(
        `content/games/${file}: "devices" に不正な値が含まれています(値: ${JSON.stringify(
          device
        )})。DEVICES(site/lib/devices.ts)のいずれかのキーを指定してください`
      );
    }
  }

  if (new Set(devices).size !== devices.length) {
    throw new Error(
      `content/games/${file}: "devices" に重複した値が含まれています`
    );
  }
```

- [ ] **Step 5: テストを実行して通ることを確認する**

Run: `cd site && npm test`
Expected: PASS（14件）

- [ ] **Step 6: ビルドが失敗することを確認する**

Run: `cd site && npm run build`
Expected: FAIL。既存3件の JSON に `devices` が無いため、`"devices" は1つ以上の要素を持つ配列である必要があります` で失敗する。これは想定どおりで、必須フィールドの検証が実データに効いていることの確認になる。

- [ ] **Step 7: 既存3件の JSON に `devices` を追加する**

`site/content/games/rungame-sample.json`:

```json
{
  "slug": "rungame-sample",
  "title": "Space Runner",
  "description": "5〜8歳向け宇宙テーマのエンドレスランナーゲーム。",
  "playUrl": "/play/rungame-sample/",
  "genre": "action",
  "devices": ["pc", "mobile-landscape"],
  "ageRange": "5〜8歳",
  "players": "ひとり用",
  "difficulty": "やさしめ",
  "featured": true
}
```

`site/content/games/shogi-vs-cpu.json`:

```json
{
  "slug": "shogi-vs-cpu",
  "title": "しょうぎ どうじょう",
  "description": "コンピュータと対戦できる本将棋。強さは3段階から選べる。",
  "playUrl": "/play/shogi-vs-cpu/",
  "genre": "puzzle",
  "devices": ["pc", "mobile-portrait"],
  "ageRange": "8歳〜",
  "players": "ひとり用",
  "difficulty": "むずかしめ"
}
```

`site/content/games/character-tactics.json`:

```json
{
  "slug": "character-tactics",
  "title": "とりでの なかまたち",
  "description": "4人のなかまを動かして、島のとりでを守るシミュレーションゲーム。",
  "playUrl": "/play/character-tactics/",
  "genre": "simulation",
  "devices": ["pc", "mobile-landscape"],
  "ageRange": "6〜10歳",
  "players": "ひとり用",
  "difficulty": "ふつう"
}
```

- [ ] **Step 8: ビルドが通ることを確認する**

Run: `cd site && npm run build`
Expected: 成功

- [ ] **Step 9: コミット**

```bash
git add site/lib/devices.ts site/lib/games.ts site/lib/games.test.ts site/content/games/
git commit -m "feat(site): ゲームデータに対応デバイス(devices)を必須フィールドとして追加"
```

---

### Task 3: `controls` フィールドの追加

操作方法を任意フィールドとして追加する。

`rungame-sample` にのみ値を入れる。この値は `origin/main` のコードから読み取れる事実に基づく（`src/scenes/Game.ts` の `keydown-SPACE` / `keydown-UP` / `pointerdown`、`src/utils/jumpController.ts` の `maxJumps = 2`、`src/utils/orientationLock.ts` の `lock('landscape')`）。残る2件は spec のとおり実機確認後に追記するため、このタスクでは設定しない。1件だけ入れるのは、Task 5 の表示を「値がある場合」「値が無い場合」の両方で確認できるようにするためでもある。

**Files:**
- Modify: `site/lib/games.ts`
- Modify: `site/lib/games.test.ts`
- Modify: `site/content/games/rungame-sample.json`

**Interfaces:**
- Consumes: `validateGame(data, file)`、`Game` 型（Task 1、Task 2）
- Produces: `Game` 型に `controls?: string[]`（任意）が追加される

- [ ] **Step 1: 失敗するテストを書く**

`site/lib/games.test.ts` の `describe("validateGame", ...)` の中に追記する。

```ts
  it("controls が配列でなければエラーになる", () => {
    expect(() =>
      validateGame({ ...VALID_GAME, controls: "タップでジャンプ" }, "sample.json")
    ).toThrow(/"controls"/);
  });

  it("controls に空文字が含まれていればエラーになる", () => {
    expect(() =>
      validateGame(
        { ...VALID_GAME, controls: ["タップでジャンプ", ""] },
        "sample.json"
      )
    ).toThrow(/"controls"/);
  });

  it("controls が未設定でも通る", () => {
    expect(validateGame(VALID_GAME, "sample.json")).toEqual(VALID_GAME);
  });

  it("controls に文字列の配列を指定できる", () => {
    const game = { ...VALID_GAME, controls: ["タップでジャンプ"] };
    expect(validateGame(game, "sample.json")).toEqual(game);
  });
```

- [ ] **Step 2: テストを実行して失敗することを確認する**

Run: `cd site && npm test`
Expected: FAIL。`controls` の検証が存在しないため、エラーを期待する2件が失敗する。

- [ ] **Step 3: `site/lib/games.ts` にバリデーションを追加する**

`Game` 型に `controls` を追加する（`images` の上）。

```ts
  controls?: string[];
  images?: string[];
  featured?: boolean;
```

`validateGame` の `images` の検証ブロックの直前に追加する。

```ts
  const controls = record.controls;
  if (controls !== undefined) {
    if (
      !Array.isArray(controls) ||
      !controls.every(
        (control) => typeof control === "string" && control.trim() !== ""
      )
    ) {
      throw new Error(
        `content/games/${file}: "controls" は空でない文字列の配列である必要があります`
      );
    }
  }
```

- [ ] **Step 4: テストを実行して通ることを確認する**

Run: `cd site && npm test`
Expected: PASS（18件）

- [ ] **Step 5: `rungame-sample.json` に `controls` を追加する**

```json
{
  "slug": "rungame-sample",
  "title": "Space Runner",
  "description": "5〜8歳向け宇宙テーマのエンドレスランナーゲーム。",
  "playUrl": "/play/rungame-sample/",
  "genre": "action",
  "devices": ["pc", "mobile-landscape"],
  "controls": [
    "スペースキー・↑キー・画面タップのどれかでジャンプ",
    "空中でもう一度でダブルジャンプ",
    "スマホでは自動で横向きに固定されます"
  ],
  "ageRange": "5〜8歳",
  "players": "ひとり用",
  "difficulty": "やさしめ",
  "featured": true
}
```

- [ ] **Step 6: ビルドが通ることを確認する**

Run: `cd site && npm run build`
Expected: 成功

- [ ] **Step 7: コミット**

```bash
git add site/lib/games.ts site/lib/games.test.ts site/content/games/rungame-sample.json
git commit -m "feat(site): ゲームデータに操作方法(controls)を任意フィールドとして追加"
```

---

### Task 4: 対応デバイスをバッジとして表示する

`MetaBadges` に `devices` を渡し、既存の年齢・人数・難易度バッジと同じ見た目で並べる。バッジのクラス名が4箇所に重複するため、定数に切り出す。

**Files:**
- Modify: `site/components/MetaBadges.tsx`
- Modify: `site/components/GameCard.tsx`
- Modify: `site/app/games/[slug]/page.tsx`

**Interfaces:**
- Consumes: `DEVICES`、`DeviceKey`（Task 2）、`Game` 型の `devices`（Task 2）
- Produces: `MetaBadges` の props に `devices: DeviceKey[]` が必須で追加される。以降このコンポーネントを使う箇所はすべて `devices` を渡す必要がある

- [ ] **Step 1: `MetaBadges.tsx` を書き換える**

ファイル全体を次に置き換える。

```tsx
import { DEVICES, type DeviceKey } from "../lib/devices";

const BADGE_CLASS =
  "rounded border border-neutral-200 bg-white px-2 py-0.5 text-xs text-neutral-600";

export function MetaBadges({
  ageRange,
  players,
  difficulty,
  devices,
}: {
  ageRange: string;
  players: string;
  difficulty: string;
  devices: DeviceKey[];
}) {
  return (
    <div className="flex flex-wrap gap-2">
      <span className={BADGE_CLASS}>👶 {ageRange}</span>
      <span className={BADGE_CLASS}>🎮 {players}</span>
      <span className={BADGE_CLASS}>⭐ {difficulty}</span>
      {devices.map((device) => (
        <span key={device} className={BADGE_CLASS}>
          {DEVICES[device].icon} {DEVICES[device].label}
        </span>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: ビルドして型エラーになることを確認する**

Run: `cd site && npm run build`
Expected: FAIL。`GameCard.tsx` と `app/games/[slug]/page.tsx` が `devices` を渡していないため、必須 props の欠落として型エラーになる。

補足: `tsconfig.json` が `"strict": false` のため、環境によっては型エラーにならずビルドが通る場合がある。その場合はこのステップを「ビルドが通ること」の確認として扱い、次のステップへ進む（Step 5 の目視確認でバッジが表示されないことに気付ける）。

- [ ] **Step 3: `GameCard.tsx` で `devices` を渡す**

`MetaBadges` の呼び出しを次に変更する。他の箇所は変更しない。

```tsx
          <MetaBadges
            ageRange={game.ageRange}
            players={game.players}
            difficulty={game.difficulty}
            devices={game.devices}
          />
```

- [ ] **Step 4: 詳細ページで `devices` を渡す**

`site/app/games/[slug]/page.tsx` の `MetaBadges` の呼び出しを次に変更する。

```tsx
        <MetaBadges
          ageRange={game.ageRange}
          players={game.players}
          difficulty={game.difficulty}
          devices={game.devices}
        />
```

- [ ] **Step 5: ビルドと目視確認**

Run: `cd site && npm run build`
Expected: 成功

Run: `cd site && npm run dev`
確認する内容:
- `http://localhost:3000/games` で、各カードに「💻 PC」と各ゲームのデバイスバッジが表示される
- `http://localhost:3000/games/shogi-vs-cpu/` で「📱 スマホ・タブレット（縦向き）」が表示される
- ブラウザ幅を375px程度に狭め、バッジが5個並んでも折り返して崩れないこと

確認後、開発サーバを停止する。

- [ ] **Step 6: コミット**

```bash
git add site/components/MetaBadges.tsx site/components/GameCard.tsx "site/app/games/[slug]/page.tsx"
git commit -m "feat(site): 対応デバイスをメタ情報バッジとして表示"
```

---

### Task 5: 詳細ページに「あそびかた」を表示する

`controls` が設定されているゲームで、詳細ページに操作方法を表示する。

配置はプレイボタンの下にする。spec には「説明文の下」と書いてあるが、説明文の直後に置くとプレイボタンが下へ押し出される。プレイボタンが最初の画面に収まっている方が、子供が使う場面では扱いやすいため、ボタンより後ろに置く。

**Files:**
- Modify: `site/app/games/[slug]/page.tsx`

**Interfaces:**
- Consumes: `Game` 型の `controls?: string[]`（Task 3）
- Produces: なし

- [ ] **Step 1: 「あそびかた」セクションを追加する**

`site/app/games/[slug]/page.tsx` のプレイボタン（`<a href={game.playUrl}>…</a>`）の直後、`</main>` の直前に追加する。

```tsx
      {game.controls && game.controls.length > 0 && (
        <section className="mt-8">
          <h2 className="text-base font-bold text-neutral-900">あそびかた</h2>
          <ul className="mt-2 list-disc pl-5 text-sm leading-relaxed text-neutral-600">
            {game.controls.map((control) => (
              <li key={control}>{control}</li>
            ))}
          </ul>
        </section>
      )}
```

- [ ] **Step 2: ビルドと目視確認**

Run: `cd site && npm run build`
Expected: 成功

Run: `cd site && npm run dev`
確認する内容:
- `http://localhost:3000/games/rungame-sample/` にプレイボタンの下へ「あそびかた」が3項目の箇条書きで表示される
- `http://localhost:3000/games/shogi-vs-cpu/` には「あそびかた」の見出し自体が表示されない（`controls` 未設定のため）

確認後、開発サーバを停止する。

- [ ] **Step 3: コミット**

```bash
git add "site/app/games/[slug]/page.tsx"
git commit -m "feat(site): 詳細ページに操作方法(あそびかた)セクションを追加"
```

---

### Task 6: 画像表示を 16:9 に統一しスクリーンショットの置き場所を用意する

一覧カードと詳細メイン画像の固定高さを `aspect-video` に置き換え、16:9 の画像を切り取らずに表示する。あわせて `site/public/screenshots/` を作成する。

**Files:**
- Modify: `site/components/GameCard.tsx`
- Modify: `site/components/GameGallery.tsx`
- Create: `site/public/screenshots/.gitkeep`

**Interfaces:**
- Consumes: なし
- Produces: なし

- [ ] **Step 1: `GameCard.tsx` のサムネイル領域を `aspect-video` にする**

```tsx
      <div className="aspect-video w-full">
        <GameThumbnail genre={game.genre} images={game.images} title={game.title} />
      </div>
```

（変更前は `<div className="h-40 w-full">`）

- [ ] **Step 2: `GameGallery.tsx` のプレースホルダーを `aspect-video` にする**

画像が無い場合の早期 return を次に変更する。

```tsx
    return (
      <div
        className={`flex aspect-video w-full items-center justify-center rounded-lg text-6xl font-bold text-neutral-400 ${GENRES[genre].placeholderClassName}`}
      >
        {title.charAt(0)}
      </div>
    );
```

（変更前は `flex h-48 w-full … sm:h-72`）

- [ ] **Step 3: `GameGallery.tsx` のメイン画像領域を `aspect-video` にする**

```tsx
      <div
        className="aspect-video w-full overflow-hidden rounded-lg"
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
```

（変更前は `h-48 w-full overflow-hidden rounded-lg sm:h-72`）

サムネイルボタンの `h-16 w-16` は変更しない。

- [ ] **Step 4: スクリーンショットの置き場所を作成する**

```bash
mkdir -p site/public/screenshots
printf '' > site/public/screenshots/.gitkeep
```

- [ ] **Step 5: ビルドと目視確認**

Run: `cd site && npm run build`
Expected: 成功

Run: `cd site && npm run dev`
確認する内容:
- `http://localhost:3000/games` のカードのプレースホルダー領域が横長（16:9）になっている
- `http://localhost:3000/games/rungame-sample/` のメイン画像領域が 16:9 になり、以前より縦に大きくなっている
- ブラウザ幅を375px程度に狭め、カードが縦に潰れたり溢れたりしないこと

確認後、開発サーバを停止する。

- [ ] **Step 6: コミット**

```bash
git add site/components/GameCard.tsx site/components/GameGallery.tsx site/public/screenshots/.gitkeep
git commit -m "feat(site): 画像表示を16:9に統一しスクリーンショット配置先を用意"
```

---

### Task 7: 正典ドキュメントの更新

`new-game` skill と `README.md` を現在の仕様に合わせる。この2つが「今どう動くか」を表す正典であり、`docs/superpowers/` 配下の既存 spec は作成時点のログとして更新しない。

**Files:**
- Modify: `.claude/skills/new-game/SKILL.md`（手順5）
- Modify: `README.md`（「site/ (Next.js カタログサイト)」節）

**Interfaces:**
- Consumes: Task 2・Task 3・Task 6 で確定した仕様
- Produces: なし

- [ ] **Step 1: `new-game` skill の手順5の JSON テンプレートを更新する**

`.claude/skills/new-game/SKILL.md` の手順5にある JSON ブロックを次に差し替える。

```json
{
  "slug": "<slug>",
  "title": "<ゲームタイトル>",
  "description": "<説明文>",
  "playUrl": "/play/<slug>/",
  "genre": "<GENRES(site/lib/genres.ts)のいずれかのキー。例: action>",
  "devices": ["<DEVICES(site/lib/devices.ts)のいずれかのキー。例: pc>"],
  "ageRange": "<対象年齢。例: 5〜8歳>",
  "players": "<プレイ人数。例: ひとり用>",
  "difficulty": "<難易度。例: やさしめ>"
}
```

- [ ] **Step 2: 手順5の説明文にフィールドの追加分を記載する**

JSON ブロックの直後にある `images` の説明（「`images` (screenshot画像パスの配列)は任意フィールド。…」で始まる段落）を、次の内容に差し替える。

```markdown
`devices` は必須で、`site/lib/devices.ts` の `DEVICES` に定義されたキー(`pc` / `mobile-landscape` / `mobile-portrait`)を1つ以上、重複なく指定する。PCとスマホの両方に対応するなら `["pc", "mobile-landscape"]` のように複数指定する。

任意フィールドは次の3つ。

| フィールド | 内容 |
|---|---|
| `controls` | 操作方法。空でない文字列の配列。詳細ページに「あそびかた」として箇条書きで表示される |
| `images` | スクリーンショットのパスの配列(下記「スクリーンショットの規約」参照) |
| `featured` | `true` にするとトップページのピックアップに表示される |

既存の `site/content/games/rungame-sample.json` も参考にできる。

### スクリーンショットの規約

| 項目 | 規約 |
|---|---|
| 置き場所 | `site/public/screenshots/<slug>/` |
| ファイル名 | `01.png`, `02.png` の連番 |
| JSONでの参照 | `"images": ["/screenshots/<slug>/01.png"]` |
| 枚数 | 1〜5点。先頭のファイルが一覧カードのサムネイルになる |
| 比率 | 16:9。表示側も16:9のため、この比率なら切り取られない |
| 解像度 | 1280×720 を基本 |
| ファイルサイズ | 1枚あたり300KB以内が目安。`next.config.js` で `images: { unoptimized: true }` を指定しており画像最適化は動作しないため、超える場合はWebPを使う |

ゲームの論理解像度が16:9の場合(例: `rungame-sample` は720×405、`character-tactics` は960×540)、ブラウザのウィンドウ比率が16:9でないと描画領域の周囲に余白が入る。描画領域だけを切り出すか、ウィンドウを16:9に合わせて撮影する。
```

- [ ] **Step 3: skill の記述が実装と一致していることを確認する**

Run: `grep -n "mobile-landscape\|screenshots" .claude/skills/new-game/SKILL.md site/lib/devices.ts`
Expected: skill に書いたキー名（`pc` / `mobile-landscape` / `mobile-portrait`）が `site/lib/devices.ts` の定義と一致していること。

- [ ] **Step 4: `README.md` の必須フィールドの説明を更新する**

「### site/ (Next.js カタログサイト)」節の次の一文を探す。

> `slug`/`title`/`description`/`playUrl`/`genre`/`ageRange`/`players`/`difficulty` が必須で、`genre` は `site/lib/genres.ts` の `GENRES` に定義されたキーのいずれかである必要がある(`site/lib/games.ts` の `getAllGames()` がビルド時に検証し、不正な場合はエラーになる)。フィールドの詳細は `.claude/skills/new-game/SKILL.md` 参照。

これを次に差し替える。

```markdown
`slug`/`title`/`description`/`playUrl`/`genre`/`devices`/`ageRange`/`players`/`difficulty` が必須。`genre` は `site/lib/genres.ts` の `GENRES` に、`devices` は `site/lib/devices.ts` の `DEVICES` に定義されたキーである必要がある(`site/lib/games.ts` の `getAllGames()` がビルド時に検証し、不正な場合はエラーになる)。スクリーンショットは `site/public/screenshots/<slug>/` に16:9で置く。フィールドとアセットの詳細は `.claude/skills/new-game/SKILL.md` 参照。
```

- [ ] **Step 5: `README.md` の開発コマンドにテストを追記する**

「### site/ (Next.js カタログサイト)」節のコマンドブロックを次に差し替える。

````markdown
```bash
cd site
npm install
npm run dev    # 開発サーバ
npm test       # Vitest でバリデーションのテストを実行
npm run build  # 静的書き出し (out/)
```
````

- [ ] **Step 6: 最終確認**

Run: `cd site && npm test && npm run build`
Expected: どちらも成功

- [ ] **Step 7: コミット**

```bash
git add .claude/skills/new-game/SKILL.md README.md
git commit -m "docs: devices/controls とスクリーンショット規約を正典ドキュメントに反映"
```

---

## 実装完了後に残る手作業

計画の実行では完了しない。ユーザーが行う。

1. **スクリーンショットの撮影と配置** — 3ゲーム分を `site/public/screenshots/<slug>/01.png` 以降に置き、各 JSON の `images` に追記する
2. **`shogi-vs-cpu` の `devices` の実機確認** — 現在の値 `["pc", "mobile-portrait"]` はコードからの推論。実機で横持ちが快適なら `mobile-landscape` を追加または差し替える
3. **`shogi-vs-cpu` / `character-tactics` の `controls` の記載** — 実機で操作を確認してから各 JSON に追記する
4. **デプロイ** — `main` へのマージ後、`Site (Next.js)` ワークフローの production environment 承認
