#!/usr/bin/env bash
set -e

# usage: ./generate_project.sh --lang js --size 10 --complexity 5 --out ./data/demo_js
LANG="js"
SIZE=1000
COMPLEXITY=1000
OUT_DIR="./data/demo_js"

while [[ $# -gt 0 ]]; do
  case $1 in
    --lang) LANG="$2"; shift 2;;
    --size) SIZE="$2"; shift 2;;
    --complexity) COMPLEXITY="$2"; shift 2;;
    --out) OUT_DIR="$2"; shift 2;;
    *) echo "Unknown argument: $1"; exit 1;;
  esac
done

if [[ "$LANG" != "ts" && "$LANG" != "js" ]]; then
  echo "Unsupported language: $LANG (supported: ts, js)"
  exit 1
fi

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR/src"

EXT="$LANG"  

for ((f=1; f<=SIZE; f++)); do
  FILE="$OUT_DIR/src/file_$f.$EXT"
  echo "// Auto-generated $LANG file $f" > "$FILE"
  echo "export function func$f() {" >> "$FILE"

  for ((c=1; c<=COMPLEXITY; c++)); do
    echo "  const obj$c = { a: $RANDOM, b: $RANDOM, c: $RANDOM };" >> "$FILE"
    echo "  for (let i$c = 0; i$c < $COMPLEXITY; i$c++) {" >> "$FILE"
    echo "    for (let j$c = 0; j$c < $COMPLEXITY; j$c++) {" >> "$FILE"
    echo "      const tmp$c = i$c + j$c + obj$c.a + obj$c.b + obj$c.c;" >> "$FILE"
    echo "    }" >> "$FILE"
    echo "  }" >> "$FILE"
  done

  echo "}" >> "$FILE"
done

ENTRY_FILE="$OUT_DIR/src/entry.$EXT"
echo "// Entry file for $LANG benchmark" > "$ENTRY_FILE"
for ((f=1; f<=SIZE; f++)); do
  echo "export * from './file_$f';" >> "$ENTRY_FILE"
done

echo "Generated $SIZE $LANG files with complexity $COMPLEXITY in $OUT_DIR/src (entry.$EXT created)"
