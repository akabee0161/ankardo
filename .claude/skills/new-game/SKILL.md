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

### 2. ゲームリポジトリ側: ビルドのベースパスとディレクトリ構造をankardoの配信パスに合わせる

フレームワークのbase path設定を `/play/<slug>/` にする。

- Vite: `vite.config.ts` の `base: '/play/<slug>/'`
- Next.js (`output: 'export'`): `next.config.js` の `basePath: '/play/<slug>'`
- その他: 各フレームワークの相当する設定(アセットの絶対パス解決に影響するため必須)

**ベースパスの設定だけでは不十分。** Cloudflare Workers Static Assetsは、パス付きルート(`ankardo.com/play/<slug>/*`)を使う場合、**ビルド出力のディレクトリ構造自体もそのパスと同じ階層にネストされていること**を要求する(例: `out/index.html` ではなく `out/play/<slug>/index.html`)。ネストされていないと `wrangler deploy` が `Workers which have static assets cannot be routed on a URL which has a path component` エラーで失敗する。

- Vite: `build.outDir` を `out/play/<slug>` にする(単に `out` のままにしない)
- Next.js: `distDir`/出力先を同様に `/play/<slug>` サブディレクトリの下にネストする

### 3. ゲームリポジトリ側: `wrangler.toml` を作成

`assets.directory` にはビルド出力の**ルート**(上記でネストする前の起点、例 `./out`)を指定する。Wranglerがその中から `play/<slug>/*` を探す。

```toml
name = "ankardo-game-<slug>"
compatibility_date = "<作成日>"

routes = [
  { pattern = "ankardo.com/play/<slug>/*", zone_name = "ankardo.com" }
]

[assets]
directory = "./out"
not_found_handling = "404-page"
```

### 4. ゲームリポジトリ側: デプロイ用GitHub Actions workflowを作成

`.github/workflows/deploy.yml` に、`main` push時に build → `cloudflare/wrangler-action` で deploy するworkflowを作成する。ankardoの `.github/workflows/site.yml` を参照し、以下を共通要件として揃える。

- actionsはSHAピン留め
- `environment: production`
- `permissions: contents: read`
- テストがあれば build 前に実行する

一方、以下は `site/` ディレクトリ構成を前提にした設定であり、多くのゲームリポジトリ(ルート直下にビルド設定がある構成)ではそのままコピーすると動作しない。リポジトリの実際の構成に合わせて調整すること(`site/` サブディレクトリを持つゲームリポジトリなら流用してよい)。

- `on.push.paths: ["site/**"]`(ルート直下構成なら不要。指定するならそのリポジトリの実際のソースパスに合わせる)
- `defaults.run.working-directory: site`
- `cache-dependency-path: site/package-lock.json`
- Wrangler の `workingDirectory: site`

**Wranglerのバージョンを明示的に固定すること。** `cloudflare/wrangler-action` はリポジトリにWranglerがインストールされていない場合、自動で古いバージョン(3.90.0)をインストールする。このバージョンはStep 2で必要になるパス付きルート+Assetsのネスト構造をサポートしておらず、`Workers which have static assets cannot be routed on a URL which has a path component` エラーで失敗する。

- `package.json` の `devDependencies` に `wrangler` (`^4`系) を追加する
- Wrangler 4はNode.js 22以上を要求する。`actions/setup-node` の `node-version` を `"22"` 以上にする(20のままだとバージョンチェックに失敗し、結局古いWranglerにフォールバックしてしまう)

### 5. ankardo側: ゲームをカタログに登録

`site/content/games/<slug>.json` を作成する(必須フィールドを指定する。`genre` は `site/lib/genres.ts` の `GENRES` に定義されたキーのいずれかである必要があり、`site/lib/games.ts` の `getAllGames()` が実行時にビルド時検証する):

```json
{
  "slug": "<slug>",
  "title": "<ゲームタイトル>",
  "description": "<説明文>",
  "playUrl": "/play/<slug>/",
  "genre": "<GENRES(site/lib/genres.ts)のいずれかのキー。例: action>",
  "devices": ["<DEVICES(site/lib/devices.ts)のいずれかのキー。例: pc>"],
  "ageRange": "<対象年齢。例: 5〜8歳>",
  "players": "<プレイ人数。例: ひとり用>",
  "difficulty": "<難易度。例: やさしめ>"
}
```

`devices` は必須で、`site/lib/devices.ts` の `DEVICES` に定義されたキー(`pc` / `mobile-landscape` / `mobile-portrait`)を1つ以上、重複なく指定する。PCとスマホの両方に対応するなら `["pc", "mobile-landscape"]` のように複数指定する。

任意フィールドは次の3つ。

| フィールド | 内容 |
|---|---|
| `controls` | 操作方法。空でない文字列の配列。詳細ページに「あそびかた」として箇条書きで表示される |
| `images` | スクリーンショットのパスの配列(下記「スクリーンショットの規約」参照) |
| `featured` | `true` にするとトップページのピックアップに表示される |

既存の `site/content/games/rungame-sample.json` も参考にできる。

### スクリーンショットの規約

| 項目 | 規約 |
|---|---|
| 置き場所 | `site/public/screenshots/<slug>/` |
| ファイル名 | `01.png`, `02.png` の連番 |
| JSONでの参照 | `"images": ["/screenshots/<slug>/01.png"]` |
| 枚数 | 1〜5点。先頭のファイルが一覧カードのサムネイルになる |
| 比率 | 16:9。表示側も16:9のため、この比率なら切り取られない |
| 解像度 | 1280×720 を基本 |
| ファイルサイズ | 1枚あたり300KB以内が目安。`next.config.js` で `images: { unoptimized: true }` を指定しており画像最適化は動作しないため、超える場合はWebPを使う |

ゲームの論理解像度が16:9の場合(例: `rungame-sample` は720×405、`character-tactics` は960×540)、ブラウザのウィンドウ比率が16:9でないと描画領域の周囲に余白が入る。描画領域だけを切り出すか、ウィンドウを16:9に合わせて撮影する。

`site/lib/games.ts` がこのディレクトリを自動的に拾うため、コード変更は不要。ただし必須フィールドが欠落・`genre` が不正な値の場合は `next build` 時にエラーで失敗する。

### 6. ゲームリポジトリのGitHub Secretsを設定

個人アカウント配下のリポジトリにはOrganization secretsのようなリポジトリ横断の共有機能がないため、リポジトリごとに設定する必要がある。`ankardo/scripts/setup-game-secrets.sh` を使う:

```bash
CLOUDFLARE_API_TOKEN=... CLOUDFLARE_ACCOUNT_ID=... \
  ./scripts/setup-game-secrets.sh <owner>/<ゲームリポジトリ名>
```

`gh secret set` を実行するため `gh auth login` 済みで、対象リポジトリへのadmin権限が必要。

### 7. 手動確認事項(エージェントが自動実行できない項目)

- 上記スクリプトの実行(Cloudflare認証情報を保有するユーザーが実行するか、値を渡して実行を承認する)
- ゲームリポジトリに `production` environment保護ルール(必須レビュアー、`main`ブランチのみ許可)を設定する(ankardo側と同様)
- `wrangler deploy`(実際にCloudflare上へ反映する操作)は、Cloudflare認証情報を保有するユーザーの明示的な承認を得てから実行する
- ankardo側の `site/` を再ビルド・デプロイし、カタログ一覧・詳細ページに反映されたことを確認する
