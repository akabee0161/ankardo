# 共通素材（知育ゲーム）の出典とクレジット

2026-11-25 に確認した。素材を替えたら、この表も直す。

## ゲームの画面に出すクレジット（タイトル画面の下に小さく）

```text
VOICEVOX:ずんだもん
鳴き声: Amada44（CC BY-SA 3.0）・Secretlondon（CC BY-SA 3.0）ほか / Wikimedia Commons・Freesound
```

- 鳴き声を使わないゲーム（なまえタッチなど、動物の鳴き声を鳴らさないもの）は、1 行目だけを出す。鳴き声を使うゲームは 2 行とも出す
- 「ほか」の 4 つ（ねこ・うし・にわとり・ぞう）はクレジットが要らない（CC0・パブリックドメイン）。ただし出典は下に残す
- CC BY-SA の 2 つ（いぬ・ぶた）の `cry/dog.wav`・`cry/pig.wav` は、加工物にも元と同じ CC BY-SA 3.0 がかかる

## 名前の声

声は VOICEVOX Engine で作った（`shared-assets/tools/voice.py`）。話者は `voice/manifest.json` の `speaker_name`。

- クレジット: `VOICEVOX:ずんだもん`（必須）
- 規約: https://zunko.jp/con_ongen_kiyaku.html（2026-11-25 に確認。商用・非商用とも利用できる。クレジット表記が必要。政治・宗教活動、情報商材、嘘やフェイク、風俗営業などでの利用は禁止）
- 子ども向けの知育ゲームは禁止事項に当たらない

## 鳴き声

6 種類の動物の録音を、Wikimedia Commons と Freesound から取った。再配布が許される条件（CC0・パブリックドメイン・CC BY-SA）の録音だけを使い、公開リポジトリに置いてよい。

使わなかったもの（理由を残す）:

- 効果音ラボ: 規約で再配布が禁止され、音が主役のアプリも再配布にあたる（https://soundeffect-lab.info/agreement/ 、2026-11-25 に確認）
- Commons の「Single Cow Moo」: 元が Sound Ideas 社の市販ライブラリの録音で、CC BY-SA の表示が誤り。Commons で削除が提案されている（2026-07-17〜）
- Commons の「UVB Pirats（polish cow）」: 短波ラジオ局の放送の録音で、牛の音の出所が不明

`cry/<id>.wav` は、元の録音から鳴いている部分だけを切り出し（1 秒前後。長いものでも 2.5 秒）、モノラルにして、音量の最大値を 0.9 にそろえ、前後に短い減衰（入り 0.01 秒・終わり 0.04 秒）を付けた加工物。形式を wav にそろえたのは、ffmpeg が無く、ogg を mp3 にできないことと、ogg が古い iOS で鳴らないため。

### dog

- 録音: Barking of a dog（Amada44）
- 出典: https://commons.wikimedia.org/wiki/File%3ABarking_of_a_dog.ogg
- 規約: CC BY-SA 3.0 https://creativecommons.org/licenses/by-sa/3.0
- クレジット: 要る（作者名・ライセンス名・出典）。加工した `cry/dog.wav` にも同じ CC BY-SA 3.0 がかかる
- 加工: 元の 0.0〜1.5 秒（元は 2.61 秒）。依頼者の承認（2026-11-25）

### cat

- 録音: Meow of a pleading cat（Heismark）
- 出典: https://commons.wikimedia.org/wiki/File%3AMeow_of_a_pleading_cat.oga
- 規約: パブリックドメイン（Commons のライセンス表示。ライセンス URL は無い）
- クレジット: 要らない（任意）
- 加工: 元の 3.6〜5.0 秒（元は 11.85 秒）。元が 8kHz の古い録音で、音がこもる（依頼者が承知の上で選んだ）

### cow

- 録音: Cow moo #8（spurioustransients。ウェールズの野原で録音。2 回鳴くうちの 1 回）
- 出典: https://freesound.org/people/spurioustransients/sounds/513565/
- 規約: CC0 https://creativecommons.org/publicdomain/zero/1.0/
- クレジット: 要らない（任意）
- 加工: Freesound のプレビュー（mp3）の 3.0〜4.8 秒（元は 10.8 秒）。ステレオをモノラルに

### pig

- 録音: Mudchute pig 1・2・3（Secretlondon）。3 つの短い鳴き声（0.36・0.33・0.20 秒）を、0.15 秒の間を空けてつないだ（1.2 秒）
- 出典: https://commons.wikimedia.org/wiki/File%3AMudchute_pig_1.ogg 、https://commons.wikimedia.org/wiki/File%3AMudchute_pig_2.ogg 、https://commons.wikimedia.org/wiki/File%3AMudchute_pig_3.ogg
- 規約: CC BY-SA 3.0 http://creativecommons.org/licenses/by-sa/3.0/
- クレジット: 要る（作者名・ライセンス名・出典。つないだことも示す）。加工した `cry/pig.wav` にも同じ CC BY-SA 3.0 がかかる
- 加工: 3 つの音量をそろえ、つないだ。依頼者が「もう少し長い音」を望んだため（2026-11-25 に承認）

### chicken

- 録音: Medium rooster crowing（alys。元は PDSounds http://www.pdsounds.org/sounds/medium_rooster_crowing ）
- 出典: https://commons.wikimedia.org/wiki/File%3AMedium_rooster_crowing.ogg
- 規約: パブリックドメイン（Commons のライセンス表示。ライセンス URL は無い）
- クレジット: 要らない（任意）
- 加工: 元の 2.9〜5.4 秒（元は 8.31 秒）。元のファイルに Ogg Skeleton の付加ストリームが混ざり、ライブラリが読めなかったため、そのページを除いて音声（Vorbis）だけを取り出してから切った

### elephant

- 録音: Elephant voice - trumpeting（தகவலுழவன்）
- 出典: https://commons.wikimedia.org/wiki/File%3AElephant_voice_-_trumpeting.ogg
- 規約: CC0 http://creativecommons.org/publicdomain/zero/1.0/deed.en
- クレジット: 要らない（任意）
- 加工: 元の 0.05〜1.44 秒（元は 1.44 秒、ステレオをモノラルに）。元の音量が小さかったため、約 3 倍に上げた
