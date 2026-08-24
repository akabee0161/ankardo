# Session Handover

## Generated: 2026-08-24T22:49:28Z

## Current State

- **Branch**: `catalog-assets-and-metadata`(mainから分岐。未push)
- **Last Commit**: `e7df584` docs: カタログのアセット規約とメタデータ拡張の実装計画を追加
- **Uncommitted Changes**: なし(このHANDOVER.md自体を除く)

## What Was Done

ゲームが3件揃った段階で、次に進める方向性をユーザーと対話して決め、設計と実装計画をドキュメント化した。**コードは1行も変更していない。**

1. 現状調査。以下を確認した。
   - `site/public/` が存在せず、`images` フィールドは実装済みだが画像の置き場所が未定。3ゲームとも画像なし(プレースホルダー表示)
   - `app/layout.tsx` に共通ヘッダー/フッターがなく、`/games` からトップへ戻れない
   - `site/` にテストが1本もない(`package.json` に `test` script なし)
   - 対応デバイス・操作方法がカタログのどこにも記載されていない
2. 各ゲームリポジトリ(`../rungame-sample`、`../shogi-vs-cpu`、GitHub上の `character-tactics`)の `origin/main` のコードを調査し、対応デバイスを判定した(根拠はspecに記載)
3. 設計を `docs/superpowers/specs/2026-08-25-catalog-assets-and-metadata-design.md` に記述しコミット
4. 実装計画を `docs/superpowers/plans/2026-08-25-catalog-assets-and-metadata.md` に記述しコミット(7タスク、各タスクにコードと検証コマンドを記載)

## What Remains

### 最優先: 段階①の実装

`docs/superpowers/plans/2026-08-25-catalog-assets-and-metadata.md` の Task 1〜7 を順に実行する。計画は自己完結しており、コードと検証コマンドがすべて記載されている。

- [ ] Task 1: Vitest 導入、`validateGame` を export、既存バリデーションの回帰テスト(8件)、CI に `npm test` 追加
- [ ] Task 2: `site/lib/devices.ts` 新設、`devices` を必須フィールド化、既存3件のJSON更新(テスト+6件)
- [ ] Task 3: `controls` を任意フィールドとして追加、`rungame-sample` に暫定値(テスト+4件)
- [ ] Task 4: `MetaBadges` に対応デバイスのバッジを表示
- [ ] Task 5: 詳細ページに「あそびかた」セクションを追加
- [ ] Task 6: 画像表示を `aspect-video`(16:9)に統一、`site/public/screenshots/` を作成
- [ ] Task 7: `.claude/skills/new-game/SKILL.md` と `README.md` を更新

### 実装完了後のユーザー手作業(エージェントでは完了できない)

- [ ] スクリーンショットの撮影と配置(3ゲーム分、`site/public/screenshots/<slug>/01.png` 以降)、各JSONの `images` に追記
- [ ] `shogi-vs-cpu` の `devices` を実機確認。現在の値 `["pc", "mobile-portrait"]` はコードからの推論
- [ ] `shogi-vs-cpu` / `character-tactics` の `controls` を実機で確認して各JSONに追記
- [ ] PR作成 → mainマージ → `Site (Next.js)` ワークフローの production environment 承認

### 段階②(段階①完了後)

内容: 共通ヘッダー/フッター、ファビコン、ワードマーク。**まだ設計していない。**

段階①の完了後に着手する。理由は、スクリーンショットが入った実際の画面を見てからヘッダーのデザインを決める方が判断の根拠が得られるため。着手時は brainstorming から始めて spec を書く。

`/games` や `/games/<slug>` からトップへ戻る導線がない点は体裁の問題ではなく機能欠陥に近いため、段階②の中では優先度が高い。

### 段階③(段階②完了後、またはゲームが増えてから)

内容: ジャンル絞り込み。**まだ設計していない。**

実装時の注意: `GENRES`(7ジャンル)の全てを絞り込みUIに出すと、実使用は3ジャンル(`action` / `puzzle` / `simulation`)のため空のジャンルが4つ並ぶ。**定義済みの全ジャンルではなく「実際にゲームが存在するジャンル」だけを表示する方式**にすること。

絞り込みの軸をジャンルのみにするか `devices` や `ageRange` も含めるかは、段階③の設計時に判断する。

## Key Decisions Made

