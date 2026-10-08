#!/bin/sh
# Check the committed fonts and install the TDS package into a temporary tree.
set -eu
cd "$(dirname "$0")"
MILLS8A_CHECK_PYTHON=${MILLS8A_CHECK_PYTHON:-python3}
"$MILLS8A_CHECK_PYTHON" -m unittest discover -s revival -v
"$MILLS8A_CHECK_PYTHON" revival/check_fonts.py --strict
./make-tds.sh
MILLS8A_CHECK_TMP=$(mktemp -d)
trap 'rm -rf "$MILLS8A_CHECK_TMP"' EXIT HUP INT TERM
export TEXMFHOME="$MILLS8A_CHECK_TMP/texmf"
export TEXMFCACHE="$MILLS8A_CHECK_TMP/lua/cache"
mkdir -p "$TEXMFHOME" "$MILLS8A_CHECK_TMP/pdf" "$TEXMFCACHE"
unzip -q mills8a.tds.zip -d "$TEXMFHOME"
for engine in pdflatex lualatex; do
    if [ "$engine" = pdflatex ]; then output=pdf; else output=lua; fi
    if ! "$engine" -interaction=nonstopmode -halt-on-error \
        -output-directory="$MILLS8A_CHECK_TMP/$output" tex/font-regression.tex \
        > "$MILLS8A_CHECK_TMP/$output/console.log" 2>&1; then
        cat "$MILLS8A_CHECK_TMP/$output/console.log" >&2
        exit 1
    fi
    if rg -n 'Missing character|Font shape .* undefined' \
        "$MILLS8A_CHECK_TMP/$output/font-regression.log"; then
        exit 1
    fi
    pdffonts "$MILLS8A_CHECK_TMP/$output/font-regression.pdf"
    pdffonts "$MILLS8A_CHECK_TMP/$output/font-regression.pdf" | rg -q Mills8A
done
rg -q 'MILLS-SMALLCAPS9: m8ar9cj8t' "$MILLS8A_CHECK_TMP/pdf/font-regression.log"
rg -q 'MILLS-BOLD-SMALLCAPS: m8abcj8t' "$MILLS8A_CHECK_TMP/pdf/font-regression.log"
echo 'Font regressions, pdfLaTeX and LuaLaTeX passed.'
