# __TITLE__

2 歳向けの知育ゲーム。字が読めなくても遊べる。

公開先: https://ankardo.com/play/chiiku-template-slug/

## 作り方

- Vite + TypeScript + Vitest + Biome。`base` は `/play/chiiku-template-slug/`、ビルドの出力は `out/play/chiiku-template-slug/`
- `src/common/`: 知育ゲームで共通の部分（素材の一覧・音・長押し・タイトル画面・「？」・⏏・はねる動き）。ankardo の `templates/chiiku-game/` の写し（写した元は `template.md`）
- `src/game/`: このゲームの遊び
- `public/chiiku/`: 共通素材（絵・声・一覧・クレジット）。ankardo の `shared-assets/chiiku/` のコピーで、手で直さない。コピーし直すには ankardo のフォルダで `./scripts/copy-assets.sh chiiku <このリポジトリのパス> [--no-cry]`（鳴き声 `cry/` を使わないゲームは `--no-cry`）。コピー元は `chiiku-assets.md`

```sh
npx npm@10 ci   # ロックファイルは CI と同じ npm 10 で作る。`npm install` は使わない（手元の npm が違うとロックが壊れ、deploy が止まる。依存を足すときは CLAUDE.md の手順）
npm run dev     # 開発サーバ（素材を入れてから）
npm test        # Vitest
npm run lint    # Biome
npm run build   # tsc → vite build（out/ に出る）
```

## クレジット

- 声: VOICEVOX:ずんだもん（タイトル画面の下に出す）
- 素材の出典と条件は `public/chiiku/CREDITS.md`
