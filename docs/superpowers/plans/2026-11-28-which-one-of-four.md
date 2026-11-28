# 知育ゲーム 2 本目「どれかな？（4 択）」`which-one-of-four` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 「〇〇は どれ？」と声で聞き、4 枚の絵から選ぶゲームを作って公開する。4 枚には、似たもの（いぬとねこ、トマトとりんご）を一緒に出す問題を混ぜる。

**Architecture:** 1 本目（`which-one-of-two`）と同じ流れ（5 問・点・正解の音 → 声 → 500ms で次へ・区切りの画面）で、選ぶ絵を 4 つにする。共通部分（`src/common/`）・声・音は 1 本目で足してあり、ひな形にも入っているので、**ankardo のひな形にも共通素材にも足すものは無い**。新しいリポジトリ `which-one-of-four` の `src/game/` に、問題の作り方（`questions.ts`・`similar.ts`）とゲーム本体（`game.ts`）・見た目（`style.css`）を書く。`game.ts` は 1 本目のものを写して、選ぶ数を可変にする。

**Tech Stack:** ひな形と同じ（Vite 5・TypeScript 5・Vitest 2・Biome 1.9）。新しい依存は足さない。

**Spec:** `docs/superpowers/specs/2026-11-24-chiiku-games-design.md` の 4 章「共通の決まり」と 6 章の 5 番（ログ。「20 種類」「fish」「うみ」は 21 種類・`sea`・「みずのいきもの」に読み替える）。見本は `akabee0161/which-one-of-two`（`src/game/` と `CLAUDE.md`）。1 本ごとの流れは `docs/superpowers/plans/2026-11-26-chiiku-games-step3-template.md` の「残りの 8 本」。1 本目の計画は `docs/superpowers/plans/2026-11-27-which-one-2.md`（ログ）。

## 依頼者に確かめること（承認のときに）

下は、私が決めた案。違えば、承認のときに直す。

1. **題**: 画面の題とカタログの題は、1 本目の「どれかな？」と見分けるため、`どれかな？（4つ）`。slug は `which-one-of-four`
2. **対象**: `ageRange` は `3歳〜`（設計書の「3 歳」）、`difficulty` は `ふつう`。`devices` は `["pc", "mobile-landscape"]`
3. **似たものの組**（下の `SIMILAR_GROUPS`）: いぬ・ねこ／うし・ぶた／トマト・りんご・いちご／バナナ・とうもろこし／きんぎょ・ふぐ／ちょう・とんぼ。足す・外す絵があれば直す
4. **1 回（5 問）の中身**: 似たものを混ぜる問題が 2 問、ほかの 3 問は似ていない 4 枚。答えは 5 問とも別の絵。4 枚の並びと答えの位置は毎回混ぜる
5. **間違えたとき**: 1 本目と同じ。間違えた絵は揺れて、そのまま残る（3 つ間違えても全部残る）。点は変えない

## Global Constraints

- 1 本目の計画の Global Constraints を全部引き継ぐ: 字を読めない子ども向け（指示は声、ボタンは絵だけ）／時間制限・ゲームオーバー・点数なし／記録は残さない（`localStorage` も使わない）／消音スイッチを無視しない／声は VOICEVOX:ずんだもん／鳴き声は使わない（`copy-assets.sh` に `--no-cry`、クレジットは `VOICEVOX:ずんだもん` の 1 行）
- 決まっていること（1 本目で依頼者が決めた。聞き直さない）: 点は正解ごとに 1 つ灯り、間違えても消えない／正解の音 → 声のあと 500ms（`NEXT_GAP_MS`）で次へ／5 問のあとは ▶（つづける）と 🏠（やめる）で、どちらも通常のタップ／決まり文句の声は承認済み（直さない）
- 触れて選ぶ絵・ボタンは `attachActivate`（`src/common/activate.ts`）で受ける。自分で `pointerdown`・`keydown` を書かない
- 素材は ankardo の `shared-assets/chiiku/` が正で、手で直さない。ゲーム側に 21 種類の一覧を書き写さない（`items.json` を `loadItems` で読む）。**例外**: 似たものの組（`similar.ts`）は ID だけを持ち、`items.json` に無い ID があれば、どの ID かを示して止める
- `package-lock.json` はひな形のまま。依存を足したときだけ npm 10 で作り直す
- 見た目が変わる直し（カードの並べ方など）は、直す前に依頼者に確かめる。画像は HTML + Artifact で見せる
- 進捗の欄（`HANDOVER.md`）だけを直すときは、PR を作らず main へ直接 push する（`~/.claude/rules/progress.md`）。ただし新しいリポジトリの `main` に `HANDOVER.md` が入るまでは、PR のブランチで直す
- CodeRabbit の指摘は、1 件ずつ現在のコードと照らして妥当かを確かめてから直す。共通部分（`src/common/`）を直したら、ankardo のひな形にも要るかを考え、要るなら PR を分ける

