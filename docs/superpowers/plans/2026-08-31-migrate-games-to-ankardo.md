# dragon-shooter / sea-defence の ankardo 移行 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** hermit-life(AWS)でホストしている `dragon-shooter` と `sea-defence` を ankardo(GitHub + Cloudflare Workers)の `ankardo.com/play/<slug>/` へ完全移行し、hermit-life 側からは撤去する。

**Architecture:** 各ゲームは独立した GitHub リポジトリとして自己完結デプロイする(ankardo と Terraform state や Cloudflare provider 権限を共有しない)。ゲーム側の変更は Vite の `base`/`build.outDir` と Cloudflare 用のデプロイ設定のみで、ゲームロジックには触れない。ankardo 側はカタログ JSON を2件追加するだけ。hermit-life 側は一覧エントリと CDK パイプラインスタックを削除し、共有 S3 バケット上の実体を手動で消す。

**Tech Stack:** Vite / TypeScript / Cloudflare Workers Static Assets(Wrangler 4) / GitHub Actions / AWS CDK(撤去側)

**Spec:** `docs/superpowers/specs/2026-08-31-migrate-games-to-ankardo-design.md`

**このリポジトリ(ankardo)以外を触るタスクがある。** 各タスクの冒頭に作業ディレクトリを明記してあるので必ず確認すること。

## Global Constraints

- **スコープはホスティング移行のみ。** ゲーム本体のロジック・難易度・UI 文言は変更しない。カタログ表示名は英語表記(`Dragon Shooter` / `Sea Defence`)のまま。
- **旧 URL のリダイレクトは作らない。** `hermit-life.net/labs/games/<slug>/` は移行後 404 になる。これは承認済みの決定。
- **`build.outDir` は `out/play/<slug>` にネストする。** Cloudflare Workers Static Assets はパス付きルートに対し、ビルド出力のディレクトリ構造自体が同じ階層にネストされていることを要求する。`out/index.html` のままだと `wrangler deploy` が `Workers which have static assets cannot be routed on a URL which has a path component` で失敗する。
- **`wrangler` は `^4.0.0` を `devDependencies` に入れる。** 入れないと `cloudflare/wrangler-action` が古い 3.90.0 を自動インストールし、上記のネスト構造をサポートせず失敗する。
- **`node-version` は `'22'`。** Wrangler 4 は Node.js 22 以上を要求する。20 だとバージョンチェックに失敗して古い Wrangler にフォールバックする。
- **GitHub Actions の action は SHA ピン留め。** `environment: production`、`permissions: contents: read` を必ず指定する。
- **`wrangler.toml` の `assets.directory` は `./out`**(ネストする前の起点)。Wrangler がその中から `play/<slug>/*` を探す。
- **GitHub リポジトリは public。** 既存の ankardo ゲームリポジトリに揃える。
- **CodeCommit リポジトリの削除は Task 7 まで行わない。** Task 3・4 のデプロイ確認が通るまでロールバック先を残す。
- **手動承認が必要な操作**(エージェントは無承認で実行してはならない): `scripts/setup-game-secrets.sh` の実行、`production` environment 保護ルールの設定、`wrangler deploy`(GitHub Actions 経由を含む)、`cdk destroy`、`aws s3 rm --recursive`、CodeCommit リポジトリの削除。

---

## ファイル構成

**ゲームリポジトリ側**(`dragon-shooter` / `sea-defence` の各リポジトリで同じ構成)

- Modify: `vite.config.ts` — `base` と `build.outDir` を ankardo の配信パスに合わせる
- Create: `wrangler.toml` — Cloudflare Worker 名・ルート・Assets ディレクトリ
- Modify: `package.json` — `wrangler` devDependency と `engines.node`
- Modify: `package-lock.json` — `npm install` による再生成(`npm ci` が CI で通るために必須)
- Create: `.github/workflows/deploy.yml` — main への push で build → deploy
- Modify: `.gitignore` — `.wrangler/` を追加

**ankardo 側**

- Create: `site/content/games/dragon-shooter.json`
- Create: `site/content/games/sea-defence.json`
- Modify: `HANDOVER.md`

**hermit-life 側**

- Modify: `src/app/labs/games/page.tsx` — `games` 配列から2エントリ削除
- Modify: `infra/bin/infra.ts` — `DragonShooterPipelineStack` / `SeaDefencePipelineStack` の定義削除
- Modify: `CLAUDE.md` — 「labs/games — ゲームホスティング構成」の表を実態に合わせる

---

### Task 1: 両ゲームリポジトリを GitHub へ移設

**作業ディレクトリ:** `/home/akabee/development/sea-defence` と `/home/akabee/development/dragon-shooter`

**Files:** このタスクではファイルを一切変更しない。git remote の操作のみ。

**Interfaces:**
- Produces: GitHub 上に `akabee0161/sea-defence` と `akabee0161/dragon-shooter`(いずれも public、`main` がデフォルトブランチ)。以降のタスクはこの2リポジトリの `origin` が GitHub を指している前提で動く。