- **スクリーンショットは手動で撮る。CI での自動生成(Playwright)は導入しない** — 現在の更新頻度では撮り直しが発生せず削減できる手間がない。また自動撮影で得られるのは主にタイトル画面で、カード映えする画面を撮るにはゲーム側への撮影用フックの実装が別途必要。後から導入する際の障壁はCIの有無ではなく規約の不在であるため、規約をspecで確定させることで将来同じパスへ出力する形で追加できる
- **置き場所は `site/public/screenshots/<slug>/`。`public/games/` にはしない** — ページのルートが `/games/<slug>/` で、静的書き出しで `out/games/<slug>/index.html` が生成される。同じディレクトリに画像を混ぜるとパスがページかアセットか判別しづらい
- **比率は16:9。表示側も `aspect-video` に統一する** — 現在の表示側は場所ごとに比率が異なり全て `object-cover`。詳細メイン画像では上下が約30%欠ける。`rungame-sample`(720×405)と `character-tactics`(960×540)がどちらも16:9であることも根拠
- **`devices` はデバイスと向きを合成した列挙型(`pc` / `mobile-landscape` / `mobile-portrait`)にし、必須フィールドにする** — 別フィールドに分けるとPCに向きを指定するような無意味な組み合わせが表現可能になる。必須にするのは段階③の絞り込みで欠損データの扱いが煩雑になるのを避けるため
- **`controls` は構造化せず文字列配列にし、任意フィールドにする** — 記載内容がゲームごとに異なり、構造を固定すると当てはまらない項目が出る
- **テストは `validateGame` に限定し、表示コンポーネントには書かない** — 表示側はロジックを持たず、JSXがそのまま出ることを確認するだけになる
- **一覧の並び替え機能は実装しない** — ゲーム3件では選択肢として機能しない
- **`controls` の表示位置は「プレイボタンの下」** — specには「説明文の下」と書いたが、説明文の直後だとプレイボタンが下へ押し出される。実装計画側でプレイボタンの後ろに変更した(計画に理由を記載済み)

## Known Issues / Blockers

- **ローカルのゲームリポジトリのクローンが古い**。`../rungame-sample` は `origin/main` より3コミット遅れ、`../shogi-vs-cpu` は `docs/` しか無い状態(リモートには実装済み)。`character-tactics` はローカルに未クローン。スクリーンショットをローカルで撮る場合は `git pull` が必要(本番URLから撮るなら不要)
- `site/tsconfig.json` が `"strict": false`。実装計画の Task 4 Step 2 は型エラーでビルドが失敗することを期待しているが、環境によっては通る可能性がある(計画に補足済み)
- Terraform stateがCIとローカルで共有されていない。当面 `allow_overwrite` でしのいでいる。根本対応は長期バックログ。詳細は `infra/README.md`

## Context Files

次のセッションで読む順。

1. `docs/superpowers/plans/2026-08-25-catalog-assets-and-metadata.md` — 実装計画。これだけで Task 1〜7 を実行できる
2. `docs/superpowers/specs/2026-08-25-catalog-assets-and-metadata-design.md` — 設計と判断理由。計画に疑問が出たらこちらを読む
3. `README.md` — リポジトリ構成とドキュメント運用ルール(正典)
4. `.claude/skills/new-game/SKILL.md` — ゲーム追加手順(正典)。Task 7 で更新する
5. `site/lib/games.ts` / `site/lib/genres.ts` — 変更対象の中心

## Long-term Backlog(ユーザー指示: 当面対応不要。ユーザーが長期バックログについて尋ねた場合のみ話題に出す)

- リモートbackend導入(Terraform Cloud / S3等でCI・ローカルのstateを共有)。導入時は既存リソースを `terraform import` で新backendに取り込む必要あり。詳細は `infra/README.md`
- Cloudflareダッシュボードの推奨事項: `www.ankardo.com` 用レコード追加、MXレコード(SPF/DKIM/DMARC)設定
- ジャンルアイコン(7種、現状は色+ラベルのみで機能する)
- マスコットキャラクター等のイラスト(将来イラスト主導のブランド強化を行う場合に必要)
- SEO対策、OGP画像、アナリティクス — サイトが最終的に一般公開を目指すため将来必要になるが、当面は身内・知人の範囲で利用する段階のため対応しない

## Recommended Next Steps

1. 新しいセッションを開始する: `claude`
2. 「`HANDOVER.md` を読んで、前のセッションの続きから作業して」と指示する
3. 最初のアクション: ブランチ `catalog-assets-and-metadata` にいることを確認し、`docs/superpowers/plans/2026-08-25-catalog-assets-and-metadata.md` の Task 1 Step 1 から実行する(`cd site && npm install -D vitest`)
