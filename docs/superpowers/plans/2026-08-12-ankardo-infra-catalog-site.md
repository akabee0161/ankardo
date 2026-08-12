# Ankardo インフラ・カタログサイト Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `ankardo.com` を Cloudflare(Terraform + Wrangler)上に公開できる状態にし、Next.js製のゲームカタログサイト(トップ・一覧・個別詳細ページ)を配信する基盤を構築する。

**Architecture:** モノレポ `infra/`(Terraformでゾーン・DNS・SSL設定を管理)と `site/`(Next.js静的書き出しのカタログサイト、Wranglerでルート `ankardo.com/*` にデプロイ)の2本柱。将来の各ゲームは別リポジトリからルート `ankardo.com/play/<slug>/*` に独立デプロイする想定(本計画の対象外)。GitHub Actionsで `infra/` と `site/` それぞれのCI/CDを構築する。

**Tech Stack:** Terraform (Cloudflare provider ~> 4), Wrangler CLI, Next.js (App Router, `output: 'export'`), TypeScript, GitHub Actions

## Global Constraints

- ドメインは `ankardo.com`(Cloudflareで登録・DNS管理、Route53への移管は行わない)
- SSL証明書はCloudflareの証明書機能を使用する(ACM不使用)
- ルーティング: `ankardo.com/games*` はカタログサイトが専有、`ankardo.com/play/*` は各ゲームリポジトリが専有(このパス設計は変更しない)
- IaCの分担: Cloudflareゾーン/DNS/SSL設定は **Terraform**(`infra/`)、Worker(サイト・ゲーム双方)のデプロイは **Wrangler** に一本化する
- Next.jsは `output: 'export'` による静的書き出しを使用する(SSR機能は使わない)
- **`terraform apply` および `wrangler deploy`(実際にCloudflare上へ反映する操作)は、Cloudflare認証情報を保有するユーザーの明示的な承認を得てから実行する。** 各タスクの自動検証は `terraform validate` / `terraform plan` / `next build` / dry-run 相当にとどめ、本番反映は別途ユーザーに確認を取ってから行うこと
- 参照元spec: `docs/superpowers/specs/2026-08-12-ankardo-infra-design.md`

---

## Task 1: Terraformセットアップとゾーン参照

**Files:**
- Create: `infra/versions.tf`
- Create: `infra/providers.tf`
- Create: `infra/variables.tf`
- Create: `infra/zone.tf`
- Create: `infra/.gitignore`

**Interfaces:**
- Consumes: なし(最初のタスク)
- Produces: `data.cloudflare_zone.ankardo`(Task 2で参照する既存ゾーンへの参照)、`var.domain`(値: `"ankardo.com"`)

- [ ] **Step 1: Terraform CLIをインストール(未インストールのため)**

このサンドボックス環境には Terraform がインストールされていない。ネットワークアクセスがある環境で以下を実行する。

```bash
TF_VERSION=$(curl -s https://checkpoint-api.hashicorp.com/v1/check/terraform | python3 -c "import sys,json; print(json.load(sys.stdin)['current_version'])")
curl -sLo /tmp/terraform.zip "https://releases.hashicorp.com/terraform/${TF_VERSION}/terraform_${TF_VERSION}_linux_amd64.zip"
unzip -o /tmp/terraform.zip -d ~/.local/bin
terraform version
```

Expected: `Terraform v<version>` が出力される(`~/.local/bin` がPATHに含まれていることを前提とする)。

- [ ] **Step 2: infra/versions.tf を作成**

```hcl
terraform {
  required_version = ">= 1.7.0"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}
```

- [ ] **Step 3: infra/providers.tf を作成**

```hcl
# CLOUDFLARE_API_TOKEN 環境変数から自動的にAPIトークンを読み込む
provider "cloudflare" {}
```

- [ ] **Step 4: infra/variables.tf を作成**

```hcl
variable "domain" {
  description = "Ankardoのルートドメイン"
  type        = string
  default     = "ankardo.com"
}
```

- [ ] **Step 5: infra/zone.tf を作成**

```hcl
# ankardo.com は Cloudflare Registrar で既に登録済み・ゾーンも自動作成済みのため、
# 新規作成ではなく既存ゾーンを data source で参照する
data "cloudflare_zone" "ankardo" {
  name = var.domain
}
```

