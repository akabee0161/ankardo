# Ankardo

子供向けインディーゲームカタログサイト。ドメイン `ankardo.com` を Cloudflare(Terraform + Wrangler)上に公開する。

設計の背景・経緯は `docs/superpowers/specs/2026-08-12-ankardo-infra-design.md` 参照(このドキュメント運用ルールについては下記「ドキュメント運用ルール」を参照)。

## 構成

モノレポ構成。

```text
ankardo/
├── infra/     # Terraform (Cloudflareゾーン・DNS・SSL設定)
├── site/      # Next.js カタログサイト(静的書き出し、トップ・一覧・個別詳細・このサイトについて)
├── illust-asset-forge/  # forge(イラスト生成)のコピー。知育ゲームの共通の絵をここで作る
├── shared-assets/       # 書き出した共通素材(chiiku/: 絵・名前の声・鳴き声・クレジット)と、その道具(tools/)
├── scripts/
│   ├── copy-forge.sh    # forge をゲームリポジトリへコピーする
│   ├── copy-assets.sh   # shared-assets の素材をゲームリポジトリへコピーする
│   └── setup-game-secrets.sh
└── .github/workflows/
    ├── infra.yml  # infra/ 変更時の terraform plan/apply
    └── site.yml   # site/ 変更時の next build → wrangler deploy
```

ゲーム本体はゲームごとに別リポジトリとして作成し、`ankardo.com/play/<slug>/*` に独立デプロイする(このリポジトリの対象外)。ただし、複数のゲームで使う素材は、このリポジトリが作って各ゲームへ配る(下記「共通素材」)。

### 共通素材

幼児向けの知育ゲーム(2〜4 歳向けに何本か作る)が使う素材を、このリポジトリで作って各ゲームへ配る。素材は `shared-assets/chiiku/` にある。

| 場所 | 中身 | 作り方 |
|---|---|---|
| `items.json` | 21 種類(どうぶつ 6・むし 3・みずのいきもの 3・やさい 4・たべもの 5)の ID・種類・名前・ひらがな・読み上げの文 | 手で書く。ID は `illust-asset-forge/characters/<id>/` と同じ |
| `img/<id>.webp` | 絵(背景透明、512×512) | `illust-asset-forge` で生成・書き出し(`characters/<id>/object.png`)したものを `shared-assets/tools/build_images.py` で webp にする |
| `voice/<id>.wav`・`voice/manifest.json` | 名前の声(VOICEVOX:ずんだもん) | `shared-assets/tools/voice.py --speaker 3`(VOICEVOX Engine を `~/opt/voicevox_engine/run --host 127.0.0.1` で起動しておく) |
| `cry/<id>.wav` | 鳴き声(どうぶつ 6 つだけ) | Wikimedia Commons・Freesound の再配布可の録音を切り出したもの。出典と条件は `CREDITS.md` |
| `CREDITS.md` | 出典・条件・ゲームの画面に出すクレジットの文 | 手で書く。素材を替えたら直す(`shared-assets/tools/tests/test_credits.py` が、全部の鳴き声と声の話者が載っているかを確かめる) |

ゲームへは `scripts/copy-assets.sh chiiku <ゲームリポジトリのパス>` で配る。`<ゲーム>/public/chiiku/` を丸ごと置き換え、コピー元の commit を `<ゲーム>/chiiku-assets.md` に書く(コミットはしない)。ゲームは自分のリポジトリにコピーされた素材だけを読むので、ここで素材を直しても、コピーし直すまで公開中のゲームは変わらない。素材は `ankardo.com` から配らない(名前の変更・削除で、何も変えていないゲームの絵が出なくなるため)。

- 絵の生成は Modal の T4 で行う(`illust-asset-forge/README.md` の 10)。Modal アプリの名前は `ankardo-chiiku`、モデルの Volume は forge 本体と同じ `illust-asset-forge-models`。生成の前に、枚数と見込みの金額を依頼者に伝える
- `illust-asset-forge/UPSTREAM.md` に、forge のコピーで直したことと、ものの絵を作って分かったこと(背景の消し方など)を書いている
- テスト: `illust-asset-forge/.venv/bin/pytest shared-assets/tools/tests`(素材の道具)、`bash scripts/copy-assets.test.sh`(コピーの道具)
- `shared-assets/` と `illust-asset-forge/` を直しても、カタログサイトのデプロイ(`site.yml`)は動かない(`site/**` の変更でだけ動く)

### ゲームリポジトリの命名規則

`<slug>` にはゲームリポジトリの名前をそのまま使う(例: リポジトリ `rungame-sample` → `ankardo.com/play/rungame-sample/*`、`site/content/games/rungame-sample.json`)。プレフィックス(`ankardo-game-`等)は付けない。新しいゲームリポジトリを立ち上げる手順は `.claude/skills/new-game/SKILL.md` 参照。

### ルーティング

| パス | 所有者 | 内容 |
|---|---|---|
| `ankardo.com/` | カタログ(`site/`) | トップページ |
| `ankardo.com/games` | カタログ(`site/`) | ゲーム一覧ページ |
| `ankardo.com/about` | カタログ(`site/`) | このサイトについて(目的・安全性の方針・運営者と連絡先) |
| `ankardo.com/games/<slug>` | カタログ(`site/`) | 個別ゲームのランディング/詳細ページ |
| `ankardo.com/sitemap.xml` / `ankardo.com/robots.txt` | カタログ(`site/`) | 検索エンジン向け(`site/app/sitemap.ts` / `site/app/robots.ts`) |
| `ankardo.com/play/<slug>/*` | 各ゲームリポジトリ | プレイ可能なゲーム本体(独立デプロイ) |

