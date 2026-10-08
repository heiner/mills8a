"""Complete the checked-in math font without the unavailable scan masters.

Draw the missing calligraphic capitals, provide their optical sizes, and
construct a real bold math version by expanding the Mills outlines. The
four historical calligraphic capitals are never replaced. Run this after
build_math.py/build_sizes.py and before pdftex/build_pdftex.py.

The operation is repeatable: new drawings are rebuilt from calligraphic.py,
Greek fill-ins come from the unmodified Latin Modern source, and the bold
font is always derived from the normal font, never from a previous bold.
"""

import copy
import os
import subprocess
import unicodedata

import pathops
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables

from calligraphic import HISTORICAL, STROKES, charstring, codepoint
from pdftex.build_pdftex import OML, OMS, OPS, OPS_NAMED, EXTRA, math_tables

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
BOLD_GROW = 11  # units per edge: about the existing synthesized bold italic
GREEK_GROW = 15  # bring untraced Greek hairlines up to the printed text weight
MATH_GREEK = set(range(0x1D6E2, 0x1D71C))  # includes omicron, absent from TeX's OML slots
RULE_THICKNESS = 80  # 0.08 em, twice Latin Modern's rule weight


def expanded(gs, name, advance, growth, advance_growth=None):
    """Offset an outline, union overlaps, and retain its left side bearing."""
    original = pathops.Path()
    gs[name].draw(original.getPen())
    if not list(original):
        return T2CharStringPen(advance, None).getCharString(), advance
    border = pathops.Path(original)
    border.stroke(2 * growth, pathops.LineCap.ROUND_CAP, pathops.LineJoin.ROUND_JOIN, 4)
    original.addPath(border)
    original.convertConicsToQuads(0.1)
    shape = pathops.simplify(original).transform(1, 0, 0, 1, growth, 0)
    shape.convertConicsToQuads(0.1)
    advance = round(advance + (2 * growth if advance_growth is None else advance_growth))
    pen = T2CharStringPen(advance, None)
    shape.draw(pen)
    return pen.getCharString(), advance


def install_outline(font, name, cs, advance):
    top = font["CFF "].cff.topDictIndex[0]
    cs.private, cs.globalSubrs = top.Private, top.GlobalSubrs
    top.CharStrings[name] = cs
    bounds = BoundsPen(None)
    cs.draw(bounds)
    box = bounds.bounds or (0, 0, 0, 0)
    font["hmtx"][name] = (advance, round(box[0]))
    return box


def update_math_metrics(font, names):
    """Recalculate accent centres/overhangs; discard obsolete cut-in kerns."""
    info = font["MATH"].table.MathGlyphInfo
    gs = font.getGlyphSet()
    order = {g: i for i, g in enumerate(font.getGlyphOrder())}
    italics, accents = {}, {}
    for n in names:
        bp = BoundsPen(gs)
        gs[n].draw(bp)
        x0, _, x1, _ = bp.bounds or (0, 0, 0, 0)
        italics[n] = max(0, round(x1 - font["hmtx"][n][0]))
        accents[n] = round((x0 + x1) / 2)
    for table, cov_key, vals_key, count_key, updates in (
        (info.MathItalicsCorrectionInfo, "Coverage", "ItalicsCorrection", "ItalicsCorrectionCount", italics),
        (info.MathTopAccentAttachment, "TopAccentCoverage", "TopAccentAttachment", "TopAccentAttachmentCount", accents),
    ):
        coverage = getattr(table, cov_key)
        values = dict(zip(coverage.glyphs, getattr(table, vals_key)))
        for name, value in updates.items():
            record = otTables.MathValueRecord()
            record.Value, record.DeviceTable = value, None
            values[name] = record
        coverage.glyphs = sorted(values, key=order.__getitem__)
        setattr(table, vals_key, [values[n] for n in coverage.glyphs])
        setattr(table, count_key, len(values))
    kern = info.MathKernInfo
    if kern:
        pairs = [(g, r) for g, r in zip(kern.MathKernCoverage.glyphs, kern.MathKernInfoRecords)
                 if g not in names]
        kern.MathKernCoverage.glyphs = [g for g, _ in pairs]
        kern.MathKernInfoRecords = [r for _, r in pairs]
        kern.MathKernCount = len(pairs)


def complete_calligraphic(font):
    cmap = font.getBestCmap()
    _, _, _, ssty = math_tables(font)
    changed = set()
    assert set(STROKES) == set("ABCDEFGHIJKLMNOPQRSTUVWXYZ") - set(HISTORICAL)
    for letter in STROKES:
        base = cmap[codepoint(letter)]
        for level, name in enumerate([base] + ssty.get(base, [])):
            cs, advance, _ = charstring(letter, growth=(0, 5, 8)[min(level, 2)])
            install_outline(font, name, cs, advance)
            changed.add(name)
    update_math_metrics(font, changed)
    return changed


