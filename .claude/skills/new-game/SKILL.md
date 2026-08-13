---
name: new-game
description: ankardoのサブリソースとして新しいゲームリポジトリをankardo.com/play/<slug>/*にホストするための初期設定手順。新しいゲームを追加する、ゲームリポジトリをankardoに接続する、といった依頼のときに使う。
---

# 新しいゲームリポジトリをankardoに接続する

ankardoのゲームは各ゲームごとに独立したリポジトリで開発し、Wranglerで `ankardo.com/play/<slug>/*` に自己完結デプロイする(設計の背景は `docs/superpowers/specs/2026-08-12-ankardo-infra-design.md` 参照)。Terraform state やCloudflare provider権限を共有する必要はない。

実例: `rungame-sample`(Phaser 3 + Vite製ゲーム)。このリポジトリの `wrangler.toml` / `.github/workflows/deploy.yml` をテンプレートとして参照してよい。

## 前提

- ゲームは静的アセット(HTML/CSS/JS)としてビルドできること。SSRは不要(Workers Static Assetsで配信)
- ビルド出力先ディレクトリが1つに定まっていること(例: `out/`, `dist/`)

## 手順

### 1. slugを決める

`<slug>` にはゲームリポジトリの名前をそのまま使う。プレフィックス(`ankardo-game-`等)は付けない。例: リポジトリ `rungame-sample` → slug `rungame-sample`。

### 2. ゲームリポジトリ側: ビルドのベースパスをankardoの配信パスに合わせる

フレームワークのbase path設定を `/play/<slug>/` にする。

- Vite: `vite.config.ts` の `base: '/play/<slug>/'`
- Next.js (`output: 'export'`): `next.config.js` の `basePath: '/play/<slug>'`
- その他: 各フレームワークの相当する設定(アセットの絶対パス解決に影響するため必須)

### 3. ゲームリポジトリ側: `wrangler.toml` を作成

```toml
name = "ankardo-game-<slug>"
compatibility_date = "<作成日>"

routes = [
  { pattern = "ankardo.com/play/<slug>/*", zone_name = "ankardo.com" }
]

[assets]
directory = "./<ビルド出力先>"
not_found_handling = "404-page"
```

### 4. ゲームリポジトリ側: デプロイ用GitHub Actions workflowを作成

`.github/workflows/deploy.yml` に、`main` push時に build → `cloudflare/wrangler-action` で deploy するworkflowを作成する。ankardoの `.github/workflows/site.yml` と同じ構成(actionsはSHAピン留め、`environment: production`、`permissions: contents: read`)に揃える。テストがあれば build 前に実行する。

### 5. ankardo側: ゲームをカタログに登録

`site/content/games/<slug>.json` を作成する:

```json
{
  "slug": "<slug>",
  "title": "<ゲームタイトル>",
  "description": "<説明文>",
  "playUrl": "/play/<slug>/"
}
```

`site/lib/games.ts` がこのディレクトリを自動的に拾うため、コード変更は不要。

### 6. 手動確認事項(エージェントが自動実行できない項目)

- ゲームリポジトリのGitHub Secretsに `CLOUDFLARE_API_TOKEN` / `CLOUDFLARE_ACCOUNT_ID` を登録する
- ゲームリポジトリに `production` environment保護ルール(必須レビュアー、`main`ブランチのみ許可)を設定する(ankardo側と同様)
- `wrangler deploy`(実際にCloudflare上へ反映する操作)は、Cloudflare認証情報を保有するユーザーの明示的な承認を得てから実行する
- ankardo側の `site/` を再ビルド・デプロイし、カタログ一覧・詳細ページに反映されたことを確認する
