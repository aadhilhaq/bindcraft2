"""Draw the launcher's icon: the page's mark, a target ring with a binder on it.

Run at build time, so no image file has to be kept in the repository:

    python docs/brand/make_icon.py          # writes docs/brand/bindcraft.ico and .png

Pillow is a build-time dependency only; the launcher itself draws its header on a Tk canvas and
needs no image at all.
"""
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
TEAL = (13, 92, 107, 255)
RUST = (194, 96, 58, 255)
PAPER = (244, 248, 248, 255)
SIZES = (16, 32, 48, 64, 128, 256)


def draw_mark(size=256, background=PAPER):
    """The mark at one size: a teal ring, a rust diamond across it."""
    scale = 4                                   # drawn large and reduced: Pillow has no antialiasing
    big = size * scale
    image = Image.new("RGBA", (big, big), background)
    pen = ImageDraw.Draw(image)
    centre = big / 2.0
    ring = big * 0.355
    width = max(2, int(big * 0.065))
    pen.ellipse([centre - ring, centre - ring, centre + ring, centre + ring], outline=TEAL, width=width)
    d = ring * 0.62
    # a polygon outline, not a closed line: a line's two ends meet with a notch at this width
    pen.polygon([(centre - d, centre), (centre, centre - d), (centre + d, centre), (centre, centre + d)],
                outline=RUST, width=width)
    return image.resize((size, size), Image.LANCZOS)


def main():
    icons = [draw_mark(s) for s in SIZES]
    ico = os.path.join(HERE, "bindcraft.ico")
    icons[-1].save(ico, sizes=[(s, s) for s in SIZES])
    png = os.path.join(HERE, "bindcraft.png")
    draw_mark(256).save(png)
    print("wrote %s and %s" % (ico, png))


if __name__ == "__main__":
    main()
