# __TITLE__ Handover

## 進捗
作業: 幼児向け知育ゲーム
工程:
1. 共通素材を作る（forge のコピー・21 種類の絵・声・鳴き声・copy-assets.sh）（完了）
2. なまえタッチを作って公開する（完了）
3. ひな形を作り、残りの 8 本を作って公開する ← 今ここ
段階: 実装計画
次にやること:
- このゲームの小さな計画を書く（遊びの細部・決まり文句・ひな形に足す共通部分）。ankardo の HANDOVER.md の「進捗」と、docs/superpowers/plans/2026-11-26-chiiku-games-step3-template.md の「1 本ごとの流れ」を見る

## 今の状態

- ankardo の `templates/chiiku-game/` から写した直後。遊びはまだ無い（`src/game/game.ts` は ⏏ と ？ だけの画面）
- 素材（`public/chiiku/`）は、ankardo の `scripts/copy-assets.sh chiiku . [--no-cry]` で入れる