- [ ] **Step 6: infra/.gitignore を作成**

```
.terraform/
*.tfstate
*.tfstate.*
```

(`.terraform.lock.hcl` はコミット対象に含める)

- [ ] **Step 7: terraform init と validate を実行**

```bash
cd infra
terraform init
terraform validate
```

Expected: `terraform init` がproviderのダウンロードに成功し、`terraform validate` が `Success! The configuration is valid.` を出力する。この2コマンドはCloudflare認証情報がなくても実行できる。

- [ ] **Step 8: コミット**

```bash
cd /home/ubuntu/workspace/ankardo
git add infra/versions.tf infra/providers.tf infra/variables.tf infra/zone.tf infra/.gitignore
git commit -m "feat(infra): add terraform scaffold and cloudflare zone reference"
```

---

## Task 2: DNSレコードとSSL/TLS設定

**Files:**
- Create: `infra/dns.tf`
- Create: `infra/zone_settings.tf`

**Interfaces:**
- Consumes: `data.cloudflare_zone.ankardo.id`(Task 1で定義)
- Produces: なし(このタスクの成果物はCloudflare側の設定そのもの。後続タスクはこれに依存しない)

- [ ] **Step 1: infra/dns.tf を作成**

Cloudflare WorkersのRoute機能はゾーンへの到達済みリクエストをパスパターンでWorkerに振り分けるため、実際の配信先IPを指すオリジンは不要。ただし、リクエストがCloudflareのエッジに到達するには、ルートドメインの proxied(オレンジクラウド)なDNSレコードが必要。

```hcl
resource "cloudflare_record" "root" {
  zone_id = data.cloudflare_zone.ankardo.id
  name    = "@"
  type    = "A"
  content = "192.0.2.1" # プレースホルダー。Workers Routeが全リクエストを処理するため実際に疎通しない
  proxied = true
  comment = "Placeholder origin - traffic is served entirely by Cloudflare Workers routes"
}
```

- [ ] **Step 2: infra/zone_settings.tf を作成**

```hcl
resource "cloudflare_zone_settings_override" "ankardo" {
  zone_id = data.cloudflare_zone.ankardo.id

  settings {
    ssl = "full"
  }
}
```

- [ ] **Step 3: terraform validate を実行**

```bash
cd infra
terraform validate
```

Expected: `Success! The configuration is valid.`

- [ ] **Step 4: terraform plan を実行(要Cloudflare認証情報)**

```bash
cd infra
export CLOUDFLARE_API_TOKEN="<ユーザーが発行したトークン>"
terraform plan
```

Expected: `cloudflare_record.root` の作成、`cloudflare_zone_settings_override.ankardo` の作成がplanに表示される。**この環境にはCloudflare認証情報がないため、このステップはユーザーが自身の認証情報で実行する。**

- [ ] **Step 5: terraform apply の実行はユーザーの承認を得てから行う**

`terraform plan` の内容をユーザーと一緒に確認し、明示的な承認を得てから `terraform apply` を実行する。エージェントが無承認で実行してはならない(Global Constraints参照)。

- [ ] **Step 6: コミット**

```bash
cd /home/ubuntu/workspace/ankardo
git add infra/dns.tf infra/zone_settings.tf
git commit -m "feat(infra): add proxied dns record and ssl/tls zone setting"
```

---

## Task 3: Next.jsカタログサイトの雛形

**Files:**
- Create: `site/package.json`
- Create: `site/next.config.js`
- Create: `site/lib/games.ts`
- Create: `site/content/games/sample-quest.json`
- Create: `site/app/layout.tsx`
- Create: `site/app/page.tsx`
- Create: `site/app/games/page.tsx`
- Create: `site/app/games/[slug]/page.tsx`
- Create: `site/app/not-found.tsx`
- Create: `site/.gitignore`

**Interfaces:**
- Consumes: なし
- Produces: `Game` 型、`getAllGames(): Game[]`、`getGame(slug: string): Game | undefined`(`site/lib/games.ts` からexport。将来ゲーム追加時、`site/content/games/<slug>.json` を追加するだけでこれらの関数が自動的に拾う)。ビルド成果物 `site/out/`(Task 4が消費)

- [ ] **Step 1: site/ ディレクトリを初期化しNext.js関連パッケージをインストール**

