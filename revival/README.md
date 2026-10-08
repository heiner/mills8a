# Mills 8A: a revival of Monotype Modern 8A from 1947 scans

A font family traced from the type of the *Bulletin of the AMS*, 1947,
which was 11 pt Monotype Modern 8A on 12 pt leading. Nothing is drawn by
hand: every master glyph is the average of the copies of that sort found on
the page scans, and the spacing is measured from the text.

![comparison](../docs/comparison.png)

| font | what it is |
|---|---|
| `Mills8A-Regular.otf` | 11 pt roman, figures, punctuation, small caps (`smcp`), f-ligatures (`liga`), random impressions (`rand`) |
| `Mills8A-Italic.otf` | 11 pt italic and Greek, f-ligatures, `rand` |
| `Mills8A-Math.otf` | OpenType MATH font: the letters, figures, operators and **real script sorts** for indices, on Latin Modern Math |
| `Mills8A-Bold.otf` | bold, from the 1947 title capitals |
| `Mills8A-BoldItalic.otf` | bold italic: the italic thickened to the bold stems (synthesized) |
| `Mills8A-Regular9.otf`, `Mills8A-Italic9.otf` | 9 pt cut for footnotes and references |

## Using it (pdfLaTeX)

`pdftex/` has the family as standard pdfLaTeX fonts: Type 1 outlines,
TFM metrics, virtual fonts, `.fd` files and a map file.

```latex
\usepackage{mills8a}        % T1 text, small caps, bold, 9pt, and math
```

with `pdftex/tex` on `TEXINPUTS` and `pdftex/fonts` on `TFMFONTS`, `VFFONTS`,
`T1FONTS`, `ENCFONTS` and `TEXFONTMAPS` (see `render.sh`).

The f-ligatures are in the TFM ligature tables (`otftotfm`), and small
caps are a separate font. Math uses one font per family and size, as TeX
always has: operators, math italic and symbols each come at 11 pt, 6.48 pt and
5.51 pt. The script fonts are cut from `Mills8A-Math.otf`'s script variants,
so **the real 1947 script sorts work in pdfLaTeX too**, the way `cmmi7` and
`cmmi5` always did. The TeX math parameters (script shifts and so on) are
the symbol font's fontdimens; `mills.tex` sets the Mills display
superscript shift with `\fontdimen13\textfont2`.

Second-order indices (the exponent of an exponent) are set as on the Mills
page: in the first-order size, not 5.5 pt (the 1947 x of `[A^{3^x}]` is
0.68 of its 3, about the ratio within one size), and raised 0.52 em of
the index font, its foot 28 px above the 3's at 600 dpi as printed
(ours: 28-29 px). The flat "3−n" of the Mills displays is how the source
writes them, as printed.

Compared with the OpenType fonts (below) it lacks