## Review Focus

1. 21 種類の実物で 5 問を何度作っても、各問の 4 枚が全部別の絵で、答えが 5 問とも別になる（Task 2）
2. 似たもの問題の 4 枚に、答えと同じ組の絵が 2 枚以上入る。似ていない問題には、同じ組の絵が 2 枚入らない（トマトとりんごが、似ていない問題に一緒に出ない）（Task 2）
3. 似たものの組に `items.json` に無い ID がある、または種類が 4 つ未満で似ていない問題を作れない → 何が足りないかを示して止まる（Task 2）
4. 3 つ間違えたあとに正解 → 3 枚とも揺れて残り、点は 1 つだけ灯り、次へ 1 回だけ進む。正解を受け付けたあとの連打・click だけの起動で二重に進まない（Task 3）
5. 4 枚が、スマホ横向き（高さ約 360px）と PC（1280×720）で、はみ出さず、全部が画面に収まる。カードが指で押せる大きさ（短い辺 100px 以上）を保つ（Task 3）

---

## File Structure

```text
which-one-of-four/   # 新しいリポジトリ（ひな形 templates/chiiku-game を写したもの）
├── src/common/                 # 写し。直さない
├── public/chiiku/              # 素材のコピー（--no-cry）。直さない
└── src/game/
    ├── similar.ts (+ similar.test.ts)   # 新規: SIMILAR_GROUPS（ID の組）と、その検査 checkGroups
    ├── questions.ts (+ questions.test.ts)  # 新規: buildQuestions
    ├── game.ts (+ game.test.ts)         # 新規: 1 本目の game.ts を写し、選ぶ数を可変にする
    └── test-helpers.ts                  # 新規: ITEMS_21（実物と同じ ID・偏り）・seeded（1 本目から写す）
src/style.css                            # 変更: .cards を 4 枚に
CLAUDE.md  README.md  HANDOVER.md        # 新規／変更: 遊びの決まり・進捗

ankardo/
└── site/content/games/which-one-of-four.json  site/public/_redirects  site/public/screenshots/which-one-of-four/01.png   # Task 5
```

---

### Task 1: リポジトリを作り、ひな形と素材を写す

**Files:**
- Create: 新しいリポジトリ `akabee0161/which-one-of-four`（ひな形を写した一式）

**Interfaces:**
- Produces: 動くひな形の `which-one-of-four`（`npx vitest run && npx biome check . && npx tsc --noEmit && npm run build` が通る状態）。`src/common/` は ankardo の main のひな形（PR #41 のあと）と同じ

- [ ] **Step 1（依頼者の手作業）:** 依頼者に、GitHub に空のリポジトリ `which-one-of-four` を作ってよいか確かめる（README・LICENSE を付けない）。あわせて `scripts/setup-game-secrets.sh` で Cloudflare の秘密の値を入れてもらう（`~/workspace/ankardo` から。1 本目と同じ手順）
- [ ] **Step 2:** `~/workspace` に clone し、空コミットで `main` を作って push する（`git commit --allow-empty -m "chore: 初期化"` → `git branch -M main` → `git push -u origin main`）。そのあと `git switch -c feat/which-one-of-four`。git の author が `akabee0161` になっていることを、最初のコミットの前に確かめる
- [ ] **Step 3:** ankardo のルートで `./scripts/copy-template.sh chiiku-game which-one-of-four 'どれかな？（4つ）' ~/workspace/which-one-of-four` → `./scripts/copy-assets.sh chiiku ~/workspace/which-one-of-four --no-cry`
- [ ] **Step 4:** `npm ci && npx vitest run && npx biome check . && npx tsc --noEmit && npm run build` が通る。素材の確認は `CI=true npx vitest run src/common/assets.test.ts`
- [ ] **Step 5: コミット**（`chore: ひな形と共通素材を写す`）。まだ push しない（Task 4 でまとめて出す）

---

