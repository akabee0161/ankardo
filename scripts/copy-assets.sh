#!/usr/bin/env bash
# ankardo の共通素材（shared-assets/<名前>/）を、ゲームリポジトリの public/<名前>/ へ丸ごと置き換えてコピーする。
#   ./scripts/copy-assets.sh <名前> <ゲームリポジトリのパス> [--no-cry]
# 名前は chiiku（知育ゲーム用の絵・声・鳴き声）だけ。コピー先の public/<名前>/ は丸ごと置き換える（古いファイルは残らない）。
# <ゲーム>/<名前>-assets.md に、コピー元の commit（未コミットの変更があれば +dirty）とコピーした日を書く。コミットはしない。
# --no-cry を付けると、鳴き声（cry/）を入れない。鳴き声を鳴らさないゲームに付ける（CC BY-SA の録音を、使わないゲームで配らないため）。
# 手順と経緯は .claude/skills/new-game/SKILL.md の「共通素材を使うなら」。
set -euo pipefail

# git のフックの中などから呼ばれると GIT_DIR などが入っていて、git -C でも呼び出し元のリポジトリを読んでしまう。
# git が挙げる「リポジトリの場所を決める変数」をすべて外す
# shellcheck disable=SC2046
unset $(git rev-parse --local-env-vars)

usage() {
  echo "使い方: $0 <chiiku> <ゲームリポジトリのパス> [--no-cry]" >&2
  exit 2
}

no_cry=0
if [ $# -eq 3 ]; then
  [ "$3" = "--no-cry" ] || usage
  no_cry=1
  set -- "$1" "$2"
fi
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
keep_work=0 # 前のコピーへ戻せなかったときは、旧素材・旧メモが入っているので消さない
trap 'if [ "$keep_work" != 1 ]; then rm -rf "$work"; fi' EXIT

mkdir "$work/out"
cp -R "$src/." "$work/out/"
if [ "$no_cry" = 1 ]; then
  rm -rf "$work/out/cry"
fi

mkdir -p "$game/public"
note_dest="$game/${set_name}-assets.md"

# メモに書く「コピーしたコマンド」。使ったオプションごと書き、そのまま再実行しても同じコピーになるようにする
copy_cmd="scripts/copy-assets.sh ${set_name} ."
if [ "$no_cry" = 1 ]; then
  copy_cmd="$copy_cmd --no-cry"
fi

# コピー元メモも、素材を入れ替える前に組み立てておく（入れ替えの後で失敗する作業を残さない）
cat > "$work/note.md" << EOF
# ${set_name} の共通素材のコピー

\`public/${set_name}/\` は、ankardo の \`shared-assets/${set_name}/\` を \`${copy_cmd}\` でコピーしたもの。
手で直さない。直すときは ankardo の素材を直し、コピーし直す（コピーのたびに \`public/${set_name}/\` は丸ごと置き換わる）。

- コピー元: ankardo の \`shared-assets/${set_name}/\`
- commit: ${commit}
- コピーした日: $(date +%F)
- 鳴き声（\`cry/\`）: $([ "$no_cry" = 1 ] && echo "入れていない（--no-cry）" || echo "入れた")

\`+dirty\` が付いているときは、コピー元に未コミットの変更があった。クレジットは \`public/${set_name}/CREDITS.md\` にある。
EOF

# 素材とメモは 1 つの成功単位。どちらかの入れ替えに失敗したら、両方を前の状態へ戻す。
# 旧素材・旧メモは、両方の入れ替えが済むまで $work の中に残す（EXIT で消えるのは、成功した後か、戻した後）
assets_swapped=0
rollback() {
  local failed=0
  if [ "$assets_swapped" = 1 ] && ! rm -rf "$dest"; then
    failed=1 # $dest が残っていると、旧素材を戻せない（中へ入ってしまう）
  elif [ -e "$work/old" ] && ! mv "$work/old" "$dest"; then
    failed=1
  fi
  if [ -e "$work/old-note.md" ] && ! mv "$work/old-note.md" "$note_dest"; then
    failed=1
  fi
  if [ "$failed" = 1 ]; then
    keep_work=1
    echo "エラー: 前のコピーへ戻せなかった。旧素材は $work/old、旧メモは $work/old-note.md に残してある。手で $dest と $note_dest に戻す" >&2
  fi
}

if [ -e "$dest" ]; then
  mv "$dest" "$work/old"
fi
if ! mv "$work/out" "$dest"; then
  rollback
  echo "エラー: $dest へ移せなかった（前のコピーに戻した）" >&2
  exit 1
fi
assets_swapped=1
if [ -e "$note_dest" ]; then
  if ! mv "$note_dest" "$work/old-note.md"; then
    rollback
    echo "エラー: $note_dest を退避できなかった（前のコピーに戻した）" >&2
    exit 1
  fi
fi
if ! mv "$work/note.md" "$note_dest"; then
  rollback
  echo "エラー: $note_dest を置けなかった（前のコピーに戻した）" >&2
  exit 1
fi

echo "コピーした: $dest（ankardo の $commit）"
