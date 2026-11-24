"""The two portrait filters used on jplepecki.tech: risograph and copper halftone."""
import numpy as np
from PIL import Image, ImageDraw

from .kernels import to_luma, unsharp_mask, stretch, equalize, local_contrast

PAPER = (236, 232, 222)

# A 4x4 Bayer matrix: thresholds spread evenly from 0 to 15/16, arranged so that
# neighbouring cells are as different as possible. Tiling it over the image turns
# a smooth grey into a regular dot pattern instead of a single hard cut.
BAYER4 = np.array([[0, 8, 2, 10],
                   [12, 4, 14, 6],
                   [3, 11, 1, 9],
                   [15, 7, 13, 5]]) / 16


def _bayer_tile(shape):
    h, w = shape
    return np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w]


def _shift(mask, dx, dy):
    """Move a layer right/down without wrapping around the edges."""
    out = np.zeros_like(mask)
    out[dy:, dx:] = mask[:mask.shape[0] - dy, :mask.shape[1] - dx]
    return out


def prepare(rgb, alpha=None, gamma=1.0, sharpen=0.8, tone="stretch"):
    """RGB [0,1] -> sharpened, tone-mapped brightness [0,1].

    tone="stretch" keeps the photo's own contrast; tone="equalize" flattens the
    histogram for punchier local contrast (better for coarse dots).
    """
    gray = to_luma(rgb)
    subject = alpha > 0.5 if alpha is not None else None
    gray = equalize(gray, subject) if tone == "equalize" else stretch(gray, mask=subject)
    if tone == "equalize":
        gray = local_contrast(gray)
    gray = gray ** gamma
    return unsharp_mask(gray, sharpen), subject


def riso(rgb, alpha=None, dark_ink=(30, 80, 70), light_ink=(255, 120, 80),
         offset=(3, 2), gamma=1.0):
    """Two-colour risograph.

    A riso printer lays down one flat ink per pass. Two thresholds split the image:
    the shadows go to the dark ink, everything below the highlights goes to the light
    ink. Each layer is dithered with the Bayer matrix, the light layer is printed a
    few pixels off (real drums never line up), and inks combine by multiplying,
    exactly like translucent ink on paper.
    """
    gray, subject = prepare(rgb, alpha, gamma)
    t = _bayer_tile(gray.shape)
    dark = gray < 0.35 + 0.3 * (t - 0.5)
    light = gray < 0.75 + 0.4 * (t - 0.5)
    if subject is not None:
        dark &= subject
        light &= subject

    out = np.full(gray.shape + (3,), PAPER, dtype=float)
    for mask, ink, (dx, dy) in ((light, light_ink, offset), (dark, dark_ink, (0, 0))):
        m = _shift(mask, dx, dy)
        out[m] *= np.array(ink) / 255.0  # multiply blend: ink filters the light
    return Image.fromarray(out.astype(np.uint8))


def copper_halftone(rgb, alpha=None, cell=9, ink=(196, 122, 58), board=(18, 24, 20),
                    gamma=1.0, supersample=3, area_correct=False):
    """Copper dots on a dark circuit board.

    The image is cut into `cell` x `cell` squares; each square becomes one dot sized
    by the square's brightness. A dot's AREA grows with radius squared, so the
    tone-accurate choice is radius = sqrt(brightness) (`area_correct=True`). That looks
    flat on a face, so by default the radius is roughly linear in brightness, which
    shrinks mid-tone dots and reads as more contrast. Drawn at `supersample`x and
    scaled down for smooth circles.
    """
    gray, subject = prepare(rgb, alpha, gamma, tone="equalize")
    h, w = gray.shape
    s = supersample
    img = Image.new("RGB", (w * s, h * s), board)
    draw = ImageDraw.Draw(img)
    r_max = cell * 0.7  # > cell/2, so bright areas merge into solid copper
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            cy, cx = min(h - 1, y + cell // 2), min(w - 1, x + cell // 2)
            if subject is not None and not subject[cy, cx]:
                continue
            v = gray[y:y + cell, x:x + cell].mean()
            r = (np.sqrt(v) if area_correct else v ** 0.9) * r_max
            if r < 0.5:
                continue
            px, py = (x + cell / 2) * s, (y + cell / 2) * s
            draw.ellipse([px - r * s, py - r * s, px + r * s, py + r * s], fill=ink)
    return img.resize((w, h), Image.LANCZOS)


def load(path, width=480):
    """Load an image as RGB [0,1] plus an optional alpha mask (from a transparent PNG)."""
    im = Image.open(path)
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im = im.convert("RGBA")
    arr = np.asarray(im).astype(float) / 255.0
    alpha = arr[..., 3] if arr[..., 3].min() < 1.0 else None
    return arr[..., :3], alpha
