"""Finish the committed OpenType fonts, without repeating OCR or tracing.

Also run at the end of build.sh, before the pdfTeX conversion. The typographic
line metrics are kept separate from the Windows metrics used for clipping.
"""
import argparse
import math
import unicodedata
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import TTFont

from unicode_fonts import add_accented_smallcaps, add_mark_features, add_unicode

FONTS = Path(__file__).resolve().parent / "fonts"


def glyph_bounds(font, name):
    glyphs = font.getGlyphSet()
    pen = BoundsPen(glyphs)
    glyphs[name].draw(pen)
    return pen.bounds


def update_ink_metrics(font):
    boxes = [glyph_bounds(font, name) for name in font.getGlyphOrder()]
    boxes = [box for box in boxes if box is not None]
    os2 = font["OS/2"]
    # These are clipping bounds, not a request to change the document's leading.
    os2.usWinAscent = max(os2.usWinAscent, math.ceil(max(b[3] for b in boxes)))
    os2.usWinDescent = max(os2.usWinDescent, math.ceil(-min(b[1] for b in boxes)))
    # Version 4 defines USE_TYPO_METRICS. Enlarging clipping bounds must not
    # make supported layout engines use those bounds as the line pitch.
    os2.version = max(os2.version, 4)
    os2.fsSelection |= 0x80
    if not os2.fsSelection & (0x01 | 0x20):
        os2.fsSelection |= 0x40
    cmap = font.getBestCmap()
    for ch, field in (("x", "sxHeight"), ("H", "sCapHeight")):
        if ord(ch) in cmap:
            setattr(os2, field, round(glyph_bounds(font, cmap[ord(ch)])[3]))


def set_advance(font, name, advance):
    top = font["CFF "].cff.topDictIndex[0]
    width = None if advance == top.Private.defaultWidthX else advance - top.Private.nominalWidthX
    pen = T2CharStringPen(width, None, roundTolerance=0)
    top.CharStrings[name].draw(pen)
    top.CharStrings[name] = pen.getCharString(top.Private, top.GlobalSubrs)
    font["hmtx"].metrics[name] = (advance, font["hmtx"].metrics[name][1])


def normalize_accent_advances(font):
    cmap = font.getBestCmap()
    order = font.getGlyphOrder()
    for cp, name in cmap.items():
        ch = chr(cp)
        decomposed = unicodedata.normalize("NFD", ch)
        if (not ch.isalpha() or len(decomposed) < 2
                or not all(unicodedata.combining(c) for c in decomposed[1:])
                or ord(decomposed[0]) not in cmap):
            continue
        base = cmap[ord(decomposed[0])]
        advance = font["hmtx"][base][0]
        # Rare sorts have an underdetermined spacing fit. An accent does not
        # change its letter's Monotype set width; retain the traced ink itself.
        for variant in [name] + [n for n in order if n.startswith(name + ".r")]:
            if font["hmtx"][variant][0] != advance:
                set_advance(font, variant, advance)


def finish(font):
    if "MATH" not in font:
        add_unicode(font)
        normalize_accent_advances(font)
        add_accented_smallcaps(font)
        add_mark_features(font)
    update_ink_metrics(font)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fonts", nargs="*", type=Path,
                        help="OTF files; defaults to revival/fonts/*.otf")
    args = parser.parse_args()
    for path in args.fonts or sorted(FONTS.glob("*.otf")):
        font = TTFont(path, recalcTimestamp=False)
        finish(font)
        font.save(path)
        print(f"Finished {path.name}")


if __name__ == "__main__":
    main()
