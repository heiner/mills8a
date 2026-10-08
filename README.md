# Mills 8A

A digital revival of **Monotype Modern No. 8A**, the typeface of the
*Bulletin of the American Mathematical Society* in the 1940s, for LaTeX.
It is named after W. H. Mills, *A prime-representing function* (Bull. AMS 53,
1947), the page this project started from.

![Mills 8A type specimen](docs/specimen.png)

To see it at its real size, print [`mills-specimen-a4.pdf`](mills-specimen-a4.pdf) or
[`mills-specimen-letter.pdf`](mills-specimen-letter.pdf) at actual size (100%, not
"fit to page"): the text is then 11 pt, as in the 1947 *Bulletin*.

Monotype Modern 8A (Lanston Monotype's series 8, roman with italic) is a
Scotch-style "modern" face: strong contrast, ball terminals, cast in hot metal
and printed by letterpress. It was a standard face of American mathematical
printing from the 1920s to the 1960s, and it is the face Knuth modelled
Computer Modern on. Mills 8A is not a redrawing. Its glyphs are traced from the
type itself: averaged from about 900,000 letter impressions on 461 scanned
pages of the *Bulletin* and the *Transactions* (1940–1948). The shapes, the
weight of the ink, the Monotype unit widths and the real 1947 script sorts are
all as they were printed.

## The 1947 page, reset

The Mills page as printed in 1947 (left), and reset from the LaTeX source in
Mills 8A (right):

![1947 scan and Mills 8A](docs/comparison.png)

[`mills-compare.pdf`](mills-compare.pdf) has the two side by side and then
each on its own page; [`mills-8a.pdf`](mills-8a.pdf) is the page alone.

<details>
<summary>Six more first pages from the scans, reset the same way</summary>

Each reset is in `tex/pages/`, set with `tex/bulletin1947.sty`; `./compare-pages.sh` rebuilds
the images from the scans.

**P. Erdős, *Some asymptotic formulas for multiplicative functions*, Bull. Amer. Math. Soc. 53 (1947)**

![P. Erdős, first page: scan and Mills 8A](docs/pages/erdos1947.png)

**J. L. Doob, *Probability in function space*, Bull. Amer. Math. Soc. 53 (1947)**

![J. L. Doob, first page: scan and Mills 8A](docs/pages/doob1947.png)

**M. Kac, *On the notion of recurrence in discrete stochastic processes*, Bull. Amer. Math. Soc. 53 (1947)**

![M. Kac, first page: scan and Mills 8A](docs/pages/kac1947.png)

**E. L. Post, *Recursively enumerable sets of positive integers and their decision problems*, Bull. Amer. Math. Soc. 50 (1944)**

![E. L. Post, first page: scan and Mills 8A](docs/pages/post1944.png)

**S. Wright, *Statistical genetics and evolution*, Bull. Amer. Math. Soc. 48 (1942)**

![S. Wright, first page: scan and Mills 8A](docs/pages/wright1942.png)

**Th. von Kármán, *The engineer grapples with nonlinear problems*, Bull. Amer. Math. Soc. 46 (1940)**

![Th. von Kármán, first page: scan and Mills 8A](docs/pages/vonkarman1940.png)

</details>

## Installing

The built fonts are in the repository, so nothing needs to be built:

    git clone https://github.com/heiner/mills8a && cd mills8a
    ./make-tds.sh        # assemble the TeX tree (build/tds) and mills8a.tds.zip
    ./install.sh         # copy it into your personal TeX tree (TEXMFHOME)

`install.sh` puts the files where TeX looks by default (`~/texmf` on
Linux, `~/Library/texmf` on macOS: whatever `kpsewhich -var-value
TEXMFHOME` says), so no environment variables and no `updmap` are needed:
the package loads its own map file. Alternatively unzip
`mills8a.tds.zip` into that directory yourself.

- **MiKTeX:** unzip `mills8a.tds.zip` into a new directory, add it as a
  root directory (MiKTeX Console → Settings → Directories) and refresh the
  file name database.
- **dvips** (`latex` + `dvips` instead of `pdflatex`): also run
  `./install.sh --dvips`, which enables the map file with `updmap-user`.

## Using it

```latex
\usepackage{mills8a}            % or [osf] for old-style figures in text
```

The Bulletin set 11 pt type on 12 pt leading; `tex/mills.tex` is a complete
example, including the 1947 script positions.

## What is in the family

| font | contents |
|---|---|
| Mills8A-Regular | roman, small caps, f-ligatures, lining and old-style figures, accents (Latin-1, Latin Extended-A) |
| Mills8A-Italic | italic, Greek, f-ligatures |
| Mills8A-Bold, -BoldItalic | bold (from the titles); bold italic (synthesized) |
| Mills8A-Regular9, -Italic9 | the 9 pt cut, for footnotes and references |
| Mills8A-Math | the 1947 letters, Greek, operators, relations, Fraktur, display ∑ ∏ ∫, and the real first- and second-order **script sorts** for indices |

### OpenType fonts

This fork adds extended Latin small caps, Unicode supplements and combining-mark
positioning, repairs accent widths and clipping metrics, and optimizes CFF
storage. Compact OTF and WOFF2 exports are available through
`python3 revival/export_fonts.py`; see [the build documentation](revival/README.md)
for dependencies and optional screen hinting.

The family is also built as OpenType fonts (`revival/fonts`, with an OpenType
math font) for LuaLaTeX and other software. They can set each letter as one
of up to 8 real 1947 impressions at random (feature `rand`); `tex/mills.tex`
run with LuaLaTeX shows the setup (`fontspec`, `unicode-math`); the
installed tree includes them, so they are found by file name. The
difference from the pdfLaTeX page is slight.

<details>
<summary>More on how it was made</summary>

### How it was made

1. **Segment** each 600 dpi page into glyph impressions, with Tesseract for a
   first reading and the page's lines (`revival/segment.py`, `baselines.py`).
2. **Normalize the scans**: each paper's ink weight and type size are measured
   against the Erdős paper and corrected (`docweight.py`).
3. **Cluster** identical sorts and label them (`cluster.py`, `classify.py`,
   `assign.py`). Rules do most of it; `overrides.tsv` holds the hand
   corrections, each naming one impression, so re-clustering does not
   invalidate it.
4. **Average** each sort's impressions at 4× resolution, aligned to ¼ px
   (`masters.py`). Old-style figures come from the years in the Bulletin's
   running heads (`oldstyle.py`).
5. **Trace and space** the masters into OpenType fonts (`build_font.py`). Side
   bearings are fitted from about 440,000 letter pairs in the text and land on
   Monotype's 18-unit grid. Then accents (`accents.py`), the math font on Latin
   Modern Math's tables (`build_math.py`), bold and 9 pt (`build_sizes.py`),
   and the pdfLaTeX fonts (`pdftex/build_pdftex.py`).
6. **Check**: `check_fonts.py` tests baselines, heights, side bearings and the
   script sorts of every font, and `proof/` has proof sheets of everything the
   family sets.

`revival/README.md` describes each step, the measurements behind it, and
where each glyph comes from.

### How much is real

Traced from the 1940s scans (each glyph the average of its printed
impressions):

- every roman and italic letter and figure at 11 pt, the roman J from its
  9 pt sort (66 impressions) scaled up;
- the old-style figures, from the years in the Bulletin's running heads;
- punctuation, with the 1947 quotes ‘ ’ “ ”, the question mark (10
  impressions) and the en dash (a 9 pt sort, scaled);
- the accented ü á (roman) and ü Ü ä (italic), and the dieresis;
- 23 small capitals;
- bold, from the title lines and run-in heads (told by the word, not the
  letter): the capitals but J K X Z, the lowercase but q w z, the figures
  0–7 and the hyphen;
- Greek (with Γ Σ Φ and θ), most math operators and relations, ∮ ∨, the
  display ∑ ∏ ∫, Fraktur 𝔄 𝔅 ℭ 𝔇 𝔊 𝔎 𝔔 ℜ ℑ 𝔖 𝔗 𝔛 and script 𝒜 𝒞 ℒ 𝒰;
- the 9 pt cut: 80 roman and 54 italic sorts;
- 43 script sorts for indices (40 first-order, 3 second-order), among
  them the short 1947 index arrow.

Filled in otherwise:

- from the 1922 Lanston *Specimen Book* (No. 8A at 9–18 pt): small caps
  J Q X and `$`;
- built from 1947 sorts: the *fl*/*ffl* and italic *ffi*/*ffl* ligatures,
  the em dash, the colon and ellipsis, `\cdot` and `\cdots` (from the
  period), bold J K X Z q w z 8 9 and bold italic (thickened, to the real
  bold's weight and x-height), and the script sizes that have no legible
  real sort (the text glyph scaled: among them the index 2 3 4 8, whose
  real sorts fill in);
- from Latin Modern, thickened to the type's weight: accents other than the
  dieresis (the acute of á and é is real only in those letters), rarer punctuation and symbols (`# % @` † ‡ ¶ « » ß Æ Œ Ø Ł
  and so on), and the math symbols the scans lack.

Spacing is measured as well: side bearings from about 440,000 letter
pairs in the text, the thin space 1947 set before `:` and `;`, and the
script positions and gaps of the Mills page. A few bearings that the
pairs cannot fix (the small-cap A before a period) are set by hand from
the scans.

</details>

## Sources

- The scans: *Bulletin* and *Transactions of the AMS*, 1940–1948, from the
  AMS back-issue archive. Only the crops in the comparisons are included
  here.
- *The Monotype Specimen Book of Type Faces*, Lanston Monotype, 1922
  (public domain).
- Latin Modern and Latin Modern Math: some text glyphs and the base of
  `Mills8A-Math.otf`.
