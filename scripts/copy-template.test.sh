#!/usr/bin/env bash
# copy-template.sh の確認。ネットワークは使わず、手元に作った偽のひな形と偽の preview.yml からコピーする。
#   ./scripts/copy-template.test.sh
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
fail() { echo "FAIL $*" >&2; exit 1; }
snapshot() { (cd "$1" && find . -mindepth 1 | sort; find . -type f -exec md5sum {} + | sort); }

# 偽のひな形: 置き換え用の 3 つの文字を含むテキストと、含まないバイナリ。管理外の node_modules/ も置く
repo="$work/repo"
git init -q -b main "$repo"
tpl="$repo/templates/chiiku-game"
mkdir -p "$tpl/src" "$tpl/.github/workflows" "$tpl/img" "$tpl/dir with space"
printf '{"name":"chiiku-template-slug","title":"__TITLE__"}\n' > "$tpl/package.json"
printf '<title>__TITLE__</title>\n' > "$tpl/index.html"
printf 'const t = "__TITLE__"; // chiiku-template-slug\n' > "$tpl/src/main.ts"
printf 'compatibility_date = "__DATE__"\n' > "$tpl/wrangler.toml"
printf 'name: deploy chiiku-template-slug\n' > "$tpl/.github/workflows/deploy.yml"
printf 'chiiku-template-slug __TITLE__ __DATE__\n' > "$tpl/dir with space/note.md"
printf '\000\001chiiku-template-slug\377\000' > "$tpl/img/blob.bin"
: > "$tpl/empty.txt"
printf 'node_modules/\n' > "$repo/.gitignore"
git -C "$repo" add .
git -C "$repo" -c user.name=test -c user.email=test@example.com commit -q -m init
mkdir -p "$tpl/node_modules/x"
printf 'x' > "$tpl/node_modules/x/junk.js"
commit="$(git -C "$repo" rev-parse HEAD)"
today="$(date +%F)"

preview="$work/preview.yml"
printf 'name: preview\non: push\n' > "$preview"

export TEMPLATE_ROOT="$repo/templates"
export PREVIEW_TEMPLATE="$preview"

new_game() { mkdir "$1"; git init -q -b main "$1"; }

# 1. .git だけのフォルダへ写すと、ファイルが全部入り、置き換え用の文字が残らない
g1="$work/g1"
new_game "$g1"
out="$("$here/copy-template.sh" chiiku-game my-game 'どれかな？' "$g1")" || fail "copy failed"
case "$out" in コピーした:*"$commit"*) ;; *) fail "unexpected output: $out" ;; esac
for f in package.json index.html src/main.ts wrangler.toml .github/workflows/deploy.yml "dir with space/note.md" img/blob.bin empty.txt; do
  [ -f "$g1/$f" ] || fail "missing $f"
done
[ ! -e "$g1/node_modules" ] || fail "copied node_modules"
if grep -rIq 'chiiku-template-slug\|__TITLE__\|__DATE__' "$g1" --exclude-dir=.git; then fail "placeholder left behind"; fi
grep -q '"name":"my-game"' "$g1/package.json" || fail "slug not replaced"
grep -q '<title>どれかな？</title>' "$g1/index.html" || fail "title not replaced"
grep -q "compatibility_date = \"$today\"" "$g1/wrangler.toml" || fail "date not replaced"
[ -z "$(find "$g1" -maxdepth 1 -name '.copy-template.*')" ] || fail "left a work folder behind"

# 2. preview.yml は元とバイト単位で同じ。バイナリも元と同じ
cmp -s "$preview" "$g1/.github/workflows/preview.yml" || fail "preview.yml differs"
cmp -s "$tpl/img/blob.bin" "$g1/img/blob.bin" || fail "binary was changed"

# 3. template.md に commit と日付。未コミットの変更があると +dirty
grep -q "$commit" "$g1/template.md" || fail "template.md lacks the commit"
grep -q "$today" "$g1/template.md" || fail "template.md lacks the date"
if grep -q 'dirty' "$g1/template.md"; then fail "clean template marked dirty"; fi
printf '// edit\n' >> "$tpl/src/main.ts"
g3="$work/g3"
new_game "$g3"
"$here/copy-template.sh" chiiku-game my-game 'x' "$g3" > /dev/null || fail "dirty copy failed"
grep -q "$commit+dirty" "$g3/template.md" || fail "dirty not marked"
git -C "$repo" checkout -q -- templates/chiiku-game/src/main.ts

# 4. .git 以外のファイルがあると、終了コード 1 で何も増えない
g4="$work/g4"
new_game "$g4"
printf '# readme\n' > "$g4/README.md"
before="$(snapshot "$g4")"
set +e
"$here/copy-template.sh" chiiku-game my-game 'x' "$g4" 2> /dev/null
rc=$?
set -e
[ "$rc" = 1 ] || fail "non-empty destination exit $rc"
[ "$before" = "$(snapshot "$g4")" ] || fail "non-empty destination was changed"