def complete_greek(font):
    """Weight-match the existing Greek fill-ins; keep all historical sorts."""
    lm_path = subprocess.run(["kpsewhich", "latinmodern-math.otf"], check=True,
                             capture_output=True, text=True).stdout.strip()
    lm = TTFont(lm_path)
    italic = TTFont(os.path.join(FONTS, "Mills8A-Italic.otf"))
    real = italic.getBestCmap()
    cmap, lm_cmap, gs = font.getBestCmap(), lm.getBestCmap(), lm.getGlyphSet()
    _, _, _, ssty = math_tables(font)
    _, _, _, lm_ssty = math_tables(lm)
    greek = {0x3B1 + i: 0x1D6FC + i for i in range(25)}
    greek.update({0x3F5: 0x1D716, 0x3D1: 0x1D717, 0x3D5: 0x1D719,
                  0x3F1: 0x1D71A, 0x3D6: 0x1D71B})
    changed = set()
    for plain, cp in greek.items():
        if plain in real or cp not in cmap:
            continue
        base, source = cmap[cp], lm_cmap[cp]
        targets = [base] + ssty.get(base, [])
        sources = [source] + lm_ssty.get(source, [])
        for level, name in enumerate(targets):
            src = sources[min(level, len(sources) - 1)]
            cs, advance = expanded(gs, src, lm["hmtx"][src][0], GREEK_GROW + 3 * level)
            install_outline(font, name, cs, advance)
            changed.add(name)
    update_math_metrics(font, changed)
    lm.close()
    italic.close()
    return changed


def complete_rules(font, thickness):
    """Match fraction/radical rules and the radical outlines at every size.

    Work from pristine LM each time. Radical tips overlap the rule by half
    its thickness: unlike letters, their advance grows by only one radius.
    Assembly pieces stay based at y=0, with their advances updated to match.
    """
    path = subprocess.run(["kpsewhich", "latinmodern-math.otf"], check=True,
                          capture_output=True, text=True).stdout.strip()
    lm = TTFont(path)
    gs = lm.getGlyphSet()
    old_rule = lm["MATH"].table.MathConstants.RadicalRuleThickness.Value
    growth = (thickness - old_rule) / 2
    variants = font["MATH"].table.MathVariants
    construction = variants.VertGlyphConstruction[variants.VertGlyphCoverage.glyphs.index("radical")]
    parts = {p.glyph for p in construction.GlyphAssembly.PartRecords}
    names = {r.VariantGlyph for r in construction.MathGlyphVariantRecord} | parts
    boxes = {}
    for name in sorted(names):
        cs, advance = expanded(gs, name, lm["hmtx"][name][0], growth, advance_growth=growth)
        if name in parts:
            cs.private = font["CFF "].cff.topDictIndex[0].Private
            cs.globalSubrs = font["CFF "].cff.GlobalSubrs
            source_bounds = BoundsPen(gs)
            gs[name].draw(source_bounds)
            # Extensible pieces need flat connection edges. Rounded offset
            # caps would touch at a point and leave pinholes in TeX's stack.
            dy = growth if name == "uni23B7" else 0
            shape = pathops.Path()
            cs.draw(TransformPen(shape.getPen(), (1, 0, 0, 1, 0, dy)))
            x0, _, x1, _ = shape.bounds
            ymax = source_bounds.bounds[3] + (growth if name != "radical.ex" else 0)
            clip = pathops.Path()
            clip.moveTo(x0 - 1, 0)
            clip.lineTo(x1 + 1, 0)
            clip.lineTo(x1 + 1, ymax)
            clip.lineTo(x0 - 1, ymax)
            clip.close()
            shape = pathops.op(shape, clip, pathops.PathOp.INTERSECTION)
            pen = T2CharStringPen(advance, None)
            shape.draw(pen)
            cs = pen.getCharString()
        boxes[name] = install_outline(font, name, cs, advance)
    for record in construction.MathGlyphVariantRecord:
        box = boxes[record.VariantGlyph]
        record.AdvanceMeasurement = round(box[3] - box[1]) + 1
    for part in construction.GlyphAssembly.PartRecords:
        box = boxes[part.glyph]
        part.FullAdvance = round(box[3] - box[1])
    constants = font["MATH"].table.MathConstants
    for key in ("FractionRuleThickness", "RadicalRuleThickness",
                "OverbarRuleThickness", "UnderbarRuleThickness", "RadicalExtraAscender"):
        getattr(constants, key).Value = thickness
    update_math_metrics(font, names)
    lm.close()


