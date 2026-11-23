#!/usr/bin/env bash
# copy-forge.sh の確認。ネットワークは使わず、手元に作った forge の代わりのリポジトリからコピーする。
#   ./scripts/copy-forge.test.sh
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
fail() { echo "FAIL $*" >&2; exit 1; }
snapshot() { (cd "$1" && find . -type f -exec md5sum {} + | sort); }

# forge の代わり: 管理下のファイル（HANDOVER.md と docs/superpowers/ を含む）と、管理外の build/
src="$work/forge"
git init -q -b main "$src"
mkdir -p "$src/tools" "$src/docs/superpowers/specs"
printf 'print("hi")\n' > "$src/tools/render.py"
printf '# handover\n' > "$src/HANDOVER.md"
printf '# spec\n' > "$src/docs/superpowers/specs/x.md"
printf 'build/\n' > "$src/.gitignore"
git -C "$src" add .
git -C "$src" -c user.name=test -c user.email=test@example.com commit -q -m init
mkdir -p "$src/build"
printf 'x' > "$src/build/junk.png"
commit="$(git -C "$src" rev-parse HEAD)"

game="$work/game"
mkdir "$game"
export FORGE_URL="file://$src"

# 1. pixel は、管理下のファイルだけが、そのままの中身で入る（HANDOVER.md と docs/superpowers/ も入る）
"$here/copy-forge.sh" pixel "$game" > /dev/null
dest="$game/pixel-asset-forge"
expected="$(git -C "$src" ls-files | sort)"
actual="$(cd "$dest" && find . -type f ! -name UPSTREAM.md | sed 's|^\./||' | sort)"
[ "$expected" = "$actual" ] || fail "file list differs: $actual"
cmp -s "$src/tools/render.py" "$dest/tools/render.py" || fail "tools/render.py differs"
[ -f "$dest/HANDOVER.md" ] || fail "pixel did not copy HANDOVER.md"
[ ! -e "$dest/build" ] || fail "build/ was copied"
[ ! -e "$dest/.git" ] || fail ".git was copied"

# 2. UPSTREAM.md にコピー元と commit が入る
grep -q "$commit" "$dest/UPSTREAM.md" || fail "UPSTREAM.md lacks the commit"
grep -q "$FORGE_URL" "$dest/UPSTREAM.md" || fail "UPSTREAM.md lacks the source"
grep -q "pixel-asset-forge のコピー" "$dest/UPSTREAM.md" || fail "UPSTREAM.md lacks the forge name"
grep -q "## forge に戻す候補" "$dest/UPSTREAM.md" || fail "UPSTREAM.md lacks the candidate section"

# 3. 既にあるときは止まり、中身が変わらない
before="$(snapshot "$dest")"
if "$here/copy-forge.sh" pixel "$game" 2> /dev/null; then fail "second run succeeded"; fi
[ "$before" = "$(snapshot "$dest")" ] || fail "second run changed files"

# 4. 取得に失敗したときは、pixel-asset-forge/ を残さない
other="$work/other"
mkdir "$other"
if FORGE_URL="file://$work/nope" "$here/copy-forge.sh" pixel "$other" 2> /dev/null; then fail "bad source accepted"; fi
[ ! -e "$other/pixel-asset-forge" ] || fail "left pixel-asset-forge/ behind after a failure"

# 5. 一時フォルダはゲームリポジトリの中に作る（/tmp と別のファイルシステムでも mv が一度に移るように）
#    TMPDIR を使えない場所にしても成功し、作業用のフォルダを残さない
third="$work/third"
mkdir "$third"
TMPDIR="$work/no-such-dir" "$here/copy-forge.sh" pixel "$third" > /dev/null || fail "depends on TMPDIR"
[ -f "$third/pixel-asset-forge/UPSTREAM.md" ] || fail "copy missing when TMPDIR is unusable"
leftover="$(find "$third" -maxdepth 1 -name '.copy-forge.*')"
[ -z "$leftover" ] || fail "left a work folder behind: $leftover"

# 6. 呼び出し元の GIT_DIR（git のフックの中などで入る）に引きずられず、forge を読む
decoy="$work/decoy"
git init -q -b main "$decoy"
git -C "$decoy" -c user.name=test -c user.email=test@example.com commit -q --allow-empty -m decoy
fourth="$work/fourth"
mkdir "$fourth"
GIT_DIR="$decoy/.git" GIT_WORK_TREE="$decoy" "$here/copy-forge.sh" pixel "$fourth" > /dev/null 2>&1 || fail "failed with GIT_DIR set"
grep -q "$commit" "$fourth/pixel-asset-forge/UPSTREAM.md" || fail "UPSTREAM.md records another repository's commit"
cmp -s "$src/tools/render.py" "$fourth/pixel-asset-forge/tools/render.py" || fail "copied another repository's files"

# 7. 引数が足りない・フォルダが無いときは止まる
if "$here/copy-forge.sh" 2> /dev/null; then fail "no argument accepted"; fi
if "$here/copy-forge.sh" pixel 2> /dev/null; then fail "missing game path accepted"; fi
if "$here/copy-forge.sh" pixel "$work/missing" 2> /dev/null; then fail "missing folder accepted"; fi

# 8. illust は illust-asset-forge/ にコピーし、HANDOVER.md と docs/superpowers/ を持ち込まない
"$here/copy-forge.sh" illust "$game" > /dev/null
idest="$game/illust-asset-forge"
[ -f "$idest/tools/render.py" ] || fail "illust copy missing files"
[ ! -e "$idest/HANDOVER.md" ] || fail "illust copied HANDOVER.md"
[ ! -e "$idest/docs/superpowers" ] || fail "illust copied docs/superpowers"
[ ! -e "$idest/.git" ] || fail "illust copied .git"
grep -q "illust-asset-forge のコピー" "$idest/UPSTREAM.md" || fail "UPSTREAM.md names another forge"
grep -q "$commit" "$idest/UPSTREAM.md" || fail "illust UPSTREAM.md lacks the commit"
grep -q "illust-asset-forge/UPSTREAM.md" "$idest/UPSTREAM.md" || fail "illust UPSTREAM.md diff command has another path"
[ -d "$game/pixel-asset-forge" ] || fail "illust removed the pixel copy"

# 9. forge の名前が無い・違うときは止まり、何も作らない
if "$here/copy-forge.sh" "$other" 2> /dev/null; then fail "missing forge name accepted"; fi
if "$here/copy-forge.sh" voxel "$other" 2> /dev/null; then fail "unknown forge accepted"; fi
[ -z "$(ls -A "$other")" ] || fail "left files after a bad forge name"

echo "ok"
