#!/bin/sh
# Rebuild the Mills 8A fonts from the scans.
#   scans/*.pdf              1947 Bulletin AMS articles (600 dpi), see README
#   scans/lanston1922-p49.jp2  from ./fetch-specimen.sh
set -e
cd "$(dirname "$0")"
mkdir -p work fonts
python3 segment.py        # glyph instances + OCR guesses
python3 baselines.py      # robust per-line baselines
python3 docweight.py      # type size and stroke weight of each scan vs. the Erdős paper
python3 cluster.py        # group identical sorts
python3 classify.py       # slant / weight / size measurements
python3 assign.py         # labels: rules + overrides.tsv
python3 boldwords.py      # which impressions are bold: title lines and run-in heads
python3 masters.py        # average each sort at 4x
python3 oldstyle.py       # old-style figures from the years in the Bulletin running heads
python3 specimen.py       # 1922 alphabets for missing letters
python3 build_font.py     # trace, space, assemble fonts/*.otf
python3 accents.py        # accented letters, dotless i/j, punctuation fills
python3 build_math.py     # Mills8A-Math.otf: 1947 letters and script sorts on Latin Modern Math
python3 build_sizes.py    # Mills8A-Bold.otf, Mills8A-{Regular,Italic}9.otf
python3 finish_fonts.py   # final glyph bounds and OpenType metadata
python3 optimize_fonts.py # share repeated CFF outline programs without changing ink
python3 pdftex/build_pdftex.py   # the same fonts as Type 1 + TFM for pdfLaTeX