def make_bold(font):
    bold = copy.deepcopy(font)
    cmap, gs = font.getBestCmap(), font.getGlyphSet()
    _, _, _, ssty = math_tables(font)
    points = set(OML.values()) | set(OMS.values()) | set(OPS.values()) | set(EXTRA.values()) | MATH_GREEK
    names = {cmap[cp] for cp in points if cp in cmap}
    names.update(n for n in OPS_NAMED.values() if n in gs)
    names.update(n for n in gs if n.startswith("tex.acc."))
    names.update({"tex.mapstochar", "summation.v1", "product.v1", "integral.v1"} & set(gs))
    names.update(v for n in list(names) for v in ssty.get(n, []))
    for name in sorted(names):
        cs, advance = expanded(gs, name, font["hmtx"][name][0], BOLD_GROW)
        install_outline(bold, name, cs, advance)
    update_math_metrics(bold, names)
    top = bold["CFF "].cff.topDictIndex[0]
    bold["CFF "].cff.fontNames = ["Mills8A-MathBold"]
    top.FullName, top.FamilyName, top.Weight = "Mills 8A Math Bold", "Mills 8A Math", "Bold"
    for name_id, text in ((1, "Mills 8A Math"), (2, "Bold"), (3, "Mills8A-MathBold"),
                          (4, "Mills 8A Math Bold"), (6, "Mills8A-MathBold"),
                          (16, "Mills 8A Math"), (17, "Bold")):
        for record in list(bold["name"].names):
            if record.nameID == name_id:
                bold["name"].setName(text, name_id, record.platformID, record.platEncID, record.langID)
    bold["OS/2"].usWeightClass = 700
    bold["OS/2"].fsSelection = (bold["OS/2"].fsSelection & ~0x40) | 0x20
    bold["head"].macStyle |= 1
    return bold, names


def unicode_bold(font, bold):
    """Use the same outlines for Unicode bold Latin/Greek/script alphabets."""
    cmap = font.getBestCmap()
    _, _, _, ssty = math_tables(font)
    changed = set()
    candidates = (set(OML.values()) | set(OPS.values()) | MATH_GREEK
                  | {codepoint(c) for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"})
    for cp in sorted(candidates):
        name = unicodedata.name(chr(cp), "")
        if name.startswith("MATHEMATICAL ITALIC "):
            target = name.replace("MATHEMATICAL ITALIC ", "MATHEMATICAL BOLD ITALIC ")
        elif cp == 0x210E:
            target = "MATHEMATICAL BOLD ITALIC SMALL H"
        elif "SCRIPT CAPITAL" in name:
            target = "MATHEMATICAL BOLD SCRIPT CAPITAL " + name[-1]
        elif name.startswith("GREEK "):
            target = "MATHEMATICAL BOLD " + name.removeprefix("GREEK ").replace(" LETTER", "")
        elif name.startswith("LATIN "):
            target = "MATHEMATICAL BOLD " + name.removeprefix("LATIN ").replace(" LETTER", "")
        elif name.startswith("DIGIT "):
            target = "MATHEMATICAL BOLD " + name
        else:
            continue
        try:
            dst_cp = ord(unicodedata.lookup(target))
        except KeyError:
            continue
        if cp not in cmap or dst_cp not in cmap:
            continue
        src, dst = cmap[cp], cmap[dst_cp]
        sources, targets = [src] + ssty.get(src, []), [dst] + ssty.get(dst, [])
        for i, dest in enumerate(targets):
            source = sources[min(i, len(sources) - 1)]
            # Copy the program, rather than drawing it through another pen:
            # a second conversion can round away one-unit contour details.
            cs = copy.copy(bold["CFF "].cff.topDictIndex[0].CharStrings[source])
            install_outline(font, dest, cs, bold["hmtx"][source][0])
            changed.add(dest)
    update_math_metrics(font, changed)
    return changed


def main():
    path = os.path.join(FONTS, "Mills8A-Math.otf")
    font = TTFont(path, recalcTimestamp=False)
    calligraphic = complete_calligraphic(font)
    greek = complete_greek(font)
    complete_rules(font, RULE_THICKNESS)
    bold, bold_names = make_bold(font)
    complete_rules(bold, RULE_THICKNESS + 2 * BOLD_GROW)
    unicode_names = unicode_bold(font, bold)
    # Both math versions expose the completed Unicode bold alphabets.
    unicode_bold(bold, bold)
    font.save(path)
    bold.save(os.path.join(FONTS, "Mills8A-MathBold.otf"))
    print(f"Reconstructed 22 calligraphic capitals ({len(calligraphic)} optical-size glyphs).")
    print(f"Weight-matched {len(greek)} Greek fill-in glyphs; generated {len(bold_names)} bold outlines")
    print(f"and {len(unicode_names)} Unicode bold alphabet glyphs.")


if __name__ == "__main__":
    main()
