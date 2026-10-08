"""Regression checks for the completed math alphabets (no scans needed).

Run with the font-building Python environment after complete_math.py.
Checks actual saved outlines and rasterized ink, not just font coverage.
"""

import os
import string
import subprocess
import unicodedata
import unittest

import numpy as np
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.freetypePen import FreeTypePen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont
from fontTools.tfmLib import TFM
from scipy.ndimage import distance_transform_edt

from calligraphic import HISTORICAL, codepoint
from pdftex.build_pdftex import OML, math_tables

FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")


def drawing(font, name):
    pen = RecordingPen()
    font.getGlyphSet()[name].draw(pen)
    return pen.value


def raster(font, name):
    gs = font.getGlyphSet()
    pen = FreeTypePen(gs)
    gs[name].draw(pen)
    return pen.array(transform=(0.5, 0, 0, 0.5, 0, 0), contain=True) > 0.5


class MathCompletionChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.normal = TTFont(os.path.join(FONTS, "Mills8A-Math.otf"))
        cls.bold = TTFont(os.path.join(FONTS, "Mills8A-MathBold.otf"))
        cls.text = TTFont(os.path.join(FONTS, "Mills8A-Regular.otf"))
        path = subprocess.run(["kpsewhich", "latinmodern-math.otf"], check=True,
                              capture_output=True, text=True).stdout.strip()
        cls.lm = TTFont(path)
        cls.cmap = cls.normal.getBestCmap()
        cls.ssty = math_tables(cls.normal)[3]

    @classmethod
    def tearDownClass(cls):
        for font in (cls.normal, cls.bold, cls.text, cls.lm):
            font.close()

    def test_historical_capitals_are_unchanged(self):
        for letter in HISTORICAL:
            with self.subTest(letter=letter):
                cp = codepoint(letter)
                name = self.cmap[cp]
                source = self.text.getBestCmap()[cp]
                self.assertEqual(drawing(self.normal, name), drawing(self.text, source))
                self.assertEqual(self.normal["hmtx"][name], self.text["hmtx"][source])

    def test_all_capitals_have_distinct_drawings_and_optical_sizes(self):
        lm_cmap = self.lm.getBestCmap()
        seen = set()
        for letter in string.ascii_uppercase:
            with self.subTest(letter=letter):
                name = self.cmap[codepoint(letter)]
                signature = repr(drawing(self.normal, name))
                self.assertNotIn(signature, seen)
                seen.add(signature)
                self.assertEqual(len(self.ssty[name]), 2)
                if letter not in HISTORICAL:
                    self.assertNotEqual(drawing(self.normal, name),
                                        drawing(self.lm, lm_cmap[codepoint(letter)]))
                for glyph in [name] + self.ssty[name]:
                    bp = BoundsPen(self.normal.getGlyphSet())
                    self.normal.getGlyphSet()[glyph].draw(bp)
                    self.assertIsNotNone(bp.bounds)
                    x0, y0, x1, y1 = bp.bounds
                    self.assertGreater(x1 - x0, 100)
                    self.assertGreater(y1 - y0, 400)
                    self.assertGreater(self.normal["hmtx"][glyph][0], 100)

    def test_reconstruction_stroke_weight_matches_historical_capitals(self):
        radii = {}
        for letter in string.ascii_uppercase:
            mask = raster(self.normal, self.cmap[codepoint(letter)])
            distance = distance_transform_edt(mask)
            radii[letter] = np.percentile(distance[mask], 99)
        target = np.median([radii[c] for c in HISTORICAL])
        for letter in set(string.ascii_uppercase) - set(HISTORICAL):
            with self.subTest(letter=letter):
                self.assertGreater(radii[letter] / target, 0.70)
                self.assertLess(radii[letter] / target, 1.50)

    def test_bold_greek_has_more_ink_at_all_sizes(self):
        # OML slots 0--39 include Greek capitals, lowercase and variants.
        for slot, cp in OML.items():
            if slot > 0x27:
                continue
            base = self.cmap[cp]
            for name in [base] + self.ssty.get(base, []):
                with self.subTest(codepoint=hex(cp), glyph=name):
                    normal_ink = raster(self.normal, name).sum()
                    bold_ink = raster(self.bold, name).sum()
                    self.assertGreater(bold_ink, 1.02 * normal_ink)
                    self.assertGreater(self.bold["hmtx"][name][0], self.normal["hmtx"][name][0])

    def test_unicode_bold_greek_uses_the_same_bold_outlines(self):
        for cp in range(0x1D6FC, 0x1D715):
            target = unicodedata.name(chr(cp)).replace("MATHEMATICAL ITALIC", "MATHEMATICAL BOLD ITALIC")
            dst = ord(unicodedata.lookup(target))
            with self.subTest(codepoint=hex(cp)):
                self.assertEqual(drawing(self.normal, self.cmap[dst]),
                                 drawing(self.bold, self.cmap[cp]))

    def test_rule_weights_agree_in_opentype_and_tex_metrics(self):
        for font, prefix, thickness in ((self.normal, "m8a", 80), (self.bold, "m8ab", 102)):
            with self.subTest(font=prefix):
                constants = font["MATH"].table.MathConstants
                for name in ("FractionRuleThickness", "RadicalRuleThickness",
                             "OverbarRuleThickness", "UnderbarRuleThickness"):
                    self.assertEqual(getattr(constants, name).Value, thickness)
                ex = TFM(os.path.join(FONTS, "..", "pdftex", "fonts", prefix + "ex.tfm"))
                self.assertAlmostEqual(ex.fontdimens["DEFAULTRULETHICKNESS"], thickness / 1000, places=5)
                for slot in (0o160, 0o161, 0o162, 0o163, 0o166):
                    self.assertAlmostEqual(ex.chars[slot]["height"], thickness / 1000, places=5)
                self.assertEqual(ex.chars[0o164]["varchar"], {"top": 0o166, "bot": 0o164, "rep": 0o165})
                for suffix in ("", "s", "ss"):
                    sy = TFM(os.path.join(FONTS, "..", "pdftex", "fonts", prefix + "sy" + suffix + ".tfm"))
                    self.assertAlmostEqual(sy.chars[0x70]["height"], thickness / 1000, places=5)

    def test_radical_assembly_has_flat_full_weight_joins(self):
        for font, thickness in ((self.normal, 80), (self.bold, 102)):
            for name, edges in (("uni23B7", (0,)), ("radical.ex", (0, -1)), ("radical.tp", (-1,))):
                ink = raster(font, name)
                first, last = np.flatnonzero(ink.any(axis=1))[[0, -1]]
                ink = ink[first:last + 1]  # discard fractional-pixel canvas padding
                for row in edges:
                    with self.subTest(font=font["name"].getDebugName(6), glyph=name, edge=row):
                        # Raster scale is half an em: a full-width flat joint
                        # must meet the next piece across the entire stem.
                        self.assertGreaterEqual(ink[row].sum(), 0.9 * thickness / 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
