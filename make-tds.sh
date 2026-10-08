#!/bin/sh
# Assemble the installable TeX Directory Structure (TDS) tree of Mills 8A in
# build/tds/ and zip it as mills8a.tds.zip (the layout CTAN distributes).
#   ./make-tds.sh
# The fonts must be built (revival/build.sh) and the specimen rendered
# (./render.sh); this only copies and zips.
set -e
cd "$(dirname "$0")"
P=revival/pdftex
T=build/tds
rm -rf "$T"
d() { mkdir -p "$T/$1"; }
d tex/latex/mills8a;            cp $P/tex/mills8a.sty $P/tex/*.fd "$T/tex/latex/mills8a/"
d tex/lualatex/mills8a;         cp tex/mills8a-jitter.lua "$T/tex/lualatex/mills8a/"
d fonts/tfm/public/mills8a;     cp $P/fonts/*.tfm "$T/fonts/tfm/public/mills8a/"
d fonts/vf/public/mills8a;      cp $P/fonts/*.vf "$T/fonts/vf/public/mills8a/"
d fonts/type1/public/mills8a;   cp $P/fonts/*.pfb "$T/fonts/type1/public/mills8a/"
d fonts/enc/dvips/mills8a;      cp $P/fonts/*.enc "$T/fonts/enc/dvips/mills8a/"
d fonts/map/dvips/mills8a;      cp $P/fonts/mills8a.map "$T/fonts/map/dvips/mills8a/"
d fonts/opentype/public/mills8a; cp revival/fonts/*.otf "$T/fonts/opentype/public/mills8a/"
d doc/fonts/mills8a
cp README.md VERSION "$T/doc/fonts/mills8a/"
cp LICENSE GUST-FONT-LICENSE.txt "$T/doc/fonts/mills8a/"
for f in mills-specimen-a4.pdf mills-specimen-letter.pdf mills-8a.pdf; do
  [ -f "$f" ] && cp "$f" "$T/doc/fonts/mills8a/"
done
cp tex/mills.tex tex/specimen.tex "$T/doc/fonts/mills8a/"
cp proof/math-alphabets.tex "$T/doc/fonts/mills8a/"
cp proof/math-rules.tex "$T/doc/fonts/mills8a/"
cp proof/math-alphabets.pdf proof/math-rules.pdf "$T/doc/fonts/mills8a/"
cp proof/alphabet-macros.tex proof/font-alphabets.tex "$T/doc/fonts/mills8a/"
rm -f mills8a.tds.zip
(cd "$T" && zip -qr ../../mills8a.tds.zip .)
echo "mills8a.tds.zip: $(cd "$T" && find . -type f | wc -l) files, version $(cat VERSION)"
