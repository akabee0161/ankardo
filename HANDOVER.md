# Session Handover

## Generated: 2026-08-17T10:30:00Z

## Current State

- **Branch**: main
- **Last Commit**: `bd8537d` feat(games): add character-tactics to catalog
- **Uncommitted Changes**: なし(作業ディレクトリはクリーン)

## What Was Done

1. `.claude/skills/new-game/SKILL.md` の手順5に従い、`site/content/games/character-tactics.json` を新規作成(`genre: simulation` は `site/lib/genres.ts` の定義済みキーであることを確認済み)
2. `next build` を実行し、`/games/character-tactics` の一覧・詳細ページが正常に生成されることを確認
3. `feat(games): add character-tactics to catalog` としてコミットし、ユーザー指示により(軽微な修正のため)PRを経由せず `main` に直接マージ・push済み

## What Remains

- [ ] ankardo 側 `site/` の再ビルド・デプロイ(ユーザーが手動で実施)
- [ ] カタログ一覧・詳細ページに反映されたことの確認
- [ ] `https://ankardo.com/play/character-tactics/` の実機確認(PC・スマホ横持ち)
- [ ] (character-tactics リポジトリ側) `production` environment 保護ルールの設定 — ankardo側の作業ではないため、対応する場合は character-tactics リポジトリのセッションで行う

## Long-term Backlog(ユーザー指示: 当面対応不要。ユーザーが長期バックログについて尋ねた場合のみ話題に出す)

- リモートbackend導入(Terraform Cloud / S3等でCI・ローカルのstateを共有)。導入時は既存リソースを `terraform import` で新backendに取り込む必要あり。詳細は `infra/README.md`
- Cloudflareダッシュボードの推奨事項: `www.ankardo.com` 用レコード追加、MXレコード(SPF/DKIM/DMARC)設定
- トップページ用ビジュアルアセット(2026-08-16、トップページ再設計の一環で洗い出し。詳細は `docs/superpowers/specs/2026-08-16-top-page-redesign-design.md`)
  - ファビコン(`site/app/icon.png` 等)
  - サイトロゴ/ワードマーク(SVG1点、現状はテキスト表記で代替)
  - ジャンルアイコン(7種、現状は色+ラベルのみで機能)
  - マスコットキャラクター等のイラスト(将来イラスト主導のブランド強化を行う場合に必要)

## Key Decisions Made

- **character-tactics のカタログ登録はPRを経由せず直接 `main` にマージ**: ユーザー判断(軽微な修正のため)。以降も同種の軽微なカタログ追加は同様の運用で問題ないか、都度確認が必要

## Known Issues / Blockers

- Terraform stateがCIとローカルで共有されていない。当面 `allow_overwrite` でしのいでいるが、今後追加するリソースの種類によっては同じ「already exists」エラーが再発する可能性がある(根本対応は長期バックログ)