- random impressions: every letter is its averaged master;
- the baseline wobble;
- nothing in big operators: the virtual font `m8aex` is `cmex10` with the
  1947 text ∑ and display ∑ and ∏ put in its slots (delimiters and the
  other big operators stay Computer Modern's).

Measured on the Mills page, both versions have the same darkness as the scan
(ratio 1.01–1.02) and the same script sorts. The text width matches the scan
within 0.2% (an unjustified line, "where *K* is a fixed positive integer.",
is 0.518 of the measure in both); line breaks still differ in places, as
TeX justifies differently from the 1947 compositor.

### Old-style figures

`\usepackage[osf]{mills8a}` (family `m8aj`); in LuaLaTeX
`Numbers=OldStyle` (the `onum` feature). All ten are 1940s sorts from the
Bulletin's running heads; math keeps lining figures, as in print.

### The OpenType fonts (LuaLaTeX)

An extra; the difference from the pdfLaTeX fonts is slight.

```latex
\usepackage{unicode-math}
\setmainfont{Mills8A-Regular.otf}[RawFeature=+rand,
  SizeFeatures={{Size=-10, Font=Mills8A-Regular9.otf}, {Size=10-}},
  SmallCapsFont=Mills8A-Regular.otf, SmallCapsFeatures={RawFeature=+smcp},
  ItalicFont=Mills8A-Italic.otf,
  ItalicFeatures={SizeFeatures={{Size=-10, Font=Mills8A-Italic9.otf}, {Size=10-}}},
  BoldFont=Mills8A-Bold.otf]
\setmathfont{Mills8A-Math.otf}
\DeclareMathSizes{11}{11}{6.48}{5.51}   % the measured script sizes
\directlua{require("mills8a-jitter").enable(0.04, 1947)}   % optional, tex/
```

Set it 11 on 12 pt. `tex/mills.tex` (run with LuaLaTeX) is a complete example. It
also sets the Mills paper's display-style script positions and fixed
leading (see *Scripts* below).

LuaLaTeX is needed for the randomness: XeLaTeX loads the fonts, but its
HarfBuzz shaping gives every repeat of a word the same impressions.

The text fonts include zero-advance combining grave, acute, circumflex,
tilde, macron, breve, dot, dieresis, ring, double acute, caron, cedilla and
ogonek marks, with `mark` and `mkmk` positioning. Common European letters
missing from the scans, the euro and trademark signs come from Latin Modern,
scaled to the corresponding style's x-height or cap height. This extends
coverage without claiming a historical source for those additions. Nonbreaking
spaces and hyphens have explicit Unicode mappings. Kerning remains absent.
Roman, bold and the 9 pt roman cut expose `smcp`, including accented letters
and Æ/Œ/Ø/Ł counterparts. Accented small caps use the existing small-cap
letters and accents; missing special forms use scaled capitals. Small-cap ß
uses two small-cap S letters.

`python3 finish_fonts.py` reapplies the Unicode supplements, OpenType features
and clipping-metric repairs to the committed fonts without rebuilding the scan
pipeline. It also runs automatically in `build.sh`. Font regression checks:

```sh
python3 -m unittest discover -s revival -v  # from the repository root
```

Install the Python tools with `python3 -m pip install -r revival/requirements.txt`.
Finishing also requires the Latin Modern OpenType fonts supplied by TeX Live.

`python3 revival/optimize_fonts.py` shares repeated CFF outline programs;
the shipped OpenType fonts use this lossless optimization. It runs in
`build.sh` before the Type 1 conversion. Optional screen hints are available
with `--hint --output-dir build/hinted`. The hints use measured alignment
zones and stem widths. They can increase file size and are deliberately kept
as a separate export; the primary fonts preserve the unhinted print outlines.
The hinting tool rounds fractional outline coordinates to the nearest unit;
it leaves advances and OpenType layout features unchanged.

For websites or installations that do not need random impressions:

```sh
python3 revival/export_fonts.py  # from the repository root
```

`build/web/` contains the complete family as WOFF2. `build/compact/` contains
OTF and WOFF2 versions without `rand`, named **Mills 8A Compact** so they can
be installed alongside the complete family. Unicode coverage, ligatures,
small caps, old-style figures, combining marks and math features are retained.
Both directories include the font licences. The generated exports stay out
of Git; regenerate them from the committed fonts.

The pdfLaTeX conversion also omits unused random impressions. Its T1 package
selects the 9 pt small caps below 10 pt, supports bold small caps, and loads
the added euro and trademark signs through its symbol font.

Run `./verify.sh` from the root to test the fonts and install the TDS zip
into a temporary TeX tree, then typeset `tex/font-regression.tex` with
pdfLaTeX and LuaLaTeX. This requires TeX Live's LaTeX, LuaTeX and recommended
fonts packages, `poppler-utils`, ripgrep, and the Python requirements above.
Rebuilding the Type 1 files additionally requires `lcdf-typetools`.

## Sources

- `scans/erdos1947.pdf`: P. Erdős, *Some asymptotic formulas for
  multiplicative functions*, Bull. AMS 53 (1947). 9 pages.
- `scans/niven1947.pdf`: I. Niven, *A simple proof that π is irrational*,
  Bull. AMS 53 (1947). 1 page.
- `scans/post1944.pdf`: E. L. Post, *Recursively enumerable sets of positive
  integers and their decision problems*, Bull. AMS 50 (1944). 33 pages.
- `scans/doob1947.pdf`: J. L. Doob, *Probability in function space*, Bull.
  AMS 53 (1947). 16 pages.
- `scans/kac1947.pdf`: M. Kac, *On the notion of recurrence in discrete
  stochastic processes*, Bull. AMS 53 (1947). 9 pages.
- `scans/vonneumanngoldstine1947.pdf`: J. von Neumann and H. H. Goldstine,
  *Numerical inverting of matrices of high order*, Bull. AMS 53 (1947).
  79 pages.
- `scans/vonkarman1940.pdf`: Th. von Kármán, *The engineer grapples with
  nonlinear problems*, Bull. AMS 46 (1940). 69 pages.
- `scans/wright1942.pdf`: S. Wright, *Statistical genetics and evolution*,
  Bull. AMS 48 (1942). 24 pages.
- `scans/courant1943.pdf`: R. Courant, *Variational methods for the
  solution of problems of equilibrium and vibrations*, Bull. AMS 49 (1943).
  23 pages.
- `scans/feller1945.pdf`: W. Feller, *The fundamental limit theorems in
  probability*, Bull. AMS 51 (1945). 33 pages.
- `scans/lewy1946.pdf`: H. Lewy, *Water waves on sloping beaches*, Bull. AMS
  52 (1946). 39 pages.
- `scans/neugebauer1948.pdf`: O. Neugebauer, *Mathematical methods in
  ancient astronomy*, Bull. AMS 54 (1948). 29 pages.
- `scans/kleene1943.pdf`: S. C. Kleene, *Recursive predicates and
  quantifiers*, Trans. AMS 53 (1943). 33 pages.
- `scans/eilenbergmaclane1945.pdf`: S. Eilenberg and S. Mac Lane, *General
  theory of natural equivalences*, Trans. AMS 58 (1945). 64 pages.
- `scans/lanston1922-p49.jp2`, `-p51.jp2`: *The Monotype Specimen Book of
  Type Faces*, Lanston Monotype, 1922, pp. 49 and 51, "No. 8A" at 9, 10,
  11, 12, 14 and 18 pt. Public domain; get them with `./fetch-specimen.sh`.
- Latin Modern Math (GUST Font License), the base of `Mills8A-Math.otf`.

The AMS PDFs are 600 dpi bilevel scans (461 pages; the 1940-48 papers were
added for the old-style figures of their years). They're not in the
repository; put copies in `scans/` under these names.

## Building

The scans are not in the repository (see *Sources* above for the list). With
them in `scans/`:

    ./fetch-specimen.sh     # the 1922 specimen pages (public domain)
    ./build.sh              # the fonts
    ../render.sh            # the PDFs, proof sheets and the images in the top-level README

Requires TeX Live (pdfLaTeX, `lcdf-typetools`; LuaLaTeX for the OpenType example), Tesseract, potrace,
and Python 3 with numpy, scipy, Pillow and fontTools. The built fonts are
committed in `fonts/` and `pdftex/fonts/`.

## Pipeline (`./build.sh`, about 1 h 15 min on 4 cores; OCR and clustering are most of it)

| step | what it does |
|---|---|
| `segment.py` | connected components + Tesseract hOCR → ~440,000 glyph instances. Side-by-side pieces in one OCR box (a letter and its subscript) become separate instances |
| `baselines.py` | re-estimates each line's baseline from the letters sitting on it (display math throws Tesseract's off) |
| `docweight.py` | each scan's type size and stroke weight against the Erdős paper (ink-corrected widths and heights, and stroke widths, of the same letters). The *Transactions* type is ~3.5% smaller at the same 12 pt line pitch; Post's scan is ~0.5 px per edge heavier |
| `cluster.py` | groups baseline-aligned instances whose shapes overlap (IoU ≥ 0.72) |
| `classify.py` | measures slant, stroke weight and size; a letter's roman or italic style comes from comparing it with the reference fonts in `ref/` (built from the hand-checked first scans), since the slant measure takes the diagonals of a roman *v w y A V W X Y* for italic. Letters matching neither (×, Ω, Fraktur) are left to `overrides.tsv` |
| `assign.py` | labels each group (glyph, style, size): rules plus hand corrections in `overrides.tsv`, which name one impression per group (`page@x,y`, see `okey.py`) so re-clustering doesn't invalidate them |
| `masters.py` | upsamples every instance 4×, aligns to 1/4 px by FFT cross-correlation, resamples each scan to the Erdős size and weight, averages up to 400 impressions per sort; keeps up to 8 single impressions per sort for `rand` |
| `oldstyle.py` | old-style figures: the Bulletin sets the year in its running heads ("1947]") in old-style figures; 1940-1948 give all ten, averaged from 10-161 impressions each, scaled from the ~8 pt head to the text x-height and brought to the 11 pt stem |
| `check_fonts.py` | consistency checks over all fonts: baselines, x- and cap heights, side bearings, figure widths, script sorts against their text glyphs |
| `specimen.py` | cuts the 1922 alphabets at six sizes (659 impressions) |
| `build_font.py` | potrace outlines, fitted spacing, ligatures, CFF OpenType text fonts (fontTools) |
| `accents.py` | accented Latin-1 / Latin Extended-A letters, dotless *ı ȷ*, the missing punctuation |
| `build_math.py` | the MATH font |
| `build_sizes.py` | bold, bold italic and 9 pt |
| `pdftex/build_pdftex.py` | the family as Type 1 / TFM fonts for pdfLaTeX |