## 開発

### site/ (Next.js カタログサイト)

```bash
cd site
npm install
npm run dev    # 開発サーバ
npm test       # Vitest でバリデーション・MobileNav・sitemap/robots のテストを実行
npm run build  # 静的書き出し (out/)
```

`MobileNav` のテストだけはファイル冒頭の docblock で `jsdom` 環境を指定している。他のテストは `node` 環境で動く。

ゲームを追加する場合は `site/content/games/<slug>.json` を追加すると一覧・詳細ページに反映される。`slug`/`title`/`description`/`playUrl`/`genre`/`devices`/`ageRange`/`players`/`difficulty` が必須。`genre` は `site/lib/genres.ts` の `GENRES` に、`devices` は `site/lib/devices.ts` の `DEVICES` に定義されたキーである必要がある(`site/lib/games.ts` の `getAllGames()` がビルド時に検証し、不正な場合はエラーになる)。ゲームを追加すると `sitemap.xml` にも自動で載る(カタログ内のページのみ。`/play/<slug>/*` は含めない)。絶対URLの基準は `site/lib/site.ts` の `SITE_URL`。スクリーンショットは `site/public/screenshots/<slug>/` に16:9で置く。あわせて `site/public/_redirects` に `/games/<slug> /games/<slug>/ 301` を1行足す(末尾スラッシュなしの URL を正規の URL へ恒久転送するため。足し忘れると `site/lib/redirects.test.ts` が失敗し、デプロイが止まる)。`/games/:slug` のようなプレースホルダは `/games/` 配下の `.txt` まで転送してしまうので使わない。フィールドとアセットの詳細は `.claude/skills/new-game/SKILL.md` 参照。ゲームリポジトリ側の初期設定も同ファイル参照。

#### ブランドアセット

- シンボルは `site/components/CatfishMark.tsx`（ナマズの正面顔、SVG 1点）。色は `currentColor` で、呼び出し側が決める
- ブランド色は藍 `#1f3a5f`。`site/app/globals.css` の `@theme` に `--color-brand` として定義し、`text-brand` / `bg-brand` で使う。既存ボタンの `bg-neutral-900` は据え置き
- ファビコンは `site/app/icon.svg`(白地の角丸四角＋藍のナマズ)。Next.js のファイル規約で `<link rel="icon">` が自動生成される
- ヘッダー/フッターのリンクは `site/lib/nav.ts` に集約する。リンクを増やすときはこのファイルだけを変更する
- Webフォントは読み込まない(表示速度優先の既存方針)

### infra/ (Terraform)

Cloudflareゾーン・DNS・SSL設定を管理する。ローカルでの `terraform apply` はユーザーの明示的な承認を得てから実行する(エージェントが無承認で実行してはならない)。既知の制約(Terraform stateがCIとローカルで共有されていない件)は `infra/README.md` 参照。

Google Search Console はドメイン プロパティ(`ankardo.com`)で登録しており、所有権確認用の TXT レコードは Cloudflare 上に置いたまま Terraform の管理外にしている(理由は `infra/README.md` の「Terraform の管理外のレコード」)。レコードを消すと所有権が失効するため削除しない。Google Analytics などのページ内解析は入れていない(about ページの「Cookie は使わない」という記述と両立させるため)。

## デプロイ

- `infra/**` を変更してmainにpush → `Infra (Terraform)` ワークフローが `terraform apply` を実行(production environmentの承認が必要)
- `site/**` を変更してmainにpush → `Site (Next.js)` ワークフローが `next build` → `wrangler deploy` を実行(承認なしで自動デプロイされる。environment は使わず、Cloudflare の認証情報はリポジトリの secret `CLOUDFLARE_API_TOKEN` / `CLOUDFLARE_ACCOUNT_ID` から読む)
- `wrangler deploy` で使う wrangler のバージョンは `.github/workflows/site.yml` の `wranglerVersion` で固定している。3.113.0 より古い wrangler では `site/public/_redirects` が転送ルールとして読まれず、ただのファイルとして公開される(2026-10 に `/games` の 301 が効かず 307 になっていた原因)。バージョンを外したり下げたりしないこと

- ゲームのリポジトリは、`develop` ブランチへのマージで確認用のプレビュー（Cloudflare Access の受付の後ろ）が自動で上がり、本番へは `develop` から `main` への PR で出す。ひな形は `.claude/skills/new-game/preview.yml`（`site/lib/preview-template.test.ts` で固定）、手順は `.claude/skills/new-game/SKILL.md` 参照

## ドキュメント運用ルール

- **`docs/superpowers/` 配下(specs / plans)は作成時点のログ。** ファイル名の日付時点での記録として扱い、後から実装や運用が変わっても遡って更新しない。「未実施」「TODO」等の当時の記述が現状と食い違っていても、それはバグではなく履歴。
- **最新の状態を表す正典はこの `README.md`(および各ディレクトリの `README.md`、例: `infra/README.md`)。** 実装・手順・制約・前提が変わったら、更新するのはこちら。
- **`HANDOVER.md` はセッション間の作業引き継ぎ用ワーキングメモ。** 直前セッションでの作業内容・残タスクを記録する目的で、セッションごとに上書きされる。恒久的な正典ではない。
- 使い分け: 「なぜこの設計にしたか」を知りたいときはログ(`docs/`)を読む。「今どう動くか・どう操作するか」を知りたいときは正典(README群)を読む。**両者が食い違う場合は常に正典が正しい。**