**注意:** `sea-defence` には `feature/fix-minor-things` と `feature/score-caluculate-fix` の未マージブランチが CodeCommit 上にある。**main にマージはしない。ブランチのまま GitHub へ移す。** Task 7 で CodeCommit を削除するため、ここで移し損ねると失われる。

- [ ] **Step 1: sea-defence の現状を確認する**

```bash
cd /home/akabee/development/sea-defence
git status --short --branch
git branch -r
```

期待: 作業ディレクトリがクリーンで `## main...origin/main` と表示される。`origin/main`・`origin/feature/fix-minor-things`・`origin/feature/score-caluculate-fix`・`origin/HEAD` が見える。

未コミットの変更がある場合はここで停止し、ユーザーに確認する。

- [ ] **Step 2: sea-defence の remote を張り替える**

既存の CodeCommit remote を `codecommit` にリネームし、GitHub リポジトリを作って `origin` にする。

```bash
cd /home/akabee/development/sea-defence
git remote rename origin codecommit
git fetch codecommit
gh repo create akabee0161/sea-defence --public
git remote add origin https://github.com/akabee0161/sea-defence.git
```

- [ ] **Step 3: sea-defence の全ブランチをローカルに実体化する**

CodeCommit 側のリモート追跡ブランチをローカルブランチにする(そうしないと `git push --all` が拾わない)。`HEAD` は擬似 ref なので除外する。

```bash
cd /home/akabee/development/sea-defence
for b in $(git branch -r --format='%(refname:strip=3)' | grep -v '^HEAD$'); do
  git branch --track "$b" "codecommit/$b" 2>/dev/null || true
done
git branch
```

期待: `main`・`feature/fix-minor-things`・`feature/score-caluculate-fix` の3本がローカルブランチとして並ぶ(`main` は既存なので `--track` は失敗するが `|| true` で無視される)。

- [ ] **Step 4: sea-defence を GitHub へ push する**

```bash
cd /home/akabee/development/sea-defence
git push origin --all
git branch -u origin/main main
```

- [ ] **Step 5: sea-defence の移設を検証する**

```bash
cd /home/akabee/development/sea-defence
git ls-remote --heads origin
git log --oneline -1 main
git log --oneline -1 origin/main
```

期待: `origin` に3ブランチが存在し、ローカル `main` と `origin/main` の SHA が一致する。

- [ ] **Step 6: dragon-shooter を同じ手順で移設する**

`dragon-shooter` は `main` のみ(2026-08-31 に CodeCommit から clone 済み)。

```bash
cd /home/akabee/development/dragon-shooter
git status --short --branch
git remote rename origin codecommit
git fetch codecommit
gh repo create akabee0161/dragon-shooter --public
git remote add origin https://github.com/akabee0161/dragon-shooter.git
for b in $(git branch -r --format='%(refname:strip=3)' | grep -v '^HEAD$'); do
  git branch --track "$b" "codecommit/$b" 2>/dev/null || true
done
git push origin --all
git branch -u origin/main main
```

- [ ] **Step 7: dragon-shooter の移設を検証する**

```bash
cd /home/akabee/development/dragon-shooter
git ls-remote --heads origin
git log --oneline -1 main
git log --oneline -1 origin/main
```

期待: `origin` に `main` が存在し、ローカルと SHA が一致する。

このタスクではコミットは発生しない(ファイルを変更していない)。

---

### Task 2: デプロイ基盤の設定

**作業ディレクトリ:** `/home/akabee/development/ankardo`

**Files:** ファイル変更なし。GitHub 側の設定のみ。

**Interfaces:**
- Consumes: Task 1 が作った `akabee0161/sea-defence` と `akabee0161/dragon-shooter`
- Produces: 両リポジトリに `CLOUDFLARE_API_TOKEN` / `CLOUDFLARE_ACCOUNT_ID` の Secrets と、必須レビュアー付きの `production` environment。Task 3・4 の workflow はこの2つが揃っていないと失敗する。

**このタスクは全ステップがユーザーの承認または実行を必要とする。** Cloudflare 認証情報を扱い、リポジトリ設定を変更するため、エージェントが独断で実行してはならない。

- [ ] **Step 1: Secrets の設定をユーザーに依頼する**

`ankardo/scripts/setup-game-secrets.sh` は `gh secret set` を実行する。`gh auth login` 済みかつ対象リポジトリへの admin 権限が必要。Cloudflare 認証情報を保有するユーザーが実行する:

```bash
cd /home/akabee/development/ankardo
CLOUDFLARE_API_TOKEN=... CLOUDFLARE_ACCOUNT_ID=... \
  ./scripts/setup-game-secrets.sh akabee0161/sea-defence
CLOUDFLARE_API_TOKEN=... CLOUDFLARE_ACCOUNT_ID=... \
  ./scripts/setup-game-secrets.sh akabee0161/dragon-shooter
```

- [ ] **Step 2: Secrets が設定されたことを検証する**

```bash
gh secret list --repo akabee0161/sea-defence
gh secret list --repo akabee0161/dragon-shooter
```