```bash
mkdir -p site
cd site
npm init -y
npm install next@latest react@latest react-dom@latest
npm install -D typescript @types/node @types/react @types/react-dom
```

- [ ] **Step 2: site/package.json の scripts を編集**

`"scripts"` フィールドを以下に置き換える(`npm init -y` が生成した `"test"` エントリ等は削除):

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build"
  }
}
```

- [ ] **Step 3: site/next.config.js を作成**

```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;
```

- [ ] **Step 4: site/lib/games.ts を作成**

```ts
import fs from "node:fs";
import path from "node:path";

export type Game = {
  slug: string;
  title: string;
  description: string;
  playUrl: string;
  screenshot?: string;
};

const GAMES_DIR = path.join(process.cwd(), "content", "games");

export function getAllGames(): Game[] {
  const files = fs.readdirSync(GAMES_DIR).filter((f) => f.endsWith(".json"));
  const games = files.map((file) => {
    const raw = fs.readFileSync(path.join(GAMES_DIR, file), "utf-8");
    return JSON.parse(raw) as Game;
  });
  return games.sort((a, b) => a.slug.localeCompare(b.slug));
}

export function getGame(slug: string): Game | undefined {
  return getAllGames().find((game) => game.slug === slug);
}
```

- [ ] **Step 5: site/content/games/sample-quest.json を作成**

実ゲームが1本もまだ存在しないため、パイプライン検証用のプレースホルダーデータを1件用意する。最初の実ゲーム公開時にこのファイルを実データに置き換える(または削除して新しいファイルを追加する)。

```json
{
  "slug": "sample-quest",
  "title": "Sample Quest (placeholder)",
  "description": "これはカタログサイトの雛形を検証するためのサンプルデータです。最初の実ゲーム公開時に置き換えてください。",
  "playUrl": "/play/sample-quest/"
}
```

- [ ] **Step 6: site/app/layout.tsx を作成**

```tsx
import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Ankardo",
  description: "子供向けインディーゲームカタログ Ankardo",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
```

- [ ] **Step 7: site/app/page.tsx を作成**

```tsx
import Link from "next/link";

export default function Home() {
  return (
    <main>
      <h1>Ankardo</h1>
      <p>子供向けインディーゲームのカタログサイトです。</p>
      <Link href="/games">ゲーム一覧を見る</Link>
    </main>
  );
}
```

- [ ] **Step 8: site/app/games/page.tsx を作成**

```tsx
import Link from "next/link";
import { getAllGames } from "../../lib/games";

