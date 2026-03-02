import io
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from moodlens.api.app import create_app
from moodlens.api.dependencies import get_services
from moodlens.models import PhotoAdjustments


def _make_jpeg_bytes(width: int = 400, height: int = 300) -> bytes:
    img = Image.new("RGB", (width, height), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.read()


def _make_webp_bytes() -> bytes:
    img = Image.new("RGB", (400, 300), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="WEBP")
    buf.seek(0)
    return buf.read()


_MOCK_ADJ = PhotoAdjustments(
    temperature=0.3,
    saturation=1.1,
    style_notes="Warm golden mood",
)


@pytest.fixture
def mock_services():
    svc = MagicMock()
    svc.settings.max_image_size_mb = 10
    svc.settings.output_format = "webp"
    svc.image_enhancer.enhance.return_value = _make_webp_bytes()
    svc.mood_interpreter.interpret.return_value = _MOCK_ADJ
    return svc


@pytest.fixture
def client(mock_services):
    app = create_app()
    app.dependency_overrides[get_services] = lambda: mock_services
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ── Health ───────────────────────────────────────────────────────────────────

def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body


# ── Preset moods ─────────────────────────────────────────────────────────────

def test_enhance_preset_vintage(client, mock_services):
    response = client.post(
        "/api/v1/enhance",
        files={"image": ("photo.jpg", _make_jpeg_bytes(), "image/jpeg")},
        data={"mood": "vintage"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_preset"] is True
    assert body["mood_used"] == "vintage"
    assert body["image_url"].startswith("data:image/webp;base64,")
    mock_services.mood_interpreter.interpret.assert_not_called()


@pytest.mark.parametrize("preset", ["vintage", "hawaii", "cinematic", "moody_rainy"])
def test_enhance_all_presets_skip_claude(client, mock_services, preset):
    response = client.post(
        "/api/v1/enhance",
        files={"image": ("photo.jpg", _make_jpeg_bytes(), "image/jpeg")},
        data={"mood": preset},
    )
    assert response.status_code == 200
    mock_services.mood_interpreter.interpret.assert_not_called()


# ── Free-text moods ──────────────────────────────────────────────────────────

def test_enhance_freetext_calls_claude(client, mock_services):
    response = client.post(
        "/api/v1/enhance",
        files={"image": ("photo.jpg", _make_jpeg_bytes(), "image/jpeg")},
        data={"mood": "dreamy pastel anime"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_preset"] is False
    mock_services.mood_interpreter.interpret.assert_called_once_with("dreamy pastel anime")


def test_enhance_intensity_override(client, mock_services):
    response = client.post(
        "/api/v1/enhance",
        files={"image": ("photo.jpg", _make_jpeg_bytes(), "image/jpeg")},
        data={"mood": "vintage", "intensity": "0.5"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["intensity_used"] == pytest.approx(0.5)


def test_enhance_response_has_style_notes(client):
    response = client.post(
        "/api/v1/enhance",
        files={"image": ("photo.jpg", _make_jpeg_bytes(), "image/jpeg")},
        data={"mood": "vintage"},
    )
    assert response.status_code == 200
    assert "style_notes" in response.json()


# ── Validation ────────────────────────────────────────────────────────────────

def test_enhance_rejects_unsupported_content_type(client):
    response = client.post(
        "/api/v1/enhance",
        files={"image": ("photo.gif", b"GIF89a...", "image/gif")},
        data={"mood": "vintage"},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_enhance_rejects_oversized_image(client, mock_services):
    mock_services.settings.max_image_size_mb = 1
    big_bytes = b"x" * (1024 * 1024 * 2)
    response = client.post(
        "/api/v1/enhance",
        files={"image": ("big.jpg", big_bytes, "image/jpeg")},
        data={"mood": "vintage"},
    )
    assert response.status_code == 400
    assert "too large" in response.json()["detail"].lower()


def test_enhance_missing_mood_returns_422(client):
    response = client.post(
        "/api/v1/enhance",
        files={"image": ("photo.jpg", _make_jpeg_bytes(), "image/jpeg")},
    )
    assert response.status_code == 422


def test_enhance_missing_image_returns_422(client):
    response = client.post("/api/v1/enhance", data={"mood": "vintage"})
    assert response.status_code == 422
