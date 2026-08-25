# Session Handover

## Generated: 2026-08-25T10:00:00Z

## Current State

- **Branch**: `catalog-screenshots`(mainから分岐、push済み。PR未作成)
- **段階①**: 完了・デプロイ済み(PR #6 マージ済み)
- **段階②**: 設計と実装計画が完了。**実装はこれから**
- **Uncommitted Changes**: なし

ブランチ名は当初スクリーンショット投入用に切ったもので、その後に段階②の spec と実装計画のコミットが乗っている。名前と中身が一致していないが実害はないためそのまま使っている。

## What Was Done

### 段階①(完了)

`docs/superpowers/plans/2026-08-25-catalog-assets-and-metadata.md` の Task 1〜7 を実装し、PR #6 としてマージ・本番デプロイ済み。`devices` の必須化、`controls` の追加、対応デバイスのバッジ表示、「あそびかた」セクション、画像の16:9統一、Vitest の導入。

`shogi-vs-cpu` の `devices` はユーザーが実機確認済みで `["pc", "mobile-portrait"]` を確定値とした。

### スクリーンショット(1件のみ投入)

`rungame-sample` の1枚(1280×720)を `site/public/screenshots/rungame-sample/01.png` に配置し、JSONの `images` に追記した(コミット `3902bd2`)。残り2ゲームは未撮影のまま、ユーザー判断で段階②へ進んだ。

### 段階②(設計・計画のみ)

- spec: `docs/superpowers/specs/2026-08-25-site-header-footer-and-brand-design.md`
- 実装計画: `docs/superpowers/plans/2026-08-25-site-header-footer-and-brand.md`(7タスク)

ブランドアセットはブレインストーミングで造形まで確定済み。シンボルの SVG パスは spec に確定値として記載してある。

## What Remains

### 1. 段階②の実装(次に着手する)

実装計画の Task 1〜7 を順に実行する。実行方法は subagent-driven-development か executing-plans のどちらか。**ユーザーはまだどちらを選ぶか決めていない。**

計画の実行では完了しない手作業:

- [ ] PR の作成とマージ、`Site (Next.js)` の production environment 承認
- [ ] 問い合わせフォームの送信テスト(回答が届くことの確認)
- [ ] スマートフォン実機でのハンバーガーメニューの確認

### 2. スクリーンショットの追加投入(任意・随時)

- [ ] `shogi-vs-cpu` / `character-tactics` の撮影と配置、各JSONの `images` 追記

規約は `.claude/skills/new-game/SKILL.md` の「スクリーンショットの規約」(16:9 / 1280×720基本 / `01.png` からの連番 / 1枚300KB以内)。撮り方は Chrome DevTools のデバイスツールバーで 1280×720・DPR 1 にし、`Ctrl+Shift+P` → `Capture screenshot`。画像を渡せば配置・JSON更新・検証はエージェント側で引き取れる。

### 3. 段階③(段階②完了後、またはゲームが増えてから)

内容: ジャンル絞り込み。**まだ設計していない。**

実装時の注意: `GENRES`(7ジャンル)の全てを絞り込みUIに出すと、実使用は3ジャンル(`action` / `puzzle` / `simulation`)のため空のジャンルが4つ並ぶ。**定義済みの全ジャンルではなく「実際にゲームが存在するジャンル」だけを表示する方式**にすること。

### タスクから除外したもの

- **`shogi-vs-cpu` / `character-tactics` の `controls` 追記**。任意フィールドで未記載でも不具合はなく、個別ゲームの設定値の作り込みでサイトの開発タスクではないと判断して外した(2026-08-25、ユーザー指示)。プレイ時のメモを渡せば JSON へ反映する

## Key Decisions Made

### 段階②(ブランドとナビゲーション)

- **シンボルはナマズにする** — サイト名 Ankardo は、ナマズを押さえる要石の伝説に由来する(要石 = anchor stone → 綴りを変えて do を付けた)。ナマズをキーキャラクターにする予定があるため、将来マスコットのイラストを入れてもモチーフが揃う。錨そのものの図案化は、記号として海事を指してしまうため不採用
- **造形は「正面顔＋下向きのヒゲ2本＋への字の浅い口＋胸ビレ＋三日月の尾」** — 尾は付け根が太く先端が細いテーパーで、逆向きに強く反らせる。先端に団扇型の尾ビレが軸上にまっすぐ付く。確定した SVG パスは spec に記載
- **ブランド色は藍 `#1f3a5f`。既存ボタンの `bg-neutral-900` は据え置き** — ボタンまで藍に寄せると全ページの再確認が必要になり、段階②のスコープを超える
- **ファビコンは白地の角丸四角に藍のナマズ** — 透過だと暗いタブで藍が沈む。ヘッダーは逆に地を敷かない(アプリアイコンめいて重くなるため)
- **モバイルは全画面メニュー(ユーザー判断)** — リンク2本の現状には過剰で、エージェントの推奨はヘッダー直下のパネル型だった。段階③でリンクが増える見込みと、実装コストを許容する判断から全画面を採用。Esc・背後スクロール抑止・フォーカス復帰を含めて実装する
- **about の解析に関する記述は将来を含む書き方にする** — 「アクセス解析を行う場合も、個人を特定しない集計のみで Cookie は使わない」。ユーザーは今後アクセス解析を導入する意向があり、「解析していない」と断定すると導入時に虚偽になる。**この文言は制約でもあり、GA4 のような識別子ベースの解析を入れるなら about の書き換えが必要**。Cloudflare Web Analytics のような Cookie 不使用の集計なら書き換え不要
- **連絡先は Google フォーム。メールアドレスは公開しない** — GitHub Issue を主たる連絡手段にはしない(一般の保護者が使う手段ではない)
- **プレイページ(各ゲームリポジトリ)からの戻り導線は段階②の対象外**

### 段階①(カタログのメタデータ)

- **スクリーンショットは手動で撮る。CI での自動生成は導入しない** — 自動撮影で得られるのは主にタイトル画面で、カード映えする画面にはゲーム側の撮影用フックが要る。規約を spec で確定させてあるので、後から同じパスへ出力する形で追加できる
- **置き場所は `site/public/screenshots/<slug>/`、比率は16:9、表示側も `aspect-video` に統一**
- **`devices` はデバイスと向きを合成した列挙型で必須フィールド** — 別フィールドに分けるとPCに向きを指定する無意味な組み合わせが表現可能になる
- **`controls` は文字列配列の任意フィールド** — 記載内容がゲームごとに異なり、構造を固定すると当てはまらない項目が出る
- **テストは `validateGame` に限定し、表示コンポーネントには書かない** — 段階②では `MobileNav` のみ例外(実際の振る舞いを持つため)
- **一覧の並び替え機能は実装しない** — ゲーム3件では選択肢として機能しない
- **`next dev` の `AGENTS.md`/`CLAUDE.md` 自動生成は無効化**(`next.config.js` の `agentRules: false`)

## Known Issues / Blockers

- **問い合わせフォームの URL は到達確認をしていない**。`curl` の実行が許可されなかったため。実装後にブラウザで開いて確認すること
- **`apple-icon.png` の生成は不確実**。ImageMagick の内蔵 SVG レンダラーは `transform="rotate(…)"` の解釈が不完全なことがある。実装計画では「崩れていたら PNG を捨てて先へ進む」と判断基準を決めてある
- **ローカルのゲームリポジトリのクローンが古い**。`../rungame-sample` は `origin/main` より遅れ、`../shogi-vs-cpu` は `docs/` しか無い。`character-tactics` は未クローン。スクリーンショットは本番URLから撮れば影響しない
- **Terraform state が CI とローカルで共有されていない**。当面 `allow_overwrite` でしのいでいる。詳細は `infra/README.md`

## Context Files

次のセッションで読む順。

1. このHANDOVER.md
2. `docs/superpowers/plans/2026-08-25-site-header-footer-and-brand.md` — 段階②の実装計画。これに沿って実装する
3. `docs/superpowers/specs/2026-08-25-site-header-footer-and-brand-design.md` — 段階②の設計と判断理由
4. `README.md` — 現在の仕様・手順の正典

## Long-term Backlog(ユーザー指示: 当面対応不要。ユーザーが長期バックログについて尋ねた場合のみ話題に出す)

- アクセス解析の導入(上記 Key Decisions の about の文言が制約になる)
- 既存ボタン(`bg-neutral-900`)をブランド色に寄せるかの判断
- リモートbackend導入(Terraform Cloud / S3等でCI・ローカルのstateを共有)。詳細は `infra/README.md`
- Cloudflareダッシュボードの推奨事項: `www.ankardo.com` 用レコード追加、MXレコード(SPF/DKIM/DMARC)設定
- ジャンルアイコン(7種、現状は色+ラベルのみで機能する)
- マスコットキャラクターのイラスト(ナマズ。シンボルと同じモチーフで揃う)
- SEO対策、OGP画像 — 一般公開を目指す段階になったら必要

## Recommended Next Steps

1. 新しいセッションを開始する: `claude`
2. 「`HANDOVER.md` を読んで、前のセッションの続きから作業して」と指示する
3. 最初のアクション: **段階②の実装**。`docs/superpowers/plans/2026-08-25-site-header-footer-and-brand.md` を subagent-driven-development か executing-plans で Task 1 から実行する
4. 全タスク完了後に PR を作成し、マージと production environment 承認へ進む