期待: 両方に `CLOUDFLARE_ACCOUNT_ID` と `CLOUDFLARE_API_TOKEN` が並ぶ(値は表示されない)。

- [ ] **Step 3: 自分の GitHub ユーザー ID を取得する**

次のステップで必須レビュアーに指定するため、数値 ID が必要。

```bash
gh api user --jq .id
```

- [ ] **Step 4: production environment に保護ルールを設定する**

`<USER_ID>` を Step 3 の出力に置き換えて実行する。`protected_branches: true` により `main` からのデプロイのみ許可される。必須レビュアーを付けることで、以降の `wrangler deploy` は毎回ユーザーの承認待ちになる(= Global Constraints の「`wrangler deploy` は承認を得てから」を仕組みとして満たす)。

```bash
for repo in sea-defence dragon-shooter; do
  gh api -X PUT "repos/akabee0161/$repo/environments/production" --input - <<JSON
{
  "reviewers": [{"type": "User", "id": <USER_ID>}],
  "deployment_branch_policy": {"protected_branches": true, "custom_branch_policies": false}
}
JSON
done
```

- [ ] **Step 5: environment 設定を検証する**

```bash
gh api repos/akabee0161/sea-defence/environments/production \
  --jq '{name, reviewers: [.protection_rules[] | select(.type=="required_reviewers") | .reviewers[].reviewer.login], branch_policy: .deployment_branch_policy}'
gh api repos/akabee0161/dragon-shooter/environments/production \
  --jq '{name, reviewers: [.protection_rules[] | select(.type=="required_reviewers") | .reviewers[].reviewer.login], branch_policy: .deployment_branch_policy}'
```

期待: 両方とも `name: "production"`、`reviewers` に `akabee0161`、`branch_policy.protected_branches: true`。

---

### Task 3: sea-defence を ankardo 仕様に対応してデプロイする

**作業ディレクトリ:** `/home/akabee/development/sea-defence`

**Files:**
- Modify: `vite.config.ts`
- Create: `wrangler.toml`
- Modify: `package.json`
- Modify: `package-lock.json`(`npm install` が再生成)
- Create: `.github/workflows/deploy.yml`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: Task 2 が設定した Secrets と `production` environment
- Produces: `ankardo.com/play/sea-defence/` で動作するゲーム。Task 5 のカタログ JSON の `playUrl` がこの URL を指す。

**このタスクを dragon-shooter より先に完了させること。** Wrangler のバージョン固定と Static Assets のネスト構造は実地でしか検証できない既知の失敗要因なので、1本目で潰してから2本目に流す(spec の採用案A)。

- [ ] **Step 1: vite.config.ts を書き換える**

現状は `base: '/labs/games/sea-defence/'` / `outDir: 'out'`。ankardo の配信パスに合わせ、出力を `out/play/sea-defence` にネストする。ファイル全体を以下に置き換える:

```ts
import { defineConfig } from 'vite';

export default defineConfig({
  base: '/play/sea-defence/',
  build: {
    outDir: 'out/play/sea-defence',
    emptyOutDir: true,
  },
});
```

- [ ] **Step 2: wrangler.toml を作成する**

```toml
name = "ankardo-game-sea-defence"
compatibility_date = "2026-08-31"

routes = [
  { pattern = "ankardo.com/play/sea-defence/*", zone_name = "ankardo.com" }
]

[assets]
directory = "./out"
not_found_handling = "404-page"
```

`directory` はネストする前の起点 `./out` であって `./out/play/sea-defence` ではない。Wrangler が `out` の中から `play/sea-defence/*` を探す。

- [ ] **Step 3: package.json に wrangler と engines を追加する**

`devDependencies` に `wrangler` を足し、`engines` を追加する。ファイル全体を以下に置き換える:

```json
{
  "name": "sea-defence",
  "version": "0.1.0",
  "private": true,
  "engines": { "node": ">=22" },
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "biome check src/",
    "format": "biome format --write src/"
  },
  "devDependencies": {
    "@biomejs/biome": "2.4.15",
    "typescript": "^5.4.5",
    "vite": "^5.2.11",
    "wrangler": "^4.0.0"
  }
}
```

- [ ] **Step 4: package-lock.json を再生成する**

CI は `npm ci` を使う。`npm ci` は `package.json` と `package-lock.json` の不一致で失敗するため、lock の更新とコミットが必須。

```bash
cd /home/akabee/development/sea-defence
npm install
```

- [ ] **Step 5: .gitignore に .wrangler/ を追加する**

現状は `node_modules/` / `dist/` / `out/` / `docs/superpowers/` / `.claude/settings.local.json`。末尾に1行足す:

```
.wrangler/
```

- [ ] **Step 6: .github/workflows/deploy.yml を作成する**

`character-tactics` の workflow がベース。sea-defence はテストを持たないので `npm test` は入れず、既存の Biome lint(`npm run lint`)をデプロイ前ゲートにする。