### Task 2: 問題の作り方（`similar.ts`・`questions.ts`）

**Files:**
- Create: `src/game/similar.ts`・`src/game/similar.test.ts`・`src/game/questions.ts`・`src/game/questions.test.ts`・`src/game/test-helpers.ts`（`which-one-of-two` の `test-helpers.ts` を写し、`ITEMS_21` を実物の `items.json` と同じ ID に直す）

**Interfaces:**
- Consumes: `ItemsFile`・`Item`（`src/common/assets.ts`）、`ROUND_SIZE`（`src/common/progress.ts`、5）
- Produces:
  - `export const CHOICES = 4`、`export const SIMILAR_QUESTIONS = 2`
  - `export const SIMILAR_GROUPS: readonly (readonly string[])[]` = `[['dog','cat'],['cow','pig'],['tomato','apple','strawberry'],['banana','corn'],['goldfish','pufferfish'],['butterfly','dragonfly']]`
  - `export function checkGroups(file: ItemsFile, groups = SIMILAR_GROUPS): void`（`items.json` に無い ID があれば、その ID を入れた Error を投げる）
  - `export type Question = { answer: Item; choices: Item[]; similar: boolean }`（`choices` は `CHOICES` 個で、`answer` を含み、並びは混ぜてある）
  - `export function buildQuestions(file: ItemsFile, random?: () => number): Question[]`（`ROUND_SIZE` 問。足りないときは、何が足りないかを示す Error）

- [ ] **Step 1: テストを書く**（`questions.test.ts`。実物の `public/chiiku/items.json` があれば実物、無ければ `ITEMS_21`。乱数は `seeded(0..199)` の 200 通りで確かめる）
  - `it('makes 5 questions of 4 different pictures each, and the 5 answers are all different')`: `questions` の長さ `ROUND_SIZE`、各 `choices` の長さ `CHOICES`・ID が全部別・`choices` に `answer` を含む、`answer.id` が 5 つとも別
  - `it('makes exactly 2 similar questions, from 2 different groups')`: `similar: true` が `SIMILAR_QUESTIONS` 問。その `choices` のうち、答えと同じ組の絵が 2 枚以上。2 問の答えの組は別
  - `it('never puts two pictures of the same group in a plain question')`: `similar: false` の問題の `choices` で、同じ組に入る絵が 2 枚以上ない（トマトとりんごが一緒に出ない）
  - `it('puts the answer in every position over many rounds')`: 200 通りで、答えの位置 0〜3 がどれも 1 回以上出る
  - `it('throws a message naming the missing id when a group has an id not in items.json')`、`it('throws a message saying what is missing when there are fewer than 4 categories')`、`it('throws when there are fewer than 5 questions worth of pictures')`（メッセージに、足りない数を入れる）
- [ ] **Step 2: `similar.test.ts` を書く:** `SIMILAR_GROUPS` の ID が、実物の `items.json` に全部ある／どの ID も 2 つ以上の組に入らない／どの組も 2 つ以上の絵を持つ
- [ ] **Step 3:** `npx vitest run src/game` が、実装が無いので落ちることを確かめる
- [ ] **Step 4: 実装する。** 似たもの問題は、答え（組に入る絵からランダム）と、同じ組の絵（最大 `CHOICES - 1` 個）に、組に入らない絵を別々の種類から足して `CHOICES` 個にする。似ていない問題は、4 つの別の種類から 1 枚ずつ取り、同じ組の絵が 2 枚入ったら取り直す。2 つの似たもの問題は、別の組から作る。答えが 5 問とも別になるよう、使った答えは除く。`random` は `Math.random` が既定で、並べ替えは 1 本目の `shuffle`（Fisher–Yates）と同じ
- [ ] **Step 5:** `npx vitest run src/game && npx biome check . && npx tsc --noEmit` が通る
- [ ] **Step 6: コミット**（`feat: 4 択の問題の作り方を足す`）

---

### Task 3: ゲーム本体（`game.ts`・`style.css`）

**Files:**
- Create: `src/game/game.ts`・`src/game/game.test.ts`（どちらも `which-one-of-two` から写す）
- Modify: `src/style.css`（`.cards` を 4 枚に）、`src/main.ts`（ひな形のまま。題が `どれかな？（4つ）` になっていることだけ確かめる）

