# Ankardo

子供向けインディーゲームカタログサイト。ドメイン `ankardo.com` を Cloudflare(Terraform + Wrangler)上に公開する。

設計の背景・経緯は `docs/superpowers/specs/2026-08-12-ankardo-infra-design.md` 参照(このドキュメント運用ルールについては下記「ドキュメント運用ルール」を参照)。

## 構成

モノレポ構成。

```
ankardo/
├── infra/     # Terraform (Cloudflareゾーン・DNS・SSL設定)
├── site/      # Next.js カタログサイト(静的書き出し、トップ・一覧・個別詳細ページ)
└── .github/workflows/
    ├── infra.yml  # infra/ 変更時の terraform plan/apply
    └── site.yml   # site/ 変更時の next build → wrangler deploy
```

ゲーム本体は将来、ゲームごとに別リポジトリとして作成し、`ankardo.com/play/<slug>/*` に独立デプロイする(このリポジトリの対象外)。

### ルーティング

| パス | 所有者 | 内容 |
|---|---|---|
| `ankardo.com/` | カタログ(`site/`) | トップページ |
| `ankardo.com/games` | カタログ(`site/`) | ゲーム一覧ページ |
| `ankardo.com/games/<slug>` | カタログ(`site/`) | 個別ゲームのランディング/詳細ページ |
| `ankardo.com/play/<slug>/*` | 各ゲームリポジトリ | プレイ可能なゲーム本体(独立デプロイ) |

## 開発

### site/ (Next.js カタログサイト)

```bash
cd site
npm install
npm run dev    # 開発サーバ
npm run build  # 静的書き出し (out/)
```

ゲームを追加する場合は `site/content/games/<slug>.json` を追加するだけで一覧・詳細ページに反映される(`site/lib/games.ts` 参照)。

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