```yaml
name: deploy

on:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - uses: actions/setup-node@39370e3970a6d050c480ffad4ff0ed4d3fdee5af # v4.1.0
        with:
          node-version: '22'
          cache: npm
      - run: npm ci
      - run: npm run lint
      - run: npm run build
      - uses: cloudflare/wrangler-action@392082e81ffbcb9ebdde27400634aa004b35ea37 # v3.14.0
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
```

- [ ] **Step 7: ローカルで lint とビルドを実行する**

```bash
cd /home/akabee/development/sea-defence
npm run lint
npm run build
```

期待: lint は `Checked NN files` で終わりエラーなし(移行前の時点で既に通ることを確認済み)。build は成功する。

- [ ] **Step 8: ビルド出力のネスト構造を検証する**

これが Wrangler の要求を満たしているかを事前に判定できる唯一のローカル検証。

```bash
cd /home/akabee/development/sea-defence
ls out/play/sea-defence/index.html
grep -o '/play/sea-defence/[^"]*' out/play/sea-defence/index.html | head -5
```

期待: `out/play/sea-defence/index.html` が存在する。`index.html` 内のアセット参照が `/play/sea-defence/assets/...` の形になっている(`/labs/games/` が残っていたら Step 1 の `base` が効いていない)。

- [ ] **Step 9: コミットする**

```bash
cd /home/akabee/development/sea-defence
git add vite.config.ts wrangler.toml package.json package-lock.json .gitignore .github/workflows/deploy.yml
git status --short
git commit -m "feat: migrate hosting to ankardo.com/play/sea-defence"
```

`git status --short` の出力に想定外のファイル(特に `out/` や認証情報を含みうるファイル)が混ざっていないか確認してから commit する。

- [ ] **Step 10: push してデプロイを起動する**

```bash
cd /home/akabee/development/sea-defence
git push origin main
gh run list --repo akabee0161/sea-defence --limit 1
```

push により `deploy` workflow が起動し、`production` environment の必須レビュアー設定によって**承認待ちで停止する**。

- [ ] **Step 11: ユーザーにデプロイ承認を依頼する**

GitHub の Actions 画面から `production` へのデプロイを承認してもらう。承認されるまでエージェントは待機する。

- [ ] **Step 12: workflow の完了を確認する**

```bash
gh run watch --repo akabee0161/sea-defence
```

失敗した場合、`Workers which have static assets cannot be routed on a URL which has a path component` が出ていれば Wrangler のバージョンかネスト構造の問題(Global Constraints 参照)。ログで実際に使われた Wrangler のバージョンを確認する。

- [ ] **Step 13: 実 URL で動作確認する**

```bash
curl -sS -o /dev/null -w '%{http_code}\n' https://ankardo.com/play/sea-defence/
```

期待: `200`。

続いてブラウザでプレイ可能なことを手動確認する(白画面や画像欠けは base path の誤りを示す)。Task 5 で `ageRange` / `difficulty` の妥当性を判断する材料にもなるので、実際に少し遊んでおく。

---

### Task 4: dragon-shooter を ankardo 仕様に対応してデプロイする

**作業ディレクトリ:** `/home/akabee/development/dragon-shooter`

**Files:**
- Modify: `vite.config.ts`
- Create: `wrangler.toml`
- Modify: `package.json`
- Modify: `package-lock.json`
- Create: `.github/workflows/deploy.yml`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: Task 2 の Secrets と `production` environment、Task 3 で検証済みの手順
- Produces: `ankardo.com/play/dragon-shooter/` で動作するゲーム。Task 5 のカタログ JSON の `playUrl` がこの URL を指す。

**Task 3 が完了してから着手すること。**

- [ ] **Step 1: vite.config.ts を書き換える**

現状は `base: "/labs/games/dragon-shooter/"` / `outDir: "out"`。ファイル全体を以下に置き換える:

```ts
import { defineConfig } from "vite";

export default defineConfig({
  base: "/play/dragon-shooter/",
  build: {
    outDir: "out/play/dragon-shooter",
    emptyOutDir: true,
  },
});
```

このゲームは `import.meta.env.BASE_URL` でアセットパスを解決している(`src/core/AssetLoader.ts`)ため、`base` の変更が `public/assets/levels/*.json` の読み込みにも波及する。Step 8 の動作確認でステージが読めることまで見る。

- [ ] **Step 2: wrangler.toml を作成する**

```toml
name = "ankardo-game-dragon-shooter"
compatibility_date = "2026-08-31"

routes = [
  { pattern = "ankardo.com/play/dragon-shooter/*", zone_name = "ankardo.com" }
]

[assets]
directory = "./out"
not_found_handling = "404-page"
```

- [ ] **Step 3: package.json に wrangler と engines を追加する**

`name` が `"shooting-test"` のままだが、Cloudflare Worker 名は `wrangler.toml` の `name` で決まるため配信に影響しない。ホスティング移行のみのスコープにより変更しない。ファイル全体を以下に置き換える:

