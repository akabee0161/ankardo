# 幼児向け知育ゲーム 工程 3（ひな形と残り 8 本） Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** なまえタッチ（name-touch）の共通部分を ankardo のひな形 `templates/chiiku-game/` に切り出し、1 つのスクリプトで新しい知育ゲームのリポジトリの中身を作れるようにする。あわせて、残り 8 本を作る順と 1 本ごとの流れを決める。

**Architecture:** ひな形は、そのまま `npm ci && npm test && npm run build` が通る Vite + TypeScript のプロジェクト一式で、slug・題・日付だけを置き換え用の文字にしておく。`scripts/copy-template.sh` が空のゲームのリポジトリへ写して置き換え、写した元の commit を `template.md` に書く（forge・共通素材と同じ「写した後は各ゲームで自由に直す」扱い）。プレビューのワークフローは、ひな形に複製を持たず、正本の `.claude/skills/new-game/preview.yml` をスクリプトが写す。

**Tech Stack:** bash（スクリプトとそのテスト）、Vite 5・TypeScript 5・Vitest 2（jsdom）・Biome 1.9・wrangler 4（ひな形）、npm 10（Node 22。ロックファイル）

**Spec:** `docs/superpowers/specs/2026-11-24-chiiku-games-design.md`（工程 1・2 の計画は `docs/superpowers/plans/2026-11-24-chiiku-games-step1-2.md`。どちらもログ。「20 種類」「fish」「うみ」は 21 種類・`sea`・「みずのいきもの」に読み替える）

## 依頼者が決めたこと（2026-11-26）

- 保護者向けの「？」（`help.ts`）はひな形に入れる
- PR のときに動く CI（pull_request）は、ひな形に足さない
- `deploy.yml` に concurrency は足さない
- カタログのなまえタッチのスクリーンショットの撮り直しは、工程 3 の最初にやる（Task 0）

## Global Constraints

- 字を読めない子ども向け: 指示は声、ボタンは絵だけ。字は親のための題・クレジット・「？」の説明だけ
- 時間制限・ゲームオーバー・点数なし。記録はサーバーにも端末にも残さない（`localStorage` も使わない）
- 消音スイッチは無視しない（利用者の意思）。`audio.ts` の `unlock()` の決まりを変えない
- 「はじめる」のタッチの中（`await` の前）で `audio.unlock()` を呼ぶ。ゲームを終えるボタンは長押し 1.5 秒でタイトル画面に戻る
- 素材は ankardo の `shared-assets/chiiku/` が正。ゲームの `public/chiiku/` は `copy-assets.sh` のコピーで、手で直さない。ひな形には素材を入れない
- git: 機能ブランチ → `develop` への PR。`develop`・`main` へ直接 push しない。マージは依頼者
- ゲームの `package-lock.json` は Node 22 の npm 10 で、`node_modules` の無い場所で作る（`npx npm@10 install --package-lock-only`）。出す前に `npx npm@10 ci` が通ることと、全パッケージに `integrity` があることを確かめる
- slug は `^[a-z0-9]+(-[a-z0-9]+)*$`、42 文字以内（プレビューのホスト名 `develop-ankardo-game-<slug>` を 63 文字以内にするため）

## Review Focus

