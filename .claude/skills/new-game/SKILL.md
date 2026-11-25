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

**`package-lock.json` は、CI と同じ npm で、`node_modules` の無い場所で作る。** CI は `npm ci` を使い、Node 22 の npm 10 で動く。手元の npm が違う版(例: Node 24 の npm 11)でロックファイルを作ると、`npm ci` が止まって本番デプロイが失敗することがある(name-touch で 2 回起きた。wrangler の中の peer 依存(vitest 5・vite 8・rolldown)を、npm 11 は「使われていない」として落とし、npm 10 は必要と見たため)。

- 作り方: 空のフォルダに `package.json` だけを置き、`npx npm@10 install --package-lock-only`。できた `package-lock.json` をゲームに戻す
- `node_modules` がある場所で `--package-lock-only` を使わない。手元に入っているパッケージの `resolved`・`integrity`(取得元と改ざん検出のハッシュ)が書かれなくなる
- 出す前に、`npx npm@10 ci` が通ること、全パッケージに `integrity` があることを確かめる

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

あわせて `site/public/_redirects` に次の1行を足す(末尾スラッシュなしの詳細ページ URL を正規の URL へ 301 で転送するため。足し忘れると `site/lib/redirects.test.ts` が失敗する)。

```txt
/games/<slug> /games/<slug>/ 301
```

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

## 確認用のプレビュー（develop ブランチ）を足す

ゲームのリポジトリでは、機能ブランチ → `develop` への PR をマージすると、`develop` の固定のプレビュー（`https://develop-<Worker 名>.akabee0161.workers.dev/play/<slug>/`。`/` は 404 になる）が自動で上がる。プレビューは Cloudflare Access の受付の後ろにあり、ログインした人だけが開ける。本番（ankardo.com）へは、`develop` から `main` への PR をマージして出す（`deploy.yml` が動く）。

手順（新しいゲームのリポジトリで）:

1. `.claude/skills/new-game/preview.yml`（このリポジトリのひな形。先頭は `# template-version: 1`）を、ゲームの `.github/workflows/preview.yml` にそのまま写す
2. `wrangler.toml` の `routes` の前に `preview_urls = true` を足し、末尾に空の `[previews]` を足す（`wrangler preview` が要求する。足さないと `Your Wrangler configuration is missing a previews block` で失敗する）
3. wrangler を 4.135.0 以上にする（`npm install -D wrangler@^4.135.0`）。Worker Previews は、これより古い wrangler では使えない
4. ゲームの `CLAUDE.md` に、機能ブランチ → `develop` → `main` の流れを書く
5. この PR は `develop` がまだないので `main` に向け、マージしたあと、**`main` の本番の `deploy` が成功するまで待つ**（`production` の承認が要るリポジトリでは、承認する）。`preview_urls = true` は本番の `deploy` で Worker に反映されるので、先に `develop` を push すると、プレビューは成功しても URL が付かない（`"urls": []`。sea-defence で起きた。承認後に `Preview (develop)` を動かし直すと付く）
6. `main` から `develop` を作って push する。ワークフローの成功を見てから、ログインなしで `curl` し、`302` で `cloudflareaccess.com` に転送されることを確かめる

守ること:

- **`wrangler deploy` を書かない。`environment` を使わない。** プレビューのワークフローは `develop` への push で動き、`production` の承認の外で動くので、本番に出す手段を持たせない。Cloudflare のトークンは、最後の `wrangler preview` のステップの `env` にだけ渡す
- ひな形を直すときは、先にこのリポジトリのひな形を直し（`site/lib/preview-template.test.ts` が固定している）、それから各ゲームのリポジトリへ手で写す
- ホスト名の最初の部分（`develop-` + Worker 名）は 63 文字以内にする
- 受付（Cloudflare Access）はアカウント内の全 Worker のプレビューを対象にしている。受付が作られているか分からないうちは、プレビューを有効にしない

## ドット絵を使うなら（pixel-asset-forge）

ドット絵のアセットは pixel-asset-forge（以下 forge）で作る。forge をゲームリポジトリの `pixel-asset-forge/` へ丸ごとコピーし、ゲームの中でエンジンを直しながらアセットを作る。

### コピーする

```bash
./scripts/copy-forge.sh pixel <ゲームリポジトリのパス>
```

forge の main の最新 commit の中身が `<ゲームリポジトリ>/pixel-asset-forge/` に入り、コピー元の commit を書いた `UPSTREAM.md` ができる。`pixel-asset-forge/` が既にあるときは何もせずに止まる。コミットはしないので、ゲーム側で中身を見てから、ゲーム側の変更とは分けて1つのコミットにする。

1 回の実行でコピーするのは 1 つ。ドット絵とイラストの両方を使うゲームは、`pixel` と `illust` で 2 回実行する。使わないほうは実行しない。

### コピーした後にゲーム側で行うこと

