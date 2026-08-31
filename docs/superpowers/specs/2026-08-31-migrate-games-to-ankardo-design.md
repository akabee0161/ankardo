# dragon-shooter / sea-defence の ankardo 移行 方針

## 背景

`dragon-shooter` と `sea-defence` は個人サイト hermit-life(`hermit-life.net`)の `/labs/games/<slug>/` 配下でホストされている。ホスティング基盤は AWS(CodeCommit + CDK パイプライン + 共有 S3 バケット + CloudFront)。

この2本を ankardo(`ankardo.com/play/<slug>/`、GitHub + Cloudflare Workers)へ移し、hermit-life 側からは撤去する。

先行事例として `rungame-sample` が ankardo 上に存在するが、これは hermit-life の `rungame` とは別リポジトリとして新規に作られたもので、hermit-life 側にも `rungame` が残る併存状態にある。今回はこの形を取らず、完全移行とする。

## スコープ

**含む:** 配信先の移動(ホスティング移行)。ゲームリポジトリの GitHub 移設、ビルド設定とデプロイ設定の変更、ankardo カタログへの登録、hermit-life 側の撤去。

**含まない:** ゲーム本体のロジック・難易度・UI 文言の変更。カタログ表示名の日本語化(`Dragon Shooter` / `Sea Defence` の英語表記のまま登録する)。旧 URL からのリダイレクト。

## 確定した方針

| 論点 | 決定 |
|---|---|
| hermit-life 側の扱い | 完全移行。一覧エントリ・CDK スタック・S3 実体・CodeCommit リポジトリを削除する |
| 旧 URL のリダイレクト | 行わない。`/labs/games/<slug>/` は 404 になる |
| git 履歴 | CodeCommit の履歴ごと GitHub へ push する(作り直さない) |
| 移行スコープ | ホスティング移行のみ。ゲーム内容とタイトル表記は変更しない |
| 作業順序 | 2本をフェーズ単位で並行して進め、Cloudflare への初回デプロイのみ sea-defence を先行させる |

### 作業順序について検討した案

1. **フェーズ並行・初回デプロイのみ sea-defence 先行**(採用)— 手動承認が必要なステップ(Secrets 設定・production environment 保護ルール・`wrangler deploy`)が3つあり、1本ずつ完結させると承認の往復が倍になる。一方 Wrangler の既知の詰まりどころ(バージョン固定と Static Assets のネスト構造)は実地でしか確認できないため、初回デプロイだけ1本で検証してから2本目に流す。
2. **完全逐次**(見送り)— 安全側だが承認往復が倍になり、hermit-life 側の `infra/bin/infra.ts` 編集と `cdk destroy` も2回に分かれる。
3. **完全並行**(見送り)— 最短だが、初回デプロイが失敗した場合に2本同時の切り分けになる。

## 対象リポジトリの現状

両ゲームとも Vite + TypeScript 構成で、ankardo 実装済みの `character-tactics` と同型。ビルド設定の変更は `base` と `build.outDir` の2箇所で足りる。

| | dragon-shooter | sea-defence |
|---|---|---|
| 構成 | Vite 7 + PixiJS 8 | Vite 5 + HTML5 Canvas(ライブラリなし) |
| 現 `base` | `/labs/games/dragon-shooter/` | `/labs/games/sea-defence/` |
| 現 `build.outDir` | `out` | `out` |
| テスト | なし | なし |
| lint | なし | Biome(`npm run lint`) |
| ローカル作業コピー | `/home/akabee/development/dragon-shooter`(2026-08-31 に CodeCommit から clone) | `/home/akabee/development/sea-defence` |

`dragon-shooter` の `package.json` の `name` は `"shooting-test"` のままだが、Cloudflare Worker 名は `wrangler.toml` の `name` で決まるため配信には影響しない。ホスティング移行のみのスコープにより変更しない。

## 移行後の構成

```text
ankardo.com/games/dragon-shooter   # カタログ詳細 (ankardo/site)
ankardo.com/play/dragon-shooter/*  # ゲーム本体 (akabee0161/dragon-shooter が自己完結デプロイ)
ankardo.com/games/sea-defence
ankardo.com/play/sea-defence/*     # (akabee0161/sea-defence)
```

