#!/usr/bin/env bash
# 知育ゲームのひな形（templates/chiiku-game/）を、空のリポジトリへ写して素材を入れ、
# npm ci → テスト → lint → ビルドが通るかを確かめる。ひな形を直したら、各ゲームへ写す前に流す。
#   ./scripts/check-chiiku-template.sh
# ネットワーク（npm の取得）を使う。成功で終了コード 0。どこかで落ちたら、そのコマンドの出力の終わりを出して 0 以外。
# ひな形は git に載っている（add 済みを含む）ファイルだけが写る。
set -euo pipefail

# git のフックの中などから呼ばれると GIT_DIR などが入っていて、git -C でも呼び出し元の
# リポジトリを読んでしまう。git が挙げる「リポジトリの場所を決める変数」をすべて外す
# shellcheck disable=SC2046
unset $(git rev-parse --local-env-vars)

here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
game="$work/check-game"
log="$work/step.log"
mkdir "$game"
git init -q -b main "$game"

# 1 つのコマンドを流し、出力は $log にためる。落ちたら終わりの 40 行を出して止まる
step() {
  local label="$1"
  shift
  echo "== $label"
  if ! "$@" > "$log" 2>&1; then
    echo "FAIL: $label" >&2
    tail -n 40 "$log" >&2
    exit 1
  fi
}

step "写す（copy-template.sh）" "$here/copy-template.sh" chiiku-game check-game 'かくにん' "$game"
step "素材を入れる（copy-assets.sh chiiku --no-cry）" "$here/copy-assets.sh" chiiku "$game" --no-cry
cd "$game"
step "npm ci" npx --yes npm@10 ci
step "テスト（deploy.yml と同じ CI=true。素材の入れ忘れも見る）" env CI=true npm test
step "lint" npx biome check .
step "ビルド" npm run build

[ -f out/play/check-game/index.html ] || { echo "FAIL: out/play/check-game/index.html が無い" >&2; exit 1; }
[ -f out/play/check-game/chiiku/items.json ] || { echo "FAIL: out/play/check-game/chiiku/items.json が無い" >&2; exit 1; }
if grep -rIl 'chiiku-template-slug\|__TITLE__\|__DATE__' . --exclude-dir=node_modules --exclude-dir=.git > "$log"; then
  echo "FAIL: 置き換え用の文字が残っている:" >&2
  cat "$log" >&2
  exit 1
fi

echo "ok"