`scripts.py` is not part of the build: it proposes labels for script-size
groups by template matching (`work/scripts.png`), which were checked by eye
and entered in `overrides.tsv`.

## Measured facts about the 1947 type

- **Size:** 11 pt on 12 pt. The x-height is 0.40 em and the cap height
  0.61 em; the scans add about 2 px of ink spread per edge at 600 dpi.
- **Spacing:** Monotype never letterspaces within a word, so the distance
  between ink edges of neighbours is P[a] + L[b]. A least-squares fit over
  about 5,000 letter pairs leaves 0.85 px RMS. The advances land on a grid
  of **4.9 px ≈ 1/18 of a 10.6–10.7 pt set** (fitted independently for
  roman, italic and small caps), the Monotype unit system: e = 8, n = 10,
  m = 15, i = 5, w = 13 units.
- **No kerning:** of 145 frequent letter pairs, none deviates from the
  fitted spacing by more than 1.5 px (0.016 em, under a third of a unit), so
  the fonts have no kerning table, as Monotype had none.
- **Word space:** 6 units (a third of the set).
- **Scripts:** two levels. First-order indices and exponents are **58.9%**
  of the body, second-order **50.1%** (heights with ink spread removed).
  On the Erdős pages superscripts are raised 274 units and subscripts
  lowered 88; on the Mills page, displays raise exponents to cap height
  (0.66 em) and subscripts sit 0.14 em down. Compositors differed.
