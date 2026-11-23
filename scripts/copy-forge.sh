#!/usr/bin/env bash
# pixel-asset-forge または illust-asset-forge の main の最新 commit を、ゲームリポジトリへ丸ごとコピーする。
#   ./scripts/copy-forge.sh <pixel|illust> <ゲームリポジトリのパス>
# pixel は <ゲーム>/pixel-asset-forge/、illust は <ゲーム>/illust-asset-forge/ に入る。
# 1 回の実行で 1 つ。両方使うゲームは 2 回実行する。
# 手順と経緯は .claude/skills/new-game/SKILL.md の「ドット絵を使うなら」「イラストを使うなら」。
set -euo pipefail

# git のフックの中などから呼ばれると GIT_DIR などが入っていて、git -C でも呼び出し元の
# リポジトリを読んでしまう。git が挙げる「リポジトリの場所を決める変数」をすべて外す
# shellcheck disable=SC2046
unset $(git rev-parse --local-env-vars)

usage() {
  echo "使い方: $0 <pixel|illust> <ゲームリポジトリのパス>" >&2
  exit 2
}

if [ $# -ne 2 ]; then
  usage
fi
case "$1" in
  pixel) name="pixel-asset-forge" ;;
  illust) name="illust-asset-forge" ;;
  *) usage ;;
esac
# FORGE_URL はコピー元の上書き（テスト用）
FORGE_URL="${FORGE_URL:-https://github.com/akabee0161/$name.git}"

game="$2"
if [ ! -d "$game" ]; then
  echo "エラー: $game が無い" >&2
  exit 1
fi
dest="$game/$name"
if [ -e "$dest" ]; then
  echo "エラー: $dest は既にある（上書きしない）" >&2
  exit 1
fi

# 一時フォルダで組み立ててから移すので、途中で失敗しても $dest は残らない。
# 一時フォルダをゲームリポジトリの中に作るのは、mv を同じファイルシステムの中の
# rename にして、一度に移すため（/tmp が別のファイルシステムだとコピーと削除になる）
work="$(mktemp -d "$game/.copy-forge.XXXXXX")"
trap 'rm -rf "$work"' EXIT

git clone --quiet --depth 1 --branch main "$FORGE_URL" "$work/forge"
commit="$(git -C "$work/forge" rev-parse HEAD)"
mkdir "$work/out"
git -C "$work/forge" archive --format=tar HEAD | tar -x -C "$work/out"

# illust は、引き継ぎをゲームの HANDOVER.md 1 つにするため、forge の HANDOVER.md と、
# forge の当時のログ（docs/superpowers/）を持ち込まない
if [ "$1" = "illust" ]; then
  rm -rf "$work/out/HANDOVER.md" "$work/out/docs/superpowers"
  rmdir --ignore-fail-on-non-empty "$work/out/docs" 2> /dev/null || true
fi

cat > "$work/out/UPSTREAM.md" << EOF
# UPSTREAM

このフォルダは $name のコピーで、このゲーム専用に自由に直してよい。

- コピー元: $FORGE_URL
- commit: $commit
- コピーした日: $(date +%F)

forge 本体も並行して開発が続く。forge の改善をこちらへ取り込む仕組みは無く、要るものはその都度手で持ってくる。

## forge に戻す候補

ここでエンジン・規約・道具を直したら、何を・なぜ直したかを1行足す。

## ゲームの開発が終わったら

上の候補と、このフォルダを足したコミットからの差分を材料に、forge の issue を出す。
差分は \`git diff \$(git log --format=%H --diff-filter=A -1 -- $name/UPSTREAM.md) -- $name/\` で見られる。
取り込むときに、そのまま採用するか、抽象化してから入れるかを1件ずつ決める。
EOF

mv "$work/out" "$dest"
echo "コピーした: $dest（$FORGE_URL の $commit）"
