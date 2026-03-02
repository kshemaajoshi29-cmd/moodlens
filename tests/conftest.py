import io

import pytest
from PIL import Image
from unittest.mock import MagicMock


@pytest.fixture
def mock_settings():
    from moodlens.config import Settings

    settings = MagicMock(spec=Settings)
    settings.openrouter_api_key = "sk-or-v1-test"
    settings.openrouter_model = "anthropic/claude-haiku-4-5"
    settings.max_image_size_mb = 10
    settings.output_format = "webp"
    return settings


@pytest.fixture
def sample_image_bytes() -> bytes:
    img = Image.new("RGB", (800, 600), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.read()


@pytest.fixture
def sample_pil_image() -> Image.Image:
    return Image.new("RGB", (800, 600), color=(100, 150, 200))
