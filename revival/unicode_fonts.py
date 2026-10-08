"""Unicode supplements and mark positioning for the Mills 8A text fonts."""
import math
import subprocess
import unicodedata
from functools import lru_cache

from fontTools.agl import UV2AGL
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

MARKS = {0x300: "grave", 0x301: "acute", 0x302: "circumflex", 0x303: "tilde",
         0x304: "macron", 0x306: "breve", 0x307: "dotaccent", 0x308: "dieresis",
         0x30A: "ring", 0x30B: "hungarumlaut", 0x30C: "caron",
         0x327: "cedilla", 0x328: "ogonek"}
BELOW = {0x327, 0x328}


def bounds(font, name):
    glyphs = font.getGlyphSet()
    pen = BoundsPen(glyphs)
    glyphs[name].draw(pen)
    return pen.bounds


def record(font, name, transform=(1, 0, 0, 1, 0, 0)):
    pen = RecordingPen()
    font.getGlyphSet()[name].draw(TransformPen(pen, transform))
    return pen


def put_glyph(font, name, drawing, advance):
    top = font["CFF "].cff.topDictIndex[0]
    advance = round(advance)
    width = None if advance == top.Private.defaultWidthX else advance - top.Private.nominalWidthX
    pen = T2CharStringPen(width, None, roundTolerance=0)
    drawing.replay(pen)
    charstring = pen.getCharString(top.Private, top.GlobalSubrs)
    order = list(font.getGlyphOrder())
    if name not in top.CharStrings.charStrings:
        top.CharStrings.charStringsIndex.append(charstring)
        top.CharStrings.charStrings[name] = len(top.CharStrings.charStringsIndex) - 1
        order.append(name)
        top.charset = order
        font.setGlyphOrder(order)
        font["maxp"].numGlyphs = len(order)
    else:
        top.CharStrings[name] = charstring
    box = charstring.calcBounds(None)
    font["hmtx"].metrics[name] = (round(advance), round(box[0]) if box else 0)


def map_character(font, cp, name):
    for table in font["cmap"].tables:
        if table.isUnicode() and (table.format != 4 or cp < 0x10000):
            table.cmap[cp] = name


@lru_cache(maxsize=4)
def latin_modern(italic, bold):
    style = "bolditalic" if italic and bold else "italic" if italic else "bold" if bold else "regular"
    path = subprocess.run(["kpsewhich", f"lmroman10-{style}.otf"],
                          check=True, capture_output=True, text=True).stdout.strip()
    if not path:
        raise RuntimeError(f"Latin Modern {style} is required (install TeX Live fonts).")
    return TTFont(path)


def mark_position(font, name, mark_cp, gap=45):
    box = bounds(font, name)
    slant = -math.tan(math.radians(font["post"].italicAngle))
    if mark_cp in BELOW:
        # Ogoneks attach at the right foot; cedillas sit below the centre.
        x = box[2] - 25 if mark_cp == 0x328 else (box[0] + box[2]) / 2
        return x, box[1]
    y = box[3] + gap
    x = (box[0] + box[2]) / 2 + slant * (y - (box[1] + box[3]) / 2)
    return x, y


def compose(font, base, mark_cp):
    mark = f"uni{mark_cp:04X}"
    x, y = mark_position(font, base, mark_cp)
    drawing = record(font, base)
    drawing.value.extend(record(font, mark, (1, 0, 0, 1, x, y)).value)
    return drawing


