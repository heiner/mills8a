"""Regression checks for the shipped fonts: python -m unittest discover -s revival."""
import unittest
import unicodedata
import uharfbuzz as hb

from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

from finish_fonts import FONTS, finish, glyph_bounds, normalize_accent_advances, update_ink_metrics
from optimize_fonts import subroutinize


def shape(path, text, features=None):
    font = TTFont(path)
    hbfont = hb.Font(hb.Face(path.read_bytes()))
    hbfont.scale = (1000, 1000)
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(hbfont, buffer, {"rand": False, **(features or {})})
    return [(font.getGlyphName(info.codepoint), pos)
            for info, pos in zip(buffer.glyph_infos, buffer.glyph_positions)]


class FontTests(unittest.TestCase):
    def test_finishing_recreates_missing_smallcap_features(self):
        font = TTFont(FONTS / "Mills8A-Regular9.otf")
        features = font["GSUB"].table.FeatureList
        features.FeatureRecord = [r for r in features.FeatureRecord if r.FeatureTag != "smcp"]
        features.FeatureCount = len(features.FeatureRecord)
        finish(font)
        self.assertIn("smcp", [r.FeatureTag for r in font["GSUB"].table.FeatureList.FeatureRecord])

    def test_clipping_bounds_do_not_define_line_pitch(self):
        for path in sorted(FONTS.glob("*.otf")):
            os2 = TTFont(path)["OS/2"]
            with self.subTest(font=path.name):
                self.assertGreaterEqual(os2.version, 4)
                self.assertTrue(os2.fsSelection & 0x80)
                if not os2.fsSelection & (0x01 | 0x20):
                    self.assertTrue(os2.fsSelection & 0x40)

    def test_subroutinization_preserves_every_outline_and_metric(self):
        font = TTFont(FONTS / "Mills8A-Regular.otf")
        glyphs = font.getGlyphSet()
        originals = {}
        for name in font.getGlyphOrder():
            pen = RecordingPen()
            glyphs[name].draw(pen)
            originals[name] = pen.value
        metrics = dict(font["hmtx"].metrics)
        cmap = dict(font.getBestCmap())
        subroutinize(font)
        glyphs = font.getGlyphSet()
        self.assertEqual(metrics, font["hmtx"].metrics)
        self.assertEqual(cmap, font.getBestCmap())
        for name, drawing in originals.items():
            pen = RecordingPen()
            glyphs[name].draw(pen)
            with self.subTest(glyph=name):
                self.assertEqual(drawing, pen.value)

    def test_cff_widths_match_horizontal_metrics(self):
        for path in sorted(FONTS.glob("*.otf")):
            font = TTFont(path)
            top = font["CFF "].cff.topDictIndex[0]
            for name in font.getGlyphOrder():
                charstring = top.CharStrings[name]
                charstring.draw(RecordingPen())
                with self.subTest(font=path.name, glyph=name):
                    self.assertEqual(charstring.width, font["hmtx"][name][0])

    def test_accented_smallcaps_and_ligature_letters(self):
        for style in ("Regular", "Regular9", "Bold"):
            path = FONTS / f"Mills8A-{style}.otf"
            with self.subTest(style=style):
                glyphs = shape(path, "aáäæœßąďøłı", {"smcp": True})
                self.assertTrue(all(name.endswith(".sc") for name, _ in glyphs))
                cmap = TTFont(path).getBestCmap()
                for ch in "áäą":
                    name = cmap[ord(ch)] + ".sc"
                    font = TTFont(path)
                    self.assertEqual(font["hmtx"][name][0], font["hmtx"]["a.sc"][0])

    def test_unicode_supplements_in_every_text_style(self):
        text = "€ ™ Ąą Ęę Įį Ųų ďľĽť Đđ Ħħ Ŋŋ"
        for path in sorted(FONTS.glob("*.otf")):
            if "Math" in path.name:
                continue
            with self.subTest(font=path.name):
                self.assertNotIn(".notdef", [n for n, _ in shape(path, text)])

    def test_decomposed_and_stacked_marks(self):
        for path in sorted(FONTS.glob("*.otf")):
            if "Math" in path.name:
                continue
            with self.subTest(font=path.name):
                self.assertEqual([n for n, _ in shape(path, "á")],
                                 [n for n, _ in shape(path, "a\u0301")])
                glyphs = shape(path, "a\u0304\u0301\u0308")
                self.assertNotIn(".notdef", [n for n, _ in glyphs])
                marks = [pos for name, pos in glyphs if name.startswith("uni03")]
                self.assertTrue(marks)
                self.assertTrue(all(pos.x_advance == 0 for pos in marks))
                self.assertGreater(marks[-1].y_offset, marks[0].y_offset)
                dotless = shape(path, "i\u0304\u0301\u0308")
                self.assertNotIn(".notdef", [n for n, _ in dotless])

    def test_smallcaps_are_selectable_in_every_roman_style(self):
        for style in ("Regular", "Regular9", "Bold"):
            with self.subTest(style=style):
                glyphs = shape(FONTS / f"Mills8A-{style}.otf", "abcxyz", {"smcp": True})
                self.assertEqual([name for name, _ in glyphs],
                                 [ch + ".sc" for ch in "abcxyz"])

    def test_random_impressions_follow_smallcaps_and_keep_their_widths(self):
        path = FONTS / "Mills8A-Regular.otf"
        plain = shape(path, "abcxyz", {"smcp": True})
        random = shape(path, "abcxyz", {"smcp": True, "rand": True})
        self.assertEqual([name.split(".r")[0] for name, _ in random],
                         [name for name, _ in plain])
        self.assertEqual([pos.x_advance for _, pos in random],
                         [pos.x_advance for _, pos in plain])

    def test_smallcaps_do_not_keep_lowercase_ligatures(self):
        for style in ("Regular", "Regular9", "Bold"):
            path = FONTS / f"Mills8A-{style}.otf"
            with self.subTest(style=style):
                glyphs = shape(path, "officefiflffifflff", {"smcp": True})
                self.assertEqual([name for name, _ in glyphs],
                                 [ch + ".sc" for ch in "officefiflffifflff"])

    def test_accents_keep_the_base_letter_advance(self):
        for path in sorted(FONTS.glob("*.otf")):
            font = TTFont(path)
            if "MATH" in font:
                continue
            cmap = font.getBestCmap()
            for cp, name in cmap.items():
                ch = chr(cp)
                d = unicodedata.normalize("NFD", ch)
                if (ch.isalpha() and len(d) > 1 and ord(d[0]) in cmap
                        and all(unicodedata.combining(c) for c in d[1:])):
                    with self.subTest(font=path.name, character=ch):
                        self.assertEqual(font["hmtx"][name][0],
                                         font["hmtx"][cmap[ord(d[0])]][0])

    def test_accent_spacing_repair_keeps_traced_ink(self):
        font = TTFont(FONTS / "Mills8A-Regular.otf")
        box = glyph_bounds(font, "aacute")
        font["hmtx"].metrics["aacute"] = (378, font["hmtx"]["aacute"][1])
        normalize_accent_advances(font)
        self.assertEqual(box, glyph_bounds(font, "aacute"))
        self.assertEqual(font["hmtx"]["a"][0], font["hmtx"]["aacute"][0])

    def test_windows_metrics_contain_every_outline(self):
        for path in sorted(FONTS.glob("*.otf")):
            font = TTFont(path)
            os2 = font["OS/2"]
            for name in font.getGlyphOrder():
                with self.subTest(font=path.name, glyph=name):
                    box = glyph_bounds(font, name)
                    if box:
                        self.assertLessEqual(box[3], os2.usWinAscent)
                        self.assertGreaterEqual(box[1], -os2.usWinDescent)

    def test_clipping_repair_preserves_leading_and_outlines(self):
        font = TTFont(FONTS / "Mills8A-Regular.otf")
        metrics = (font["hhea"].ascent, font["hhea"].descent,
                   font["hhea"].lineGap, font["OS/2"].sTypoAscender,
                   font["OS/2"].sTypoDescender, font["OS/2"].sTypoLineGap)
        box = glyph_bounds(font, "Aring")
        font["OS/2"].usWinAscent = 900
        update_ink_metrics(font)
        self.assertEqual(box, glyph_bounds(font, "Aring"))
        self.assertEqual(metrics, (font["hhea"].ascent, font["hhea"].descent,
                                  font["hhea"].lineGap, font["OS/2"].sTypoAscender,
                                  font["OS/2"].sTypoDescender, font["OS/2"].sTypoLineGap))


if __name__ == "__main__":
    unittest.main()
