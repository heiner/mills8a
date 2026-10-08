"""Construct the 22 calligraphic capitals missing from the historical scans.

These are new drawings, not recovered Monotype sorts and not a substitution
of another font. A, C, L and U remain the historical outlines. The drawings
use their roundhand vocabulary: looped entrances, broad curved downstrokes,
oval counters and curled terminals. Coordinates are in the 1000-unit em,
y upwards; the nominal cap line is 700. Each stroke is (nib rx, nib ry,
SVG centreline). Thin connecting strokes use a smaller nib.

Requires fontTools and skia-pathops. Kept separate from the font builder so
the design can be edited and reviewed without rebuilding from page scans.
"""

import pathops
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.svgLib.path import parse_path


HISTORICAL = "ACLU"
# The historical outlines' 99th-percentile inscribed stroke radius is
# about 28 units at half-em raster scale; the unscaled pen drawings are
# about 17. This factor brings the reconstructed strokes to that weight.
NIB_SCALE = 1.6
SCRIPT_EXCEPTIONS = {"B": 0x212C, "E": 0x2130, "F": 0x2131, "H": 0x210B,
                     "I": 0x2110, "L": 0x2112, "M": 0x2133, "R": 0x211B}


def codepoint(letter):
    return SCRIPT_EXCEPTIONS.get(letter, 0x1D49C + ord(letter) - ord("A"))


