import tempfile
import unittest
from pathlib import Path

from fontTools.ttLib import TTFont

from export_fonts import export
from finish_fonts import FONTS
from test_fonts import shape


class ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.output = Path(cls.directory.name)
        export(cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def test_compact_fonts_keep_coverage_features_and_spacing(self):
        for path in sorted(FONTS.glob("*.otf")):
            original = TTFont(path)
            compact_path = self.output / "compact" / path.name.replace("Mills8A", "Mills8ACompact")
            font = TTFont(compact_path)
            with self.subTest(font=path.name):
                self.assertEqual(original.getBestCmap(), font.getBestCmap())
                old_features = {r.FeatureTag for r in original["GSUB"].table.FeatureList.FeatureRecord}
                features = {r.FeatureTag for r in font["GSUB"].table.FeatureList.FeatureRecord}
                self.assertEqual(old_features - {"rand"}, features)
                self.assertNotEqual(original["name"].getDebugName(6), font["name"].getDebugName(6))
                for text, opts in (("office á € Ą", {}), ("123", {"onum": True}),
                                   ("aáäæœ", {"smcp": True})):
                    a, b = shape(path, text, opts), shape(compact_path, text, opts)
                    self.assertEqual([n for n, _ in a], [n for n, _ in b])
                    self.assertEqual([(p.x_advance, p.x_offset, p.y_offset) for _, p in a],
                                     [(p.x_advance, p.x_offset, p.y_offset) for _, p in b])
                if "rand" in old_features:
                    self.assertLess(compact_path.stat().st_size, path.stat().st_size / 3)
                if "MATH" in original:
                    self.assertIn("MATH", font)
                    self.assertEqual(original["MATH"].table.MathConstants.ScriptPercentScaleDown,
                                     font["MATH"].table.MathConstants.ScriptPercentScaleDown)

    def test_woff2_round_trip_preserves_font_tables(self):
        for path in sorted(FONTS.glob("*.otf")):
            original = TTFont(path)
            web_path = self.output / "web" / path.with_suffix(".woff2").name
            font = TTFont(web_path)
            with self.subTest(font=path.name):
                self.assertEqual(original.getBestCmap(), font.getBestCmap())
                self.assertEqual(original["hmtx"].metrics, font["hmtx"].metrics)
                for tag in ("CFF ", "GSUB", "GPOS", "GDEF", "MATH"):
                    if tag in original:
                        self.assertEqual(original.getTableData(tag), font.getTableData(tag))
                self.assertLess(web_path.stat().st_size, path.stat().st_size)


if __name__ == "__main__":
    unittest.main()
