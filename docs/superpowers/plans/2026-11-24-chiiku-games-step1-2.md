# 幼児向け知育ゲーム 工程 1・2 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ankardo に共通素材（20 種類の絵・名前の声・鳴き声）を作って配る仕組みを入れ、1 本目の「なまえタッチ」を `ankardo.com/play/name-touch/` に公開する。

**Architecture:** ankardo に illust-asset-forge をコピーし、ものを 1 つ描くテンプレート `object` と背景の透明化を足して Modal で 20 枚を作る。書き出した絵・VOICEVOX の声・鳴き声を `ankardo/shared-assets/chiiku/` にまとめ、`scripts/copy-assets.sh` でゲームの `public/chiiku/` にコピーする。なまえタッチは Vite + TypeScript の新しいリポジトリで、あとでひな形に切り出す共通部分を `src/common/` に分けて作る。

**Tech Stack:** Python 3.14（forge・素材の道具、pytest）、Modal（T4）、VOICEVOX Engine 0.26.1（`~/opt/voicevox_engine`）、Vite・TypeScript・Vitest・Biome（ゲーム）、Wrangler 4、bash（コピーの道具）。

**Spec:** `docs/superpowers/specs/2026-11-24-chiiku-games-design.md`

## Global Constraints

- 20 種類と種類分けは設計書 3.1 のとおり（動物 6・虫 3・魚 3・野菜 4・その他の食べ物 4）
- 素材の ID と種類のキーはこの計画で決める（Task 3・5 の表）。以後すべての道具・ゲームがこの ID を使う
- ゲームは字が読めない前提。指示は声、ボタンは絵だけ（設計書 4 章）
- 時間制限・ゲームオーバー・点数なし。記録はサーバーにも端末にも残さない（`localStorage` も使わない）
- 最初に大きな「はじめる」ボタン。ゲームを終えるボタンは長押し **1.5 秒**（この計画で決めた値）で、タイトル画面に戻る
- 端末は横向きを主にし PC でも遊べる。カタログの `devices` は `["pc", "mobile-landscape"]`
- 9 本のリポジトリ名は設計書 2 章の表。1 本目は `name-touch`
- クレジット（`VOICEVOX:<話者名>`、鳴き声のサイトで要るもの）を各ゲームのタイトル画面の下に小さく出す
- forge のコピーで直したことは `illust-asset-forge/UPSTREAM.md` の「forge に戻す候補」に 1 行足す
- 依頼者に見せる絵・音は Artifact のページで見せ、承認を受けてから次へ進む（承認前にコミットしない）
- Modal で生成する前に、枚数と見込みの金額（1 枚約 20 秒、12 枚で 10 円前後）を依頼者に伝える
- 進捗は `HANDOVER.md` の `## 進捗` に書き、push の前に今の状態に直す

## Review Focus

1. 背景の透明化が、白い部分を含むもの（ぶたの鼻の白い光、おにぎりのご飯、にわとりの白い体）を内側まで透明にしてしまう → 外につながる背景だけを消し、線で囲まれた白は残す（Task 2 のテスト `test_cutout_keeps_white_enclosed_by_outline`）
2. 「はじめる」の前の音・iOS Safari の音の解禁 → 最初のタッチの中で `AudioContext.resume()` と無音の再生をしてから声を鳴らす（Task 9 のテスト `unlock is called inside the start tap`）
3. 子どもの連打・同時タッチ → 同じ絵を続けて叩いたら前の声を止めて最初から鳴らす。別の絵を叩いたら前の声を止める（Task 10 のテスト `tapping again restarts the voice`）
4. 長押しの途中で指が外れた・短いタップ → 終えない（Task 9 のテスト `short tap does not exit`、`pointerleave cancels`）
5. 素材のコピーし直しで古いファイルが残る → コピー先の `public/chiiku/` を丸ごと置き換える（Task 8 のテスト `removed files disappear on recopy`）

---

## 依頼者の手作業（最初に全部並べる）

