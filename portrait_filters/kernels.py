"""The building blocks: turning RGB into one brightness channel, and 2D convolution.

Every filter in this repo starts the same way. A photo is three numbers per pixel
(red, green, blue). Print processes like risograph and halftone don't care about
colour, only about how much ink goes where, so the first step is collapsing RGB
into one brightness value, then shaping that brightness with small kernels.
"""
import numpy as np

# Rec. 709 luma weights. Green dominates because human eyes are most sensitive to it;
# averaging R, G and B equally makes skies too dark and skin too flat.
LUMA = np.array([0.2126, 0.7152, 0.0722])


def to_luma(rgb: np.ndarray) -> np.ndarray:
    """RGB in [0, 1] (H, W, 3) -> brightness in [0, 1] (H, W).

    This is itself a 1x1 kernel applied across channels: a dot product per pixel.
    """
    return rgb[..., :3] @ LUMA


def convolve(img: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """Slide `kernel` over `img` and sum the weighted neighbours at every pixel.

    Edges are padded by repeating the border pixel so the output keeps the input size.
    (Strictly this is cross-correlation; for the symmetric kernels below it is identical.)
    """
    kh, kw = kernel.shape
    ph, pw = kh // 2, kw // 2
    padded = np.pad(img, ((ph, ph), (pw, pw)), mode="edge")
    out = np.zeros_like(img, dtype=float)
    h, w = img.shape
    for dy in range(kh):
        for dx in range(kw):
            out += kernel[dy, dx] * padded[dy:dy + h, dx:dx + w]
    return out


# Weights sum to 1 -> overall brightness is preserved, detail is averaged away.
BOX_BLUR = np.ones((3, 3)) / 9
GAUSSIAN = np.array([[1, 2, 1],
                     [2, 4, 2],
                     [1, 2, 1]]) / 16

# Weights sum to 1, but the centre is pushed up and the neighbours subtracted:
# a pixel that differs from its surroundings gets exaggerated.
SHARPEN = np.array([[0, -1, 0],
                    [-1, 5, -1],
                    [0, -1, 0]])

# Weights sum to 0 -> flat areas go to zero, only changes (edges) survive.
EDGE = np.array([[-1, -1, -1],
                 [-1, 8, -1],
                 [-1, -1, -1]])


def unsharp_mask(gray: np.ndarray, amount: float = 1.0) -> np.ndarray:
    """Sharpen by adding back the detail a blur removes: g + amount * (g - blur(g))."""
    detail = gray - convolve(gray, GAUSSIAN)
    return np.clip(gray + amount * detail, 0.0, 1.0)


def stretch(gray: np.ndarray, low: float = 1, high: float = 99, mask=None) -> np.ndarray:
    """Map the `low`..`high` percentile range to 0..1 so the darkest and brightest
    parts of the subject use the full tonal range."""
    values = gray[mask] if mask is not None else gray
    lo, hi = np.percentile(values, [low, high])
    return np.clip((gray - lo) / max(hi - lo, 1e-6), 0.0, 1.0)


def equalize(gray: np.ndarray, mask=None, bins: int = 256) -> np.ndarray:
    """Histogram equalisation: remap brightness so every tone is used equally often.

    The cumulative histogram (CDF) of the subject's pixels becomes the new brightness,
    so a face lit flatly by a phone flash gets spread across the whole range.
    """
    values = gray[mask] if mask is not None else gray.ravel()
    hist, edges = np.histogram(values, bins=bins, range=(0.0, 1.0))
    cdf = np.cumsum(hist).astype(float)
    cdf /= cdf[-1]
    return np.interp(gray, edges[:-1], cdf)


def local_contrast(gray: np.ndarray, radius: float = 12, amount: float = 0.8) -> np.ndarray:
    """Unsharp mask with a BIG blur: boosts contrast between regions (eye sockets vs
    cheeks) rather than between neighbouring pixels. Same idea as `unsharp_mask`,
    only the Gaussian is wide, so it is computed with Pillow instead of the 3x3 loop.
    """
    from PIL import Image, ImageFilter
    img = Image.fromarray((gray * 255).astype(np.uint8))
    blurred = np.asarray(img.filter(ImageFilter.GaussianBlur(radius))).astype(float) / 255
    return np.clip(gray + amount * (gray - blurred), 0.0, 1.0)
