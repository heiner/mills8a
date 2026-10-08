"""Mills 8A for pdfLaTeX, using only standard TeX font machinery.

Everything here is classic: Type 1 fonts, TFM metrics (from property lists
through pltotf, or from otftotfm), virtual fonts, encoding vectors, a
pdftex map file, .fd files and a small package, mills8a.sty.

* Text (T1): otftotfm on the OpenType fonts, with the f-ligatures in the TFM
  ligature table; small caps as a separate font; bold; the 9pt cut.
* Math, as TeX has always done it, one font per family and size:
    operators (OT1-like, family 0)  letters, figures, + = ( ) [ ] ...
    letters   (OML, family 1)       math italic and Greek
    symbols   (OMS, family 2)       − → ∞ ... and the TeX math parameters
    largesymbols (OMX, family 3)    cmex10 with the 1947 sum and product (VF)
  each at text (11pt), script (6.48pt) and scriptscript (5.51pt) size.  The
  script fonts are the ssty variants of Mills8A-Math.otf -- the real 1947
  script sorts where they exist -- so pdfLaTeX gets them through ordinary
  size-specific fonts (like cmmi7, cmmi5) rather than an OpenType feature.

Large symbols (OMX) are a virtual font: cmex10, except the summation and
display product, which are the 1947 sorts.  What does not carry over: the
random impressions (one master per letter) and the baseline wobble.

Writes fonts/ (tfm, vf, pfb, enc, mills8a.map) and tex/ (mills8a.sty, *.fd).
"""
import datetime
import os
import re
import subprocess
import tempfile

from fontTools.ttLib import TTFont
from fontTools import subset

VERSION = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                            "VERSION")).read().strip()

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "fonts")
OUT = os.path.join(HERE, "fonts")
TEX = os.path.join(HERE, "tex")

SCRIPT, SSCRIPT = 0.589, 0.501          # measured script / scriptscript scale
TEXT_PT = 11.0