**Interfaces:**
- Consumes: `buildQuestions`・`Question`（Task 2）、`playCorrect`・`playWrong`（`src/common/feedback.ts`）、`createBouncer`・`WIGGLE_MS`（`src/common/bounce.ts`）、`attachActivate`、`createProgressDots`・`ROUND_SIZE`、`showRoundEnd`、`createExitButton`、`createHelp`（`closeIfOpen` を、区切りの画面へ替える前に呼ぶところまで 1 本目と同じ）
- Produces: `export function startGame(root: HTMLElement, deps: GameDeps): void`、`export const NEXT_GAP_MS = 500`（1 本目と同じ形）

- [ ] **Step 1: `game.test.ts` を、1 本目から写して直す。** 偽の `audio`・`vi.useFakeTimers()`・固定の `random` は同じ。変えるところ: カードは 4 枚／間違いは 3 枚とも揺れて残る
  - `it('shows 4 cards and asks the question')`: `.card` が 4 枚、最初に `voice/ask-<答え>.wav` を `play` する
  - `it('keeps all wrong cards, wiggling, and lights only one dot after the right card')`: 3 枚の間違いを順に触る → 3 枚とも `wiggle`・`.card` は 4 枚のまま・点 0。そのあと正解 → 点 1・次の問題は `NEXT_GAP_MS` のあとに 1 回だけ
  - `it('answers only once when the right card is touched again, or a wrong card after it')`（正解のあとの連打・click だけの起動）
  - 1 本目の、⏏ の長押しで次へ進まない／5 問のあとの区切りの画面（つづける・やめる）／「？」を開いたまま区切りの画面へ替わったら閉じる、のテストは、そのまま写す
- [ ] **Step 2:** `npx vitest run src/game/game.test.ts` が、実装が無いので落ちることを確かめる
- [ ] **Step 3: 実装する。** `game.ts` は 1 本目を写し、`Question.choices` が可変の長さでも動くように、カードを `choices.map` で作る（2 枚前提の書き方があれば直す）。`audio.preload` には、4 枚分の `voice/ask-<id>.wav` と、答えの `voice/ok-<id>.wav`・`sfx/correct.wav`・`sfx/wrong.wav` を渡す。`style.css` の `.cards` は、横向きの画面で 4 枚が 1 列に並び（PC・スマホ横向き）、画面が細いときだけ 2×2 にする。カードの短い辺は 100px 以上。**カードの並べ方は見た目が変わるので、Step 5 で依頼者に確かめてから確定する**
- [ ] **Step 4:** `npx vitest run && npx biome check . && npx tsc --noEmit && npm run build` が通る
- [ ] **Step 5: ブラウザで確かめる。** `npx vite preview --port 4317` を起動し、Playwright（`NODE_PATH=/home/ubuntu/workspace/web-novel-engine/node_modules`、Chromium）で ▶ → 問題 → 不正解 → 正解 → 5 問 → 区切りの画面 → つづける まで通す（次の問題は、カードの ID の並びが変わるまで待つ）。1280×720 と 800×360 の 2 つの大きさで問題の画面を撮り、4 枚がはみ出さないこと、コンソールにエラーが無いことを確かめる。**撮った 2 枚を、HTML + Artifact で依頼者に見せ、承認をもらってから** Step 6 へ（直す指示が出たら、直して見せ直す）
- [ ] **Step 6: コミット**（`feat: どれかな？（4 択）のゲーム本体を作る`）

---

### Task 4: 文書を書き、最初の PR を出す

**Files:**
- Create/Modify: `CLAUDE.md`・`README.md`・`HANDOVER.md`（`which-one-of-two` のものを見本に）

- [ ] **Step 1:** `CLAUDE.md` の「このゲームの遊びの決まり」を書く: 4 枚・5 問（似たもの 2 問）・答えは 5 問とも別・間違えた絵は揺れて残る・正解のあと 500ms で次へ・5 問のあとは `showRoundEnd`。ブランチの決まり（機能ブランチ → `develop` → `main`。最初の PR だけ `main` 向け）は、ひな形のものを残す
- [ ] **Step 2:** `HANDOVER.md` の進捗の欄は、ankardo の `HANDOVER.md` と同じ作業名（`幼児向け知育ゲーム`）で、`~/.claude/rules/progress.md` の書式に従う
- [ ] **Step 3:** Task 3 までの確認（`npx vitest run && npx biome check . && npx tsc --noEmit && npm run build`、`CI=true npx vitest run src/common/assets.test.ts`）をもう一度通す。コミットし、`feat/which-one-of-four` を push して `main` 向けの PR を作る。マージで本番に出るので、依頼者がマージする
- [ ] **Step 4:** CodeRabbit の指摘は、依頼者が始めたレビューの結果を PR のコメントで読み、1 件ずつ確かめて直す。共通部分を直したら、ひな形にも要るかを依頼者に報告する
- [ ] **Step 5:** マージ後、`deploy` の成功と、本番 `https://ankardo.com/play/which-one-of-four/` が開くことを確かめる