1. 題に `<`・`&`・`'`・`"`・`\`・改行が入る → `index.html` の `<title>` や `main.ts` の文字列が壊れるので、スクリプトが何も書かずに止まる（Task 1 のテスト）
2. `gh repo create --add-readme` などで、写し先に README などが既にある → 何も書かずに止まる。`.git` だけなら進む（Task 1）
3. ひな形の作業中に未コミットの変更がある → `template.md` の commit に `+dirty` が付く（Task 1）
4. git のフックの中から呼ばれて `GIT_DIR` などが入っている → 呼び出し元ではなく ankardo の commit を書く（copy-forge.sh と同じく `git rev-parse --local-env-vars` を外す。Task 1）
5. 写した直後で、まだ `copy-assets.sh` を流していない → テストとビルドは通る（素材は実行時に読むだけ）。素材を入れずに出すと画面が「読み込めませんでした」になるので、確認のスクリプトは素材を入れてからビルドする（Task 3）

## 依頼者の手作業（依存の順）

| 順 | いつ | 作業 |
|---|---|---|
| 1 | Task 0 の後 | 撮り直したスクリーンショットを見て承認し、ankardo の PR（`fix/name-touch-screenshot` → `main`）をマージする |
| 2 | Task 2 の前 | 実機（iPhone・iPad。電話や画面ロックから戻したとき）で、なまえタッチの音の解禁と再開、「？」の表示を確かめる（name-touch の HANDOVER.md の「次にやること」）。消音スイッチを入れると鳴らないのが正しい。直すところが出たら、先に name-touch で直してから切り出す |
| 3 | Task 4 の後 | ankardo の PR（`feat/chiiku-template` → `main`）と、name-touch の PR（`docs/template-source` → `develop`）をマージする |
| 4 | 8 本それぞれ | 下の「1 本ごとの流れ」の表 |

## File Structure

```text
ankardo/
├── templates/chiiku-game/            # 新規。ひな形（このまま npm ci・テスト・ビルドが通る）
│   ├── package.json  package-lock.json  tsconfig.json  vite.config.ts  vitest.config.ts
│   ├── biome.json  wrangler.toml  index.html  .gitignore
│   ├── .github/workflows/deploy.yml  # name-touch と同じ（concurrency なし）。preview.yml は置かない
│   ├── CLAUDE.md  HANDOVER.md  README.md
│   └── src/
│       ├── main.ts                   # 素材の読み込み → タイトル画面 → startGame
│       ├── style.css                 # ゲームごとの見た目（ひな形では空に近い）
│       ├── game/game.ts game.test.ts # 遊びの置き場（ひな形は ⏏ と ？ だけの画面）
│       └── common/                   # name-touch の src/common/ ＋ 下の 2 つ
│           ├── assets.ts audio.ts long-press.ts screens.ts help.ts common.css（と各テスト）
│           ├── exit-button.ts exit-button.test.ts   # 新規。⏏ の長押し（name-touch の game から）
│           └── bounce.ts bounce.test.ts             # 新規。はねる動き（同上）
├── scripts/
│   ├── copy-template.sh  copy-template.test.sh      # 新規
│   └── check-chiiku-template.sh                     # 新規。写す → 素材 → npm ci → テスト・lint・ビルド
├── site/public/screenshots/name-touch/01.png       # Task 0 で撮り直す
├── .claude/skills/new-game/SKILL.md                # 「知育ゲームをひな形から作る」を足す
├── README.md  HANDOVER.md
name-touch/CLAUDE.md                                # 共通の直しはひな形が正、と 1 行
```

置き換え用の文字（ひな形の中のどのファイルにも、この 3 つ以外の置き換えは無い）:

| 文字 | 置き換える先 | 使う場所 |
|---|---|---|
| `chiiku-template-slug` | slug | `package.json`・`package-lock.json` の name、`vite.config.ts` の base・outDir、`wrangler.toml` の name・route、各文書 |
| `__TITLE__` | 題（例「どれかな？」） | `index.html` の `<title>`、`main.ts` のタイトル画面、`CLAUDE.md`・`README.md`・`HANDOVER.md` の見出し |
| `__DATE__` | 写した日（`date +%F`） | `wrangler.toml` の `compatibility_date` |

slug の置き換え用の文字を `__SLUG__` にしないのは、npm が `_` で始まる name を受け付けず、ひな形の中でロックファイルを作れないため。

---

### Task 0: カタログのなまえタッチのスクリーンショットを撮り直す

**Files:**
- Modify: `site/public/screenshots/name-touch/01.png`

- [ ] **Step 1:** `main` から `fix/name-touch-screenshot` を切る
- [ ] **Step 2:** Playwright（入っている Chromium）で `https://ankardo.com/play/name-touch/` を 1280×720・deviceScaleFactor 1 で開き、▶ を押して最初のページ（どうぶつ）が出たところを撮る。PNG で 300KB を超えたら WebP にする（拡張子が変わるなら `site/content/games/name-touch.json` の `images` も直す）
- [ ] **Step 3:** 今の画像と新しい画像を data URI で並べた HTML を Artifact で依頼者に見せ、承認をもらう（承認までコミットしない）
- [ ] **Step 4:** `cd site && npm test && npm run build` が通ることを確かめ、コミットして push し、`main` 向けの PR を作る