def run(*cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


# ------------------------------------------------------------------ text

TEXT_FONTS = [
    # otf, tfm name, features
    ("Mills8A-Regular.otf", "m8ar8t", ["liga"]),
    ("Mills8A-Regular.otf", "m8arc8t", ["liga", "smcp"]),
    ("Mills8A-Italic.otf", "m8ari8t", ["liga"]),
    ("Mills8A-Bold.otf", "m8ab8t", ["liga"]),
    ("Mills8A-BoldItalic.otf", "m8abi8t", ["liga"]),
    ("Mills8A-Regular9.otf", "m8ar98t", ["liga"]),
    ("Mills8A-Regular9.otf", "m8ar9c8t", ["liga", "smcp"]),
    ("Mills8A-Bold.otf", "m8abc8t", ["liga", "smcp"]),
    ("Mills8A-Italic9.otf", "m8ari98t", ["liga"]),
    # the same with old-style figures (family m8aj, option osf)
    ("Mills8A-Regular.otf", "m8arj8t", ["liga", "onum"]),
    ("Mills8A-Regular.otf", "m8arcj8t", ["liga", "smcp", "onum"]),
    ("Mills8A-Italic.otf", "m8arij8t", ["liga", "onum"]),
    ("Mills8A-Bold.otf", "m8abj8t", ["liga", "onum"]),
    ("Mills8A-BoldItalic.otf", "m8abij8t", ["liga", "onum"]),
    ("Mills8A-Regular9.otf", "m8ar9j8t", ["liga", "onum"]),
    ("Mills8A-Regular9.otf", "m8ar9cj8t", ["liga", "smcp", "onum"]),
    ("Mills8A-Bold.otf", "m8abcj8t", ["liga", "smcp", "onum"]),
    ("Mills8A-Italic9.otf", "m8ari9j8t", ["liga", "onum"]),
]


SYM_ENC = """/m8asym [ /section /dagger /daggerdbl /paragraph /Euro /trademark
""" + " ".join(["/.notdef"] * 250) + """ ] def
"""


def text_fonts():
    maplines = []
    done = set()
    for otf, name, feats in TEXT_FONTS:
        args = ["otftotfm", "-e", "ec", "--no-type1", "--no-updmap", "--force"]
        args += [f"-f{f}" for f in feats]
        r = run(*args, os.path.join(SRC, otf), name, cwd=OUT)
        for line in r.stdout.splitlines():
            if line.strip():
                maplines.append(re.sub(r"<([\w-]+)\.otf", r"<\1.pfb", line))
        if otf not in done:
            run("cfftot1", os.path.join(SRC, otf), otf[:-4] + ".pfb", cwd=OUT)
            done.add(otf)
    # § † ‡ ¶ (LaTeX takes them from TS1): a small font in its own encoding
    with open(os.path.join(OUT, "m8asym.enc"), "w") as fh:
        fh.write(SYM_ENC)
    r = run("otftotfm", "-e", "m8asym.enc", "--no-type1", "--no-updmap", "--force",
            os.path.join(SRC, "Mills8A-Regular.otf"), "m8asym", cwd=OUT)
    for line in r.stdout.splitlines():
        if line.strip():
            maplines.append(re.sub(r"<([\w-]+)\.otf", r"<\1.pfb", line))
    return maplines


# ------------------------------------------------------------------ math

OML = {}            # slot -> unicode
# italic capital Greek (U+1D6E4.. in order ΓΔΘΛΞΠΣΥΦΨΩ)
for i, cp in enumerate([0x1D6E4, 0x1D6E5, 0x1D6E9, 0x1D6EC, 0x1D6EF, 0x1D6F1, 0x1D6F4,
                        0x1D6F6, 0x1D6F7, 0x1D6F9, 0x1D6FA]):
    OML[i] = cp
# lowercase Greek: α β γ δ ϵ ζ η θ ι κ λ μ ν ξ π ρ σ τ υ ϕ χ ψ ω ε ϑ ϖ ϱ ς φ
for i, cp in enumerate([0x1D6FC, 0x1D6FD, 0x1D6FE, 0x1D6FF, 0x1D716, 0x1D701, 0x1D702, 0x1D703,
                        0x1D704, 0x1D705, 0x1D706, 0x1D707, 0x1D708, 0x1D709, 0x1D70B, 0x1D70C,
                        0x1D70E, 0x1D70F, 0x1D710, 0x1D719, 0x1D712, 0x1D713, 0x1D714, 0x1D700,
                        0x1D717, 0x1D71B, 0x1D71A, 0x1D70D, 0x1D711]):
    OML[0x0B + i] = cp
OML.update({0x3A: ord("."), 0x3B: ord(","), 0x3C: ord("<"), 0x3D: ord("/"), 0x3E: ord(">"),
            0x40: 0x2202, 0x60: 0x2113, 0x7B: 0x1D6A4, 0x7C: 0x1D6A5, 0x7D: 0x2118})
for i in range(26):
    OML[0x41 + i] = 0x1D434 + i
    OML[0x61 + i] = 0x210E if i == 7 else 0x1D44E + i

OMS = {0x00: 0x2212, 0x01: 0x22C5, 0x02: 0x00D7, 0x03: 0x2217, 0x04: 0x00F7, 0x05: 0x22C4,
       0x06: 0x00B1, 0x07: 0x2213, 0x08: 0x2295, 0x09: 0x2296, 0x0A: 0x2297, 0x0B: 0x2298,
       0x0C: 0x2299, 0x0D: 0x25EF, 0x0E: 0x2218, 0x0F: 0x2219, 0x10: 0x224D, 0x11: 0x2261,
       0x12: 0x2286, 0x13: 0x2287, 0x14: 0x2264, 0x15: 0x2265, 0x16: 0x2AAF, 0x17: 0x2AB0,
       0x18: 0x223C, 0x19: 0x2248, 0x1A: 0x2282, 0x1B: 0x2283, 0x1C: 0x226A, 0x1D: 0x226B,
       0x1E: 0x227A, 0x1F: 0x227B, 0x20: 0x2190, 0x21: 0x2192, 0x22: 0x2191, 0x23: 0x2193,
       0x24: 0x2194, 0x25: 0x2197, 0x26: 0x2198, 0x27: 0x2243, 0x28: 0x21D0, 0x29: 0x21D2,
       0x2A: 0x21D1, 0x2B: 0x21D3, 0x2C: 0x21D4, 0x2D: 0x2196, 0x2E: 0x2199, 0x2F: 0x221D,
       0x30: 0x2032, 0x31: 0x221E, 0x32: 0x2208, 0x33: 0x220B, 0x34: 0x25B3, 0x35: 0x25BD,
       0x36: 0x0338, 0x38: 0x2200, 0x39: 0x2203, 0x3A: 0x00AC, 0x3B: 0x2205, 0x3C: 0x211C,
       0x3D: 0x2111, 0x3E: 0x22A4, 0x3F: 0x22A5, 0x40: 0x2135, 0x5B: 0x222A, 0x5C: 0x2229,
       0x5D: 0x228E, 0x5E: 0x2227, 0x5F: 0x2228, 0x60: 0x22A2, 0x61: 0x22A3, 0x62: 0x230A,
       0x63: 0x230B, 0x64: 0x2308, 0x65: 0x2309, 0x66: ord("{"), 0x67: ord("}"), 0x68: 0x27E8,
       0x69: 0x27E9, 0x6A: ord("|"), 0x6B: 0x2016, 0x6C: 0x2195, 0x6D: 0x21D5, 0x6E: ord("\\"),
       0x6F: 0x2240, 0x70: 0x221A, 0x71: 0x2A3F, 0x72: 0x2207, 0x73: 0x222B, 0x74: 0x2294,
       0x75: 0x2293, 0x76: 0x2291, 0x77: 0x2292, 0x78: 0x00A7, 0x79: 0x2020, 0x7A: 0x2021,
       0x7B: 0x00B6, 0x7C: 0x2663, 0x7D: 0x2662, 0x7E: 0x2661, 0x7F: 0x2660}
SCRIPT_CAPS = {"B": 0x212C, "E": 0x2130, "F": 0x2131, "H": 0x210B, "I": 0x2110,
               "L": 0x2112, "M": 0x2133, "R": 0x211B}   # not in the U+1D49C run
for i in range(26):                       # calligraphic capitals
    OMS[0x41 + i] = SCRIPT_CAPS.get(chr(0x41 + i), 0x1D49C + i)

# operators: OT1-like layout of upright Greek capitals, letters, figures,
# punctuation and the math accents
OPS = {}
for c in "!()*+,-./0123456789:;=?[]ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz":
    OPS[ord(c)] = ord(c)
for i, cp in enumerate([0x393, 0x394, 0x398, 0x39B, 0x39E, 0x3A0, 0x3A3, 0x3A5, 0x3A6, 0x3A8,
                        0x3A9]):
    OPS[i] = cp
# accents as spacing glyphs made for TeX in Mills8A-Math.otf (tex.acc.*)
OPS_NAMED = {0x12: "tex.acc.0300", 0x13: "tex.acc.0301", 0x14: "tex.acc.030C",
             0x15: "tex.acc.0306", 0x16: "tex.acc.0304", 0x17: "tex.acc.030A",
             0x5E: "tex.acc.0302", 0x5F: "tex.acc.0307", 0x7E: "tex.acc.0303",
             0x7F: "tex.acc.0308"}
# relations with no slot in the standard layouts: a small U-encoded font
EXTRA = {0: 0x2260, 1: 0x2266, 2: 0x2267, 3: 0x2245}     # ≠ ≦ ≧ ≅


def math_tables(f):
    math = f["MATH"].table
    ic = dict(zip(math.MathGlyphInfo.MathItalicsCorrectionInfo.Coverage.glyphs,
                  [v.Value for v in math.MathGlyphInfo.MathItalicsCorrectionInfo.ItalicsCorrection]))
    ta = math.MathGlyphInfo.MathTopAccentAttachment
    acc = dict(zip(ta.TopAccentCoverage.glyphs, [v.Value for v in ta.TopAccentAttachment]))
    ssty = {}
    gsub = f["GSUB"].table
    for fr in gsub.FeatureList.FeatureRecord:
        if fr.FeatureTag == "ssty":
            for li in fr.Feature.LookupListIndex:
                for st in gsub.LookupList.Lookup[li].SubTable:
                    ssty.update(st.alternates)
    return math, ic, acc, ssty


def glyph_for(f, cmap, ssty, cp, level, fallback=None):
    """Glyph name for code point cp at script level 0/1/2 in font f."""
    g = cmap.get(cp)
    if g is None and fallback:
        g = fallback.get(cp)
    if g is None:
        return None
    if level and g in ssty and len(ssty[g]) >= level and ssty[g][level - 1] in f.getGlyphOrder():
        g = ssty[g][level - 1]
    return g


def make_tex_font(name, f, glyphs, design_pt, family, fontdimens, ic=None, acc=None,
                  skewchar=None):
    """glyphs: {slot: glyph name}.  Writes name.pfb (a renamed subset of f),
    name.enc and name.tfm (via a property list); returns the map line."""
    ic, acc = ic or {}, acc or {}
    # subset to the glyphs, renamed so each TeX font is its own PS font
    psname = f"Mills8A-TeX-{name}"
    sub = TTFont(f.reader.file.name)
    opts = subset.Options()
    opts.glyph_names = True
    opts.notdef_outline = True
    opts.layout_features = []
    opts.drop_tables += ["MATH", "GSUB", "GPOS", "GDEF"]
    s = subset.Subsetter(opts)
    s.populate(glyphs=sorted(set(glyphs.values())))
    s.subset(sub)
    cff = sub["CFF "].cff
    cff.fontNames[0] = psname
    cff.topDictIndex[0].FullName = psname
    otf = os.path.join(OUT, name + ".otf")
    sub.save(otf)
    run("cfftot1", otf, name + ".pfb", cwd=OUT)
    os.remove(otf)
    # encoding vector
    vec = ["/.notdef"] * 256
    for slot, g in glyphs.items():
        vec[slot] = "/" + g
    enc = f"{name}-enc"
    with open(os.path.join(OUT, name + ".enc"), "w") as fh:
        fh.write(f"/{enc} [\n" + "\n".join(vec) + "\n] def\n")
    # metrics in design units (1000 per design size)
    gs = sub.getGlyphSet()
    hmtx = sub["hmtx"]
    from fontTools.pens.boundsPen import BoundsPen
    # values in em (PL limits reals to < 2048, too small for 1000 units);
    # SLANT is a ratio, everything else font units
    pl = [f"(FAMILY {family})", f"(DESIGNSIZE R {design_pt:.4f})",
          "(CODINGSCHEME MILLS8A)", "(FONTDIMEN"]
    for k, v in fontdimens:
        pl.append(f"   ({k} R {v if k == 'SLANT' else v / 1000:.5f})")
    pl.append("   )")
    for slot in sorted(glyphs):
        g = glyphs[slot]
        bp = BoundsPen(gs)
        gs[g].draw(bp)
        b = bp.bounds or (0, 0, 0, 0)
        pl.append(f"(CHARACTER O {slot:o}")
        pl.append(f"   (CHARWD R {hmtx[g][0] / 1000:.5f})")
        if b[3] > 0:
            pl.append(f"   (CHARHT R {b[3] / 1000:.5f})")
        if b[1] < 0:
            pl.append(f"   (CHARDP R {-b[1] / 1000:.5f})")
        if ic.get(g):
            pl.append(f"   (CHARIC R {ic[g] / 1000:.5f})")
        pl.append("   )")
    if skewchar is not None:
        # accent placement: kern with the skew character, as in cmmi
        kerns = []
        for slot, g in sorted(glyphs.items()):
            if g in acc:
                k = acc[g] - hmtx[g][0] / 2
                if abs(k) > 5:
                    kerns.append(f"   (LABEL O {slot:o})\n   (KRN O {skewchar:o} R {k / 1000:.5f})\n   (STOP)")
        if kerns:
            pl.append("(LIGTABLE\n" + "\n".join(kerns) + "\n   )")
    with open(os.path.join(OUT, name + ".pl"), "w") as fh:
        fh.write("\n".join(pl) + "\n")
    run("pltotf", name + ".pl", name + ".tfm", cwd=OUT)
    return f'{name} {psname} "{enc} ReEncodeFont" <{name}.enc <{name}.pfb'


def math_fonts():
    f = TTFont(os.path.join(SRC, "Mills8A-Math.otf"))
    reg = TTFont(os.path.join(SRC, "Mills8A-Regular.otf"))
    cmap = f.getBestCmap()
    math, ic, acc, ssty = math_tables(f)
    mc = math.MathConstants
    v = lambda x: getattr(x, "Value", x)
    lines = []
    for level, suffix, size in ((0, "", TEXT_PT), (1, "s", TEXT_PT * SCRIPT),
                                (2, "ss", TEXT_PT * SSCRIPT)):
        # family 1: math italic
        g = {s: glyph_for(f, cmap, ssty, cp, level) for s, cp in OML.items()}
        g = {s: n for s, n in g.items() if n}
        g[0x7F] = glyph_for(f, cmap, ssty, 0x2040, level) or g.get(0x3B)   # tie / skewchar
        if "tex.acc.20D7" in f.getGlyphOrder():
            g[0x7E] = "tex.acc.20D7"                                    # \vec
        lines.append(make_tex_font(f"m8ami{suffix}", f, g, size, "MILLS8A-MATHITALIC",
                                   [("SLANT", 0.25), ("SPACE", 0), ("XHEIGHT", 440),
                                    ("QUAD", 1000)], ic=ic, acc=acc, skewchar=0x7F))
        # family 0: operators
        g = {s: glyph_for(f, cmap, ssty, cp, level) for s, cp in OPS.items()}
        g = {s: n for s, n in g.items() if n}
        g.update({s: n for s, n in OPS_NAMED.items() if n in f.getGlyphOrder()})
        lines.append(make_tex_font(f"m8aop{suffix}", f, g, size, "MILLS8A-OPERATORS",
                                   [("SLANT", 0), ("SPACE", 322), ("STRETCH", 161),
                                    ("SHRINK", 107), ("XHEIGHT", 440), ("QUAD", 1000),
                                    ("EXTRASPACE", 107)]))
        # family 2: symbols, with TeX's math parameters (fontdimens 8-22)
        g = {s: glyph_for(f, cmap, ssty, cp, level) for s, cp in OMS.items()}
        g = {s: n for s, n in g.items() if n}
        if "tex.mapstochar" in f.getGlyphOrder():
            g[0x37] = "tex.mapstochar"
        dims = [("SLANT", 0.25), ("SPACE", 0), ("STRETCH", 0), ("SHRINK", 0),
                ("XHEIGHT", 440), ("QUAD", 1000), ("EXTRASPACE", 0),
                ("NUM1", v(mc.FractionNumeratorDisplayStyleShiftUp)),
                ("NUM2", v(mc.FractionNumeratorShiftUp)),
                ("NUM3", v(mc.StackTopShiftUp)),
                ("DENOM1", v(mc.FractionDenominatorDisplayStyleShiftDown)),
                ("DENOM2", v(mc.FractionDenominatorShiftDown)),
                ("SUP1", v(mc.SuperscriptShiftUp)),
                ("SUP2", v(mc.SuperscriptShiftUp)),
                ("SUP3", v(mc.SuperscriptShiftUpCramped)),
                ("SUB1", v(mc.SubscriptShiftDown)),
                ("SUB2", max(v(mc.SubscriptShiftDown), 200)),
                ("SUPDROP", v(mc.SuperscriptBaselineDropMax)),
                ("SUBDROP", v(mc.SubscriptBaselineDropMin)),
                ("DELIM1", 2390), ("DELIM2", 1010),
                ("AXISHEIGHT", v(mc.AxisHeight))]
        if level:
            # a superscript on an index, as on the Mills page ([A^{3^x}]): in
            # the index size, its foot 28 px above the 3's at 600 dpi, i.e.
            # 0.52 em of the 6.5 pt index font (cramped: 0.44)
            sup = {"SUP1": 518, "SUP2": 518, "SUP3": 440}
            dims = [(k, sup.get(k, val)) for k, val in dims]
        lines.append(make_tex_font(f"m8asy{suffix}", f, g, size, "MILLS8A-SYMBOLS", dims,
                                   ic=ic, acc=acc, skewchar=0x30))
        g = {s: glyph_for(f, cmap, ssty, cp, level) for s, cp in EXTRA.items()}
        g = {s: n for s, n in g.items() if n}
        lines.append(make_tex_font(f"m8axs{suffix}", f, g, size, "MILLS8A-EXTRA",
                                   [("SLANT", 0), ("XHEIGHT", 440), ("QUAD", 1000)]))
    return lines


# ------------------------------------------------------------------ large symbols

BIG_OPS = {0o120: "summation", 0o130: "summation.v1", 0o131: "product.v1",
           0o132: "integral.v1"}   # cmex slots


def omx_font():
    """m8aex: a virtual font that is cmex10 except for the summation (text
    and display) and the display product, which are the 1947 sorts from
    Mills8A-Math.otf, set from a small Type 1 font at their real 11pt size.
    cmex10's size chains and extensible recipes are kept as they are."""
    from fontTools.pens.boundsPen import BoundsPen
    f = TTFont(os.path.join(SRC, "Mills8A-Math.otf"))
    gs = f.getGlyphSet()
    glyphs = {k: g for k, g in zip(range(len(BIG_OPS)), BIG_OPS.values()) if g in gs}
    line = make_tex_font("m8aexops", f, glyphs, TEXT_PT, "MILLS8A-EXOPS",
                         [("SLANT", 0), ("SPACE", 0), ("QUAD", 1000)])
    k = TEXT_PT / 10.0                     # cmex10's design size is 10pt
    dims = {}
    for slot, g in zip(BIG_OPS, BIG_OPS.values()):
        if g not in gs:
            continue
        bp = BoundsPen(gs)
        gs[g].draw(bp)
        b = bp.bounds
        dims[slot] = (f["hmtx"][g][0] * k / 1000, max(0, b[3]) * k / 1000,
                      max(0, -b[1]) * k / 1000, list(BIG_OPS.values()).index(g))
    pl = run("tftopl", subprocess.run(["kpsewhich", "cmex10.tfm"], capture_output=True,
                                      text=True).stdout.strip()).stdout
    # top-level property lists start in column 0
    items, cur = [], []
    for ln in pl.splitlines():
        if ln.startswith("(") and cur:
            items.append("\n".join(cur))
            cur = []
        cur.append(ln)
    items.append("\n".join(cur))
    out = []
    for it in items:
        m = re.match(r"\(CHARACTER (C (\S)|O ([0-7]+))", it)
        if not m:
            out.append(it)
            if it.startswith("(DESIGNUNITS") or it.startswith("(CHECKSUM"):
                pass
            continue
        code = ord(m.group(2)) if m.group(2) else int(m.group(3), 8)
        body = it.rstrip()
        assert body.endswith(")")
        body = body[:-1].rstrip()
        if code in dims:
            wd, ht, dp, slot = dims[code]
            body = re.sub(r"\n\s*\(CHAR(WD|HT|DP|IC) R [-\d.]+\)", "", body)
            body += (f"\n   (CHARWD R {wd:.6f})\n   (CHARHT R {ht:.6f})\n   (CHARDP R {dp:.6f})"
                     f"\n   (MAP\n      (SELECTFONT D 1)\n      (SETCHAR O {slot:o})\n      )")
        else:
            body += f"\n   (MAP\n      (SELECTFONT D 0)\n      (SETCHAR O {code:o})\n      )"
        out.append(body + "\n   )")
    head_end = next(i for i, it in enumerate(out) if it.startswith("(CHARACTER"))
    out.insert(head_end, "(MAPFONT D 0\n   (FONTNAME cmex10)\n   )\n(MAPFONT D 1\n"
               f"   (FONTNAME m8aexops)\n   (FONTAT R {k:.4f})\n   )")
    with open(os.path.join(OUT, "m8aex.vpl"), "w") as fh:
        fh.write("\n".join(out) + "\n")
    run("vptovf", "m8aex.vpl", "m8aex.vf", "m8aex.tfm", cwd=OUT)
    os.remove(os.path.join(OUT, "m8aex.vpl"))
    return [line]


# ------------------------------------------------------------------ LaTeX

FD = {
    "t1m8a.fd": r"""\ProvidesFile{t1m8a.fd}[@DATE@ v@VERSION@ Mills 8A text, T1, pdfLaTeX]
\DeclareFontFamily{T1}{m8a}{}
\DeclareFontShape{T1}{m8a}{m}{n}{<-10> m8ar98t <10-> m8ar8t}{}
\DeclareFontShape{T1}{m8a}{m}{it}{<-10> m8ari98t <10-> m8ari8t}{}
\DeclareFontShape{T1}{m8a}{m}{sc}{<-10> m8ar9c8t <10-> m8arc8t}{}
\DeclareFontShape{T1}{m8a}{b}{sc}{<-> m8abc8t}{}
\DeclareFontShape{T1}{m8a}{b}{n}{<-> m8ab8t}{}
\DeclareFontShape{T1}{m8a}{b}{it}{<-> m8abi8t}{}
\DeclareFontShape{T1}{m8a}{bx}{n}{<-> ssub * m8a/b/n}{}
\DeclareFontShape{T1}{m8a}{bx}{it}{<-> ssub * m8a/b/it}{}
\DeclareFontShape{T1}{m8a}{bx}{sc}{<-> ssub * m8a/b/sc}{}
""",
    "t1m8aj.fd": r"""\ProvidesFile{t1m8aj.fd}[@DATE@ v@VERSION@ Mills 8A text, old-style figures, T1, pdfLaTeX]
\DeclareFontFamily{T1}{m8aj}{}
\DeclareFontShape{T1}{m8aj}{m}{n}{<-10> m8ar9j8t <10-> m8arj8t}{}
\DeclareFontShape{T1}{m8aj}{m}{it}{<-10> m8ari9j8t <10-> m8arij8t}{}
\DeclareFontShape{T1}{m8aj}{m}{sc}{<-10> m8ar9cj8t <10-> m8arcj8t}{}
\DeclareFontShape{T1}{m8aj}{b}{sc}{<-> m8abcj8t}{}
\DeclareFontShape{T1}{m8aj}{b}{n}{<-> m8abj8t}{}
\DeclareFontShape{T1}{m8aj}{b}{it}{<-> m8abij8t}{}
\DeclareFontShape{T1}{m8aj}{bx}{n}{<-> ssub * m8aj/b/n}{}
\DeclareFontShape{T1}{m8aj}{bx}{it}{<-> ssub * m8aj/b/it}{}
\DeclareFontShape{T1}{m8aj}{bx}{sc}{<-> ssub * m8aj/b/sc}{}
""",
    "omlm8am.fd": r"""\ProvidesFile{omlm8am.fd}[@DATE@ v@VERSION@ Mills 8A math italic, pdfLaTeX]
\DeclareFontFamily{OML}{m8am}{\skewchar\font=127 }
\DeclareFontShape{OML}{m8am}{m}{it}{<-6> m8amiss <6-8> m8amis <8-> m8ami}{}
""",
    "ot1m8aop.fd": r"""\ProvidesFile{ot1m8aop.fd}[@DATE@ v@VERSION@ Mills 8A math operators, pdfLaTeX]
\DeclareFontFamily{OT1}{m8aop}{}
\DeclareFontShape{OT1}{m8aop}{m}{n}{<-6> m8aopss <6-8> m8aops <8-> m8aop}{}
""",
    "omxm8aex.fd": r"""\ProvidesFile{omxm8aex.fd}[@DATE@ v@VERSION@ Mills 8A large symbols, pdfLaTeX]
\DeclareFontFamily{OMX}{m8aex}{}
\DeclareFontShape{OMX}{m8aex}{m}{n}{<-> sfixed * m8aex}{}
""",
    "omsm8asy.fd": r"""\ProvidesFile{omsm8asy.fd}[@DATE@ v@VERSION@ Mills 8A math symbols, pdfLaTeX]
\DeclareFontFamily{OMS}{m8asy}{\skewchar\font=48 }
\DeclareFontShape{OMS}{m8asy}{m}{n}{<-6> m8asyss <6-8> m8asys <8-> m8asy}{}
""",
    "um8axs.fd": r"""\ProvidesFile{um8axs.fd}[@DATE@ v@VERSION@ Mills 8A extra relations, pdfLaTeX]
\DeclareFontFamily{U}{m8axs}{}
\DeclareFontShape{U}{m8axs}{m}{n}{<-6> m8axsss <6-8> m8axss <8-> m8axs}{}
""",
    "um8asym.fd": r"""\ProvidesFile{um8asym.fd}[@DATE@ v@VERSION@ Mills 8A text symbols, pdfLaTeX]
\DeclareFontFamily{U}{m8asym}{}
\DeclareFontShape{U}{m8asym}{m}{n}{<-> m8asym}{}
\DeclareFontShape{U}{m8asym}{b}{n}{<-> ssub * m8asym/m/n}{}
\DeclareFontShape{U}{m8asym}{m}{it}{<-> ssub * m8asym/m/n}{}
""",
    "mills8a.sty": r"""\NeedsTeXFormat{LaTeX2e}
\ProvidesPackage{mills8a}[@DATE@ v@VERSION@ Mills 8A for pdfLaTeX: standard Type 1 / TFM fonts]
\RequirePackage[T1]{fontenc}
% osf: old-style figures in text (the 1947 Bulletin's running-head figures);
% math keeps lining figures, as in print
\newif\ifmills@osf
\DeclareOption{osf}{\mills@osftrue}
\DeclareOption{lf}{\mills@osffalse}
\ProcessOptions\relax
\ifmills@osf\renewcommand\rmdefault{m8aj}\else\renewcommand\rmdefault{m8a}\fi
\renewcommand\encodingdefault{T1}
\pdfmapfile{+mills8a.map}
% math: one font per family and size; the script sizes are the 1947 script
% sorts (measured at 58.9% and 50.1% of the 11pt body)
\DeclareSymbolFont{operators}   {OT1}{m8aop}{m}{n}
\DeclareSymbolFont{letters}     {OML}{m8am}{m}{it}
\DeclareSymbolFont{symbols}     {OMS}{m8asy}{m}{n}
\DeclareSymbolFont{largesymbols}{OMX}{m8aex}{m}{n}
% second-order indices in the first-order size, as 1947 sets them (the
% x of [A^{3^x}] on the Mills page; the 5.5 pt sorts are hard to read)
\DeclareMathSizes{11}{11}{6.48}{6.48}
\DeclareMathSizes{10.95}{11}{6.48}{6.48}
% the 1947 sorts for relations the standard layouts have no slot for;
% set at the start of the document so they win over amssymb's
\DeclareSymbolFont{millsextra}{U}{m8axs}{m}{n}
\def\mills@rel#1#2{\mathchardef#1=\numexpr"3000+\symmillsextra*"100+#2\relax}
\AtBeginDocument{%
  \mills@rel\neq0 \let\ne\neq
  \mills@rel\leqq1 \mills@rel\geqq2 \mills@rel\cong3
  % \cdots as on the 1947 page: dots 0.65 em apart
  \def\mills@cdots{\mathinner{\cdotp\mkern3.75mu\cdotp\mkern3.75mu\cdotp}}%
  \let\@cdots\mills@cdots \DeclareRobustCommand\cdots{\mills@cdots}}
% section, dagger, double dagger and pilcrow from the 1947 text font
\DeclareTextCommand{\textsection}{T1}{{\usefont{U}{m8asym}{m}{n}\char0}}
\DeclareTextCommand{\textdagger}{T1}{{\usefont{U}{m8asym}{m}{n}\char1}}
\DeclareTextCommand{\textdaggerdbl}{T1}{{\usefont{U}{m8asym}{m}{n}\char2}}
\DeclareTextCommand{\textparagraph}{T1}{{\usefont{U}{m8asym}{m}{n}\char3}}
\DeclareTextCommand{\texteuro}{T1}{{\usefont{U}{m8asym}{m}{n}\char4}}
\DeclareTextCommand{\texttrademark}{T1}{{\usefont{U}{m8asym}{m}{n}\char5}}
\endinput
""",
}


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(TEX, exist_ok=True)
    lines = text_fonts() + math_fonts() + omx_font()
    with open(os.path.join(OUT, "mills8a.map"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    date = datetime.date.today().strftime("%Y/%m/%d")
    for fn, body in FD.items():
        body = body.replace("@DATE@", date).replace("@VERSION@", VERSION)
        with open(os.path.join(TEX, fn), "w") as fh:
            fh.write("% Copyright 2026 heiner. MIT License, see LICENSE.\n" + body)
    for fn in os.listdir(OUT):
        if fn.endswith(".pl"):
            os.remove(os.path.join(OUT, fn))
    print(f"{len(lines)} map lines; fonts in {OUT}")


if __name__ == "__main__":
    main()
