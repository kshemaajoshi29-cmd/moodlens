"""
Pure Pillow + NumPy colour-grading pipeline.

No generative AI, no Stable Diffusion — every operation is a deterministic
pixel-level transformation. Faces, composition, and content are 100% preserved.

Pipeline order (matches professional LUT/colour-grading tools):
  temperature → tint → saturation → brightness → contrast →
  shadows_lift → split_tone → vignette → grain → sharpness
"""

import io

import numpy as np
from PIL import Image, ImageEnhance, ImageOps

from ..models import PhotoAdjustments


# ── Individual operations ────────────────────────────────────────────────────

def _temperature(img: Image.Image, value: float) -> Image.Image:
    """Shift white balance. +1 = warm amber, -1 = cool blue."""
    if value == 0:
        return img
    delta = int(abs(value) * 28)
    r, g, b = img.split()
    if value > 0:
        r = r.point(lambda x: min(255, x + delta))
        b = b.point(lambda x: max(0, x - delta // 2))
    else:
        b = b.point(lambda x: min(255, x + delta))
        r = r.point(lambda x: max(0, x - delta // 2))
    return Image.merge("RGB", (r, g, b))


def _tint(img: Image.Image, value: float) -> Image.Image:
    """Green–magenta tint. +1 = magenta, -1 = green."""
    if value == 0:
        return img
    delta = int(abs(value) * 18)
    r, g, b = img.split()
    if value > 0:  # magenta: lift R+B, dip G
        r = r.point(lambda x: min(255, x + delta // 2))
        g = g.point(lambda x: max(0, x - delta))
        b = b.point(lambda x: min(255, x + delta // 2))
    else:  # green: lift G, dip R+B
        g = g.point(lambda x: min(255, x + delta))
        r = r.point(lambda x: max(0, x - delta // 2))
        b = b.point(lambda x: max(0, x - delta // 2))
    return Image.merge("RGB", (r, g, b))


def _shadows_lift(img: Image.Image, amount: float) -> Image.Image:
    """Raise the black point for a faded/matte look (like lifting the toe of a film curve)."""
    lift = int(amount * 65)
    return img.point(lambda x: lift + int(x * (255 - lift) / 255))


def _split_tone(
    img: Image.Image, shadows_tint: list[int], highlights_tint: list[int]
) -> Image.Image:
    """Apply different colour casts to shadow and highlight regions independently."""
    arr = np.array(img, dtype=np.float32)
    lum = arr.mean(axis=2, keepdims=True) / 255.0  # luminance mask 0-1
    shadow_w = 1.0 - lum
    highlight_w = lum
    for c, (s, h) in enumerate(zip(shadows_tint, highlights_tint)):
        arr[:, :, c] += shadow_w[:, :, 0] * s
        arr[:, :, c] += highlight_w[:, :, 0] * h
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def _vignette(img: Image.Image, intensity: float) -> Image.Image:
    """Darken edges with a smooth radial gradient."""
    w, h = img.size
    x = np.linspace(-1, 1, w)[None, :]
    y = np.linspace(-1, 1, h)[:, None]
    radius = np.sqrt(x**2 + y**2)
    mask = np.clip(1.0 - radius * intensity * 1.1, 0.0, 1.0)[:, :, None]
    arr = np.array(img, dtype=np.float32) * mask
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8))


def _grain(img: Image.Image, intensity: float) -> Image.Image:
    """Add luminance-channel film grain (Gaussian noise)."""
    arr = np.array(img, dtype=np.float32)
    noise = np.random.normal(0, intensity * 55, arr.shape[:2])[:, :, None]
    return Image.fromarray((arr + noise).clip(0, 255).astype(np.uint8))


def _scale(adj: PhotoAdjustments, intensity: float) -> PhotoAdjustments:
    """Interpolate all adjustments toward neutral. 0 = no change, 1 = full effect."""
    if intensity >= 1.0:
        return adj
    t = intensity
    return PhotoAdjustments(
        temperature=adj.temperature * t,
        tint=adj.tint * t,
        saturation=1.0 + (adj.saturation - 1.0) * t,
        brightness=1.0 + (adj.brightness - 1.0) * t,
        contrast=1.0 + (adj.contrast - 1.0) * t,
        shadows_lift=adj.shadows_lift * t,
        shadows_tint=[int(v * t) for v in adj.shadows_tint],
        highlights_tint=[int(v * t) for v in adj.highlights_tint],
        vignette=adj.vignette * t,
        grain=adj.grain * t,
        sharpness=1.0 + (adj.sharpness - 1.0) * t,
        style_notes=adj.style_notes,
    )


# ── Public interface ─────────────────────────────────────────────────────────

class ImageEnhancer:
    """Applies colour-grading adjustments to an image using pure Pillow + NumPy.

    No API calls, no generative models — deterministic and fast.
    """

    def enhance(
        self,
        image_bytes: bytes,
        adjustments: PhotoAdjustments,
        intensity: float = 1.0,
        output_format: str = "webp",
    ) -> bytes:
        img = Image.open(io.BytesIO(image_bytes))
        img = ImageOps.exif_transpose(img)  # honour EXIF orientation before any processing
        img = img.convert("RGB")
        adj = _scale(adjustments, intensity)

        img = _temperature(img, adj.temperature)
        img = _tint(img, adj.tint)
        img = ImageEnhance.Color(img).enhance(adj.saturation)
        img = ImageEnhance.Brightness(img).enhance(adj.brightness)
        img = ImageEnhance.Contrast(img).enhance(adj.contrast)

        if adj.shadows_lift > 0:
            img = _shadows_lift(img, adj.shadows_lift)
        if any(adj.shadows_tint) or any(adj.highlights_tint):
            img = _split_tone(img, adj.shadows_tint, adj.highlights_tint)
        if adj.vignette > 0:
            img = _vignette(img, adj.vignette)
        if adj.grain > 0:
            img = _grain(img, adj.grain)

        img = ImageEnhance.Sharpness(img).enhance(adj.sharpness)

        buf = io.BytesIO()
        fmt = output_format.upper()
        if fmt == "JPG":
            fmt = "JPEG"
        img.save(buf, format=fmt, quality=92)
        buf.seek(0)
        return buf.read()
