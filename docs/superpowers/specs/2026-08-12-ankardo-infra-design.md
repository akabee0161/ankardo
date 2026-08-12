# Ankardo インフラ・カタログサイト設計

- 日付: 2026-08-12
- ステータス: 承認済み

## 背景

子供向けインディーゲームサイト「Ankardo」を展開する。ドメイン `ankardo.com` は Cloudflare で登録・DNS管理する(Route53 でのアカウントレベル制限のため、AWSではなくCloudflareを採用。詳細経緯は本ドキュメントの対象外)。

サイトはブランド/カタログのトップページと、別リポジトリで開発される複数の自作ゲームを、同一ドメイン上でホストする構成を目指す。

## 確定方針

- **DNS**: Cloudflareを使用(Route53への移管は行わない)
- **SSL証明書**: Cloudflareの証明書機能を使用(ACM不使用)
- **ホスティング**: Cloudflare Workers(Workers Static Assets)
- **IaC**: Terraform + Wrangler のハイブリッド
- **メール(MX等)**: 対象外。後日別途検討

## アーキテクチャ

### リポジトリ構成(モノレポ)

このリポジトリ(`ankardo`)には以下を内包する。

```
ankardo/
├── infra/     # Terraform (Cloudflareゾーン・DNS管理)
└── site/      # Next.js カタログサイト(静的書き出し)
```

ゲーム本体は将来、ゲームごとに別リポジトリ(例: `ankardo-game-<slug>`)として作成する。カタログリポジトリ・Terraformリポジトリとは独立してデプロイできることを要件とする。

### ルーティング設計

| パス | 所有者 | 内容 |
|---|---|---|
| `ankardo.com/` | カタログ(`site/`) | トップページ |
| `ankardo.com/games` | カタログ(`site/`) | ゲーム一覧ページ |
| `ankardo.com/games/<slug>` | カタログ(`site/`) | 個別ゲームのランディング/詳細ページ(静的生成) |
| `ankardo.com/play/<slug>/*` | 各ゲームリポジトリ | 実際にプレイ可能なゲーム本体(独立デプロイ) |

**設計判断:** ランディングページ(`/games/<slug>`)とゲーム本体を同一の `/games/<slug>/*` 配下に置く案も検討したが、カタログとゲームという異なる所有者(異なるリポジトリ)が同じパスツリーを共有すると、将来ゲーム側がAPIやリーダーボード等のパスを追加するたびに衝突リスクの調整が必要になる。そのため `/games/*` はカタログが完全専有、`/play/*` はゲームが完全専有という分離を採用した。

Cloudflare Workersのルーティングは「最も具体的なパターンが優先」されるため、各ゲームが `ankardo.com/play/<slug>/*` という具体的なルートを登録すれば、カタログの `ankardo.com/*`(catch-all)より優先して正しく振り分けられる。ゲーム未デプロイ時やパス不一致時は、カタログのcatch-allが拾うため、カタログ側でカスタム404ページとして適切に処理する。

### カタログサイト技術選定

Next.js(静的書き出し `output: 'export'`)を採用。

**検討の経緯:** 静的コンテンツ中心という要件だけを見ればAstro(コンテンツ重視の静的サイトジェネレータ)が技術的に最適との考え方もあるが、以下の理由でNext.js静的書き出しを選定した。

- カタログサイトはページ数が少なく、Astroの Islands Architecture(JS削減)の恩恵が実質的に小さい規模である
- Next.jsの静的書き出しはCloudflareへのデプロイ上も純粋な静的アセット配信となり、Astroと同等のシンプルさで済む(Next.js on Cloudflare特有のアダプタの複雑さも回避できる)
- 開発者の既存知識(React/Next.js)を活かせ、本プロジェクトで新たに学習するCloudflare Workers/Terraformに学習コストを集中できる

**将来の制約:** カタログサイト自体にSSRや動的機能(ログイン、パーソナライズ等)が必要になった場合、静的書き出しでは対応できず、Workersアダプタの導入または別フレームワークへの移行が必要になる。現状の要件(静的カタログ)ではその可能性は低いと判断している。

### IaC構成

| 対象 | ツール | 理由 |
|---|---|---|
| Cloudflareゾーン設定(DNS、SSL/TLSモード等) | **Terraform**(`infra/`) | ドメイン全体に関わる共有・低頻度変更のリソース。変更履歴・レビューの重要度が高い |
| カタログサイトのデプロイ(ルート `ankardo.com/*`) | **Wrangler**(`site/` 内) | Next.js静的書き出し + Workers Static Assetsのデプロイに特化したCloudflare公式ツール |
| 各ゲームのデプロイ(ルート `ankardo.com/play/<slug>/*`) | **Wrangler**(各ゲームリポジトリ内) | ゲームリポジトリが完全に自己完結してデプロイできる(Terraform stateやCloudflare provider権限を共有する必要がない) |

TerraformのCloudflare providerはWorkerスクリプト自体のデプロイには不向き(バンドルアップロードをTerraformで扱うのは実用的でない)なため、Workerのデプロイは全てWranglerに一本化する。Terraformはゾーン/DNSのような永続的・共有的なリソースの管理に限定する。

### CI/CD (GitHub Actions)

このリポジトリは既存のGitHubリポジトリにpushして運用する(リポジトリURLは別途共有予定)。

- `infra/` 配下の変更: PR時に `terraform plan` を実行、mainブランチへのマージ時に `terraform apply` を実行
- `site/` 配下の変更: mainブランチへのpush時に `next build` → `wrangler deploy` を実行
- Cloudflare APIトークンは GitHub Actions の Secrets に登録して使用する

### データフロー: ゲーム追加時の作業フロー

1. **ゲームリポジトリ側**(自己完結): `wrangler.toml` にルート `ankardo.com/play/<slug>/*` を設定し、独立してデプロイする
2. **カタログリポジトリ側**: `site/content/games/<slug>.json`(またはMDX)にタイトル・説明・スクリーンショット・プレイURL(`/play/<slug>/`)を追加する
3. カタログを `next build && next export` してWranglerで再デプロイする。これにより静的ページ `/games/<slug>` が生成・公開される

スクリーンショット等のランディング素材はカタログリポジトリ側で管理し、ゲームリポジトリの内部構造には依存しない。

### エラーハンドリング

- カタログ側にNext.jsのカスタム404ページを用意する。未登録の `/play/<slug>` パスや存在しない `/games/<slug>` パスへのアクセスもここで処理する
- デプロイ後にCloudflare Universal SSL証明書の発行状況を確認する

## スコープ

### 今回の対象

- Terraformによるゾーン/DNS管理の構築(`infra/`)
- Next.jsカタログサイトの骨格(トップページ・一覧ページ・個別詳細ページの雛形)構築とデプロイ(`site/`)
- GitHub Actionsによる `infra/` と `site/` それぞれのCI/CD構築

### 今回の対象外

- 実際のゲーム本体の実装(別リポジトリ・将来作業)
- メール(MX等)設定
- カタログサイトの動的機能(ログイン、パーソナライズ等)

## 未確定事項 / 今後の検討事項

- GitHub リポジトリのURL(ユーザーより別途共有予定)
- Cloudflare APIトークンの発行・権限スコープ(実装フェーズで対応)
