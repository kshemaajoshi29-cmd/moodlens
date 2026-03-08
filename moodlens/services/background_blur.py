"""
Portrait-mode background blur using rembg (u2net ONNX) + Pillow + NumPy.

rembg is imported lazily inside apply() so that importing this module at
server startup costs nothing — the ~170 MB ONNX model is only loaded on
the first call that actually needs background blur.
"""

import io
import threading

import numpy as np
from PIL import Image, ImageFilter

# Module-level session cache — one instance shared across threads.
_rembg_session = None
_rembg_lock = threading.Lock()


def _get_session():
    """Return (or create) a cached rembg u2net session (double-checked lock)."""
    global _rembg_session
    if _rembg_session is None:
        with _rembg_lock:
            if _rembg_session is None:
                import rembg  # deferred — heavy import
                _rembg_session = rembg.new_session("u2net")
    return _rembg_session


class BackgroundBlur:
    """Stateless portrait-mode blur. Instantiate per-request — no shared state."""

    def apply(
        self,
        image_bytes: bytes,
        blur_radius: int = 21,
        background_intensity: float = 1.0,
        feather_radius: int = 15,
    ) -> bytes:
        """
        Apply background blur to an image.

        Args:
            image_bytes:          Raw input image bytes.
            blur_radius:          Gaussian blur radius applied to the background (px).
            background_intensity: Saturation of blurred background (1.0 = colour, 0 = B&W).
            feather_radius:       Gaussian blur applied to the alpha mask edge (px).

        Returns:
            PNG bytes of the composited image (subject sharp, background blurred).
        """
        import rembg  # deferred

        session = _get_session()

        # 1. Remove background → RGBA bytes (alpha = subject mask)
        rgba_bytes = rembg.remove(image_bytes, session=session, only_mask=False)
        rgba_img = Image.open(io.BytesIO(rgba_bytes)).convert("RGBA")

        # 2. Load original as RGB, resize to match rembg output
        original = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        original = original.resize(rgba_img.size, Image.LANCZOS)

        # 3. Feather the alpha mask for smooth subject edges
        alpha = rgba_img.split()[3]
        alpha_feathered = alpha.filter(ImageFilter.GaussianBlur(feather_radius))

        # 4. Blur the background
        blurred_bg = original.filter(ImageFilter.GaussianBlur(blur_radius))

        # 5. Optional background desaturation
        if background_intensity < 1.0:
            from PIL import ImageEnhance
            blurred_bg = ImageEnhance.Color(blurred_bg).enhance(background_intensity)

        # 6. NumPy alpha composite: subject sharp over blurred background
        orig_arr = np.array(original, dtype=np.float32)
        blur_arr = np.array(blurred_bg, dtype=np.float32)
        mask = np.array(alpha_feathered, dtype=np.float32)[:, :, None] / 255.0

        composite = orig_arr * mask + blur_arr * (1.0 - mask)
        result_img = Image.fromarray(composite.clip(0, 255).astype(np.uint8))

        buf = io.BytesIO()
        result_img.save(buf, format="PNG")
        buf.seek(0)
        return buf.read()