- **Baseline wobble:** impressions of flat-bottomed letters scatter by 1.0 px
  around their line (40% exactly on it, 87% within 1 px, 98% within 2 px),
  independently of their neighbours. The random impressions already give
  0.89 px; another 0.04 pt per glyph matches the rest.
- **The 1922 specimen** is set 11 on 12 too: each size calibrates to
  5.9–6.1 px/pt against the 1947 letters.

## What comes from where

- **1940–47 masters:** every 11 pt roman and italic letter and figure (the
  roman J from its 9 pt sort), the punctuation with the quotes ‘ ’ “ ”, the
  question mark and the en dash, ü á and italic ü Ü ä, 23 of 26 small caps, Greek *α β γ ζ η θ κ λ μ ν ξ π σ τ χ ψ ω ϕ ϵ*
  and Γ Δ Π Σ Φ Ω, ∮ ∨, + − × ÷ = ≠ ≡ ≅ < > ≦ ≧ ≤ ≃ ∞ → ← ∈ ⊂ ∪ ∩ ⊗ ∂ ∑ ∏ ( ) [ ] { } / | § & * !,
  the display ∑ ∏ ∫, calligraphic 𝒜 𝒞 ℒ 𝒰, Fraktur 𝔄 𝔅 ℭ 𝔇 𝔊 𝔎 𝔔 ℜ ℑ 𝔖 𝔗 𝔛, the roman *fi ff ffi* and italic *fi ff* ligatures,
  bold (by the word: title lines and run-in heads) for all but J K X Z q w z 8 9,
  40 + 3 script sorts and 80 + 54 9 pt sorts.
- **1922 specimen:** only small caps J Q X and $, which the scans lack. Each is
  the average of all its impressions (up to six sizes, each scaled by its
  own calibration), so a hairline broken in one is carried by the others.
- **Thickened, for the sizes the scans lack:** script variants without a real
  script sort are the text glyph thickened to the stroke weight the real
  script sorts have (2.1 px per edge before scaling). The remaining bold
  letters are regular ones thickened to the bold stems (1.1 px), and the
  remaining 9 pt glyphs are 11 pt ones thickened to 9 pt weight.
- **Accents and punctuation** (`accents.py`): the dieresis is the 1947 one,
  cut from *ö*; the other accents are Latin Modern's, thickened to the
  hairline weight of the type and placed at Latin Modern's height above the
  x-height (or cap height). Accented letters (Latin-1 and Latin
  Extended-A, 148 per style except ogonek and the apostrophe-like carons)
  are composed from these and the 1947 letters; *ı* and *ȷ* are the 1947
  *i* and *j* without their dots. Colon, ellipsis and the quotes ‘ “ ” are
  built from the 1947 period and ’; ? # % & * @ \ ^ _ { } ~ § † ‡ are
  Latin Modern's, thickened.
- **Bold italic** is the italic thickened to the bold stems; no bold italic
  occurs in the scans.
- **Constructed ligatures**, used only where the scans and the specimen both
  lack one:
  - roman *fl* and *ffl*: the *fi* / *ffi* sort less its *i*, with the 1947
    *l* set on the *i*'s stem;
  - italic *fi*, *fl*, *ffi*, *ffl*: the last letter one *f* advance on, with
    the *f*'s terminal trimmed clear.