---

### Task 5: カタログ・プレビュー・作業ページ

**Files（ankardo）:**
- Create: `site/content/games/which-one-of-four.json`・`site/public/screenshots/which-one-of-four/01.png`
- Modify: `site/public/_redirects`（`/games/which-one-of-four /games/which-one-of-four/ 301` を、which-one-of-two の行の隣に）

- [ ] **Step 1:** ankardo の `main` から `feat/which-one-of-four-catalog` を切る。JSON は `which-one-of-two.json` と同じ形: `genre: "education"`、`devices: ["pc", "mobile-landscape"]`、`ageRange: "3歳〜"`、`players: "ひとり用"`、`difficulty: "ふつう"`。`title` は `どれかな？（4つ）`、`description` は「声で聞かれた絵を、4 つの中から選びます。似ている絵も出ます。」、`controls` は 1 本目と同じ 3 行（「絵をタッチして選びます」「もう一度聞きたいときは、スピーカーのボタンをタッチします」「左上のボタンを長押しすると、はじめの画面にもどります」）
- [ ] **Step 2:** 公開した本番を 1280×720 で開き、▶ を押して最初の問題が出たところを撮る（300KB を超えたら WebP にし、JSON の `images` も直す）。依頼者に Artifact で見せて承認をもらってから、コミットする
- [ ] **Step 3:** `cd site && npm test && npm run build` が通る。push して `main` 向けの PR を作る（依頼者がマージする）
- [ ] **Step 4:** ゲームのリポジトリで、`main` から `develop` を作って push する（本番の `deploy` の成功のあと）。`Preview (develop)` の成功と、プレビューの URL（`https://develop-ankardo-game-which-one-of-four.akabee0161.workers.dev/play/which-one-of-four/`）が、ログインなしで 302（`cloudflareaccess.com` へ）になることを確かめる
- [ ] **Step 5:** `personal-work-hub` の `main` から作業ブランチを切り、`src/links.ts` に `{ label: 'どれかな？（4つ）（プレビュー）', url: <Step 4 の URL>, note: 'develop ブランチの確認用。本番に出す前に遊んで確かめる' }`、`test/links.test.ts` の slug の一覧に `which-one-of-four`（並べ替えた順）、`README.md` のゲームの本数と名前を足す。`npm test && npm run typecheck` が通ってから、`main` 向けの PR を作る
- [ ] **Step 6:** ankardo の `HANDOVER.md` の進捗の欄を直し（`main` へ直接）、`which-one-of-four` を済みにして、次の 3 本目（`animal-voice-quiz`。鳴き声を使う最初のゲーム）の小さな計画に進めるようにする

---

## 依頼者の手作業（依存の順）

| 順 | いつ | 作業 |
|---|---|---|
| 1 | 今 | この計画の承認（上の「依頼者に確かめること」5 点） |
| 2 | Task 1 の前 | GitHub に空のリポジトリ `which-one-of-four` を作る。`scripts/setup-game-secrets.sh` で Cloudflare の秘密の値を入れる |
| 3 | Task 3 の途中 | 4 枚の並べ方（撮った 2 枚）の承認 |
| 4 | Task 4 の後 | `which-one-of-four` の PR（→ `main`）のマージ。CodeRabbit のレビューの開始 |
| 5 | Task 5 の中 | スクリーンショットの承認、ankardo の PR と personal-work-hub の PR のマージ |

## 残す課題（この計画では直さない）

- 1 本目の `src/common/` に入れていない 2 件（`activate.ts` の要素の外で離したときの抑止解除・`exit-button.ts` の別のキーを離しても長押しが続く）。このゲームはひな形から写すので、最初から入っている
- 3 択（設計書の「3〜4 択」の 3）は作らない。4 つに固定する（依頼者が slug を `which-one-of-four` と決めた）
- 声（`ask-*`・`ok-*`・`again`）と音は、1 本目で作ったものをそのまま使う。新しく作らない