| 順 | いつ | 作業 |
|---|---|---|
| 1 | Task 4 | 画風の試しの候補を見て、続けるか画風を替えるかを決める |
| 2 | Task 4 | 20 種類の候補のページを見て番号で採用を答え、書き出した 20 枚を承認する |
| 3 | Task 6 | 話者の試聴ページを聞いて、話者を 1 人選ぶ |
| 4 | Task 7 | 鳴き声 6 つの試聴ページを聞いて承認する |
| 5 | Task 8 の後 | ankardo の PR（forge のコピー・共通素材・道具）をマージする |
| 6 | Task 9 の前 | GitHub に `akabee0161/name-touch`（公開）を作る。Claude が `gh repo create` で作ってよいかは、そのとき聞く |
| 7 | Task 9 の前 | `ankardo/scripts/setup-game-secrets.sh akabee0161/name-touch` を Cloudflare の値を入れて実行する |
| 8 | Task 9 の前 | name-touch に `production` environment の保護ルール（必須レビュアー・main のみ）を設定する |
| 9 | Task 11 | name-touch の PR（機能ブランチ → develop、develop → main）のマージと本番デプロイの承認 |
| 10 | Task 11 | ankardo の PR（カタログへの登録）のマージ |

---

### Task 1: ankardo に forge をコピーする

**Files:**
- Create: `illust-asset-forge/`（`scripts/copy-forge.sh illust .` で作る）
- Modify: `illust-asset-forge/src/artgen/modal_app.py`（`APP_NAME`）
- Modify: `illust-asset-forge/UPSTREAM.md`（このゲームだけの変更）

**Interfaces:**
- Produces: `illust-asset-forge/.venv/bin/python`（forge と素材の道具を動かす venv。Pillow・pytest 入り）

- [ ] **Step 1:** ankardo の main から `feat/chiiku-shared-assets` を切る（設計書のブランチ `docs/chiiku-games-design` がマージ前なら、その上に切る）
- [ ] **Step 2:** `./scripts/copy-forge.sh illust .` を実行する。`illust-asset-forge/UPSTREAM.md` ができる
- [ ] **Step 3:** `APP_NAME = "ankardo-chiiku"` にする。`VOLUME_NAME` は `illust-asset-forge-models` のまま（forge 本体と同じモデル・同じ版なので、約 7GB を取り直さないため）。この 2 つの判断と理由を UPSTREAM.md の「このゲームだけの変更」に書く
- [ ] **Step 4:** `cd illust-asset-forge && uv python install 3.14 && uv venv --python 3.14 .venv && uv pip install --python .venv/bin/python -e '.[dev,modal]'`
- [ ] **Step 5:** `.venv/bin/pytest -q` — Expected: 全部 PASS（禁止語は `character-tactics`・`FACE_PX` だけなので ankardo では落ちない）
- [ ] **Step 6:** `.venv/` と `local/` が ankardo の git に入らないことを `git status --short` で確かめる（forge の `.gitignore` が効かなければ ankardo の `.gitignore` に足す）
- [ ] **Step 7:** コミット `chore: illust-asset-forge を共通素材用に ankardo へコピーする`

### Task 2: ものを 1 つ描くテンプレートと背景の透明化

**Files:**
- Create: `illust-asset-forge/templates/object.yaml`
- Create: `illust-asset-forge/src/artgen/cutout.py`
- Modify: `illust-asset-forge/src/artgen/config.py`（`Template.transparent_background: bool`、既定 false）
- Modify: `illust-asset-forge/src/artgen/selection.py`（`selected_name`）
- Modify: `illust-asset-forge/src/artgen/export.py`（`_accepted_names`・`_check_matches_name`・書き出し）
- Modify: `illust-asset-forge/src/artgen/intake.py`（受け付ける名前）
- Test: `illust-asset-forge/tests/test_cutout.py`、`tests/test_selection.py`、`tests/test_export.py`、`tests/test_intake.py`

**Interfaces:**
- Produces: `cutout.clear_outer_background(im: Image.Image, *, threshold: int = 240) -> Image.Image`（RGBA を返す。画像の縁から、R・G・B すべてが `threshold` 以上の画素を 4 近傍でたどって透明にする。たどり着けない白は残す）
- Produces: テンプレート `object`。採用名・書き出し名は `object.png`。書き出しは `characters/<id>/object.png`（512×512、RGBA）

