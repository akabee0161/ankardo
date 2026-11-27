#!/usr/bin/env bash
# 知育ゲームのひな形（templates/chiiku-game/）を、空のゲームのリポジトリへ写して、slug・題・日付を置き換える。
#   ./scripts/copy-template.sh chiiku-game <slug> <題> <ゲームのフォルダ>
# 終了コード: 0 成功、2 引数の誤り、1 それ以外の失敗。失敗したときは何も書かない。
# プレビューのワークフローは、ひな形に複製を持たず、正本の .claude/skills/new-game/preview.yml を写す。
# 写した後は各ゲームで自由に直してよい。写した元の commit は <ゲーム>/template.md に残る。
# 手順と経緯は .claude/skills/new-game/SKILL.md の「知育ゲームをひな形から作る」。
#
# テスト用の環境変数: TEMPLATE_ROOT（ひな形の親。既定は ankardo の templates/）、
# PREVIEW_TEMPLATE（既定は .claude/skills/new-game/preview.yml）
set -euo pipefail

# git のフックの中などから呼ばれると GIT_DIR などが入っていて、git -C でも呼び出し元の
# リポジトリを読んでしまう。git が挙げる「リポジトリの場所を決める変数」をすべて外す
# shellcheck disable=SC2046
unset $(git rev-parse --local-env-vars)

usage() {
  echo "使い方: $0 chiiku-game <slug> <題> <ゲームのフォルダ>" >&2
  exit 2
}

if [ $# -ne 4 ]; then
  usage
fi
kind="$1"
slug="$2"
title="$3"
game="$4"

if [ "$kind" != "chiiku-game" ]; then
  echo "エラー: ひな形の名前は chiiku-game だけ（$kind）" >&2
  usage
fi
# slug はプレビューのホスト名（develop-ankardo-game-<slug>）を 63 文字以内にするため 42 文字まで
if [ "${#slug}" -gt 42 ] || ! [[ "$slug" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
  echo "エラー: slug は小文字・数字・ハイフンで、42 文字以内（$slug）" >&2
  usage
fi
# 題は index.html の <title> や main.ts の文字列にそのまま入るので、壊す文字は受け付けない
if [ -z "$title" ]; then
  echo "エラー: 題が空" >&2
  usage
fi
if [[ "$title" == *[\<\&\'\"\\]* ]] || [[ "$title" == *[[:cntrl:]]* ]]; then
  echo "エラー: 題に < & ' \" \\ と改行・制御文字は使えない" >&2
  usage
fi

here="$(cd "$(dirname "$0")/.." && pwd)"
template_root="${TEMPLATE_ROOT:-$here/templates}"
preview_template="${PREVIEW_TEMPLATE:-$here/.claude/skills/new-game/preview.yml}"
name="chiiku-game"

if [ ! -d "$game" ]; then
  echo "エラー: $game が無い" >&2
  exit 1
fi
if [ ! -d "$template_root/$name" ]; then
  echo "エラー: ひな形が無い: $template_root/$name" >&2
  exit 1
fi
if [ ! -f "$preview_template" ]; then
  echo "エラー: プレビューのワークフローが無い: $preview_template" >&2
  exit 1
fi
# .git 以外が既にある（gh repo create --add-readme など）ときは、何も書かずに止まる
if [ -n "$(find "$game" -mindepth 1 -maxdepth 1 ! -name .git -print -quit)" ]; then
  echo "エラー: $game に .git 以外のファイルが既にある（上書きしない）" >&2
  exit 1
fi

commit="$(git -C "$template_root" rev-parse HEAD)"
if [ -n "$(git -C "$template_root" status --porcelain -- "$name")" ]; then
  commit="$commit+dirty"
fi
today="$(date +%F)"

# 一時フォルダで組み立ててから移すので、途中で失敗しても何も残らない。
# 一時フォルダをゲームのフォルダの中に作るのは、mv を同じファイルシステムの中の rename にするため
work="$(mktemp -d "$game/.copy-template.XXXXXX")"
trap 'rm -rf "$work"' EXIT
out="$work/out"
mkdir "$out"

# 管理下のファイルだけを写す（node_modules・out を拾わない）
texts="$work/texts"
: > "$texts"
while IFS= read -r -d '' f; do
  rel="${f#"$name"/}"
  mkdir -p "$out/$(dirname "$rel")"
  cp -p "$template_root/$f" "$out/$rel"
  if grep -Iq . "$out/$rel"; then
    printf '%s\0' "$out/$rel" >> "$texts"
  fi
done < <(git -C "$template_root" ls-files -z -- "$name")

# テキストのファイルだけを、Python の str.replace で置き換える（sed だと & や区切り文字で題が化ける）
SLUG="$slug" TITLE="$title" TODAY="$today" TEXTS="$texts" python3 -c '
import os
pairs = [
    ("chiiku-template-slug", os.environ["SLUG"]),
    ("__TITLE__", os.environ["TITLE"]),
    ("__DATE__", os.environ["TODAY"]),
]
with open(os.environ["TEXTS"], "rb") as f:
    paths = [p for p in f.read().split(b"\0") if p]
for p in paths:
    with open(p, "r", encoding="utf-8", newline="") as f:
        s = f.read()
    for old, new in pairs:
        s = s.replace(old, new)
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)
'

mkdir -p "$out/.github/workflows"
cp "$preview_template" "$out/.github/workflows/preview.yml"

cat > "$out/template.md" << EOF
# template

このゲームは ankardo の templates/$name を写して作った。写した後は、このゲーム専用に自由に直してよい。

- 写した元: ankardo の templates/$name
- commit: $commit
- 写した日: $today
- .github/workflows/preview.yml は、ankardo の .claude/skills/new-game/preview.yml の写し

共通部分（src/common/）を直したら、ほかのゲームにも要るかを考え、要るなら ankardo のひな形にも同じ直しを入れる（PR を分ける）。
EOF

# 中身（.git 以外）を移す。先頭が . のファイルも含める
find "$out" -mindepth 1 -maxdepth 1 -exec mv {} "$game"/ \;
echo "コピーした: $game（templates/$name の $commit）"
