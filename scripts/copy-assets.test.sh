#!/usr/bin/env bash
# copy-assets.sh の確認。手元に作った偽の ankardo（shared-assets/chiiku を持つ git リポジトリ）と偽のゲームを使う。
#   ./scripts/copy-assets.test.sh
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
fail() { echo "FAIL $*" >&2; exit 1; }
snapshot() { (cd "$1" && find . -type f -exec md5sum {} + | sort); }
commit_all() { git -C "$1" add -A && git -C "$1" -c user.name=test -c user.email=test@example.com commit -q -m "$2"; }

# 偽の ankardo: shared-assets/chiiku に、一覧・絵・声・鳴き声・クレジットを置いてコミットする
root="$work/ankardo"
git init -q -b main "$root"
mkdir -p "$root/shared-assets/chiiku/img" "$root/shared-assets/chiiku/voice" "$root/shared-assets/chiiku/cry"
printf '{"items":[]}\n' > "$root/shared-assets/chiiku/items.json"
printf 'webp' > "$root/shared-assets/chiiku/img/dog.webp"
printf 'wav-voice' > "$root/shared-assets/chiiku/voice/dog.wav"
printf 'wav-cry' > "$root/shared-assets/chiiku/cry/dog.wav"
printf '# credits\n' > "$root/shared-assets/chiiku/CREDITS.md"
commit_all "$root" init
commit="$(git -C "$root" rev-parse HEAD)"
export ANKARDO_ROOT="$root"

game="$work/game"
mkdir "$game"
git init -q -b main "$game"
printf 'x\n' > "$game/README.md"
commit_all "$game" game-init
game_commits="$(git -C "$game" rev-list --count HEAD)"

# 1. 全部のファイルが、そのままの中身で public/chiiku/ に入る
"$here/copy-assets.sh" chiiku "$game" > /dev/null
dest="$game/public/chiiku"
expected="$(cd "$root/shared-assets/chiiku" && find . -type f | sort)"
actual="$(cd "$dest" && find . -type f | sort)"
[ "$expected" = "$actual" ] || fail "copies all files: file list differs: $actual"
for f in items.json img/dog.webp voice/dog.wav cry/dog.wav CREDITS.md; do
  cmp -s "$root/shared-assets/chiiku/$f" "$dest/$f" || fail "copies all files: $f differs"
done

# 2. コピーし直すと、コピー先に余分に置いたファイルと、コピー元から消えたファイルが消える
printf 'stale' > "$dest/img/old.webp"
printf 'stale' > "$dest/extra.txt"
git -C "$root" rm -q shared-assets/chiiku/cry/dog.wav
commit_all "$root" remove-cry
"$here/copy-assets.sh" chiiku "$game" > /dev/null
[ ! -e "$dest/img/old.webp" ] || fail "removed files disappear on recopy: img/old.webp stayed"
[ ! -e "$dest/extra.txt" ] || fail "removed files disappear on recopy: extra.txt stayed"
[ ! -e "$dest/cry/dog.wav" ] || fail "removed files disappear on recopy: cry/dog.wav stayed"
[ -f "$dest/img/dog.webp" ] || fail "recopy lost img/dog.webp"
commit="$(git -C "$root" rev-parse HEAD)"

# 3. chiiku-assets.md に、コピー元の commit と日が書かれる
note="$game/chiiku-assets.md"
[ -f "$note" ] || fail "writes upstream note: chiiku-assets.md missing"
grep -q "$commit" "$note" || fail "writes upstream note: commit missing"
grep -q "$(date +%F)" "$note" || fail "writes upstream note: date missing"
if grep -q "${commit}+dirty" "$note"; then fail "writes upstream note: +dirty on a clean tree"; fi

# 4. shared-assets/chiiku に未コミットの変更があれば +dirty が付く
printf 'changed' > "$root/shared-assets/chiiku/img/dog.webp"
"$here/copy-assets.sh" chiiku "$game" > /dev/null
grep -q "$commit+dirty" "$note" || fail "writes upstream note: +dirty missing for an uncommitted change"
cmp -s "$root/shared-assets/chiiku/img/dog.webp" "$dest/img/dog.webp" || fail "dirty copy did not copy the working tree"
git -C "$root" checkout -q -- shared-assets/chiiku/img/dog.webp

# 5. 知らない名前は終了コード 2、無いゲームのフォルダは終了コード 1
set +e
"$here/copy-assets.sh" nope "$game" 2> /dev/null; code=$?
[ "$code" = 2 ] || fail "rejects unknown set: exit code $code"
"$here/copy-assets.sh" chiiku "$work/missing" 2> /dev/null; code=$?
[ "$code" = 1 ] || fail "rejects missing game dir: exit code $code"
"$here/copy-assets.sh" 2> /dev/null; code=$?
[ "$code" = 2 ] || fail "no argument: exit code $code"
set -e

# 6. コピー元が無いなどで失敗したときは、前のコピーを壊さない
before="$(snapshot "$dest")"
empty="$work/empty-ankardo"
git init -q -b main "$empty"
if ANKARDO_ROOT="$empty" "$here/copy-assets.sh" chiiku "$game" 2> /dev/null; then fail "failure keeps old copy: missing source accepted"; fi
[ "$before" = "$(snapshot "$dest")" ] || fail "failure keeps old copy: files changed"
leftover="$(find "$game" -maxdepth 2 -name '.copy-assets.*')"
[ -z "$leftover" ] || fail "left a work folder behind: $leftover"

# 7. ゲームのリポジトリにコミットしない
[ "$game_commits" = "$(git -C "$game" rev-list --count HEAD)" ] || fail "copy-assets.sh committed"

# 8. 呼び出し元の GIT_DIR（git のフックの中などで入る）に引きずられず、ankardo の commit を読む
decoy="$work/decoy"
git init -q -b main "$decoy"
git -C "$decoy" -c user.name=test -c user.email=test@example.com commit -q --allow-empty -m decoy
other="$work/other"
mkdir "$other"
GIT_DIR="$decoy/.git" GIT_WORK_TREE="$decoy" "$here/copy-assets.sh" chiiku "$other" > /dev/null 2>&1 || fail "failed with GIT_DIR set"
grep -q "$commit" "$other/chiiku-assets.md" || fail "records another repository's commit"

echo "OK copy-assets"