# Broad strokes use an oval nib; fine strokes and terminals are drawn
# separately. In particular the bowl joins are fine rather than monoline.
STROKES = {
    "B": [
        (35, 14, "M 120,20 C 230,-30 285,100 325,265 C 365,420 400,565 445,650"),
        (15, 12, "M 150,555 C 80,730 355,765 545,680"),
        (34, 14, "M 545,680 C 815,545 630,350 345,350"),
        (35, 14, "M 345,350 C 720,450 780,80 450,10 C 290,-25 195,10 240,90"),
    ],
    "D": [
        (35, 14, "M 100,15 C 200,-35 260,70 300,240 C 345,430 375,565 430,655"),
        (15, 12, "M 135,545 C 35,680 240,760 475,695"),
        (37, 14, "M 475,695 C 905,585 845,105 485,15 C 290,-35 140,30 195,145"),
    ],
    "E": [
        (35, 14, "M 530,580 C 650,735 385,770 245,635 C 125,505 225,355 385,360"),
        (15, 12, "M 385,360 C 535,380 475,465 350,390"),
        (37, 14, "M 350,390 C 160,340 55,170 155,45 C 240,-65 470,-15 550,135"),
        (23, 20, "M 526,575 L 530,580"),
    ],
    "F": [
        (35, 14, "M 490,665 C 385,540 345,360 285,170 C 230,-25 100,-75 75,25 C 60,90 125,105 150,65"),
        (18, 13, "M 195,540 C 95,655 280,750 465,705 C 635,650 710,645 755,740"),
        (17, 12, "M 220,355 C 345,400 425,390 550,425"),
    ],
    "G": [
        (37, 14, "M 640,575 C 755,740 545,785 330,645 C 100,485 55,180 190,55 C 300,-50 455,60 515,180"),
        (17, 12, "M 400,225 C 480,260 550,265 610,245"),
        (33, 14, "M 565,250 C 525,70 525,-120 365,-170 C 245,-210 180,-125 240,-75"),
        (23, 20, "M 637,570 L 640,575"),
    ],
    "H": [
        (35, 14, "M 95,20 C 215,-40 245,155 300,350 C 345,535 405,720 330,715 C 255,710 210,620 250,575"),
        (35, 14, "M 730,700 C 645,480 570,230 575,80 C 580,-5 675,-10 730,90"),
        (16, 12, "M 240,305 C 390,400 560,320 655,425"),
    ],
    "I": [
        (35, 14, "M 460,660 C 365,475 325,235 255,95 C 190,-35 90,-25 80,50 C 70,100 125,130 150,80"),
        (17, 12, "M 240,610 C 185,690 330,745 470,685 C 550,650 605,650 635,700"),
    ],
    "J": [
        (36, 14, "M 555,680 C 485,490 455,260 365,35 C 280,-185 95,-210 80,-90 C 70,-20 145,5 165,-55"),
        (17, 12, "M 290,590 C 235,705 415,750 565,685 C 650,645 710,655 735,710"),
    ],
    "K": [
        (35, 14, "M 95,20 C 215,-40 245,155 300,350 C 345,535 405,720 330,715 C 255,710 210,620 250,575"),
        (17, 12, "M 305,285 C 505,460 650,705 750,690 C 805,680 775,610 725,620"),
        (36, 14, "M 435,420 C 530,335 505,150 570,45 C 615,-30 715,-10 755,95"),
    ],
    "M": [
        (18, 12, "M 75,25 C 185,-85 235,155 300,370 C 350,540 390,655 425,685"),
        (35, 14, "M 425,685 C 370,445 385,230 435,80"),
        (18, 12, "M 435,80 C 530,330 665,595 750,690"),
        (35, 14, "M 750,690 C 670,430 635,245 655,100 C 665,-5 770,-25 825,100"),
        (16, 12, "M 185,585 C 110,685 305,765 425,685"),
    ],
    "N": [
        (18, 12, "M 70,30 C 195,-80 230,130 295,355 C 345,530 385,650 425,690"),
        (35, 14, "M 425,690 C 360,405 460,165 540,25"),
        (18, 12, "M 540,25 C 535,255 640,610 730,690 C 795,750 845,680 800,630"),
        (16, 12, "M 185,585 C 110,685 305,765 425,690"),
    ],
    "O": [
        (37, 14, "M 610,635 C 490,795 255,625 160,405 C 35,110 195,-65 415,45 C 650,170 755,570 610,635"),
        (16, 12, "M 610,635 C 495,725 395,590 455,510 C 500,450 605,465 635,535"),
    ],
    "P": [
        (35, 14, "M 90,10 C 220,-55 260,125 310,315 C 355,495 395,595 440,660"),
        (16, 12, "M 145,555 C 55,700 285,770 525,690"),
        (36, 14, "M 525,690 C 830,580 655,320 365,355"),
    ],
    "Q": [
        (37, 14, "M 600,635 C 480,795 255,625 160,405 C 35,110 195,-65 415,45 C 650,170 745,570 600,635"),
        (17, 12, "M 255,60 C 180,-5 205,-90 300,-80 C 420,-65 455,95 555,20"),
        (31, 14, "M 555,20 C 655,-70 740,-35 760,45"),
    ],
    "R": [
        (35, 14, "M 90,10 C 220,-55 260,125 310,315 C 355,495 395,595 440,660"),
        (16, 12, "M 145,555 C 55,700 285,770 525,690"),
        (35, 14, "M 525,690 C 830,580 655,355 350,355"),
        (35, 14, "M 350,355 C 600,435 520,115 610,25 C 670,-40 765,20 780,100"),
    ],
    "S": [
        (36, 14, "M 600,570 C 745,740 440,770 340,635 C 200,445 575,355 485,160 C 400,-30 125,-80 105,55"),
        (16, 12, "M 105,55 C 80,165 260,200 285,95"),
        (23, 20, "M 596,565 L 600,570"),
    ],
    "T": [
        (36, 14, "M 520,680 C 425,510 375,280 290,90 C 230,-45 100,-65 85,30 C 75,90 140,120 165,65"),
        (18, 13, "M 165,560 C 75,680 270,755 475,700 C 650,650 750,635 805,745"),
    ],
    "V": [
        (17, 12, "M 90,560 C 50,680 210,755 335,685"),
        (36, 14, "M 335,685 C 225,460 200,230 290,35"),
        (18, 12, "M 290,35 C 485,190 685,475 700,655 C 710,760 585,740 600,650"),
    ],
    "W": [
        (17, 12, "M 85,560 C 45,680 205,755 330,685"),
        (36, 14, "M 330,685 C 220,445 205,205 270,35"),
        (18, 12, "M 270,35 C 415,205 525,440 575,635"),
        (35, 14, "M 575,635 C 500,385 485,195 555,35"),
        (18, 12, "M 555,35 C 760,235 915,495 895,675 C 885,765 775,730 795,655"),
    ],
    "X": [
        (17, 12, "M 115,570 C 95,710 240,760 325,650"),
        (36, 14, "M 325,650 C 420,475 365,225 470,65 C 540,-40 660,-15 700,95"),
        (18, 12, "M 80,30 C 180,-75 310,200 450,375 C 595,565 730,785 780,675 C 800,625 745,595 710,625"),
    ],
    "Y": [
        (17, 12, "M 100,575 C 50,710 200,755 310,690"),
        (35, 14, "M 310,690 C 200,485 205,330 315,285 C 470,230 605,475 680,685"),
        (35, 14, "M 680,685 C 605,460 530,210 435,-10 C 345,-215 165,-205 165,-95 C 165,-30 240,-10 260,-65"),
    ],
    "Z": [
        (18, 13, "M 150,560 C 90,675 240,765 390,700 C 515,645 625,650 690,700"),
        (34, 14, "M 690,700 C 580,500 365,240 175,45"),
        (18, 13, "M 175,45 C 135,-55 305,-70 415,25 C 505,105 575,50 615,0"),
        (30, 14, "M 615,0 C 675,-65 755,-30 770,65"),
    ],
}


def outline(letter, growth=0):
    """Return a union of elliptical-nib strokes, including optical-size growth."""
    result = pathops.Path()
    for rx, ry, drawing in STROKES[letter]:
        centre = pathops.Path()
        parse_path(drawing, centre.getPen())
        rx, ry = rx * NIB_SCALE + growth, ry * NIB_SCALE + growth
        stroke = centre.transform(1 / rx, 0, 0, 1 / ry)
        stroke.stroke(2, pathops.LineCap.ROUND_CAP, pathops.LineJoin.ROUND_JOIN, 4)
        result.addPath(stroke.transform(rx, 0, 0, ry))
    result.convertConicsToQuads(0.1)
    result = pathops.simplify(result)
    return result


def charstring(letter, growth=0):
    """Return (CFF outline, advance, bounds); 35-unit optical side bearings."""
    path = outline(letter, growth)
    x0, _, x1, _ = path.bounds
    path = path.transform(1, 0, 0, 1, 35 - x0, 0)
    advance = round(x1 - x0 + 70)
    pen = T2CharStringPen(advance, None)
    path.draw(pen)
    return pen.getCharString(), advance, path.bounds