`object.yaml` の中身:

```yaml
width: 1024
height: 1024
prompt: [no humans, solo, centered, full body, simple background, white background]
negative: [human, text, watermark, signature, multiple views, cropped, out of frame, shadow]
export_size: 512
use_items: false
transparent_background: true
```

- [ ] **Step 1: 失敗するテストを書く**
  - `test_cutout.py::test_cutout_clears_white_touching_edges`: 白地の 64×64 の中央に黒い枠の円 → 四隅の alpha が 0、円の線の alpha が 255
  - `test_cutout.py::test_cutout_keeps_white_enclosed_by_outline`: 黒い枠の円の内側が白 → 内側の中心の alpha が 255
  - `test_cutout.py::test_cutout_threshold`: 縁の色が (230,230,230) なら threshold=240 で残り、threshold=220 で消える
  - `test_selection.py::test_selected_name_object`: `selected_name({"template": "object"}) == "object.png"`
  - `test_export.py::test_export_object_is_transparent_512`: `source/object.png`（白地 1024×1024・条件つき）を書き出すと `object.png` が 512×512・RGBA・四隅 alpha 0
  - `test_export.py::test_export_object_rejects_face_template`: `object.png` の条件が `template: face` なら `ExportError`
  - `test_intake.py::test_intake_accepts_object_png`: zip／Modal の取り込みで `object.png` を受け付ける
- [ ] **Step 2:** `.venv/bin/pytest tests/test_cutout.py tests/test_selection.py tests/test_export.py tests/test_intake.py -q` — Expected: 上の新しいテストが FAIL
- [ ] **Step 3: 実装する。** 名前の決まりを「face と表情は今のまま、それ以外のテンプレートは `<template>.png`」に一般化する（`fullbody.png` はこの決まりで今と同じ名前になる）。`<template>` は `_check_name_part` で検査する。書き出しは `transparent_background` のとき `clear_outer_background` → RGBA のまま `export_size` に縮める（今の `convert("RGB")` を通さない）。`face.png` が無いキャラクター（ものの絵）でも書き出せるようにする
- [ ] **Step 4:** `.venv/bin/pytest -q` — Expected: 全部 PASS（既存のテストも）
- [ ] **Step 5:** UPSTREAM.md の「forge に戻す候補」に、テンプレート名で決まる採用名・`transparent_background`・`cutout.py` を 1 行ずつ足す
- [ ] **Step 6:** コミット `feat: ものを 1 つ描くテンプレート object と、外につながる背景の透明化を足す`

### Task 3: 20 種類の設定

**Files:**
- Create: `illust-asset-forge/characters/<id>/character.yaml`（20 個）
- Test: `illust-asset-forge/tests/test_chiiku_objects.py`

ID（以後すべての道具・ゲームで使う）:

| 種類キー | ID |
|---|---|
| `animal` | `dog` `cat` `cow` `pig` `chicken` `elephant` |
| `insect` | `butterfly` `ladybug` `beetle` |
| `fish` | `goldfish` `pufferfish` `shark` |
| `vegetable` | `tomato` `carrot` `eggplant` `corn` |
| `food` | `apple` `banana` `strawberry` `onigiri` |

`character.yaml` の形（例: いぬ）。`name` は日本語の名前、`subject` は何の絵か、`appearance` は見た目、`outfit`・`items` は空、表情は `normal` 1 つ:

```yaml
name: いぬ
subject: [dog, animal focus, cute]
appearance: [shiba inu, brown fur, sitting, smiling]
outfit: []
items: []
default_expression: normal
expressions:
  normal: []
```

`expressions.normal: []` を `config` が拒むなら、`[cute]` にする（拒むかどうかは Step 2 で分かる）。かぶとむしは角のあるオス、さめは怖くない顔、おにぎりは海苔を巻いた三角、を `appearance` に入れる。

- [ ] **Step 1: 失敗するテストを書く** `test_chiiku_objects.py`
  - `test_all_twenty_load`: 上の 20 の ID がすべて `load_character` で読め、`build_prompt(…, load_template(root, "object"))` が通る
  - `test_prompt_has_no_humans`: 20 個すべてのプロンプトに `no humans` が入る
  - `test_no_extra_characters_named_like_objects`: `characters/` の中の ID は、見本 4 人と上の 20 個だけ