```json
{
  "name": "shooting-test",
  "version": "1.0.0",
  "type": "module",
  "engines": { "node": ">=22" },
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "keywords": [],
  "author": "",
  "license": "ISC",
  "description": "",
  "dependencies": {
    "pixi.js": "^8.16.0"
  },
  "devDependencies": {
    "typescript": "^5.9.3",
    "vite": "^7.3.1",
    "wrangler": "^4.0.0"
  }
}
```

- [ ] **Step 4: 依存をインストールして package-lock.json を再生成する**

このリポジトリは 2026-08-31 に clone したばかりで `node_modules` が無い。

```bash
cd /home/akabee/development/dragon-shooter
npm install
```

- [ ] **Step 5: .gitignore に .wrangler/ を追加する**

現状は `node_modules` / `dist` / `out` の3行。末尾に1行足す:

```
.wrangler/
```

- [ ] **Step 6: .github/workflows/deploy.yml を作成する**

dragon-shooter は lint もテストも持たないため、build のみをゲートにする(`npm run build` が `tsc && vite build` で型チェックを兼ねる)。sea-defence 版との差分は `npm run lint` ステップが無いことだけ。

```yaml
name: deploy

on:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - uses: actions/setup-node@39370e3970a6d050c480ffad4ff0ed4d3fdee5af # v4.1.0
        with:
          node-version: '22'
          cache: npm
      - run: npm ci
      - run: npm run build
      - uses: cloudflare/wrangler-action@392082e81ffbcb9ebdde27400634aa004b35ea37 # v3.14.0
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
```

- [ ] **Step 7: ローカルでビルドして出力構造を検証する**

```bash
cd /home/akabee/development/dragon-shooter
npm run build
ls out/play/dragon-shooter/index.html
ls out/play/dragon-shooter/assets/levels/stage1.json
grep -o '/play/dragon-shooter/[^"]*' out/play/dragon-shooter/index.html | head -5
```

期待: `index.html` と `assets/levels/stage1.json`(`public/` の内容がコピーされたもの)が存在し、`index.html` 内のアセット参照が `/play/dragon-shooter/...` になっている。

- [ ] **Step 8: コミットして push する**

```bash
cd /home/akabee/development/dragon-shooter
git add vite.config.ts wrangler.toml package.json package-lock.json .gitignore .github/workflows/deploy.yml
git status --short
git commit -m "feat: migrate hosting to ankardo.com/play/dragon-shooter"
git push origin main
```

`git status --short` に想定外のファイルが混ざっていないか確認してから commit する。

- [ ] **Step 9: ユーザーにデプロイ承認を依頼し、完了を確認する**

```bash
gh run watch --repo akabee0161/dragon-shooter
```

- [ ] **Step 10: 実 URL で動作確認する**

```bash
curl -sS -o /dev/null -w '%{http_code}\n' https://ankardo.com/play/dragon-shooter/
curl -sS -o /dev/null -w '%{http_code}\n' https://ankardo.com/play/dragon-shooter/assets/levels/stage1.json
```

期待: どちらも `200`。ステージ JSON が 404 になる場合は `BASE_URL` 経由のパス解決が効いていない。

続いてブラウザでプレイし、ステージが進行することとボスが出ることを確認する。Task 5 の `ageRange: "8歳〜"` / `difficulty: "むずかしめ"` が妥当かをここで判断する。

---

### Task 5: ankardo カタログに2件を登録する

**作業ディレクトリ:** `/home/akabee/development/ankardo`(ブランチ `migrate-games-to-ankardo`)

**Files:**
- Create: `site/content/games/sea-defence.json`
- Create: `site/content/games/dragon-shooter.json`

**Interfaces:**
- Consumes: Task 3・4 でデプロイ済みの `/play/sea-defence/` と `/play/dragon-shooter/`
- Produces: `ankardo.com/games` の一覧と `ankardo.com/games/<slug>` の詳細ページに2件が並ぶ

`site/lib/games.ts` がこのディレクトリを自動で拾うためコード変更は不要。ただし必須フィールドの欠落や `genre` の不正値は `next build` がエラーで落とす。

- [ ] **Step 1: sea-defence のカタログ JSON を作成する**

`genre` は `site/lib/genres.ts` の `GENRES` に定義されたキーであること。拠点(卵)を守るタワーディフェンスなので、同系統の `character-tactics` に揃えて `simulation` を使う。

```json
{
  "slug": "sea-defence",
  "title": "Sea Defence",
  "description": "サメから卵を守る海のタワーディフェンス。タコと珊瑚を置いて全5ウェーブを守りきろう。",
  "playUrl": "/play/sea-defence/",
  "genre": "simulation",
  "ageRange": "5〜8歳",
  "players": "ひとり用",
  "difficulty": "やさしめ"
}
```

- [ ] **Step 2: dragon-shooter のカタログ JSON を作成する**

```json
{
  "slug": "dragon-shooter",
  "title": "Dragon Shooter",
  "description": "ドラゴンを撃ち落とす全5ステージのシューティング。各ステージの最後にはボスが待ち構える。",
  "playUrl": "/play/dragon-shooter/",
  "genre": "shooting",
  "ageRange": "8歳〜",
  "players": "ひとり用",
  "difficulty": "むずかしめ"
}
```