# 5. 引数の誤りは終了コード 2 で、何も増えない
g5="$work/g5"
new_game "$g5"
before="$(snapshot "$g5")"
expect2() {
  set +e
  "$here/copy-template.sh" "$@" 2> /dev/null
  rc=$?
  set -e
  [ "$rc" = 2 ] || fail "expected exit 2, got $rc: $*"
  [ "$before" = "$(snapshot "$g5")" ] || fail "changed files: $*"
}
long43="$(printf 'a%.0s' $(seq 1 43))"
long42="$(printf 'a%.0s' $(seq 1 42))"
for bad in Bad -x x- a--b a_b "$long43" ''; do
  expect2 chiiku-game "$bad" 'ok' "$g5"
done
for bad in '' 'a<b' 'a&b' "a'b" 'a"b' 'a\b' $'a\nb' $'a\rb'; do
  expect2 chiiku-game ok "$bad" "$g5"
done
expect2 other-game ok 'ok' "$g5"
expect2 chiiku-game ok "$g5"
expect2 chiiku-game ok 'ok' "$g5" extra
expect2
# 42 文字ちょうどは通る
g5b="$work/g5b"
new_game "$g5b"
"$here/copy-template.sh" chiiku-game "$long42" 'ok' "$g5b" > /dev/null || fail "42-character slug rejected"

# 6. 呼び出し元の GIT_DIR に引きずられず、ひな形のあるリポジトリの commit を書く
decoy="$work/decoy"
git init -q -b main "$decoy"
git -C "$decoy" -c user.name=test -c user.email=test@example.com commit -q --allow-empty -m decoy
g6="$work/g6"
new_game "$g6"
GIT_DIR="$decoy/.git" GIT_WORK_TREE="$decoy" "$here/copy-template.sh" chiiku-game my-game 'x' "$g6" > /dev/null 2>&1 || fail "failed with GIT_DIR set"
grep -q "$commit" "$g6/template.md" || fail "template.md records another repository's commit"
[ -f "$g6/index.html" ] || fail "copied another repository's files"

# 7. 写し先が無いフォルダなら終了コード 1
set +e
"$here/copy-template.sh" chiiku-game my-game 'x' "$work/missing" 2> /dev/null
rc=$?
set -e
[ "$rc" = 1 ] || fail "missing destination exit $rc"

# 8. 題の中の置き換え用の文字は、そのまま題になる（置き換えの結果をもう一度置き換えない）。空白だけの題は止まる
g8="$work/g8"
new_game "$g8"
"$here/copy-template.sh" chiiku-game my-game 'x__DATE__y' "$g8" > /dev/null || fail "title with __DATE__ rejected"
grep -q '<title>x__DATE__y</title>' "$g8/index.html" || fail "title containing a placeholder was rewritten"
g8b="$work/g8b"
new_game "$g8b"
before="$(snapshot "$g8b")"
set +e
"$here/copy-template.sh" chiiku-game my-game '   ' "$g8b" 2> /dev/null
rc=$?
set -e
[ "$rc" = 2 ] || fail "blank title exit $rc"
[ "$before" = "$(snapshot "$g8b")" ] || fail "blank title changed files"

# 9. 日付は UTC（手元の時刻帯で、UTC より先の日付にならないように）
g9="$work/g9"
new_game "$g9"
TZ=Pacific/Kiritimati "$here/copy-template.sh" chiiku-game my-game 'x' "$g9" > /dev/null || fail "tz copy failed"
utc="$(date -u +%F)"
grep -q "compatibility_date = \"$utc\"" "$g9/wrangler.toml" || fail "date is not UTC ($utc)"

# 10. 写し先の中身が読めないときは、確かめられないので、何も書かずに止まる（既存のファイルを上書きしない）
if [ "$(id -u)" != 0 ]; then
  g10="$work/g10"
  new_game "$g10"
  printf 'MINE\n' > "$g10/README.md"
  chmod 300 "$g10"
  set +e
  "$here/copy-template.sh" chiiku-game my-game 'x' "$g10" 2> /dev/null
  rc=$?
  set -e
  chmod 700 "$g10"
  [ "$rc" = 1 ] || fail "unreadable destination exit $rc"
  [ "$(cat "$g10/README.md")" = "MINE" ] || fail "unreadable destination: README.md was overwritten"
fi

# 11. UTF-8 として読めないテキストがひな形にあるときは、どのファイルかを示して、何も書かずに止まる
repo2="$work/repo2"
git init -q -b main "$repo2"
mkdir -p "$repo2/templates/chiiku-game"
printf '__TITLE__\n' > "$repo2/templates/chiiku-game/ok.txt"
printf 'caf\351 __TITLE__\n' > "$repo2/templates/chiiku-game/latin1.txt"
git -C "$repo2" add .
git -C "$repo2" -c user.name=test -c user.email=test@example.com commit -q -m init
g11="$work/g11"
new_game "$g11"
before="$(snapshot "$g11")"
set +e
err="$(TEMPLATE_ROOT="$repo2/templates" "$here/copy-template.sh" chiiku-game my-game 'x' "$g11" 2>&1)"
rc=$?
set -e
[ "$rc" = 1 ] || fail "non-UTF-8 template file exit $rc"
case "$err" in *latin1.txt*) ;; *) fail "error does not name the file: $err" ;; esac
[ "$before" = "$(snapshot "$g11")" ] || fail "non-UTF-8 template file changed files"

echo "ok"