- [ ] **Step 2:** `.venv/bin/pytest tests/test_chiiku_objects.py -q` — Expected: FAIL
- [ ] **Step 3:** 20 個の `character.yaml` を書く
- [ ] **Step 4:** `.venv/bin/pytest -q` — Expected: 全部 PASS
- [ ] **Step 5:** コミット `feat: 知育ゲーム用の 20 種類の設定を足す`

### Task 4: 20 枚を生成して採用する（依頼者の確認あり）

**Files:**
- Create: `illust-asset-forge/local/jobs/*.json`（git に入らない）
- Create: `illust-asset-forge/characters/<id>/source/object.png`・`object.png`・`params.json`（20 個）

- [ ] **Step 1: 画風の試し。** `dog`・`tomato`・`butterfly`・`onigiri` を各 3 枚（計 12 枚、10 円前後）作ると依頼者に伝えてから、`.venv/bin/python -m artgen.cloud generate --jobs local/jobs/style-trial.json`
- [ ] **Step 2:** 候補のページ（`local/rounds/<日時>.html`）を Artifact で見せ、thick-line-flat で続けるか聞く。替えるなら、forge の画風の候補（`styles/`）を同じシードで並べたページを作って選んでもらい、`defaults.yaml` の `style` を替える
- [ ] **Step 3: 本番の生成。** 20 種類 × 4 枚（80 枚、約 30 分・70 円前後）と伝えてから生成する。種類ごとに 1 ページ（5 回り）にする
- [ ] **Step 4:** 依頼者が番号で答えた候補を `artgen.cloud adopt` で採用する。良い候補が無いものは、`extra`・`remove` を変えて作り直す（作り直しも枚数を先に伝える）
- [ ] **Step 5:** `artgen.cloud install <20 の ID>` → `python -m artgen.export <id>`（20 回）
- [ ] **Step 6:** 書き出した 20 枚の `object.png` を、市松模様の背景に並べた Artifact のページで見せ、透明化の失敗（内側が抜けた・縁に白が残った）が無いか承認を受ける。失敗したものは `threshold` を変えるか作り直す
- [ ] **Step 7:** 承認後にコミット `feat: 知育ゲーム用の 20 種類の絵を生成して書き出す`

### Task 5: 共通素材の一覧と絵の書き出し

**Files:**
- Create: `shared-assets/chiiku/items.json`
- Create: `shared-assets/tools/build_images.py`
- Create: `shared-assets/chiiku/img/<id>.webp`（20 個）
- Test: `shared-assets/tools/tests/test_items.py`、`shared-assets/tools/tests/test_build_images.py`

**Interfaces:**
- Produces: `items.json` の形（ゲームはこの形を読む）:

```json
{
  "categories": [
    {"key": "animal", "label": "どうぶつ"},
    {"key": "insect", "label": "むし"},
    {"key": "fish", "label": "さかな"},
    {"key": "vegetable", "label": "やさい"},
    {"key": "food", "label": "たべもの"}
  ],
  "items": [
    {"id": "dog", "category": "animal", "label": "いぬ", "kana": "いぬ", "reading": "いぬ"}
  ]
}
```

  `label` はふつうの書き方（「トマト」）、`kana` はひらがな（「とまと」。8・9 で使う）、`reading` は VOICEVOX に渡す文。並びは設計書 3.1 の表の順。
- Produces: `build_images.main(forge_root: Path, out_dir: Path, items_path: Path) -> list[Path]`（`characters/<id>/object.png` を `img/<id>.webp`（512×512、透明を保つ、quality 90）にする。`items.json` にあって絵が無い ID があれば、何も書かずに止まる）

- [ ] **Step 1: 失敗するテストを書く**
  - `test_items.py::test_twenty_items_in_spec_order`: ID が Task 3 の表の順で 20 個、種類ごとの数が 6・3・3・4・4
  - `test_items.py::test_kana_is_hiragana`: すべての `kana` が `^[ぁ-ゖー]+$`
  - `test_items.py::test_categories_match`: すべての `category` が `categories` の `key` にある
  - `test_build_images.py::test_writes_webp_with_alpha`: 偽の forge（透明な PNG 2 つ）から webp が 2 つでき、四隅の alpha が 0
  - `test_build_images.py::test_stops_when_image_missing`: 絵の無い ID があると例外で、`out_dir` に何も書かない