`ageRange` と `difficulty` は Task 4 Step 10 で実際にプレイした感触と食い違う場合、ここで調整する(調整するのはカタログ表記のみ。ゲーム本体の難易度は変更しない)。

- [ ] **Step 3: ビルドで検証する**

```bash
cd /home/akabee/development/ankardo/site
npm ci
npm run build
```

期待: ビルド成功。`getAllGames()` が必須フィールドと `genre` を検証しているため、これが通ればカタログ側の妥当性は担保される。

- [ ] **Step 4: 生成されたページを確認する**

```bash
cd /home/akabee/development/ankardo/site
ls out/games/sea-defence/index.html out/games/dragon-shooter/index.html
```

期待: 両方の詳細ページが静的生成されている(ankardo は `trailingSlash: true` なので `<slug>/index.html` の形になる)。

- [ ] **Step 5: コミットする**

```bash
cd /home/akabee/development/ankardo
git add site/content/games/sea-defence.json site/content/games/dragon-shooter.json
git commit -m "feat(games): add sea-defence and dragon-shooter to catalog"
```

- [ ] **Step 6: PR を作成してユーザーに確認を依頼する**

このブランチには Task 開始前にコミット済みの spec と本計画も含まれる。

```bash
cd /home/akabee/development/ankardo
git push -u origin migrate-games-to-ankardo
gh pr create --title "dragon-shooter / sea-defence を ankardo へ移行" \
  --body "$(cat <<'EOF'
## 変更内容

hermit-life でホストしていた dragon-shooter と sea-defence を ankardo へ移行し、カタログに登録する。

- `site/content/games/sea-defence.json` を追加(genre: simulation)
- `site/content/games/dragon-shooter.json` を追加(genre: shooting)
- 移行方針の spec と実装計画を `docs/superpowers/` に追加

ゲーム本体は別リポジトリ(`akabee0161/sea-defence` / `akabee0161/dragon-shooter`)から Cloudflare へ自己完結デプロイ済み。

## 確認した内容

- `npm run build` が成功し、`/games/sea-defence` と `/games/dragon-shooter` の詳細ページが静的生成されることを確認
- `https://ankardo.com/play/sea-defence/` と `https://ankardo.com/play/dragon-shooter/` が 200 を返し、ブラウザでプレイ可能なことを確認

## 残作業

hermit-life 側の撤去(CDK スタック破棄・S3 実体削除・CodeCommit 削除)は本 PR のスコープ外。
EOF
)"
```

マージ後、ankardo の `site` workflow が `production` の承認待ちになるので、ユーザーに承認を依頼する。デプロイ後 `https://ankardo.com/games` に2件が並ぶことを確認する。

---

### Task 6: hermit-life 側のコードを撤去する

**作業ディレクトリ:** `/home/akabee/development/hermit-life`

**Files:**
- Modify: `src/app/labs/games/page.tsx`
- Modify: `infra/bin/infra.ts`
- Modify: `CLAUDE.md`

**Interfaces:**
- Consumes: Task 5 まで完了し ankardo 側で2ゲームが公開されていること
- Produces: hermit-life の `/labs/games` から2件が消え、`infra.ts` から2スタックの定義が消える。Task 7 の `cdk destroy` はこの `infra.ts` の状態を前提にする。

**Task 5 の確認が完了してから着手すること。** ankardo 側が動く前に hermit-life から消すと、どちらでも遊べない時間ができる。

- [ ] **Step 1: 作業ブランチを作る**

`main` は CDK パイプラインが監視しており、push すると本番デプロイが走る。まずブランチを切る。

```bash
cd /home/akabee/development/hermit-life
git status --short --branch
git checkout -b remove-migrated-games
```

作業ディレクトリがクリーンでない場合はここで停止し、ユーザーに確認する。

- [ ] **Step 2: ゲーム一覧から2エントリを削除する**

`src/app/labs/games/page.tsx` の `games` 配列から `dragon-shooter` と `sea-defence` のオブジェクトを削除し、以下の状態にする:

```ts
const games = [
  {
    slug: "puzzlebobble-like",
    title: "Bubble Shooter",
    description: "シャボン玉を撃って繋げて落とすゲーム",
  },
  {
    slug: "rungame",
    title: "Space Runner",
    description: "宇宙を駆け抜けるランニングゲーム",
  },
];
```

- [ ] **Step 3: CDK スタック定義を2件削除する**

`infra/bin/infra.ts` から以下の2ブロックを削除する。`gamesPipelineStack`(dragon-shooter 用)と `seaDefencePipelineStack` の宣言、および各々の `addDependency` 行の計2組。

削除対象(dragon-shooter):

```ts
const gamesPipelineStack = new GamesPipelineStack(app, "DragonShooterPipelineStack", {
  bucket: staticSiteStack.bucket,
  distribution: staticSiteStack.distribution,
  repositoryName: "dragon-shooter",
  gameName: "dragon-shooter",
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: "ap-northeast-1",
  },
});
gamesPipelineStack.addDependency(staticSiteStack);
```