- **By hand:** the italic *f*'s overhang (`SPACING_BY_HAND`, −0.10 em, as on a
  kerned sort; the math italic *f* keeps a positive side bearing), and the
  en dash (a stretched hyphen).

Clean-ups that keep sparse sorts consistent with the frequent ones:

- **Heights.** Each sort sits at the average height of its impressions
  (aligning to a template impression had carried it to that one
  impression's baseline error), and flat-topped capitals are scaled to the
  median cap height of their style (bold title capitals come from papers
  set at slightly different sizes).
- **Math spacing from print.** The math italic letters' italic corrections
  come from the gaps measured before "(" and ")" in the scans (one vote per
  paper), the parentheses' inner side bearings from the remaining
  difference, and letters that print tucked under a "(" (*f*, *A*, *D*, *L*)
  get a left side bearing down to −20 units. *f*(*x*) is set tight, as in
  1947.

- **Bold title capitals** have the 11 pt cap height and so land in the roman
  capital sorts; impressions with strokes ≥ 18% heavier than the sort's
  lighter quartile are moved to bold sorts.
- **Impressions OCR read as another letter** with high confidence move to
  that letter's sort (bold E and F shared a cluster).
- **Figures** are sized by absolute height, and a figure clearly shorter
  than the others is replaced by the specimen's.
- **Baseline snapping:** a sort seen fewer than 30 times is placed where the
  frequent letters sit, flat or round-bottomed; real script sorts sit on
  their own baseline.

## The math font

`Mills8A-Math.otf` keeps Latin Modern Math's MATH table, extensible
delimiters and all symbols the scans don't have. On top of that:

- Math italic and upright letters, Greek, figures and operators are the
  Mills 8A glyphs (141 replaced).
- The `ssty` script (`.st`) and scriptscript (`.sts`) variants are the
  **real 1947 script sorts** where they exist. Otherwise they're the text
  glyphs thickened to the script sorts' weight, so scaled-down letters
  don't come out light.
- The display ∑ and ∏ are the 1947 display sorts.
- `ScriptPercentScaleDown` 59, `ScriptScriptPercentScaleDown` 50 and the
  superscript and subscript shifts come from the Erdős measurements. Note
  that LaTeX's `unicode-math` takes script sizes from the LaTeX size table,
  so documents need `\DeclareMathSizes{11}{11}{6.48}{5.51}`; without it,
  scripts come out 8 pt, 23% too large.
- Italic corrections and accent positions are computed from the new
  outlines; Latin Modern's cut-in kerns for the replaced glyphs are dropped.

`tex/mills.tex` overrides the display-style script positions with the Mills
paper's (`\Umathsupshiftup\displaystyle=0.66em`, subscripts 0.14em), set in
`\everydisplay` because loading the math fonts resets them. It also keeps a
fixed 12 pt line pitch (`\lineskiplimit=-3pt`) as on a metal page, and sets
footnote marks as superior figures.

## Texture and weight

- **Random impressions (`rand`).** Averaging keeps each letter's ink but
  removes the variation between impressions (fill-in, nicks, squash). Sorts
  with at least 16 clean impressions get **8 alternates** traced from single
  1947 impressions (84 sorts), and those with 8–15 get 4 (61 sorts). They're
  typical in shape (IoU ≥ 0.8 with the mean) and spread from light to heavy
  inking. luaotfload picks one per occurrence.
- **Baseline wobble** (`tex/mills8a-jitter.lua`, optional): a random
  vertical offset per glyph, 0.04 pt standard deviation. Measured on the
  same letters at 600 dpi, rendered text then scatters like the scan
  (0.99 px against 1.00; 38/87/99% within 0/1/2 px against 40/87/98%).
  Fixed seed for reproducible output. Math is not touched.
- **Ink (`MILLS8A_INK`, default 0.7).** The averaged masters are lighter
  than the Mills page: averaging many impressions keeps the typical edge,
  not the ink squeeze. 0.7 scan px of extra ink per edge matches the Mills
  paragraph's darkness (ratio 1.02 LuaLaTeX, 1.01 pdfLaTeX; same text and
  scale). `MILLS8A_INK=0 ./build.sh` gives the type as measured.

## Limits

- Few second-order script sorts (8): most scriptscript glyphs are
  thickened text glyphs.
- Math symbols beyond the scans (the text-size ∫, most arrows and operators)
  are Latin Modern's.
- No italic small caps. Bold italic, the bold lowercase, the accents except
  the dieresis, and some punctuation (? % …) are synthesized or Latin
  Modern's.
- The italic *ff* and *fi* rest on 8 and 49 impressions; their spacing is
  derived from *f* and the last letter rather than measured.
