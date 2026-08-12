#!/usr/bin/env python3
"""Draw a trainer's home-screen icons: a coloured tile with its two-letter badge.

The existing icons were drawn by hand and the recipe was never written down, so
adding an app meant guessing at the font and size. This reproduces them exactly
— FreeSerif, cap height 7/16 of the tile, optically centred — which is checked
against the shipped Portuguese icon by `python3 scripts/make_icons.py --check`.

The badge must match the letters `scripts/build_index.py` puts on the hub card,
or the tile on the home screen and the card in the hub look like two apps.

    python3 scripts/make_icons.py brazilian-trainer BR '#f2c200' '#00512e'
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ICONS = os.path.join(HERE, "..", "icons")
FONT = "/usr/share/fonts/truetype/freefont/FreeSerif.ttf"
SIZES = (192, 512)


def draw(size, badge, accent, ink):
    im = Image.new("RGB", (size, size), accent)
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype(FONT, round(size * 7 / 16))
    # textbbox, not the font's own metrics: capitals sit well above the
    # baseline and well below the ascent, so centring on the ascent leaves the
    # glyphs visibly high on the tile.
    x0, y0, x1, y1 = d.textbbox((0, 0), badge, font=font)
    d.text(((size - (x1 - x0)) / 2 - x0, (size - (y1 - y0)) / 2 - y0),
           badge, font=font, fill=ink)
    return im


def write(slug, badge, accent, ink):
    for size in SIZES:
        path = os.path.join(ICONS, f"{slug}-icon-{size}.png")
        draw(size, badge, accent, ink).save(path)
        print(f"wrote {os.path.relpath(path, os.path.join(HERE, '..'))}")


def ink_box(im):
    """Bounding box of everything that is not the tile colour."""
    bg, px, (w, h) = im.getpixel((1, 1)), im.load(), im.size
    on = [(x, y) for y in range(h) for x in range(w) if px[x, y] != bg]
    xs, ys = [p[0] for p in on], [p[1] for p in on]
    return min(xs), min(ys), max(xs), max(ys)


def check():
    """The recipe is only worth having if it matches the icons already shipped.

    Not pixel equality — the originals were drawn by hand and the two of them
    do not even agree with each other on letter width. What has to hold is the
    thing you notice on a home screen: the badge is the same height and sits in
    the same place on every tile.
    """
    for slug, badge, accent, ink in [("portuguese-trainer", "PT", (11, 107, 58), (255, 255, 255)),
                                     ("spanish-trainer", "ES", (122, 35, 49), (255, 255, 255))]:
        for size in SIZES:
            want = ink_box(Image.open(os.path.join(ICONS, f"{slug}-icon-{size}.png")).convert("RGB"))
            got = ink_box(draw(size, badge, accent, ink))
            cap = abs((want[3] - want[1]) - (got[3] - got[1]))
            off = max(abs((want[0] + want[2]) - (got[0] + got[2])) / 2,
                      abs((want[1] + want[3]) - (got[1] + got[3])) / 2)
            assert cap <= size / 96, f"{slug} {size}: cap height off by {cap}px"
            assert off <= size / 32, f"{slug} {size}: badge off-centre by {off}px"
            print(f"ok   {slug}-icon-{size}.png — cap height {cap}px, position {off}px")


if __name__ == "__main__":
    if sys.argv[1:2] == ["--check"]:
        check()
    else:
        slug, badge, accent, ink = sys.argv[1:5]
        write(slug, badge, accent, ink)