- [ ] **Step 2:** `illust-asset-forge/.venv/bin/pytest shared-assets/tools/tests -q` — Expected: FAIL
- [ ] **Step 3:** `items.json` と `build_images.py`（`python shared-assets/tools/build_images.py` で ankardo の既定のパスを使って動く CLI）を書く
- [ ] **Step 4:** テストが PASS し、`build_images.py` を実行して `img/` に 20 個できる
- [ ] **Step 5:** コミット `feat: 共通素材の一覧と、絵を webp に書き出す道具を足す`

### Task 6: 名前の声（依頼者の確認あり）

**Files:**
- Create: `shared-assets/tools/voice.py`
- Create: `shared-assets/chiiku/voice/<id>.wav`（20 個）・`shared-assets/chiiku/voice/manifest.json`
- Test: `shared-assets/tools/tests/test_voice.py`

**Interfaces:**
- Produces: `voice.synthesize(text: str, speaker: int, base_url: str) -> bytes`（`POST /audio_query?text=…&speaker=…` → `POST /synthesis?speaker=…` で WAV を返す。接続できないときは `VoiceError` で「VOICEVOX Engine を起動する（~/opt/voicevox_engine/run --host 127.0.0.1）」と案内）
- Produces: `voice.build(items_path: Path, out_dir: Path, speaker: int, base_url: str) -> list[Path]`（`voice/<id>.wav` を書く。`manifest.json` に `{"speaker": int, "speaker_name": str, "engine_version": str, "files": {id: {"text": str, "sha256": str}}}`。text・speaker・Engine の版が同じなら作り直さない）
- 接続先は環境変数 `VOICEVOX_URL`（既定 `http://127.0.0.1:50021`）

- [ ] **Step 1: 失敗するテストを書く**（標準ライブラリの `http.server` で偽の Engine を立てる）
  - `test_synthesize_calls_query_then_synthesis`: 2 つの要求が順に来て、`text`・`speaker` が渡り、返り値が偽の WAV
  - `test_build_skips_unchanged`: 2 回目の `build` では偽の Engine に要求が来ない
  - `test_build_redoes_when_speaker_changes`: speaker を変えると全部作り直す
  - `test_unreachable_engine_message`: 閉じたポートで `VoiceError`、文に `~/opt/voicevox_engine/run` を含む
- [ ] **Step 2:** テストを実行して FAIL を確かめる
- [ ] **Step 3:** `voice.py` を書く（CLI: `python shared-assets/tools/voice.py --speaker <ID>`、`--trial` で試聴ページ用に下の文を複数の話者で作る）
- [ ] **Step 4:** テストが PASS する
- [ ] **Step 5: 話者の試聴。** Engine を起動し、`/speakers` から、ゆっくりはっきりした声の候補を 6 人ほど選ぶ。各話者で「いぬ」「とうもろこし」「ぞうさんは どれ？」を作り、音を data URI で埋め込んだ Artifact のページで聞いてもらう。話者ごとの利用規約のリンクも並べる
- [ ] **Step 6:** 依頼者が選んだ話者で `voice.py --speaker <ID>` を実行し、20 個の WAV ができる
- [ ] **Step 7:** コミット `feat: VOICEVOX で名前の声を作る道具と、20 種類の声を足す`

決まり文句（「〇〇は どれ？」など）は工程 3 で、そのゲームを作るときに `voice.py` に足す。

### Task 7: 鳴き声（依頼者の確認あり）

**Files:**
- Create: `shared-assets/chiiku/cry/<id>.mp3`（`dog` `cat` `cow` `pig` `chicken` `elephant`）
- Create: `shared-assets/chiiku/CREDITS.md`
- Test: `shared-assets/tools/tests/test_credits.py`

