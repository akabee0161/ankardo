# Session Handover

## Generated: 2026-09-01T00:00:00Z

## Current State

- **Branch**: `main`(このHANDOVER更新は `handover-migrate-games-to-ankardo` ブランチで作業、PRでmainへ)
- **段階①〜③**: 完了・デプロイ済み(PR #6・#7・#8 マージ済み)
- **dragon-shooter / sea-defence の ankardo 移行**: **完了**。hermit-life(AWS CodeCommit + CDK + S3 + CloudFront)から ankardo(GitHub + Cloudflare Workers)へ完全移行し、hermit-life 側のコード・AWSリソースを撤去済み(PR #9・#10 マージ済み)
- **Uncommitted Changes**: なし

## What Was Done

### dragon-shooter / sea-defence を ankardo へ移行(完了)

- spec: `docs/superpowers/specs/2026-08-31-migrate-games-to-ankardo-design.md`
- 実装計画: `docs/superpowers/plans/2026-08-31-migrate-games-to-ankardo.md`(Task 1〜7、全完了)
- 進行ログ: `.superpowers/sdd/2026-08-31-migrate-games-to-ankardo/progress.md`(各Taskのレビュー結果・判断根拠を記録)

実装内容:

- **Task 1-2**: `akabee0161/sea-defence` / `akabee0161/dragon-shooter` の GitHub リポジトリ状態を確認、Cloudflare Secrets(`CLOUDFLARE_API_TOKEN`/`CLOUDFLARE_ACCOUNT_ID`)と `production` environment(reviewer承認必須)を両リポジトリに設定
- **Task 3**: sea-defence を Cloudflare Workers Static Assets 向けに書き換え(`vite.config.ts` の `base`/`outDir` をネスト、`wrangler.toml` 新規、GitHub Actions で `wrangler deploy`)、`https://ankardo.com/play/sea-defence/` にデプロイ・動作確認済み
- **Task 4**: dragon-shooter も同様に移行。`import.meta.env.BASE_URL` 経由のステージJSON読み込み(`assets/levels/stage1.json`)がビルド成果物のgrepで正しく解決されることを確認したうえで `https://ankardo.com/play/dragon-shooter/` にデプロイ・動作確認済み
- **Task 5**: ankardo のカタログに2件を登録(PR #9)。マージ直後、main側で先行してマージされていた `devices` フィールド必須化(PR #6, `eb6b138`)との非同期により `Site (Next.js)` のビルドが失敗 → 両ゲームに `devices: ["pc", "mobile-portrait"]` を追加するホットフィックス(PR #10)で解消
- **Task 6**: hermit-life 側の `src/app/labs/games/page.tsx` のゲーム一覧、`infra/bin/infra.ts` の `DragonShooterPipelineStack`/`SeaDefencePipelineStack` 定義、`CLAUDE.md` のゲーム表を削除・更新(コミット `1dcb169`)
- **Task 7**: AWS リソースを破棄。`DragonShooterPipelineStack`/`SeaDefencePipelineStack` を削除(**Task 6でinfra.tsから定義を消した後だと `cdk destroy` が対象を見つけられずno-opになるため `aws cloudformation delete-stack` で代替**)、S3実体(`s3://hermit-life-net-static/labs/games/{dragon-shooter,sea-defence}/`)を削除、CloudFrontキャッシュを無効化、CodeCommitリポジトリ(`dragon-shooter`/`sea-defence`)を削除(GitHub側に全ブランチが揃っていることを確認後に実施)、ローカルの `codecommit` remote を削除

### 段階③(実装完了・マージ済み)

`site/app/games/page.tsx` にジャンル絞り込みタブ(`site/components/GenreFilter.tsx`)を実装。PR #8 としてマージ・デプロイ済み。詳細は変更前バージョンのこのファイル、または `git log` を参照。

## What Remains

### 1. dragon-shooter / sea-defence 移行の残タスク

なし。完了条件(下記)を全て満たした。

- [x] `https://ankardo.com/play/sea-defence/` / `https://ankardo.com/play/dragon-shooter/` が200を返しプレイ可能
- [x] `https://ankardo.com/games` に2件が並び、詳細ページも表示される
- [x] `https://hermit-life.net/labs/games/` の一覧から2件が消え、旧URLが404/403
- [x] `https://hermit-life.net/labs/games/puzzlebobble-like/` が引き続き200(共有バケットを巻き込んでいない)
- [x] `npx cdk list` に `DragonShooterPipelineStack`/`SeaDefencePipelineStack` が出ない
- [x] CodeCommitの `dragon-shooter`/`sea-defence` が削除され、GitHub側に全ブランチが存在する

### 2. 段階②由来の残タスク(持ち越し)

- [ ] スマートフォン実機でのハンバーガーメニューの確認(縦向き・横向き双方。横向きでの自動クローズも確認) — 未実施、実機操作が必要

### 3. スクリーンショットの追加投入(任意・随時)

- [ ] `shogi-vs-cpu` / `character-tactics` の撮影と配置、各JSONの `images` 追記

規約は `.claude/skills/new-game/SKILL.md` の「スクリーンショットの規約」(16:9 / 1280×720基本 / `01.png` からの連番 / 1枚300KB以内)。撮り方は Chrome DevTools のデバイスツールバーで 1280×720・DPR 1 にし、`Ctrl+Shift+P` → `Capture screenshot`。画像を渡せば配置・JSON更新・検証はエージェント側で引き取れる。

### タスクから除外したもの

- **`shogi-vs-cpu` / `character-tactics` の `controls` 追記**。任意フィールドで未記載でも不具合はなく、個別ゲームの設定値の作り込みでサイトの開発タスクではないと判断して外した(2026-08-25、ユーザー指示)。プレイ時のメモを渡せば JSON へ反映する

## Key Decisions Made

### dragon-shooter / sea-defence の ankardo 移行

- **hermit-life から ankardo への移行は完全移行とし、旧URLのリダイレクトは作らない**(ユーザー判断)。404を受け入れる
- **移行スコープはホスティングのみ**。カタログ表示名は英語表記のまま(`Dragon Shooter`/`Sea Defence`)、ゲーム本体の内容(難易度・UI文言)は変更しない
- **先行事例の `rungame-sample` は hermit-life の `rungame` と併存しているが、今回はその形を取らなかった**。2ゲームとも hermit-life 側を完全撤去する方式を採用
- **`cdk destroy` はCDKアプリ側にスタック定義が残っている間に実行する**(Task 6の infra.ts 編集より前、または `aws cloudformation delete-stack` で代替)。今回はTask 6 → Task 7の順で計画されていたため後者で対応した。次回同様の撤去作業をする際は、CDK定義削除と物理スタック破棄の順序に注意する
- **sea-defence / dragon-shooter の `devices` は両方 `["pc", "mobile-portrait"]`**(ユーザー確認: いずれもPC・スマホ縦向き対応)

### 段階②(ブランドとナビゲーション)

- **シンボルはナマズにする** — サイト名 Ankardo は、ナマズを押さえる要石の伝説に由来する(要石 = anchor stone → 綴りを変えて do を付けた)。ナマズをキーキャラクターにする予定があるため、将来マスコットのイラストを入れてもモチーフが揃う。錨そのものの図案化は、記号として海事を指してしまうため不採用
- **造形は「正面顔＋下向きのヒゲ2本＋への字の浅い口＋胸ビレ＋三日月の尾」** — 尾は付け根が太く先端が細いテーパーで、逆向きに強く反らせる。先端に団扇型の尾ビレが軸上にまっすぐ付く。確定した SVG パスは spec に記載
- **ブランド色は藍 `#1f3a5f`。既存ボタンの `bg-neutral-900` は据え置き** — ボタンまで藍に寄せると全ページの再確認が必要になり、段階②のスコープを超える
- **ファビコンは白地の角丸四角に藍のナマズ** — 透過だと暗いタブで藍が沈む。ヘッダーは逆に地を敷かない(アプリアイコンめいて重くなるため)
- **モバイルは全画面メニュー(ユーザー判断)** — リンク2本の現状には過剰で、エージェントの推奨はヘッダー直下のパネル型だった。段階③でリンクが増える見込みと、実装コストを許容する判断から全画面を採用。Esc・背後スクロール抑止・フォーカス復帰を含めて実装した
- **about の解析に関する記述は将来を含む書き方にする** — 「アクセス解析を行う場合も、個人を特定しない集計のみで Cookie は使わない」。ユーザーは今後アクセス解析を導入する意向があり、「解析していない」と断定すると導入時に虚偽になる。**この文言は制約でもあり、GA4 のような識別子ベースの解析を入れるなら about の書き換えが必要**。Cloudflare Web Analytics のような Cookie 不使用の集計なら書き換え不要
- **連絡先は Google フォーム。メールアドレスは公開しない** — GitHub Issue を主たる連絡手段にはしない(一般の保護者が使う手段ではない)
- **プレイページ(各ゲームリポジトリ)からの戻り導線は段階②の対象外**
- **モバイルメニューの画面幅変化時クローズでは、非表示になったボタンへフォーカスを戻さない** — SiteHeaderのデスクトップナビ要素への直接参照はコンポーネント間の結合を増やすため導入せず、「非表示要素にフォーカスしない」最小修正に留めた(2026-08-26、CodeRabbitレビュー対応)

### 段階①(カタログのメタデータ)

- **スクリーンショットは手動で撮る。CI での自動生成は導入しない** — 自動撮影で得られるのは主にタイトル画面で、カード映えする画面にはゲーム側の撮影用フックが要る。規約を spec で確定させてあるので、後から同じパスへ出力する形で追加できる
- **置き場所は `site/public/screenshots/<slug>/`、比率は16:9、表示側も `aspect-video` に統一**
- **`devices` はデバイスと向きを合成した列挙型で必須フィールド** — 別フィールドに分けるとPCに向きを指定する無意味な組み合わせが表現可能になる
- **`controls` は文字列配列の任意フィールド** — 記載内容がゲームごとに異なり、構造を固定すると当てはまらない項目が出る
- **テストは `validateGame` に限定し、表示コンポーネントには書かない** — 段階②では `MobileNav` のみ例外(実際の振る舞いを持つため)
- **一覧の並び替え機能は実装しない** — 当時ゲーム3件では選択肢として機能しなかった判断(2026-08-25)。2026-09-01時点でカタログは5件(character-tactics/dragon-shooter/rungame-sample/sea-defence/shogi-vs-cpu)に増えたが、判断自体は据え置き。再検討する場合はこの前提の変化を踏まえること
- **`next dev` の `AGENTS.md`/`CLAUDE.md` 自動生成は無効化**(`next.config.js` の `agentRules: false`)

## Known Issues / Blockers

- **問い合わせフォームの URL は到達確認をしていない**。`curl` の実行が許可されなかったため。ブラウザで開いて確認すること
- **`apple-icon.png` は未作成**。ImageMagick が実装環境に無かったため生成を見送った。サイトの利用には影響しない(iOS ホーム画面追加時にページのスクリーンショットが代わりに使われるのみ)
- **ローカルのゲームリポジトリのクローンが古い**。`../rungame-sample` は `origin/main` より遅れ、`../shogi-vs-cpu` は `docs/` しか無い。`character-tactics` は未クローン。スクリーンショットは本番URLから撮れば影響しない
- **Terraform state が CI とローカルで共有されていない**。当面 `allow_overwrite` でしのいでいる。詳細は `infra/README.md`
- **auto mode の分類器が `git push`・`gh pr merge`・`gh run list`・`curl`・`aws cloudformation delete-stack` などデプロイ/削除に関わるコマンドを断続的にブロックする**。今回の移行作業ではその都度ユーザー本人に実行を依頼した。次回も同様の詰まりが起こりうる
- **`hermit-life/.claude/skills/add-game/SKILL.md`(16行目・51行目)が、移行で削除済みの `sea-defence` を例・参照先として挙げたまま**。`rungame` が生きているため手順自体は機能するが、参照先の記述は古い。修正は hermit-life main への push を伴う(CDKパイプラインが起動する)ため、今回はデプロイ回避のため見送った。次に hermit-life 側で何か変更する機会にまとめて直すとよい

## Context Files

次のセッションで読む順。

1. このHANDOVER.md
2. `README.md` — 現在の仕様・手順の正典

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
3. 最初のアクション: スマートフォン実機でのハンバーガーメニュー確認、またはスクリーンショットの追加投入から着手する