削除対象(sea-defence):

```ts
const seaDefencePipelineStack = new GamesPipelineStack(app, "SeaDefencePipelineStack", {
  bucket: staticSiteStack.bucket,
  distribution: staticSiteStack.distribution,
  repositoryName: "sea-defence",
  gameName: "sea-defence",
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: "ap-northeast-1",
  },
});
seaDefencePipelineStack.addDependency(staticSiteStack);
```

`puzzleBobblePipelineStack` と `rungamePipelineStack` は残す。`GamesPipelineStack` の import 行も残す(まだ2スタックが使っている)。

- [ ] **Step 4: CLAUDE.md のゲーム表を更新する**

「## labs/games — ゲームホスティング構成」セクションの表は現状 `dragon-shooter` の1行のみで、既に実態と乖離している(実際には4本あった)。移行後に残る2本を正しく反映する。

変更前:

```markdown
| ゲーム名 | CDK スタック |
|---|---|
| dragon-shooter | `DragonShooterPipelineStack` |
```

変更後:

```markdown
| ゲーム名 | CDK スタック |
|---|---|
| puzzlebobble-like | `PuzzlebobbleLikePipelineStack` |
| rungame | `RungamePipelineStack` |
```

- [ ] **Step 5: サイトをビルドして検証する**

```bash
cd /home/akabee/development/hermit-life
npm run build
grep -c 'dragon-shooter\|sea-defence' out/labs/games.html || echo "0件: 期待通り"
```

期待: ビルド成功。`out/labs/games.html` に2つの slug が現れない(`grep -c` が 0 を返し `||` 側が実行される)。hermit-life は `trailingSlash` を設定していないため、一覧ページの出力は `out/labs/games/index.html` ではなく `out/labs/games.html`。

- [ ] **Step 6: CDK の合成が通ることを検証する**

```bash
cd /home/akabee/development/hermit-life/infra
npx cdk list
```

期待: `BlogStaticSiteStack`・`BlogPipelineStack`・`PuzzlebobbleLikePipelineStack`・`RungamePipelineStack` の4つが並び、`DragonShooterPipelineStack` と `SeaDefencePipelineStack` が消えている。

- [ ] **Step 7: コミットする**

```bash
cd /home/akabee/development/hermit-life
git add src/app/labs/games/page.tsx infra/bin/infra.ts CLAUDE.md
git status --short
git commit -m "chore: remove dragon-shooter and sea-defence (migrated to ankardo)"
```

- [ ] **Step 8: main へ反映してデプロイする**

`main` への push が本番デプロイを起動する。ユーザーの承認を得てから実行する。

```bash
cd /home/akabee/development/hermit-life
git checkout main
git merge --ff-only remove-migrated-games
git push origin main
```

- [ ] **Step 9: デプロイ後の状態を確認する**

```bash
curl -sS https://hermit-life.net/labs/games/ | grep -c 'dragon-shooter\|sea-defence' || echo "0件: 期待通り"
```

期待: 一覧ページに2つの slug が現れない。CloudFront のキャッシュが残っている場合は Task 7 の invalidation 後に再確認する。

---

### Task 7: AWS リソースを破棄する

**作業ディレクトリ:** `/home/akabee/development/hermit-life`

**Files:** ファイル変更は `HANDOVER.md`(ankardo 側)のみ。他は AWS リソースの操作。

**Interfaces:**
- Consumes: Task 6 で `infra.ts` から2スタックの定義が消えていること

**このタスクは破壊的操作を含む。全ての AWS 操作はユーザーの明示的な承認を得てから実行すること。** 特に Step 3 の `aws s3 rm --recursive` は hermit-life 本体と**共有のバケット**に対する削除なので、プレフィックスの指定を必ず二重確認する。

- [ ] **Step 1: 削除対象を確認する**

破棄前に、何がどれだけ消えるかを目視する。

```bash
aws cloudformation describe-stacks --stack-name DragonShooterPipelineStack --query 'Stacks[0].StackStatus' --output text
aws cloudformation describe-stacks --stack-name SeaDefencePipelineStack --query 'Stacks[0].StackStatus' --output text
aws s3 ls s3://hermit-life-net-static/labs/games/dragon-shooter/ --recursive --summarize | tail -3
aws s3 ls s3://hermit-life-net-static/labs/games/sea-defence/ --recursive --summarize | tail -3
```

期待: 2スタックが存在し、S3 に各ゲームの静的ファイルが並ぶ。ここで表示されたオブジェクト数が Step 3 で消える数。

- [ ] **Step 2: CDK スタックを破棄する(要承認)**

```bash
cd /home/akabee/development/hermit-life/infra
npx cdk destroy DragonShooterPipelineStack SeaDefencePipelineStack
```

