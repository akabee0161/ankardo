# Ankardo

子供向けインディーゲームカタログサイト。ドメイン `ankardo.com` を Cloudflare(Terraform + Wrangler)上に公開する。

設計の背景・経緯は `docs/superpowers/specs/2026-08-12-ankardo-infra-design.md` 参照(このドキュメント運用ルールについては下記「ドキュメント運用ルール」を参照)。

## 構成

モノレポ構成。

```text
ankardo/
├── infra/     # Terraform (Cloudflareゾーン・DNS・SSL設定)
├── site/      # Next.js カタログサイト(静的書き出し、トップ・一覧・個別詳細・このサイトについて)
└── .github/workflows/
    ├── infra.yml  # infra/ 変更時の terraform plan/apply
    └── site.yml   # site/ 変更時の next build → wrangler deploy
```

ゲーム本体は将来、ゲームごとに別リポジトリとして作成し、`ankardo.com/play/<slug>/*` に独立デプロイする(このリポジトリの対象外)。

### ゲームリポジトリの命名規則

`<slug>` にはゲームリポジトリの名前をそのまま使う(例: リポジトリ `rungame-sample` → `ankardo.com/play/rungame-sample/*`、`site/content/games/rungame-sample.json`)。プレフィックス(`ankardo-game-`等)は付けない。新しいゲームリポジトリを立ち上げる手順は `.claude/skills/new-game/SKILL.md` 参照。

### ルーティング

| パス | 所有者 | 内容 |
|---|---|---|
| `ankardo.com/` | カタログ(`site/`) | トップページ |
| `ankardo.com/games` | カタログ(`site/`) | ゲーム一覧ページ |
| `ankardo.com/about` | カタログ(`site/`) | このサイトについて(目的・安全性の方針・運営者と連絡先) |
| `ankardo.com/games/<slug>` | カタログ(`site/`) | 個別ゲームのランディング/詳細ページ |
| `ankardo.com/play/<slug>/*` | 各ゲームリポジトリ | プレイ可能なゲーム本体(独立デプロイ) |

## 開発

### site/ (Next.js カタログサイト)

```bash
cd site
npm install
npm run dev    # 開発サーバ
npm test       # Vitest でバリデーションと MobileNav のテストを実行
npm run build  # 静的書き出し (out/)
```

`MobileNav` のテストだけはファイル冒頭の docblock で `jsdom` 環境を指定している。他のテストは `node` 環境で動く。

ゲームを追加する場合は `site/content/games/<slug>.json` を追加すると一覧・詳細ページに反映される。`slug`/`title`/`description`/`playUrl`/`genre`/`devices`/`ageRange`/`players`/`difficulty` が必須。`genre` は `site/lib/genres.ts` の `GENRES` に、`devices` は `site/lib/devices.ts` の `DEVICES` に定義されたキーである必要がある(`site/lib/games.ts` の `getAllGames()` がビルド時に検証し、不正な場合はエラーになる)。スクリーンショットは `site/public/screenshots/<slug>/` に16:9で置く。フィールドとアセットの詳細は `.claude/skills/new-game/SKILL.md` 参照。ゲームリポジトリ側の初期設定も同ファイル参照。

#### ブランドアセット

- シンボルは `site/components/CatfishMark.tsx`（ナマズの正面顔、SVG 1点）。色は `currentColor` で、呼び出し側が決める
- ブランド色は藍 `#1f3a5f`。`site/app/globals.css` の `@theme` に `--color-brand` として定義し、`text-brand` / `bg-brand` で使う。既存ボタンの `bg-neutral-900` は据え置き
- ファビコンは `site/app/icon.svg`(白地の角丸四角＋藍のナマズ)。Next.js のファイル規約で `<link rel="icon">` が自動生成される
- ヘッダー/フッターのリンクは `site/lib/nav.ts` に集約する。リンクを増やすときはこのファイルだけを変更する
- Webフォントは読み込まない(表示速度優先の既存方針)

### infra/ (Terraform)

Cloudflareゾーン・DNS・SSL設定を管理する。ローカルでの `terraform apply` はユーザーの明示的な承認を得てから実行する(エージェントが無承認で実行してはならない)。既知の制約(Terraform stateがCIとローカルで共有されていない件)は `infra/README.md` 参照。

## デプロイ

- `infra/**` を変更してmainにpush → `Infra (Terraform)` ワークフローが `terraform apply` を実行(production environmentの承認が必要)
- `site/**` を変更してmainにpush → `Site (Next.js)` ワークフローが `next build` → `wrangler deploy` を実行(production environmentの承認が必要)

## ドキュメント運用ルール

- **`docs/superpowers/` 配下(specs / plans)は作成時点のログ。** ファイル名の日付時点での記録として扱い、後から実装や運用が変わっても遡って更新しない。「未実施」「TODO」等の当時の記述が現状と食い違っていても、それはバグではなく履歴。
- **最新の状態を表す正典はこの `README.md`(および各ディレクトリの `README.md`、例: `infra/README.md`)。** 実装・手順・制約・前提が変わったら、更新するのはこちら。
- **`HANDOVER.md` はセッション間の作業引き継ぎ用ワーキングメモ。** 直前セッションでの作業内容・残タスクを記録する目的で、セッションごとに上書きされる。恒久的な正典ではない。
- 使い分け: 「なぜこの設計にしたか」を知りたいときはログ(`docs/`)を読む。「今どう動くか・どう操作するか」を知りたいときは正典(README群)を読む。**両者が食い違う場合は常に正典が正しい。**
