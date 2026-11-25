#!/usr/bin/env bash
# ankardo の共通素材（shared-assets/<名前>/）を、ゲームリポジトリの public/<名前>/ へ丸ごと置き換えてコピーする。
#   ./scripts/copy-assets.sh <名前> <ゲームリポジトリのパス>
# 名前は chiiku（知育ゲーム用の絵・声・鳴き声）だけ。コピー先の public/<名前>/ は丸ごと置き換える（古いファイルは残らない）。
# <ゲーム>/<名前>-assets.md に、コピー元の commit（未コミットの変更があれば +dirty）とコピーした日を書く。コミットはしない。
# 手順と経緯は .claude/skills/new-game/SKILL.md の「共通素材を使うなら」。
set -euo pipefail

# git のフックの中などから呼ばれると GIT_DIR などが入っていて、git -C でも呼び出し元のリポジトリを読んでしまう。
# git が挙げる「リポジトリの場所を決める変数」をすべて外す
# shellcheck disable=SC2046
unset $(git rev-parse --local-env-vars)

usage() {
  echo "使い方: $0 <chiiku> <ゲームリポジトリのパス>" >&2
  exit 2
}

if [ $# -ne 2 ]; then
  usage
fi
case "$1" in
  chiiku) set_name="chiiku" ;;
  *) usage ;;
esac

# ANKARDO_ROOT はコピー元の ankardo の場所の上書き（テスト用）
here="$(cd "$(dirname "$0")" && pwd)"
root="${ANKARDO_ROOT:-$(cd "$here/.." && pwd)}"
src="$root/shared-assets/$set_name"
game="$2"

if [ ! -d "$src" ]; then
  echo "エラー: コピー元 $src が無い" >&2
  exit 1
fi
if [ ! -d "$game" ]; then
  echo "エラー: $game が無い" >&2
  exit 1
fi
dest="$game/public/$set_name"

commit="$(git -C "$root" rev-parse HEAD)"
if [ -n "$(git -C "$root" status --porcelain -- "shared-assets/$set_name")" ]; then
  commit="$commit+dirty"
fi

# 一時フォルダで組み立ててから入れ替えるので、途中で失敗しても前のコピーは壊れない。
# 一時フォルダをゲームリポジトリの中に作るのは、mv を同じファイルシステムの中の rename にして、一度に移すため
work="$(mktemp -d "$game/.copy-assets.XXXXXX")"
trap 'rm -rf "$work"' EXIT

mkdir "$work/out"
cp -R "$src/." "$work/out/"

mkdir -p "$game/public"
if [ -e "$dest" ]; then
  mv "$dest" "$work/old"
fi
if ! mv "$work/out" "$dest"; then
  [ -e "$work/old" ] && mv "$work/old" "$dest"
  echo "エラー: $dest へ移せなかった（前のコピーに戻した）" >&2
  exit 1
fi

cat > "$work/note.md" << EOF
# ${set_name} の共通素材のコピー

\`public/${set_name}/\` は、ankardo の \`shared-assets/${set_name}/\` を \`scripts/copy-assets.sh ${set_name} .\` でコピーしたもの。
手で直さない。直すときは ankardo の素材を直し、コピーし直す（コピーのたびに \`public/${set_name}/\` は丸ごと置き換わる）。

- コピー元: ankardo の \`shared-assets/${set_name}/\`
- commit: ${commit}
- コピーした日: $(date +%F)

\`+dirty\` が付いているときは、コピー元に未コミットの変更があった。クレジットは \`public/${set_name}/CREDITS.md\` にある。
EOF
mv "$work/note.md" "$game/${set_name}-assets.md"

echo "コピーした: $dest（ankardo の $commit）"
