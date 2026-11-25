# illust-asset-forge 作業規約（Claude 向け）

人間向けの手引きは [`README.md`](README.md)。ここには Claude が守ることだけを書く。

## 役割の分担

- 量産（たくさんの候補）は、**Claude が Modal の T4 で作る**（`python -m artgen.cloud generate --jobs FILE`）。GPU は T4 だけ。同じシードでも GPU の種類が違うと絵が変わるので、T4 が空いていなければ別の GPU に替えず、待つかやり直す（条件の `gpu` が `Tesla T4` でない絵は返らない）。このサーバーには GPU が無く、Modal のコードは偽のパイプラインを使ったテストの外（実際に動かす）でしか確かめられない。Modal を動かす前に、依頼者に生成すること（枚数と利用額の見込み）をひと言伝える
- 画風の調整のように、依頼者が自分の手でタグを変えながら 1 枚ずつ試すときは、**依頼者が Colab で動かす**（`notebooks/run.ipynb`。壊さない）。ノートブックの画面（`picker`）は、偽のウィジェットでしか確かめていない。Colab は GitHub からリポジトリを取るので、設定の変更は push するまで Colab に届かない。**push は依頼者が頼んだときだけ**行う
- Modal の道は、手元のコードと設定をそのまま送るので、push せずに試せる。ジョブに画風（`style`）は付けない

## 受け取った画像の扱い

- 候補（生成された画像）はリポジトリに入れない。入れるのは `characters/<id>/source/` の採用した画像と、書き出した画像・`params.json` だけ（例外は背景のマスク `characters/<id>/matte/`。書き出しを Modal 無しで再現するために入れる）
- 採用した絵は、依頼者がノートブックのまとめのセルで作った zip で届く。**`python -m artgen.intake <zip>` で `source/` に取り込む**（`face.png`・`face_<表情>.png`・`fullbody.png` の名前、PNG に条件があること、キャラクターの一致を検査し、通らなければ何も書かずに止まる）。条件が無いときは添付で消えた可能性があるので、依頼者に知らせて止める
- 採用した絵は、zip の代わりに Google Drive のコネクター（`download_file_content`）で `DRIVE_DIR` の `selected/<id>/` から取ってもよい。取った絵を `selected/<id>/` の形（`<id>/face.png` など）に置き、`install_selection` で取り込む。1 枚ごとに絵が会話に入るので、取るのは採用した絵だけにする。表情の範囲の `selection.json`（`selected/<id>/` にある）は画像ではないので、あれば一緒に取る（無いと範囲を書き戻せない）
- Modal の道で作った候補は、このサーバーの `local/`（`.gitignore` 済み）にある。候補のページ（`local/rounds/<run_id>.html`）は Artifact で依頼者に見せる。ページには全部を並べ、Claude が機械的に外したり、目で見て選り分けたりしない（依頼者が全部を目で見て選ぶ）。依頼者が番号で答えたら、`python -m artgen.cloud adopt local/rounds/<run_id>.json <番号> [--flip]` で採用し（`--flip` は顔だけ）、`python -m artgen.cloud install <id>` で `characters/<id>/source/` に取り込む（頼んだキャラクターだけ。ほかの採用は触らない）。`install` は前回の `install` の後に採用し直した絵だけを入れ、ほかは今の `source/` から持ち越す（顔を採用し直したときの表情は持ち越さない）。出力の「消した」は、zip の道と同じく確かめる。取り込みの後の書き戻し・書き出しは、zip の道と同じ
- `intake` は `source/` を丸ごと置き換える。出力の「消した」に意図しないもの（特に `face.png`）があるときはコミットせず、依頼者に確かめる
- `intake` の出力にある書き戻しの一覧を、`character.yaml` などの設定に戻してからコミットする（以後は上書きなしで同じプロンプトになるように）。条件の `overrides` の `style` は `character.yaml` の `style` に戻す（そのキャラクターだけの上書きになる）。ただし、その画風が `defaults.yaml` の `style` と同じなら、`style` を書かず、`character.yaml` に `style` があれば消す（デフォルトに戻す）
- 画風はデフォルト（`defaults.yaml` の `style`）を全キャラクターで使う。新しいキャラクターの `character.yaml` には `style` を書かない
- 書き戻しの一覧に `overrides.style_definition`（その場で書いた画風の定義）があるときは、その `prompt`・`negative` で `styles/<style>.yaml` を作る。依頼者がその画風を全員に使いたいときは `defaults.yaml` の `style` をそれにし、`style` を書いているキャラクターがいればその行を消す。1 人だけに使いたいときはその `character.yaml` の `style` をそれにする
- 表情の範囲（`inpaint_box`）は、依頼者がノートブックで決め、`selection.json` で届く。Claude は `intake` の一覧を見て `character.yaml` に書き戻す。顔の自動検出は入れず、Claude が顔を見て範囲を決めることもしない（これは表情の範囲の決まりで、切り出しの範囲には当てはまらない。下の「切り出しと背景消し」）
- 書き出しは `python -m artgen.export <id>`