def add_unicode(font):
    style = font["name"].getDebugName(2)
    donor = latin_modern("Italic" in style, "Bold" in style)
    cmap = font.getBestCmap()
    donor_cmap = donor.getBestCmap()
    xheight = bounds(font, cmap[ord("x")])[3]
    capheight = bounds(font, cmap[ord("H")])[3]

    def borrow(cp, name=None):
        source = donor_cmap.get(cp)
        if source is None:
            return False
        name = name or UV2AGL.get(cp) or f"uni{cp:04X}"
        lower = chr(cp).islower()
        scale = (xheight / donor["OS/2"].sxHeight if lower
                 else capheight / donor["OS/2"].sCapHeight)
        put_glyph(font, name, record(donor, source, (scale, 0, 0, scale, 0, 0)),
                  donor["hmtx"][source][0] * scale)
        map_character(font, cp, name)
        cmap[cp] = name
        return True

    # Build zero-advance marks from the existing accents wherever possible.
    for cp, accent in MARKS.items():
        name = f"uni{cp:04X}"
        if name not in font.getGlyphOrder():
            source_font = font if accent in font.getGlyphOrder() else donor
            box = bounds(source_font, accent)
            scale = 1 if source_font is font else xheight / donor["OS/2"].sxHeight
            dx = -(box[0] + box[2]) / 2 * scale
            dy = -(box[3] if cp in BELOW else box[1]) * scale
            put_glyph(font, name, record(source_font, accent,
                                        (scale, 0, 0, scale, dx, dy)), 0)
        map_character(font, cp, name)
        cmap[cp] = name

    for cp in list(range(0xA1, 0x180)) + [0x20AC, 0x2122]:
        if cp in cmap:
            continue
        decomposition = unicodedata.normalize("NFD", chr(cp))
        if (len(decomposition) == 2 and ord(decomposition[0]) in cmap
                and ord(decomposition[1]) in MARKS
                and not (ord(decomposition[1]) == 0x30C and decomposition[0] in "dlLt")):
            base = cmap[ord(decomposition[0])]
            if decomposition[0] in "ij" and ord(decomposition[1]) not in BELOW:
                base = cmap[0x131 if decomposition[0] == "i" else 0x237]
            name = UV2AGL.get(cp) or f"uni{cp:04X}"
            put_glyph(font, name, compose(font, base, ord(decomposition[1])),
                      font["hmtx"][cmap[ord(decomposition[0])]][0])
            map_character(font, cp, name)
            cmap[cp] = name
        else:
            borrow(cp)

    for cp, source in ((0xA0, "space"), (0xAD, "hyphen"), (0x2011, "hyphen")):
        map_character(font, cp, source)
    space = font["hmtx"]["space"][0]
    for cp, width in ((0x2002, 500), (0x2003, 1000), (0x2009, 200), (0x202F, 200)):
        name = f"uni{cp:04X}"
        if name not in font.getGlyphOrder():
            put_glyph(font, name, RecordingPen(), min(space, width) if cp == 0x202F else width)
        map_character(font, cp, name)


def add_accented_smallcaps(font):
    if "a.sc" not in font.getGlyphOrder():
        return
    cmap = font.getBestCmap()
    smallheight = bounds(font, "h.sc")[3]
    capheight = bounds(font, cmap[ord("H")])[3]
    for cp, name in sorted(cmap.items()):
        ch = chr(cp)
        if not ch.islower() or not (cp <= 0x17F or cp == 0x237):
            continue
        target = name + ".sc"
        if target in font.getGlyphOrder():
            continue
        decomposition = unicodedata.normalize("NFD", ch)
        if (len(decomposition) == 2 and ord(decomposition[1]) in MARKS
                and cmap.get(ord(decomposition[0]), "") + ".sc" in font.getGlyphOrder()):
            base = cmap[ord(decomposition[0])] + ".sc"
            put_glyph(font, target, compose(font, base, ord(decomposition[1])),
                      font["hmtx"][base][0])
        elif ch == "ß":
            advance = font["hmtx"]["s.sc"][0]
            drawing = record(font, "s.sc")
            drawing.value.extend(record(font, "s.sc", (1, 0, 0, 1, advance, 0)).value)
            put_glyph(font, target, drawing, 2 * advance)
        elif ch in "ıȷſ":
            base = {"ı": "i.sc", "ȷ": "j.sc", "ſ": "s.sc"}[ch]
            put_glyph(font, target, record(font, base), font["hmtx"][base][0])
        elif len(ch.upper()) == 1 and ord(ch.upper()) in cmap:
            source = cmap[ord(ch.upper())]
            scale = smallheight / capheight
            put_glyph(font, target, record(font, source, (scale, 0, 0, scale, 0, 0)),
                      font["hmtx"][source][0] * scale)