各ゲームリポジトリは Terraform state や Cloudflare provider 権限を ankardo と共有しない。`ankardo/.claude/skills/new-game/SKILL.md` の手順に従う。

## フェーズ構成

### Phase 1: GitHub へリポジトリを移す

`akabee0161/dragon-shooter`、`akabee0161/sea-defence` を public で作成し、各ローカルリポジトリの `origin` を GitHub へ張り替えて履歴ごと push する。既存の ankardo ゲームリポジトリが全て public であるのに揃える。

CodeCommit リポジトリ自体の削除は Phase 6 まで行わない。Phase 4 のデプロイ確認が通るまでロールバック先を残すため。

### Phase 2: ankardo 仕様への対応

両リポジトリに対し、`character-tactics` を手本に以下を行う。

- `vite.config.ts`: `base` を `/play/<slug>/`、`build.outDir` を `out/play/<slug>` に変更する。Cloudflare Workers Static Assets はパス付きルートに対してビルド出力のディレクトリ構造自体が同じ階層にネストされていることを要求するため、`outDir` のネストは必須。
- `wrangler.toml` を新規作成する(`name = "ankardo-game-<slug>"`、`routes` に `ankardo.com/play/<slug>/*`、`assets.directory = "./out"`、`not_found_handling = "404-page"`)。
- `package.json` の `devDependencies` に `wrangler` の `^4` 系を追加し、`engines.node` を `>=22` にする。`cloudflare/wrangler-action` はリポジトリに Wrangler が無いと古い 3.90.0 を入れ、パス付きルート + Assets のネスト構造をサポートしないため失敗する。
- `.github/workflows/deploy.yml` を作成する(main への push で build → deploy)。actions は SHA ピン留め、`environment: production`、`permissions: contents: read`、`node-version: '22'`。
- `.gitignore` に `.wrangler/` を追加する(両リポジトリとも `out` は既に無視済み)。

#### デプロイ前ゲートの扱い

`character-tactics` の workflow は build 前に `npm test` を挟むが、両ゲームともテストを持たない。

- dragon-shooter: lint も無いため、ビルドのみとする(`npm run build` が `tsc && vite build` で型チェックを兼ねる)。
- sea-defence: 既存の `npm run lint`(Biome)を build 前に入れる。既存スクリプトを使うだけで追加コストがなく、デプロイ前の最低限のゲートになる。

テストの新規作成はホスティング移行のスコープ外とする。

### Phase 3: デプロイ基盤の設定

- `ankardo/scripts/setup-game-secrets.sh` で各ゲームリポジトリに `CLOUDFLARE_API_TOKEN` / `CLOUDFLARE_ACCOUNT_ID` を設定する。
- 各ゲームリポジトリに `production` environment の保護ルール(必須レビュアー、`main` ブランチのみ許可)を設定する。

いずれも Cloudflare 認証情報またはリポジトリ admin 権限を要するため、ユーザーの実行または明示的な承認を得てから行う(下記「手動承認が必要な操作」参照)。

### Phase 4: デプロイと動作確認

sea-defence を先にデプロイし、`ankardo.com/play/sea-defence/` でプレイ可能なことを確認する。通ってから dragon-shooter をデプロイして同様に確認する。

### Phase 5: ankardo カタログへの登録

`site/content/games/dragon-shooter.json` と `site/content/games/sea-defence.json` を作成する。`genre` は `site/lib/genres.ts` の `GENRES` の定義から選ぶ。

| slug | title | genre | 選定理由 |
|---|---|---|---|
| dragon-shooter | Dragon Shooter | `shooting` | ドラゴンを撃ち落とすシューティング |
| sea-defence | Sea Defence | `simulation` | 拠点(卵)を守るタワーディフェンス。同系統の `character-tactics` が `simulation` |

残りの必須フィールドは各ゲームの実装内容から以下の値とする。