## 切り出しと背景消し

- 切り出しの範囲（`character.yaml` の `cutouts` の `box`）は、依頼者が用途と切り出す所を指示し、Claude が元の絵を見て座標に直して書く。Claude の判断だけで決めた値にせず、`python -m artgen.cutout_review <id> ...` の承認用ページを Artifact で依頼者に見せて承認を受ける。承認を受けるまで、決まった範囲として扱わない
- 背景のマスクは `python -m artgen.cloud matte <id>` で Modal の CPU に作らせる。**背景除去のモデルや onnxruntime・numpy を、このサーバーで動かさず、`.venv` にも `pyproject.toml` の依存にも入れない**（メモリ 1.9GB で推論するとスワップで応答しなくなった）。これらは `matte.py` の `isnet_mask` と `modal_app.py` の `matte_remote` の中でだけ import する
- マスク（`characters/<id>/matte/`）はリポジトリに入れる（書き出しを Modal 無しで再現するため）。元の絵を差し替えたら `cloud matte` を作り直す（書き出しが古いマスクで止まる）
- 書き出しで `local/check/<id>/` に置く確認図（透明にした画素を赤で塗った絵）を、依頼者に見せる前に自分でも見る。背景の飾りが体の一部として残る・体が欠けるときは、`erase` で消すか範囲を直す
- 範囲や `erase` を直したら、`export` をやり直してから承認用ページを作る（書き出しが古いとページは作られない）
- 候補のページ（`cloud generate`・`page`・`merge`）は、既定で候補の背景を Modal で消して隣に並べる。Modal を動かす前に、枚数と利用額の見込みを依頼者に伝える

## 守ること

- リポジトリにゲーム側の事情（ファイル名・画面の大きさの定数・JSON の形）や、ゲームのリポジトリの名前を書かない。キャラクターの ID はただの名前
- modal は `modal_app.py` の中でだけ import する（`cloud.py` は使う関数の中で `modal_app` を import する）。diffusers・torch は `forge.load_pipeline()`・`forge.attach()` の中でだけ import する。`ipywidgets`・`IPython` も関数の中でだけ import する。ほかのモジュールとテストはそれらが無くても動くままにする
- 取り込みの関数（`install_selection`）は、将来 Colab から直接コミットするときに使うので、zip・標準出力に依らないままにする（zip の展開は `extract_pack`、表示は `main` が受け持つ）
- 設定の誤りは `ConfigError` で、`<相対パス>: <キーの位置>: <何がおかしいか>` の形で止める
- コミットは Conventional Commits + 日本語の要約

## テスト

```sh
uv venv .venv && uv pip install -e '.[dev]' && .venv/bin/pytest
```

## ドキュメントの扱い

- `docs/superpowers/` 配下（設計書・計画）は作成時点のログ。後から実装が変わっても遡って更新しない
- 最新の状態の正典は `README.md` と `CLAUDE.md`。両者が食い違うときは正典が正しい
