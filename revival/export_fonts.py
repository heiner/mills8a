"""Export full WOFF2 fonts and a compact family without random impressions."""
import argparse
import shutil
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

from finish_fonts import FONTS
from optimize_fonts import subroutinize


def compact(font):
    options = subset.Options()
    options.layout_features = [record.FeatureTag for record in font["GSUB"].table.FeatureList.FeatureRecord
                               if record.FeatureTag != "rand"]
    if "GPOS" in font:
        options.layout_features += [record.FeatureTag for record in font["GPOS"].table.FeatureList.FeatureRecord]
    options.name_IDs = ["*"]
    options.name_languages = ["*"]
    options.name_legacy = True
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=list(font.getBestCmap()))
    subsetter.subset(font)
    # A distinct family prevents this optional edition from shadowing the full font.
    for record in font["name"].names:
        if record.nameID in (1, 4, 16):
            record.string = record.toUnicode().replace("Mills 8A", "Mills 8A Compact").encode(record.getEncoding())
        elif record.nameID == 6:
            record.string = record.toUnicode().replace("Mills8A", "Mills8ACompact").encode(record.getEncoding())
    cff = font["CFF "].cff
    cff.fontNames[0] = cff.fontNames[0].replace("Mills8A", "Mills8ACompact")
    top = cff.topDictIndex[0]
    top.FullName = (top.FullName if hasattr(top, "FullName") else "Mills 8A").replace("Mills 8A", "Mills 8A Compact")
    if hasattr(top, "FamilyName"):
        top.FamilyName = top.FamilyName.replace("Mills 8A", "Mills 8A Compact")
    subroutinize(font)
    return font


def export(output):
    web, small = output / "web", output / "compact"
    web.mkdir(parents=True, exist_ok=True)
    small.mkdir(parents=True, exist_ok=True)
    for path in sorted(FONTS.glob("*.otf")):
        font = TTFont(path, recalcTimestamp=False)
        font.flavor = "woff2"
        font.save(web / path.with_suffix(".woff2").name)
        font.flavor = None
        font = compact(font)
        filename = path.name.replace("Mills8A", "Mills8ACompact")
        destination = small / filename
        font.save(destination)
        font.flavor = "woff2"
        font.save(destination.with_suffix(".woff2"))
        print(f"{path.name}: full {path.stat().st_size:,}; "
              f"compact {destination.stat().st_size:,}; "
              f"compact WOFF2 {destination.with_suffix('.woff2').stat().st_size:,} bytes")
    for directory in (web, small):
        for name in ("LICENSE", "GUST-FONT-LICENSE.txt"):
            shutil.copyfile(FONTS.parent.parent / name, directory / name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=FONTS.parent.parent / "build")
    args = parser.parse_args()
    export(args.output_dir)


if __name__ == "__main__":
    main()