def substitution_features(font):
    rules = {}
    for feature in font["GSUB"].table.FeatureList.FeatureRecord:
        if feature.FeatureTag == "ccmp":
            continue
        lines = []
        for index in feature.Feature.LookupListIndex:
            lookup = font["GSUB"].table.LookupList.Lookup[index]
            for sub in lookup.SubTable:
                if hasattr(sub, "mapping"):
                    lines.extend(f"sub {a} by {b};" for a, b in sorted(sub.mapping.items()))
                elif hasattr(sub, "alternates"):
                    lines.extend(f"sub {a} from [{' '.join(b)}];"
                                 for a, b in sorted(sub.alternates.items()))
                elif hasattr(sub, "ligatures"):
                    for first, ligatures in sorted(sub.ligatures.items()):
                        lines.extend(f"sub {first} {' '.join(lig.Component)} by {lig.LigGlyph};"
                                     for lig in ligatures)
                else:
                    raise ValueError(f"Unsupported {feature.FeatureTag} lookup {lookup.LookupType}")
        rules[feature.FeatureTag] = lines
    order = set(font.getGlyphOrder())
    smallcaps = {name: name + ".sc" for name in set(font.getBestCmap().values())
                 if name + ".sc" in order}
    if smallcaps:
        rules["smcp"] = [f"sub {a} by {b};" for a, b in sorted(smallcaps.items())]
    return rules


def add_mark_features(font):
    rules = substitution_features(font)
    lines = ["languagesystem DFLT dflt;", "languagesystem latn dflt;"]
    for cp in MARKS:
        kind = "BOTTOM" if cp in BELOW else "TOP"
        if cp == 0x328:
            kind = "OGONEK"
        lines.append(f"markClass uni{cp:04X} <anchor 0 0> @{kind};")
    above = " ".join(f"uni{cp:04X}" for cp in MARKS if cp not in BELOW)
    lines.append(f"@aboveMarks = [{above}];")
    lines.append("feature ccmp { sub i' @aboveMarks by dotlessi; "
                 "sub j' @aboveMarks by uni0237; } ccmp;")
    # Convert letters before f-ligatures consume them. The small caps have
    # separate F and I/L sorts, not lowercase fi/ffi ligatures.
    for tag in ("smcp", "liga", "onum", "rand"):
        if tag in rules:
            lines.append(f"feature {tag} {{ {' '.join(rules.pop(tag))} }} {tag};")
    if rules:
        raise ValueError(f"Unexpected text features: {sorted(rules)}")
    lines.append("feature mark {")
    marknames = {f"uni{cp:04X}" for cp in MARKS}
    for name in font.getGlyphOrder():
        if name in marknames or name == ".notdef":
            continue
        box = bounds(font, name)
        if box is None:
            continue
        top = mark_position(font, name, 0x301)
        bottom = mark_position(font, name, 0x327)
        ogonek = mark_position(font, name, 0x328)
        lines.append(f"pos base {name} <anchor {round(top[0])} {round(top[1])}> mark @TOP "
                     f"<anchor {round(bottom[0])} {round(bottom[1])}> mark @BOTTOM "
                     f"<anchor {round(ogonek[0])} {round(ogonek[1])}> mark @OGONEK;")
    lines.append("} mark;")
    lines.append("feature mkmk {")
    for cp in MARKS:
        name = f"uni{cp:04X}"
        kind = "OGONEK" if cp == 0x328 else "BOTTOM" if cp in BELOW else "TOP"
        box = bounds(font, name)
        x = (box[0] + box[2]) / 2
        y = box[1] - 45 if cp in BELOW else box[3] + 45
        lines.append(f"pos mark {name} <anchor {round(x)} {round(y)}> mark @{kind};")
    lines.append("} mkmk;")
    addOpenTypeFeaturesFromString(font, "\n".join(lines), tables=["GSUB", "GPOS", "GDEF"])