```bash
git commit -m "fix: カタログのなまえタッチのスクリーンショットを、絵の大きさをそろえた版で撮り直す"
```

### Task 1: ひな形を写すスクリプト `copy-template.sh`

**Files:**
- Create: `scripts/copy-template.sh`
- Test: `scripts/copy-template.test.sh`

**Interfaces:**
- Produces: `./scripts/copy-template.sh chiiku-game <slug> <題> <ゲームのフォルダ>`。終了コード 0 で成功、引数の誤りは 2、それ以外の失敗は 1。成功時に `コピーした: <フォルダ>（templates/chiiku-game の <commit>）` を 1 行出す
- 環境変数 `TEMPLATE_ROOT`（テスト用。既定は ankardo の `templates/`）と `PREVIEW_TEMPLATE`（テスト用。既定は `.claude/skills/new-game/preview.yml`）

- [ ] **Step 1: テストを書く。** `copy-forge.test.sh` と同じ形（`mktemp -d`、`fail`、ネットワークを使わない）。手元に作った偽のひな形（置き換え用の 3 つの文字を含む `package.json`・`index.html`・`src/main.ts`・`.github/workflows/deploy.yml`、置き換え用の文字を含まないバイナリ 1 つ）と偽の `preview.yml` を、`git init` したリポジトリに入れて使う。確かめること:
  1. `.git` だけがあるフォルダへ写すと、偽のひな形のファイルが全部入り、3 つの文字がどのファイルにも残らない（`grep -r` が 0 件）。`chiiku-template-slug` は slug、`__TITLE__` は題、`__DATE__` は今日になっている
  2. `.github/workflows/preview.yml` が偽の `preview.yml` とバイト単位で同じ（`cmp`）。バイナリも元と同じ
  3. `template.md` に、ひな形の commit と今日の日付がある。ひな形に未コミットの変更があると `+dirty` が付く
  4. 写し先に `.git` 以外のファイル（`README.md`）があると終了コード 1 で、何も増えない（実行前後の `find` が同じ）
  5. slug が `Bad`・`-x`・`a--b`・`a_b`・43 文字、題が空・`<`・`&`・`'`・`"`・`\`・改行を含む、ひな形の名前が `chiiku-game` 以外、引数が 4 つでない、のどれでも終了コード 2 で、何も増えない
  6. `GIT_DIR` を別のリポジトリに向けて呼んでも、`template.md` の commit は偽のひな形のもの
  7. 写し先が無いフォルダなら終了コード 1
- [ ] **Step 2:** `bash scripts/copy-template.test.sh` が、スクリプトが無いので落ちることを確かめる
- [ ] **Step 3: 実装する。** 作りは `copy-forge.sh` にならう（`set -euo pipefail`、git の場所の変数を外す、写し先の中の一時フォルダ `.copy-template.XXXXXX` で組み立ててから中身を `mv`、`trap` で一時フォルダを消す）。ひな形は `git -C <ankardo> ls-files -z templates/chiiku-game` に載っているファイルだけを写す（`node_modules`・`out` を拾わない）。置き換えは、テキストのファイル（`grep -Iq .` で判定）だけを、Python の `str.replace` で行う（sed の区切り文字や `&` の扱いで題が化けないように）。commit は `git -C <ankardo> rev-parse HEAD`、未コミットの変更は `git -C <ankardo> status --porcelain -- templates/chiiku-game` が空でなければ `+dirty`
- [ ] **Step 4:** `bash scripts/copy-template.test.sh` と `bash scripts/copy-forge.test.sh`・`bash scripts/copy-assets.test.sh` が通る
- [ ] **Step 5: コミット**（ブランチ `feat/chiiku-template` を `main` から切る）

```bash
git commit -m "feat: 知育ゲームのひな形を新しいリポジトリへ写すスクリプトを足す"
```

### Task 2: ひな形の中身 `templates/chiiku-game/`

依頼者の手作業 2（実機の確認）が済んでから始める。

**Files:**
- Create: File Structure の `templates/chiiku-game/` の全部
- 写す元: name-touch の `develop`（33476b1）の `src/common/*`・`biome.json`・`tsconfig.json`・`vitest.config.ts`・`.gitignore`・`.github/workflows/deploy.yml`・`package.json`

**Interfaces:**
- Produces（ゲームが使う。8 本の計画はこの名前で書く）:
  - `src/common/assets.ts`・`audio.ts`・`long-press.ts`・`screens.ts`・`help.ts`: name-touch と同じ（`loadItems(url): Promise<ItemsFile>`、`createAudio(): AudioPlayer`、`attachLongPress(el, ms, onFire): () => void`、`showTitle(root, { title, credits, unlock?, onStart })`、`createHelp(): HTMLElement`）
  - `src/common/exit-button.ts`: `export const EXIT_HOLD_MS = 1500`、`createExitButton(onExit: () => void): HTMLButtonElement`（字は `⏏`、`aria-label` は `おわる（ながおし）`、class は `exit-button`。画面を描き直しても同じボタンを使い回せる）
  - `src/common/bounce.ts`: `export const BOUNCE_MS = 400`、`createBouncer(): { bounce(el: HTMLElement): void; clear(): void }`（続けて呼ぶと最初からやり直す。`clear` は全部のタイマーを止めて class を外す）。CSS は `common.css` の `.bounce`（`@keyframes bounce` と `prefers-reduced-motion` の扱いは name-touch の `style.css` のまま）
  - `src/game/game.ts`: `export type GameDeps = { file: ItemsFile; audio: AudioPlayer; onExit: () => void }`、`startGame(root: HTMLElement, deps: GameDeps): void`

- [ ] **Step 1: テストを写す・書く。** name-touch の `src/common/*.test.ts` 5 つをそのまま写す。足すテスト:
  - `exit-button.test.ts`: `EXIT_HOLD_MS` 押し続けると `onExit` が 1 回呼ばれる／1499ms で離すと呼ばれない／`aria-label` が `おわる（ながおし）`
  - `bounce.test.ts`: `bounce(el)` で `el` に `bounce` が付き、`BOUNCE_MS` 後に外れる／途中でもう一度呼ぶと、そこから `BOUNCE_MS` 付いたまま／`clear()` で即座に外れ、後からタイマーが動かない
  - `game.test.ts`: `startGame` の画面に `⏏` と `？` がある／`⏏` を 1.5 秒長押しすると `audio.stop` と `onExit` が呼ばれる
- [ ] **Step 2:** テストが、実装が無いので落ちることを確かめる（下の Step 4 の環境で）
- [ ] **Step 3: 実装する。**
  - `src/common/` に name-touch の 5 つと `common.css` を写す。各ファイル先頭の「知育ゲームで共通。ゲームごとの決まりを入れない」の注記は残す
  - `exit-button.ts`・`bounce.ts` は name-touch の `src/game/name-touch.ts` の該当部分を関数にしたもの。`.exit-button`・`.bounce`・`@keyframes bounce` の CSS を `common.css` へ移す（`.bounce` は、付けた要素そのものをはねさせる。name-touch のように中の絵だけをはねさせたいゲームは、絵に付ける）
  - `main.ts`: name-touch の `main.ts` と同じ流れ。題は `__TITLE__`、`CREDITS` は `['VOICEVOX:ずんだもん']` で、「鳴き声を入れたゲーム（`copy-assets.sh` に `--no-cry` を付けない）は、`public/chiiku/CREDITS.md` の 3 行にする」と注記する
  - `game.ts`: `play-screen` の `main` に `createExitButton`（`audio.stop()` してから `onExit`）と `createHelp()` だけを置く。「ここに遊びを書く」と 1 行の注記
  - 設定のファイル: `package.json` の name は `chiiku-template-slug`、devDependencies は name-touch と同じ。`vite.config.ts` の base は `/play/chiiku-template-slug/`、outDir は `out/play/chiiku-template-slug`。`wrangler.toml` は name-touch と同じ形（`preview_urls = true`・空の `[previews]`）で、name・route・`compatibility_date = "__DATE__"` を置き換え用の文字にする。`biome.json`・`tsconfig.json`・`vitest.config.ts`・`.gitignore`・`deploy.yml` は name-touch のまま
  - `CLAUDE.md`: name-touch の `CLAUDE.md` を、なまえタッチ固有の文（「なまえタッチは鳴き声を鳴らさない」など）を外して一般化する。足すこと: `src/common/` は ankardo のひな形 `templates/chiiku-game/` の写しで、写した元は `template.md`。共通部分を直したら、ほかのゲームにも要るかを考え、要るなら ankardo のひな形にも同じ直しを入れる（PR を分ける）
  - `HANDOVER.md`: `## 進捗` の欄（作業: 幼児向け知育ゲーム。工程は ankardo の HANDOVER.md と同じ 3 つ）を題の直後に置く
  - `README.md`: 遊び方・確認のコマンド・素材のコピーの仕方だけの短いもの
- [ ] **Step 4: ひな形の中でロックファイルを作り、テストを流す。** 空の作業フォルダ（スクラッチパッド）に `package.json` だけを置いて `npx npm@10 install --package-lock-only` し、できた `package-lock.json` をひな形に置く。別の作業フォルダにひな形を写して `npx npm@10 ci && npx vitest run && npx biome check . && npx tsc --noEmit` が通る。全パッケージに `integrity` があることを確かめる（`node -e` で `packages` を見て、`resolved` のあるもの全部に `integrity` がある）
- [ ] **Step 5: コミット**

```bash
git commit -m "feat: 知育ゲームのひな形（なまえタッチの共通部分・⏏・はねる動き）を足す"
```

### Task 3: ひな形の通しの確認 `check-chiiku-template.sh`

**Files:**
- Create: `scripts/check-chiiku-template.sh`

**Interfaces:**
- Consumes: `copy-template.sh`（Task 1）、`copy-assets.sh`（既存）
- Produces: `./scripts/check-chiiku-template.sh`。引数なし。成功で終了コード 0、どこかで落ちたらそのコマンドの出力を残して 0 以外。ネットワーク（npm の取得）を使う

- [ ] **Step 1: 書く。** `mktemp -d` に `git init` したフォルダを作り、`copy-template.sh chiiku-game check-game 'かくにん' <フォルダ>` → `copy-assets.sh chiiku <フォルダ> --no-cry` → そのフォルダで `npx npm@10 ci && npm test && npx biome check . && npm run build` を流す。最後に `out/play/check-game/index.html` と `out/play/check-game/chiiku/items.json` があることと、`grep -r 'chiiku-template-slug\|__TITLE__\|__DATE__'` が 0 件であることを確かめる
- [ ] **Step 2:** 流して通ることを確かめる。わざと `templates/chiiku-game/src/common/bounce.ts` の `BOUNCE_MS` を 1 にして流すと落ちることも確かめ、戻す
- [ ] **Step 3:** 写したものを `npx vite preview` で開き、Playwright で ▶ → `⏏` と `？` が出る画面になることを 1 枚撮って確かめる（自分で見るだけ。deviceScaleFactor 1）
- [ ] **Step 4: コミット**

```bash
git commit -m "test: 知育ゲームのひな形を写して素材を入れ、テストとビルドが通るかを確かめるスクリプトを足す"
```

### Task 4: 正典を直す

**Files:**
- Modify: `.claude/skills/new-game/SKILL.md`、`README.md`、`HANDOVER.md`
- Modify（name-touch、別 PR）: `name-touch/CLAUDE.md`、`name-touch/HANDOVER.md`

- [ ] **Step 1:** `SKILL.md` に「## 知育ゲームをひな形から作る」を「共通素材を使うなら」の前に足す。中身: (1) GitHub に空のリポジトリを作って clone（README を付けない）、(2) `./scripts/copy-template.sh chiiku-game <slug> <題> <フォルダ>`、(3) `./scripts/copy-assets.sh chiiku <フォルダ> [--no-cry]`（鳴き声を使うかで決める）、(4) ロックファイルはひな形のものをそのまま使い、依存を足したときだけ npm 10 で作り直す、(5) 最初の PR は `main` 向け → 本番の deploy の成功を待つ → `develop` を作る（「確認用のプレビュー」の手順 5・6 と同じ）、(6) 作業ページのリンク集（手順 7）、(7) ひな形を直すときは先に ankardo の `templates/chiiku-game/` を直し、`check-chiiku-template.sh` を通してから各ゲームへ手で写す
- [ ] **Step 2:** `README.md` の「構成」に `templates/chiiku-game/` と 2 つのスクリプトを足し、「共通素材」のテストの行に `bash scripts/copy-template.test.sh` と `./scripts/check-chiiku-template.sh`（ネットワークを使う）を足す
- [ ] **Step 3:** ankardo の `HANDOVER.md` の進捗を直す（段階: `実装（N タスク中 M）`、次にやること: 1 本目 which-one-2）。push して `main` 向けの PR を作る
- [ ] **Step 4:** name-touch で `develop` から `docs/template-source` を切り、`CLAUDE.md` の「共通部分」の節に「`src/common/` は ankardo の `templates/chiiku-game/` に切り出した（`⏏` と はねる動きは、ひな形では `src/common/` に移した）。共通の直しは ankardo のひな形が正」を足す。`HANDOVER.md` の進捗の「次にやること」から切り出しの行を外す。`develop` 向けの PR を作る

---

## 残りの 8 本（計画のあと）

### 作る順

| 順 | slug | 理由・新しく要るもの |
|---|---|---|
| 1 | `which-one-2` | 問題を出すゲームの最初。5 問の区切り・点の並び・つづける／やめるの画面・正解／不正解の音を、先にひな形の `src/common/` に作る。決まり文句「〇〇は どれ？」「そう、〇〇！」の声 |
| 2 | `which-one-4` | 1 の区切りをそのまま使い、選ぶ数と似たものの組を足すだけ |
| 3 | `animal-voice-quiz` | 鳴き声を使う最初のゲーム（`--no-cry` を付けない）。クレジット 3 行と、詳細クレジットのページの公開 |
| 4 | `nakama-match` | 区切りを使う。「おなじ なかまは どれ？」。慣れたら種類で選ぶ（1 回の正解の数で切り替える） |
| 5 | `moji-to-e` | 区切りを使う。ひらがなを画面に出す最初のゲーム。「これは なに？」 |
| 6 | `peekaboo` | 自由遊び。隠れる場所の絵（草むら・箱・葉っぱ）を forge で新しく作る（Modal の枚数と金額を先に伝える）。「ばあ！」 |
| 7 | `moji-trace` | KanjiVG（CC BY-SA 3.0）の取り込みとクレジット。なぞりの判定 |
| 8 | `draw-and-move` | 線画（21 種類）と場面の絵を新しく作る。一番大きい。Phaser を使うかはこのとき決める |

問題を出す 5 本（1〜5）を先に並べ、1 で作った区切りを 4 本で使い回す。新しい絵が要る 3 本（6〜8）は後ろに置き、生成の費用をまとめて相談できるようにする。

### 1 本ごとの流れ

1. そのゲームの小さな計画を書く（遊びの細部・決まり文句の一覧・ひな形に足す共通部分があるか）。依頼者の承認をもらう
2. ひな形に足す共通部分があれば、先に ankardo の `templates/chiiku-game/` に足す PR を出す（`check-chiiku-template.sh` を通す）
3. 決まり文句の声を `shared-assets/tools/voice.py` に足して作り、試聴のページで依頼者に確かめてもらう（アクセントを直してから）
4. リポジトリにひな形と素材を写し、遊びを `src/game/` に書く。最初の PR は `main` 向け
5. ankardo のカタログ登録（`site/content/games/<slug>.json`、`_redirects`、スクリーンショット）の PR
6. `develop` を作り、プレビューが Access の後ろにあることを確かめ、作業ページ（personal-work-hub）のリンク集に足す PR

1 本ごとの依頼者の手作業:

| 順 | 作業 |
|---|---|
| 1 | ゲームの計画の承認と、決まり文句の声の試聴 |
| 2 | GitHub にリポジトリを作る（Claude が `gh repo create` で作ってよいかは、そのとき聞く） |
| 3 | Cloudflare の秘密の値を入れる（`scripts/setup-game-secrets.sh`） |
| 4 | ゲームの最初の PR（→ `main`）のマージ。保護ルールは設けないので、マージで本番に出る |
| 5 | ankardo のカタログ登録の PR と、personal-work-hub のリンクの PR のマージ |