1. Python 3.14 の venv を [uv](https://docs.astral.sh/uv/) で作る（3.10 では forge のテストが落ちる）: `uv python install 3.14 && uv venv --python 3.14 pixel-asset-forge/.venv && uv pip install --python pixel-asset-forge/.venv/bin/python -r pixel-asset-forge/requirements.txt`
2. ゲームのルートに対応表 `sprites.json` を書く。forge の `build/` からの相対パスを、書き出し先のファイル名に対応させる: `{ "tile/forest.png": "tile-forest.png" }`
3. 書き出す: `pixel-asset-forge/.venv/bin/python pixel-asset-forge/tools/export.py sprites.json <ゲームが PNG を読むフォルダ>`
4. 書き出した PNG をコミットする。デプロイでは Python を使わない

### forge とゲーム側のコピーの関係

- ゲーム側のコピーは、そのゲームに合わせて自由に直してよい。forge も並行して開発が続く
- ゲーム側でエンジン・規約・道具を直したら、`UPSTREAM.md` の「forge に戻す候補」に1行足す
- ゲームの開発が終わったら、候補を forge の issue にまとめる。取り込むときに、そのまま採用するか、抽象化してから入れるかを1件ずつ決める
- forge の改善をゲーム側へ取り込む仕組みは無い。要るものはその都度手で持ってくる

### 経緯

- 設計: [character-tactics の spec](https://github.com/akabee0161/character-tactics/blob/main/docs/superpowers/specs/2026-09-30-move-pixel-asset-forge-design.md)
- 移設の PR: [character-tactics #22](https://github.com/akabee0161/character-tactics/pull/22)
- リポジトリを分けておく意味の見直し: [ankardo #17](https://github.com/akabee0161/ankardo/issues/17)

## イラストを使うなら（illust-asset-forge）

顔グラなどのイラストは illust-asset-forge（以下 forge）で作る。forge をゲームリポジトリの `illust-asset-forge/` へ丸ごとコピーし、ゲームの中で画風・テンプレート・道具を直しながらキャラクターを作る。GPU を使う処理（生成）は、量産は Claude が Modal の T4 で、1 枚ずつ手で試すときは依頼者が Colab で動かす（forge の README 10）。仕組みは「ドット絵を使うなら」と同じ（コピーして自由に直す）。

### コピーする

```bash
./scripts/copy-forge.sh illust <ゲームリポジトリのパス>
```

forge の main の最新 commit の中身が `<ゲームリポジトリ>/illust-asset-forge/` に入り、コピー元の commit を書いた `UPSTREAM.md` ができる。forge の `HANDOVER.md` と `docs/superpowers/` は入らない（引き継ぎはゲームの `HANDOVER.md` 1 つにする。forge の当時のログはゲームのログではない）。`illust-asset-forge/` が既にあるときは何もせずに止まる。コミットはしないので、ゲーム側で中身を見てから、ゲーム側の変更とは分けて1つのコミットにする。

### コピーした後にゲーム側で行うこと

1. `illust-asset-forge/notebooks/run.ipynb` の準備のセルの 4 つの変数を、ゲームの値に書き換える
   - `REPO_URL`: ゲームのリポジトリの URL
   - `REPO_BRANCH`: `develop`（機能ブランチを `develop` にマージした時点で Colab に届く）
   - `SUBDIR`: `illust-asset-forge`
   - `DRIVE_DIR`: `/content/drive/MyDrive/<ゲームのリポジトリ名>/illust-asset-forge`（forge 本体の置き場と混ざらないように、ゲームごとに分ける）
2. コピーの `tests/test_notebook.py` の既定値のテストを、1 の値に合わせる。`UPSTREAM.md` の「forge に戻す候補」とは別に、ゲームで直したことを 1 行ずつ書く
3. コピーの `tests/test_repo_configs.py` のうち、forge 本体の見本だけを前提にしたテスト（`test_sample_characters_are_the_four_generic_ones`・`test_no_game_ids_or_trial_style_names`）と、禁止語の検査（`test_repo_does_not_mention_the_game`。ゲームのリポジトリ名が `REPO_URL` に入ると落ちる）を、このゲームに合わせて直す
4. コピーの `CLAUDE.md` の「リポジトリにゲーム側の事情…を書かない」を、このゲーム専用であることと、直したら `UPSTREAM.md` に 1 行足すことに書き換える
5. Python の venv を作り、テストを通す: `uv venv illust-asset-forge/.venv && uv pip install --python illust-asset-forge/.venv/bin/python -e 'illust-asset-forge[dev]' && (cd illust-asset-forge && .venv/bin/pytest)`
6. 量産は Modal の道（forge の README 10）で作る。Modal には手元のコードをそのまま送るので、push せずに試せる。Modal を使うなら `illust-asset-forge/src/artgen/modal_app.py` の `APP_NAME` をゲームの名前に書き換える（`VOLUME_NAME` は forge 本体と同じままにすると、モデル約 7GB を取り直さずに済む。理由は `UPSTREAM.md` に書く）。生成の前に、枚数と見込みの金額を依頼者に伝える。1 枚ずつ手で試すときは依頼者が Colab で動かす。Colab は `develop` を取るので、設定の変更は `develop` にマージするまで Colab に届かない

### forge とゲーム側のコピーの関係

「ドット絵を使うなら」の「forge とゲーム側のコピーの関係」と同じ。ゲーム側で直したら `UPSTREAM.md` の「forge に戻す候補」に1行足し、forge の改善は要るものだけ手で持ってくる。

### 経緯

- 設計: [character-tactics の spec](https://github.com/akabee0161/character-tactics/blob/fc34a512e9fdcdeccea1bd78679f3f9cbe62676e/docs/superpowers/specs/2026-11-22-face-gen-ai-design.md)（commit 固定。マージの前後で同じ資料が開ける）

## 共通素材を使うなら（知育ゲーム: shared-assets）

幼児向けの知育ゲームは、絵・名前の声・鳴き声を ankardo の `shared-assets/chiiku/` から取る。素材の中身と作り方は README の「共通素材」。ここは、新しいゲームがそれを使うときの手順。

### コピーする

```bash
./scripts/copy-assets.sh chiiku <ゲームリポジトリのパス>            # 鳴き声を使うゲーム
./scripts/copy-assets.sh chiiku <ゲームリポジトリのパス> --no-cry   # 鳴き声を使わないゲーム
```

鳴き声を鳴らさないゲームには `--no-cry` を付ける。付けないと、CC BY-SA の録音（`cry/dog.wav`・`cry/pig.wav`）がそのゲームの公開物に入り、使わないのにクレジットの義務だけを負う。

`<ゲーム>/public/chiiku/` に、`items.json`・`img/<id>.webp`・`voice/<id>.wav`・`voice/manifest.json`・`cry/<id>.wav`（どうぶつ 6 つ。`--no-cry` では入らない）・`CREDITS.md` が入る。`public/chiiku/` が既にあるときは、丸ごと置き換える（コピー元から消えたファイルも消える）。コピー元の commit（未コミットの変更があれば `+dirty`）とコピーした日は `<ゲーム>/chiiku-assets.md` に書かれる。コミットはしないので、ゲーム側で中身を見てから、ゲーム側の変更とは分けて 1 つのコミットにする。

### ゲーム側で守ること

1. `public/chiiku/` を手で直さない。素材を直すときは ankardo の `shared-assets/chiiku/` を直し、コピーし直す
2. `items.json` の形（`categories` と `items`。種類のキーは `animal`・`insect`・`sea`・`vegetable`・`food`、ID は 21 種類の英語名）を `loadItems` で読み、形が違えば、どの項目が違うかを示して止める。ゲーム側に 21 種類の一覧を書き写さない
3. 字を読めない子ども向けなので、名前は声（`voice/<id>.wav`）で出し、画面の字は 8・9 のゲーム（もじとえ・もじなぞり）だけ。字を出すときは `kana`（ひらがな）を使い、`label` は使わない
4. クレジットは `public/chiiku/CREDITS.md` の「ゲームの画面に出すクレジット」を、タイトル画面の下に小さく出す。鳴き声（`cry/`）を使うゲームだけ、鳴き声の行も出す
5. 音は最初のタッチの「はじめる」の中で `AudioContext.resume()` を呼び、無音の再生をしてから鳴らす（ブラウザは画面に触れるまで音を出せないため）
6. 声と鳴き声は wav。古い iOS でも鳴る

### 素材を足す・直す

- 絵: forge（`illust-asset-forge/`）で作り、`shared-assets/tools/build_images.py` で webp にする。Modal で作る前に、枚数と見込みの金額を依頼者に伝える。背景の消し方で詰まったときは `illust-asset-forge/UPSTREAM.md` の「分かったこと」
- 声: VOICEVOX Engine を起動し、`shared-assets/tools/voice.py --speaker 3`。text・話者・Engine の版が同じ声は作り直さない。決まり文句（「〇〇は どれ？」など）は、そのゲームを作るときに足す。試聴では「ぞうさんは どれ？」がどの話者でも不自然だったので、アクセントを直してから作る
- 鳴き声: 再配布が許される録音だけを使う（効果音ラボは再配布禁止で使えない）。出典・条件を `CREDITS.md` に書く。元の録音が市販ライブラリの転載でないか、Commons のページで確かめる
- どれを直しても、`illust-asset-forge/.venv/bin/pytest shared-assets/tools/tests` と `bash scripts/copy-assets.test.sh` を通す

### 経緯

- 設計: `docs/superpowers/specs/2026-11-24-chiiku-games-design.md`（ログ。決まったこと・決めた人の印）
