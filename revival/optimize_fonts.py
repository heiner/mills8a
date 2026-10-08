"""Lossless CFF subroutinization; optional automatic hints for screen use."""
import argparse
import shutil
import statistics
import subprocess
import tempfile
from pathlib import Path

import cffsubr
import numpy as np
from fontTools.pens.freetypePen import FreeTypePen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

from finish_fonts import FONTS, glyph_bounds
from unicode_fonts import put_glyph


def subroutinize(font):
    drawings = {}
    glyphs = font.getGlyphSet()
    for name in font.getGlyphOrder():
        pen = RecordingPen()
        glyphs[name].draw(pen)
        drawings[name] = pen
    cffsubr.subroutinize(font)
    glyphs = font.getGlyphSet()
    for name, original in drawings.items():
        pen = RecordingPen()
        glyphs[name].draw(pen)
        # tx can round fractional operands. Keep those few glyphs unshared
        # rather than alter any of the existing outlines.
        if pen.value != original.value:
            put_glyph(font, name, original, font["hmtx"][name][0])


def stem_width(font, character, horizontal=False):
    glyphs = font.getGlyphSet()
    name = font.getBestCmap()[ord(character)]
    box = glyph_bounds(font, name)
    pen = FreeTypePen(glyphs)
    glyphs[name].draw(pen)
    image = pen.array(width=round(box[2] - box[0]) + 8,
                      height=round(box[3] - box[1]) + 8,
                      transform=(1, 0, 0, 1, 4 - box[0], 4 - box[1])) > 0.5
    scan = image[:, image.shape[1] // 2] if horizontal else image[image.shape[0] // 2, :]
    edges = np.flatnonzero(np.diff(np.r_[0, scan.astype(int), 0]))
    widths = edges[1::2] - edges[::2]
    if not widths.size:
        raise ValueError(f"Cannot measure a stem in {name}")
    return round(float(np.median(widths)))


def alignment_zones(font):
    private = font["CFF "].cff.topDictIndex[0].Private
    cmap = font.getBestCmap()
    boxes = {ch: glyph_bounds(font, cmap[ord(ch)]) for ch in "xveosHIOl"}
    baseline = round(statistics.median(boxes[c][1] for c in "xvHIl"))
    bottom = min(baseline - 1, round(min(boxes[c][1] for c in "eos")))
    xheight = round(statistics.median(boxes[c][3] for c in "xv"))
    xround = max(xheight + 1, round(max(boxes[c][3] for c in "eos")))
    cap = round(statistics.median(boxes[c][3] for c in "HI"))
    capround = max(cap + 1, round(boxes["O"][3]))
    private.BlueValues = [bottom, baseline, xheight, xround, cap, capround]
    private.BlueFuzz, private.BlueShift, private.BlueScale = 1, 7, 0.039625
    private.StdVW = stem_width(font, "l")
    private.StdHW = stem_width(font, "H", horizontal=True)
    private.StemSnapV, private.StemSnapH = [private.StdVW], [private.StdHW]


def optimize(path, output, hint=False):
    original_size = path.stat().st_size
    font = TTFont(path, recalcTimestamp=False)
    if hint:
        autohint = shutil.which("otfautohint")
        if not autohint:
            raise RuntimeError("otfautohint is required for --hint (install afdko).")
        alignment_zones(font)
        with tempfile.TemporaryDirectory() as directory:
            source, result = Path(directory) / "source.otf", Path(directory) / "hinted.otf"
            font.save(source)
            subprocess.run([autohint, "-a", "--no-flex", "-p", "2", "-o", str(result),
                            str(source)], check=True)
            font = TTFont(result, recalcTimestamp=False)
    subroutinize(font)
    output.parent.mkdir(parents=True, exist_ok=True)
    font.save(output)
    print(f"{output.name}: {original_size:,} -> {output.stat().st_size:,} bytes")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fonts", nargs="*", type=Path)
    parser.add_argument("--hint", action="store_true",
                        help="add AFDKO hints (can increase file size)")
    parser.add_argument("--output-dir", type=Path,
                        help="write separate fonts; default: replace inputs")
    args = parser.parse_args()
    for path in args.fonts or sorted(FONTS.glob("*.otf")):
        output = args.output_dir / path.name if args.output_dir else path
        optimize(path, output, args.hint)


if __name__ == "__main__":
    main()