- [ ] **Step 1:** 無料の効果音サイト（効果音ラボなど）で 6 種類の録音を探す。サイトの規約で、ゲームでの利用・公開リポジトリへの再配布・クレジットの要否を確かめる。再配布を禁じるサイトは使わない。6 つそろわなければ依頼者に相談して止まる
- [ ] **Step 2:** 長すぎる録音は 1〜3 秒に切る必要がある。ffmpeg はこのサーバーに無いので、切る必要があれば先に依頼者に伝える（切らずに済む録音を優先する）
- [ ] **Step 3: 失敗するテストを書く**
  - `test_every_animal_has_cry`: `category == "animal"` の 6 つすべてに `cry/<id>.mp3` がある
  - `test_credits_list_every_cry_and_voice`: `CREDITS.md` に 6 つの鳴き声それぞれの出典 URL・規約 URL・クレジットの要否と、`manifest.json` の話者名の `VOICEVOX:<話者名>` がある
- [ ] **Step 4:** ファイルと `CREDITS.md` を置き、テストが PASS する
- [ ] **Step 5:** 6 つの鳴き声を並べた Artifact のページで聞いてもらい、承認を受ける
- [ ] **Step 6:** 承認後にコミット `feat: 6 種類の動物の鳴き声とクレジットを足す`

### Task 8: 素材をゲームへコピーする道具と正典

**Files:**
- Create: `scripts/copy-assets.sh`、`scripts/copy-assets.test.sh`
- Modify: `README.md`（構成・役割）、`.claude/skills/new-game/SKILL.md`（共通素材のコピー、「イラストを使うなら」の Colab の記述）、`HANDOVER.md`

**Interfaces:**
- Produces: `./scripts/copy-assets.sh chiiku <ゲームリポジトリのパス>` — `shared-assets/chiiku/` を `<ゲーム>/public/chiiku/` に丸ごと置き換えてコピーし、`<ゲーム>/chiiku-assets.md` に ankardo のコピー元の commit（未コミットの変更があれば `+dirty`）とコピーした日を書く。コミットはしない

- [ ] **Step 1: 失敗するテストを書く**（`copy-forge.test.sh` と同じ書き方。一時フォルダの偽ゲームに対して）
  - `copies all files`: `items.json`・`img/`・`voice/`・`cry/`・`CREDITS.md` がコピーされる
  - `removed files disappear on recopy`: コピー先に余分なファイルを置いて再実行すると消える
  - `writes upstream note`: `chiiku-assets.md` に commit が書かれる
  - `rejects unknown set`: `chiiku` 以外の名前で終了コード 2
  - `rejects missing game dir`: 無いパスで終了コード 1
- [ ] **Step 2:** `bash scripts/copy-assets.test.sh` — Expected: FAIL
- [ ] **Step 3:** `copy-assets.sh` を書く（一時フォルダに組み立ててから置き換え、途中で失敗しても古いコピーを壊さない）
- [ ] **Step 4:** テストが PASS する
- [ ] **Step 5:** README の構成の図とルーティングの近くに、`illust-asset-forge/`・`shared-assets/`・`copy-assets.sh` と「共通素材を作って各ゲームへ配る役」を書く。SKILL.md に「共通素材を使うなら」の節を足し、「イラストを使うなら」の Colab の記述を Modal の道がある今の状態に直す
- [ ] **Step 6:** `HANDOVER.md` の進捗を工程 1 完了・工程 2 に直す
- [ ] **Step 7:** コミットし、push して ankardo の PR を作る（依頼者の手作業 5）

### Task 9: なまえタッチのリポジトリと共通部分

依頼者の手作業 6〜8 が済んでから始める。

**Files（`name-touch` リポジトリ）:**
- Create: `package.json`・`vite.config.ts`・`tsconfig.json`・`biome.json`・`index.html`・`wrangler.toml`・`.github/workflows/deploy.yml`・`.github/workflows/preview.yml`・`CLAUDE.md`・`README.md`・`HANDOVER.md`
- Create: `src/common/assets.ts`、`src/common/audio.ts`、`src/common/long-press.ts`、`src/common/screens.ts`、`src/main.ts`
- Create: `public/chiiku/`（`copy-assets.sh` で）・`chiiku-assets.md`
- Test: `src/common/*.test.ts`

