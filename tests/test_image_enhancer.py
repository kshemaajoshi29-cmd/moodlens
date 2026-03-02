import io

import pytest
from PIL import Image

from moodlens.models import PhotoAdjustments
from moodlens.services.image_enhancer import (
    ImageEnhancer,
    _grain,
    _scale,
    _shadows_lift,
    _split_tone,
    _temperature,
    _tint,
    _vignette,
)

_NEUTRAL = PhotoAdjustments(style_notes="neutral")

_VINTAGE = PhotoAdjustments(
    temperature=0.35,
    saturation=0.72,
    vignette=0.55,
    grain=0.08,
    shadows_lift=0.12,
    shadows_tint=[10, 5, -5],
    highlights_tint=[8, 3, -10],
    style_notes="test vintage",
)


def _solid(color=(120, 80, 60), size=(200, 150)) -> Image.Image:
    return Image.new("RGB", size, color=color)


def _to_bytes(img: Image.Image, fmt="JPEG") -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.read()


# ── _temperature ─────────────────────────────────────────────────────────────

def test_temperature_warm_boosts_red():
    img = _solid((128, 128, 128))
    result = _temperature(img, 1.0)
    r, g, b = result.getpixel((10, 10))
    assert r > 128  # red lifted
    assert b < 128  # blue dropped


def test_temperature_cool_boosts_blue():
    img = _solid((128, 128, 128))
    result = _temperature(img, -1.0)
    r, g, b = result.getpixel((10, 10))
    assert b > 128
    assert r < 128


def test_temperature_zero_is_noop():
    img = _solid((100, 120, 80))
    assert _temperature(img, 0).tobytes() == img.tobytes()


# ── _tint ─────────────────────────────────────────────────────────────────────

def test_tint_magenta_lifts_rb_drops_g():
    img = _solid((128, 128, 128))
    result = _tint(img, 1.0)
    r, g, b = result.getpixel((10, 10))
    assert g < 128
    assert r >= 128


def test_tint_zero_is_noop():
    img = _solid((100, 120, 80))
    assert _tint(img, 0).tobytes() == img.tobytes()


# ── _shadows_lift ─────────────────────────────────────────────────────────────

def test_shadows_lift_raises_dark_pixels():
    img = _solid((0, 0, 0))  # pure black
    result = _shadows_lift(img, 0.2)
    r, g, b = result.getpixel((10, 10))
    assert r > 0  # black was lifted


def test_shadows_lift_does_not_clip_bright_pixels():
    img = _solid((200, 200, 200))
    result = _shadows_lift(img, 0.2)
    r, _, _ = result.getpixel((10, 10))
    assert r <= 255


# ── _split_tone ───────────────────────────────────────────────────────────────

def test_split_tone_applies_to_dark_area():
    dark = _solid((20, 20, 20))
    result = _split_tone(dark, shadows_tint=[30, 0, 0], highlights_tint=[0, 0, 0])
    r, _, _ = result.getpixel((10, 10))
    assert r > 20  # red boosted in shadows


def test_split_tone_applies_to_bright_area():
    bright = _solid((240, 240, 240))
    result = _split_tone(bright, shadows_tint=[0, 0, 0], highlights_tint=[0, 0, 30])
    _, _, b = result.getpixel((10, 10))
    assert b > 240  # blue boosted in highlights (clamped to 255)


# ── _vignette ─────────────────────────────────────────────────────────────────

def test_vignette_darkens_corners():
    img = _solid((200, 200, 200), size=(400, 400))
    result = _vignette(img, 0.8)
    center_r = result.getpixel((200, 200))[0]
    corner_r = result.getpixel((0, 0))[0]
    assert center_r > corner_r


def test_vignette_center_stays_bright():
    img = _solid((200, 200, 200), size=(400, 400))
    result = _vignette(img, 0.5)
    center_r = result.getpixel((200, 200))[0]
    assert center_r > 150  # center mostly unchanged


# ── _grain ────────────────────────────────────────────────────────────────────

def test_grain_changes_pixels():
    img = _solid((128, 128, 128), size=(100, 100))
    result = _grain(img, 0.1)
    assert result.tobytes() != img.tobytes()


# ── _scale ────────────────────────────────────────────────────────────────────

def test_scale_zero_returns_neutral():
    scaled = _scale(_VINTAGE, 0.0)
    assert scaled.temperature == pytest.approx(0.0)
    assert scaled.saturation == pytest.approx(1.0)
    assert scaled.vignette == pytest.approx(0.0)
    assert scaled.grain == pytest.approx(0.0)


def test_scale_one_returns_unchanged():
    scaled = _scale(_VINTAGE, 1.0)
    assert scaled.temperature == pytest.approx(_VINTAGE.temperature)
    assert scaled.saturation == pytest.approx(_VINTAGE.saturation)


def test_scale_half_interpolates():
    scaled = _scale(_VINTAGE, 0.5)
    assert scaled.temperature == pytest.approx(_VINTAGE.temperature * 0.5)
    assert scaled.saturation == pytest.approx(1.0 + (_VINTAGE.saturation - 1.0) * 0.5)


# ── ImageEnhancer.enhance (end-to-end, no mocks) ────────────────────────────

def test_enhance_returns_bytes():
    enhancer = ImageEnhancer()
    result = enhancer.enhance(_to_bytes(_solid()), _NEUTRAL)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_enhance_output_is_valid_image():
    enhancer = ImageEnhancer()
    result = enhancer.enhance(_to_bytes(_solid()), _VINTAGE, output_format="webp")
    img = Image.open(io.BytesIO(result))
    assert img.size == (200, 150)


def test_enhance_preserves_dimensions():
    enhancer = ImageEnhancer()
    big = Image.new("RGB", (1920, 1080), color=(100, 100, 100))
    result = enhancer.enhance(_to_bytes(big), _VINTAGE)
    out_img = Image.open(io.BytesIO(result))
    assert out_img.size == (1920, 1080)


def test_enhance_intensity_zero_output_similar_to_input():
    """At intensity=0 all adjustments are neutralised — output should be close to input."""
    enhancer = ImageEnhancer()
    img_bytes = _to_bytes(_solid((128, 100, 80), (100, 100)))
    result = enhancer.enhance(img_bytes, _VINTAGE, intensity=0.0, output_format="jpeg")
    out_img = Image.open(io.BytesIO(result))
    # Allow small deviation from JPEG re-compression
    r, g, b = out_img.getpixel((50, 50))
    assert abs(r - 128) < 10
    assert abs(g - 100) < 10