export default function GamesList() {
  const games = getAllGames();

  return (
    <main>
      <h1>ゲーム一覧</h1>
      <ul>
        {games.map((game) => (
          <li key={game.slug}>
            <Link href={`/games/${game.slug}`}>{game.title}</Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
```

- [ ] **Step 9: site/app/games/[slug]/page.tsx を作成**

```tsx
import { notFound } from "next/navigation";
import { getAllGames, getGame } from "../../../lib/games";

export function generateStaticParams() {
  return getAllGames().map((game) => ({ slug: game.slug }));
}

export default async function GameDetail({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const game = getGame(slug);

  if (!game) {
    notFound();
  }

  return (
    <main>
      <h1>{game.title}</h1>
      <p>{game.description}</p>
      <a href={game.playUrl}>プレイする</a>
    </main>
  );
}
```

- [ ] **Step 10: site/app/not-found.tsx を作成**

```tsx
export default function NotFound() {
  return (
    <main>
      <h1>ページが見つかりません</h1>
      <p>お探しのページは存在しないか、移動した可能性があります。</p>
      <a href="/">トップページに戻る</a>
    </main>
  );
}
```

- [ ] **Step 11: site/.gitignore を作成**

```
node_modules/
.next/
out/
*.tsbuildinfo
```

- [ ] **Step 12: ビルドして静的書き出しを検証**

```bash
cd site
npm run build
find out -type f -name "*.html"
```

Expected: exit code 0。出力ファイル一覧に `out/index.html`、`out/games/index.html`(または `out/games.html`)、`out/games/sample-quest/index.html`(または同等のslugパス)、`out/404.html` が含まれること。Next.jsのバージョンによって末尾スラッシュの有無で実際のパスが多少変わる場合があるため、`find` の実際の出力で該当ページが生成されていることを確認する。

- [ ] **Step 13: コミット**

```bash
cd /home/ubuntu/workspace/ankardo
git add site/package.json site/package-lock.json site/next.config.js site/lib site/content site/app site/.gitignore
git commit -m "feat(site): scaffold next.js catalog site with static export"
```

---

## Task 4: カタログサイトのWrangler設定

**Files:**
- Create: `site/wrangler.toml`

**Interfaces:**
- Consumes: `site/out/`(Task 3のビルド成果物)
- Produces: Cloudflare Worker `ankardo-site`(ルート `ankardo.com/*`)

- [ ] **Step 1: site/wrangler.toml を作成**

```toml
name = "ankardo-site"
compatibility_date = "2026-08-12"

routes = [
  { pattern = "ankardo.com/*", zone_name = "ankardo.com" }
]

[assets]
directory = "./out"
not_found_handling = "404-page"
```

- [ ] **Step 2: dry-runで設定を検証**

```bash
cd site
npx wrangler deploy --dry-run
```

Expected: 設定ファイルの構文エラーがないこと。この環境にはCloudflare認証情報がないため、認証エラーで止まる場合は想定内。認証情報がある環境(ユーザーのローカル、またはGitHub Actions)で改めて dry-run を確認する。

- [ ] **Step 3: 実際の wrangler deploy はユーザーの承認を得てから行う**

Global Constraints参照。エージェントが無承認で本番デプロイしてはならない。

- [ ] **Step 4: コミット**

```bash
cd /home/ubuntu/workspace/ankardo
git add site/wrangler.toml
git commit -m "feat(site): add wrangler config for workers static assets deploy"
```

---

## Task 5: GitHub Actions - infra CI/CD

**Files:**
- Create: `.github/workflows/infra.yml`

**Interfaces:**
- Consumes: `infra/`(Task 1, 2)、GitHub Secrets `CLOUDFLARE_API_TOKEN`(ユーザーが事前にリポジトリ設定で登録)
- Produces: なし

- [ ] **Step 1: .github/workflows/infra.yml を作成**

```yaml
name: Infra (Terraform)

on:
  pull_request:
    paths:
      - "infra/**"
  push:
    branches: [main]
    paths:
      - "infra/**"

jobs:
  terraform:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: infra
    env:
      CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
      - run: terraform init
      - run: terraform validate
      - run: terraform plan
        if: github.event_name == 'pull_request'
      - run: terraform apply -auto-approve
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
```

- [ ] **Step 2: YAML構文を検証**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/infra.yml'))" && echo "YAML OK"
```

Expected: `YAML OK` が出力される。

- [ ] **Step 3: コミット**

```bash
cd /home/ubuntu/workspace/ankardo
git add .github/workflows/infra.yml
git commit -m "ci: add terraform plan/apply workflow for infra"
```

---

## Task 6: GitHub Actions - site CI/CD

**Files:**
- Create: `.github/workflows/site.yml`

**Interfaces:**
- Consumes: `site/`(Task 3, 4)、GitHub Secrets `CLOUDFLARE_API_TOKEN`
- Produces: なし

- [ ] **Step 1: .github/workflows/site.yml を作成**

```yaml
name: Site (Next.js)

on:
  push:
    branches: [main]
    paths:
      - "site/**"

jobs:
  deploy:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: site
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: site/package-lock.json
      - run: npm ci
      - run: npm run build
      - uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          workingDirectory: site
          command: deploy
```

- [ ] **Step 2: YAML構文を検証**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/site.yml'))" && echo "YAML OK"
```

Expected: `YAML OK` が出力される。

- [ ] **Step 3: コミット**

```bash
cd /home/ubuntu/workspace/ankardo
git add .github/workflows/site.yml
git commit -m "ci: add build and deploy workflow for catalog site"
```

---

## 実装後の手動確認事項(エージェントが自動実行できない項目)

- Cloudflare APIトークンの発行(DNS編集・Workers編集権限を含むゾーンスコープ)し、ローカル環境変数とGitHub Actions Secretsの両方に登録する
- `terraform apply` を実行し、DNSレコード・SSL設定を実際に反映する
- `wrangler deploy` を実行し、カタログサイトを実際に公開する
- ブラウザで `https://ankardo.com` にアクセスし、トップページ・一覧・詳細ページ・404ページが期待通り表示されることを確認する