破棄されるのは CodePipeline・CodeBuild プロジェクト・IAM ロール。**S3 バケットは `StaticSiteStack` の所有物なので破棄されない**(`GamesPipelineStack` は `bucket` を props で受け取っているだけ)。

- [ ] **Step 3: S3 上の実体を削除する(要承認)**

`cdk destroy` では消えないため個別に削除する。プレフィックスを間違えると hermit-life 本体のコンテンツを消すことになるので、実行前にコマンド文字列を確認する。

```bash
aws s3 rm s3://hermit-life-net-static/labs/games/dragon-shooter/ --recursive
aws s3 rm s3://hermit-life-net-static/labs/games/sea-defence/ --recursive
```

- [ ] **Step 4: 削除を検証する**

```bash
aws s3 ls s3://hermit-life-net-static/labs/games/ --recursive | grep -c 'dragon-shooter\|sea-defence' || echo "0件: 期待通り"
aws s3 ls s3://hermit-life-net-static/labs/games/ --recursive | grep -c 'puzzlebobble-like\|rungame'
```

期待: 1つ目は0件。2つ目は残す2ゲームのファイル数が正の値で返る(**共有バケットの他のコンテンツを巻き込んでいないことの確認**)。

- [ ] **Step 5: CloudFront のキャッシュを無効化する**

```bash
DIST_ID=$(aws cloudformation describe-stacks --stack-name BlogStaticSiteStack \
  --query "Stacks[0].Outputs[?OutputKey=='DistributionId'].OutputValue" --output text)
echo "$DIST_ID"
aws cloudfront create-invalidation --distribution-id "$DIST_ID" \
  --paths "/labs/games/dragon-shooter/*" "/labs/games/sea-defence/*" "/labs/games/index.html"
```

- [ ] **Step 6: 旧 URL が 404 になったことを確認する**

```bash
curl -sS -o /dev/null -w '%{http_code}\n' https://hermit-life.net/labs/games/dragon-shooter/
curl -sS -o /dev/null -w '%{http_code}\n' https://hermit-life.net/labs/games/sea-defence/
curl -sS -o /dev/null -w '%{http_code}\n' https://hermit-life.net/labs/games/puzzlebobble-like/
```

期待: 前2つは 404 か 403(リダイレクトを作らない決定に沿った想定挙動)。3つ目は 200(残したゲームが壊れていないことの確認)。

- [ ] **Step 7: CodeCommit リポジトリを削除する(要承認)**

**この操作は取り消せない。** ここまでの全ステップが成功し、GitHub 側に全ブランチが揃っていることを確認してから実行する。

```bash
git ls-remote --heads https://github.com/akabee0161/sea-defence.git
git ls-remote --heads https://github.com/akabee0161/dragon-shooter.git
```

期待: sea-defence に3ブランチ(`main`・`feature/fix-minor-things`・`feature/score-caluculate-fix`)、dragon-shooter に `main`。揃っていなければ Task 1 に戻る。

確認できたら削除する:

```bash
aws codecommit delete-repository --repository-name dragon-shooter
aws codecommit delete-repository --repository-name sea-defence
```

- [ ] **Step 8: ローカルの codecommit remote を削除する**

参照先が消えたので remote 設定も片付ける。

```bash
cd /home/akabee/development/sea-defence && git remote remove codecommit && git remote -v
cd /home/akabee/development/dragon-shooter && git remote remove codecommit && git remote -v
```

期待: どちらも `origin` の GitHub URL のみが残る。

- [ ] **Step 9: HANDOVER.md を更新してコミットする**

`/home/akabee/development/ankardo/HANDOVER.md` の `Generated` / `Current State` / `What Was Done` / `What Remains` / `Key Decisions Made` を今回の作業内容に更新する。`Long-term Backlog` セクションは既存の内容を保持する(ユーザー指示により、尋ねられるまで話題に出さない項目)。

`Key Decisions Made` に以下を記録する:

- hermit-life から ankardo への移行は完全移行とし、旧 URL のリダイレクトは作らない(ユーザー判断)
- 移行スコープはホスティングのみ。カタログ表示名は英語表記のまま、ゲーム本体の内容は変更しない
- 先行事例の `rungame-sample` は hermit-life の `rungame` と併存しているが、今回はその形を取らなかった

```bash
cd /home/akabee/development/ankardo
git add HANDOVER.md
git commit -m "docs: update session handover"
```

---

## 完了条件

- `https://ankardo.com/play/sea-defence/` と `https://ankardo.com/play/dragon-shooter/` が 200 を返し、ブラウザでプレイできる
- `https://ankardo.com/games` の一覧に2件が並び、各詳細ページが表示される
- `https://hermit-life.net/labs/games/` の一覧から2件が消え、旧 URL が 404 になる
- `https://hermit-life.net/labs/games/puzzlebobble-like/` が引き続き 200 を返す(共有バケットを巻き込んでいない)
- `npx cdk list` に `DragonShooterPipelineStack` と `SeaDefencePipelineStack` が出ない
- CodeCommit の `dragon-shooter` / `sea-defence` が削除され、GitHub 側に全ブランチが存在する