**Interfaces:**
- Produces: `loadItems(url: string): Promise<ItemsFile>`（`ItemsFile = { categories: {key: string; label: string}[]; items: Item[] }`、`Item = { id: string; category: string; label: string; kana: string; reading: string }`。形が違えば `Error` で、どの項目が違うかを示す）
- Produces: `createAudio(): AudioPlayer`（`unlock(): Promise<void>` を最初のタッチの中で呼ぶ。`play(url: string): Promise<void>` は鳴っている音を止めてから鳴らす。`stop(): void`）
- Produces: `attachLongPress(el: HTMLElement, ms: number, onFire: () => void): () => void`（`pointerdown` から `ms` 続いたら 1 回 `onFire`。`pointerup`・`pointerleave`・`pointercancel` で取り消す。返り値で外す）
- Produces: `showTitle(root: HTMLElement, opts: { title: string; credits: string[]; onStart: () => void }): void`（大きな「はじめる」ボタン。ボタンは絵（▶）だけ。クレジットは下に小さく）

- [ ] **Step 1:** shogi-vs-cpu と同じ構成で土台を作る。`base: '/play/name-touch/'`、`build.outDir: 'out/play/name-touch'`、`wrangler.toml` の `name = "ankardo-game-name-touch"`、`preview_urls = true`・`[previews]`、wrangler `^4.135.0`、Node 22。`deploy.yml`・`preview.yml` は ankardo の SKILL.md の手順どおり（preview は `.claude/skills/new-game/preview.yml` をそのまま写す）
- [ ] **Step 2:** `../ankardo/scripts/copy-assets.sh chiiku .` で素材を入れる
- [ ] **Step 3: 失敗するテストを書く**
  - `assets.test.ts`: `loadItems` が正しい JSON で 20 個を返す／`items[3].kana` が無いと「items[3].kana」を含むエラー
  - `audio.test.ts`: `unlock is called inside the start tap`（`showTitle` の `onStart` の前に `unlock` が呼ばれる）／`play` を続けて呼ぶと前の音の `stop` が呼ばれる（`AudioContext` は偽物を渡す）
  - `long-press.test.ts`（偽のタイマー）: `fires after 1500ms`／`short tap does not exit`（800ms で `pointerup` → 呼ばれない）／`pointerleave cancels`
- [ ] **Step 4:** `npx vitest run` — Expected: FAIL
- [ ] **Step 5:** `src/common/` を実装する。音は Web Audio（`decodeAudioData`）で鳴らす
- [ ] **Step 6:** `npx vitest run` と `npx biome check .` と `npm run build` が通る
- [ ] **Step 7:** `CLAUDE.md` に機能ブランチ → develop → main の流れと、`src/common/` はあとでひな形に切り出すので、なまえタッチだけの決まりを入れないことを書く。`HANDOVER.md` に進捗（作業: 幼児向け知育ゲーム）を書く
- [ ] **Step 8:** コミット `feat: なまえタッチの土台と、知育ゲームで共通の部分を作る`

### Task 10: なまえタッチの遊び

**Files（`name-touch`）:**
- Create: `src/game/pages.ts`、`src/game/name-touch.ts`、`src/style.css`
- Test: `src/game/pages.test.ts`、`src/game/name-touch.test.ts`

**Interfaces:**
- Consumes: Task 9 の `loadItems`・`createAudio`・`attachLongPress`・`showTitle`
- Produces: `buildPages(file: ItemsFile): Page[]`（`Page = { category: string; items: Item[] }`。種類の順に 1 ページずつ。設計書のとおり 1 ページ 4〜6 個で、20 種類なら 5 ページ・個数は 6・3・3・4・4）
- Produces: `startNameTouch(root: HTMLElement, deps: { file: ItemsFile; audio: AudioPlayer; onExit: () => void }): void`

遊び方（設計書 6 章）: ページに絵が並び、タッチすると絵がはねて（CSS のアニメーション、約 0.4 秒）`voice/<id>.wav` を鳴らす。左右の矢印でページをめくる（最初のページに左、最後のページに右の矢印は出さない）。左上の ⏏ を 1.5 秒長押しでタイトルへ戻る。

