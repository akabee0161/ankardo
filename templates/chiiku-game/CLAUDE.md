# CLAUDE.md

__TITLE__（chiiku-template-slug）で作業する際の指針。

## ブランチとプレビュー

- 機能ブランチから `develop` への PR を最初に作る。`develop` にマージすると、Cloudflare Access の受付の後ろに確認用のプレビューが固定の URL に自動で上がる（`.github/workflows/preview.yml`）
- 本番に出すときは、`develop` から `main` への PR をマージする（`deploy.yml` が本番に出す）
- `develop` と `main` へは、直接 push しない。マージは依頼者が行う。**例外は 1 つだけ**: 開いている `develop` → `main` の PR についたレビューの指摘に対応するときは、その PR のブランチである `develop` へ直接 push してよい（新しい PR は作らない。マージはしない）。機能の追加や、指摘以外の直しは、これまでどおり機能ブランチから `develop` への PR にする。`develop` へ push すると、確認用のプレビューが上がり直す
- `preview.yml` は `develop` への push と、`develop` を選んだ手動実行（`workflow_dispatch`）だけで動き、`wrangler deploy` は書かない。ankardo の `.claude/skills/new-game/preview.yml` の写しで、`wrangler.toml` の `preview_urls = true` は確認用プレビューのためである（本番の `workers.dev` は開かない）
- `develop` ができるまでの最初の PR（ゲームの公開そのもの）だけは `main` に向ける
- `production` environment に保護ルール（必須レビュアー）は設けていない（依頼者の判断）。`main` へのマージが、承認の待ちなしに、そのまま本番に出る。マージする前に、プレビューで確かめる
- `package-lock.json` は、CI と同じ npm（Node 22 の npm 10）で、`node_modules` の無い場所で作る（`npx npm@10 install --package-lock-only`）。手元の npm が違うと、`npm ci` が止まって本番デプロイが失敗する。出す前に `npx npm@10 ci` が通ることと、全パッケージに `integrity` があることを確かめる。詳しくは ankardo の `.claude/skills/new-game/SKILL.md`

## 共通部分（src/common/）とゲームの部分

- `src/common/`（素材の一覧の読み込み・音・長押し・タイトル画面・「？」・⏏・はねる動き・共通の見た目）は、知育ゲームで共通の部分。**このゲームだけの決まりを入れない**。このゲームの遊びは `src/game/` に書く
- `src/common/` は ankardo のひな形 `templates/chiiku-game/` の写しで、写した元は `template.md`。共通部分を直したら、ほかのゲームにも要るかを考え、要るなら ankardo のひな形にも同じ直しを入れる（PR を分ける）。要らないなら `src/game/` に置く

- 問題を出すゲームは、`src/common/` の区切りを使う。`ROUND_SIZE`（5 問）・`createProgressDots(total)`（正解した数を見せる点。点数ではない）・`showRoundEnd`（つづける／やめる。どちらも通常のタップ）
- 正解は `playCorrect(audio, 声の URL)`（音 → 声の順。`true` が返ったときだけ次へ進む。`false` は ⏏ などで切られた印）、間違いは `playWrong(audio)`。揺れは `createBouncer('wiggle', WIGGLE_MS)`。素材の URL は `assetUrl('voice/…')`

## 守ること（知育ゲームの決まり）

- 字が読めない子どもが遊ぶ。指示は声、ボタンは絵だけ。字を出すのは、親のための題・クレジット・「？」の説明だけ
- 時間制限・ゲームオーバー・点数を付けない。記録はサーバーにも端末にも残さない（`localStorage` も使わない）
- 最初に大きな「はじめる」ボタンを押してもらう。その**タッチの中で**（`await` の前に）`audio.unlock()` を呼ぶ。そうしないと iOS Safari は音を出さない（`showTitle` の `unlock` がそれを行う）
- 消音スイッチは無視しない（利用者の意思）。鳴らないときは、「？」で保護者に消音ボタンと音量を確かめてもらう。`audio.ts` の `unlock()` の決まりを変えない
- ゲームを終えるボタン（⏏）は長押し 1.5 秒で、タイトル画面に戻る（子どもが間違えて出ないように）。`createExitButton` を使う
- 触れて選ぶ絵・ボタンは `attachActivate(el, 処理)`（`src/common/activate.ts`）で受ける。触れた瞬間（pointerdown）・Enter／スペース・click だけの起動（スクリーンリーダーなど）のすべてに応え、同じ操作の click で 2 度呼ばない。自分で `pointerdown` と `keydown` を書かない
- 同じ絵を続けて叩いたら前の声を止めて最初から鳴らし、別の絵を叩いたら前の声を止める
- 素材は ankardo の `shared-assets/chiiku/` が正で、`public/chiiku/` はそのコピー。**手で直さない**。直すときは ankardo の素材を直し、`ankardo/scripts/copy-assets.sh chiiku . [--no-cry]` でコピーし直す（コピー元の commit は `chiiku-assets.md`）。鳴き声（`cry/`）を使わないゲームは `--no-cry` を付ける（CC BY-SA の録音を配らず、画面のクレジットも VOICEVOX の 1 行だけで済む）。クレジットは `public/chiiku/CREDITS.md`
- 種類は 21（たべもの 5）、種類キーは `sea`（みずのいきもの。金魚を含むため）。素材の一覧（`items.json`）を正とし、ゲーム側に一覧を書き写さない

## 確認

```sh
npx vitest run && npx biome check . && npm run build
```
