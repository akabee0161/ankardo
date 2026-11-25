# UPSTREAM

このフォルダは illust-asset-forge のコピーで、このゲーム専用に自由に直してよい。

- コピー元: https://github.com/akabee0161/illust-asset-forge.git
- commit: 089c1ff2701dcac33d739c455e75257e4a0bdc84
- コピーした日: 2026-11-25

forge 本体も並行して開発が続く。forge の改善をこちらへ取り込む仕組みは無く、要るものはその都度手で持ってくる。

## このゲームだけの変更

- `src/artgen/modal_app.py` の `APP_NAME` を `ankardo-chiiku` にした。forge 本体の Modal アプリと名前がぶつからず、一覧やデプロイで見分けられるため
- `VOLUME_NAME` は `illust-asset-forge-models` のままにした。モデルと版が forge 本体と同じなので、同じ Volume を使えば約 7GB を取り直さずに済むため。入っているのはモデルのキャッシュだけで、生成物は入らない

## forge に戻す候補

ここでエンジン・規約・道具を直したら、何を・なぜ直したかを1行足す。

## ゲームの開発が終わったら

上の候補と、このフォルダを足したコミットからの差分を材料に、forge の issue を出す。
差分は `git diff $(git log --format=%H --diff-filter=A -1 -- illust-asset-forge/UPSTREAM.md) -- illust-asset-forge/` で見られる。
取り込むときに、そのまま採用するか、抽象化してから入れるかを1件ずつ決める。