- [ ] **Step 1: 失敗するテストを書く**
  - `pages.test.ts::five pages in spec order`: ページの種類が `animal` `insect` `fish` `vegetable` `food`、個数が 6・3・3・4・4
  - `name-touch.test.ts::tapping an item plays its voice`: `dog` の絵を叩くと `audio.play` が `chiiku/voice/dog.wav` で呼ばれ、絵に跳ねるクラスが付く
  - `name-touch.test.ts::tapping again restarts the voice`: 同じ絵を 2 回叩くと `play` が 2 回呼ばれる（`play` が前の音を止める）
  - `name-touch.test.ts::arrows hidden at ends`: 1 ページ目に左の矢印が無く、5 ページ目に右の矢印が無い
  - `name-touch.test.ts::long press exits`: ⏏ の長押しで `onExit` が呼ばれる
- [ ] **Step 2:** `npx vitest run` — Expected: FAIL
- [ ] **Step 3:** 実装する。絵は大きく（横向きのスマホで 1 つ 120px 以上）、余白を広く取り、誤タッチしにくくする
- [ ] **Step 4:** テスト・Biome・ビルドが通る
- [ ] **Step 5:** `npm run dev` を Playwright で開き、横向きのスマホ（iPhone 13 の横向き）とタブレット（iPad の横向き）と PC で、タイトル → 1 ページ目 → タッチで跳ねる → 最後のページを撮る。画像を Artifact のページで依頼者に見せ、承認を受ける
- [ ] **Step 6:** 承認後にコミット `feat: なまえタッチの遊びを作る`

### Task 11: 公開とカタログへの登録

**Files:**
- `name-touch`: 変更なし（PR とデプロイ）
- ankardo: Modify `site/lib/genres.ts`（`education`、ラベル「知育」）、`site/app/globals.css`（`--color-genre-education`）、Create `site/content/games/name-touch.json`、`site/public/screenshots/name-touch/01.png`、Modify `site/public/_redirects`、`HANDOVER.md`
- Test: `site/lib/games.test.ts`（既存の検証が通ること）

- [ ] **Step 1:** name-touch を ankardo の SKILL.md「確認用のプレビュー」の 5・6 の順で出す: main への PR → マージ → 本番 deploy の承認と成功を待つ → main から develop を作って push → プレビューの URL が `302` で Access に転送されることを確かめる
- [ ] **Step 2:** `https://ankardo.com/play/name-touch/` を Playwright で開き、はじめる → タッチで声が鳴る（`play` が呼ばれたことをページのログで）ことを確かめる
- [ ] **Step 3:** ankardo に別ブランチ `feat/name-touch-catalog` を切る。`genres.ts` に `education: { label: "知育", … }` を足す。色は既存の 7 色と見分けられ、文字色の対比が AA を満たすもの（決めた色と対比をコメントに書く、既存の書き方どおり）
- [ ] **Step 4:** `name-touch.json` を書く:

```json
{
  "slug": "name-touch",
  "title": "なまえタッチ",
  "description": "どうぶつ・むし・さかな・やさい・たべものの絵をタッチすると、なまえを読み上げます。",
  "playUrl": "/play/name-touch/",
  "genre": "education",
  "devices": ["pc", "mobile-landscape"],
  "controls": ["絵をタッチすると、なまえを読み上げます", "左右の矢印でページをめくります", "左上のボタンを長押しすると、はじめの画面にもどります"],
  "images": ["/screenshots/name-touch/01.png"],
  "ageRange": "2歳〜",
  "players": "ひとり用",
  "difficulty": "やさしめ"
}
```

- [ ] **Step 5:** スクリーンショット（16:9、1280×720、300KB 以内）を撮って置き、`_redirects` に `/games/name-touch /games/name-touch/ 301` を足す
- [ ] **Step 6:** `cd site && npm test && npm run build` — Expected: PASS
- [ ] **Step 7:** `HANDOVER.md` の進捗を工程 2 完了・工程 3 に直す（次にやること: 共通部分のひな形の切り出しと、残り 8 本の計画）
- [ ] **Step 8:** コミット・push して PR を作る（依頼者の手作業 10）。マージ後にカタログの一覧・詳細ページに出たことを確かめる