| slug | ageRange | players | difficulty | 根拠 |
|---|---|---|---|---|
| dragon-shooter | 8歳〜 | ひとり用 | むずかしめ | 全5ステージ、各ステージにボス、弾を撃つ敵・突進する敵・隊列突撃が登場する(`src/entities/`)。子供向けを前提に作られたゲームではない |
| sea-defence | 5〜8歳 | ひとり用 | やさしめ | README に「幼児向けの海テーマタワーディフェンス」と明記。全5 Wave、操作は長押しとタップのみ |

`dragon-shooter` は ankardo の対象読者(子供)を前提に作られていないため、上記の `ageRange` と `difficulty` は Phase 4 の動作確認で実際にプレイした上で妥当性を確認し、必要なら Phase 5 で調整する。ゲーム本体の難易度調整はスコープ外であり、行うのはカタログ表記の調整のみ。

`site/lib/games.ts` の `getAllGames()` がビルド時に必須フィールドと `genre` を検証するため、`next build` の成功がカタログ側の検証となる。

### Phase 6: hermit-life 側の撤去

Phase 4・5 の確認が完了してから着手する。

1. `src/app/labs/games/page.tsx` の `games` 配列から2エントリを削除する。
2. `infra/bin/infra.ts` から `DragonShooterPipelineStack` と `SeaDefencePipelineStack` の定義を削除する。
3. `cdk destroy DragonShooterPipelineStack SeaDefencePipelineStack` を実行する。
4. S3 上の実体を削除する。`GamesPipelineStack` は hermit-life 本体と**共有の** S3 バケット `hermit-life-net-static` の `labs/games/<slug>/` プレフィックスへ `s3 sync` する作りのため(`infra/lib/games-pipeline-stack.ts`)、スタックを destroy してもオブジェクトは残る。`aws s3 rm s3://hermit-life-net-static/labs/games/<slug>/ --recursive` を2本分実行する。
5. CloudFront invalidation を `/labs/games/dragon-shooter/*` と `/labs/games/sea-defence/*` に対して実行する。
6. hermit-life の `CLAUDE.md` の「labs/games — ゲームホスティング構成」の表を更新する。現状この表には `dragon-shooter` しか記載されておらず既に実態と乖離しているため、移行後に残る `puzzlebobble-like` と `rungame` を正しく反映する。
7. CodeCommit の `dragon-shooter` / `sea-defence` リポジトリを削除する。

## 手動承認が必要な操作

エージェントが無承認で実行してはならない操作を以下に列挙する。

- `scripts/setup-game-secrets.sh` の実行(Cloudflare 認証情報を扱う)
- `production` environment 保護ルールの設定(リポジトリ admin 権限)
- `wrangler deploy`(Cloudflare 上への反映)
- `cdk destroy`(AWS リソースの破棄)
- `aws s3 rm --recursive`(S3 オブジェクトの削除)
- CodeCommit リポジトリの削除

## 検証方法

両ゲームとも自動テストを持たないため、検証は以下による。

- **Phase 2**: ローカルで `npm run build` を実行し、`out/play/<slug>/index.html` が生成されることを確認する。Wrangler の Static Assets ネスト要求を事前に検出できる唯一のローカル検証。
- **Phase 4**: デプロイ後の実 URL でプレイ可能なことを手動確認する。アセットが読めているか(base path の誤りは白画面や 404 として現れる)を含む。
- **Phase 5**: ankardo の `next build` がカタログ JSON の必須フィールドと `genre` を検証する。
- **Phase 6**: hermit-life を再ビルド・デプロイし、`/labs/games` の一覧から2件が消えていることを確認する。

## リスクと緩和

- **初回デプロイの失敗**: Wrangler のバージョンと Assets ネスト構造が既知の失敗要因。Phase 2 のローカルビルド確認と Phase 4 の sea-defence 先行で早期に検出する。
- **移行途中でのロールバック**: Phase 4 の確認が通るまで CodeCommit リポジトリと hermit-life 側の配信を残すため、それまでは旧環境に戻せる。
- **S3 の消し残し**: `cdk destroy` だけでは実体が残り、CloudFront 経由で旧 URL が生き続ける。Phase 6 の手順4を独立したステップとして明示する。
