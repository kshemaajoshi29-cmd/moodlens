import base64
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from ...models import (
    BatchEnhanceItem,
    BatchEnhanceResponse,
    EnhanceResponse,
    PhotoAdjustments,
)
from ...presets import PRESETS
from ..dependencies import Services, get_services

router = APIRouter()

_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}
_MAX_BATCH = 20


def _resolve_mood(
    mood: str,
    reference_bytes: Optional[bytes],
    services: Services,
) -> tuple[PhotoAdjustments, str, bool]:
    """Return (adjustments, mood_used, is_preset) — resolves preset, free-text, or reference style."""
    if reference_bytes is not None:
        mood_used = services.scene_detector.describe_style(reference_bytes)
        return services.mood_interpreter.interpret(mood_used), mood_used, False
    mood_key = mood.lower().strip()
    if mood_key in PRESETS:
        return PRESETS[mood_key], mood, True
    return services.mood_interpreter.interpret(mood), mood, False


def _validate_image(upload: UploadFile, image_bytes: bytes, max_bytes: int) -> None:
    if upload.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"'{upload.filename}': unsupported type '{upload.content_type}'. "
                "Allowed: image/jpeg, image/png, image/webp, image/heic"
            ),
        )
    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"'{upload.filename}' exceeds the maximum allowed size.",
        )


@router.post("/enhance", response_model=EnhanceResponse)
async def enhance_image(
    image: UploadFile = File(..., description="Input photo (JPEG/PNG/WebP/HEIC)"),
    mood: str = Form(..., description="Preset name or free-text mood description"),
    intensity: Optional[float] = Form(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Effect intensity — 0 = no change, 1 = full effect",
    ),
    blur_background: bool = Form(default=False, description="Apply portrait-mode background blur"),
    blur_radius: int = Form(default=21, ge=5, le=50, description="Background blur strength (px)"),
    background_intensity: float = Form(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Background saturation after blur (1.0 = colour, 0 = B&W)",
    ),
    reference_image: Optional[UploadFile] = File(
        default=None,
        description="Optional moodboard/reference image to match its colour aesthetic",
    ),
    services: Services = Depends(get_services),
) -> EnhanceResponse:
    max_bytes = services.settings.max_image_size_mb * 1024 * 1024
    image_bytes = await image.read()
    _validate_image(image, image_bytes, max_bytes)

    ref_bytes = (await reference_image.read()) if reference_image is not None else None
    adjustments, mood_used, is_preset = _resolve_mood(mood, ref_bytes, services)

    effective_intensity = intensity if intensity is not None else 1.0
    enhanced_bytes = services.image_enhancer.enhance(
        image_bytes=image_bytes,
        adjustments=adjustments,
        intensity=effective_intensity,
        output_format=services.settings.output_format,
        blur_background=blur_background,
        blur_radius=blur_radius,
        background_intensity=background_intensity,
    )

    b64 = base64.b64encode(enhanced_bytes).decode()
    data_url = f"data:image/{services.settings.output_format};base64,{b64}"

    return EnhanceResponse(
        image_url=data_url,
        mood_used=mood_used,
        style_notes=adjustments.style_notes,
        intensity_used=effective_intensity,
        is_preset=is_preset,
    )


@router.post("/enhance-batch", response_model=BatchEnhanceResponse)
async def enhance_images_batch(
    images: list[UploadFile] = File(..., description="Photos to enhance (up to 20)"),
    mood: str = Form(..., description="Preset name or free-text mood description"),
    intensity: Optional[float] = Form(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Effect intensity — 0 = no change, 1 = full effect",
    ),
    blur_background: bool = Form(default=False, description="Apply portrait-mode background blur"),
    blur_radius: int = Form(default=21, ge=5, le=50, description="Background blur strength (px)"),
    background_intensity: float = Form(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Background saturation after blur (1.0 = colour, 0 = B&W)",
    ),
    reference_image: Optional[UploadFile] = File(
        default=None,
        description="Optional moodboard/reference image to match its colour aesthetic",
    ),
    services: Services = Depends(get_services),
) -> BatchEnhanceResponse:
    if len(images) > _MAX_BATCH:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {_MAX_BATCH} images per batch. Got {len(images)}.",
        )

    # Resolve mood once — same grade applied to every image in the batch
    ref_bytes = (await reference_image.read()) if reference_image is not None else None
    adjustments, mood_used, is_preset = _resolve_mood(mood, ref_bytes, services)

    max_bytes = services.settings.max_image_size_mb * 1024 * 1024
    effective_intensity = intensity if intensity is not None else 1.0

    items: list[BatchEnhanceItem] = []
    for img_file in images:
        img_bytes = await img_file.read()
        _validate_image(img_file, img_bytes, max_bytes)

        enhanced_bytes = services.image_enhancer.enhance(
            image_bytes=img_bytes,
            adjustments=adjustments,
            intensity=effective_intensity,
            output_format=services.settings.output_format,
            blur_background=blur_background,
            blur_radius=blur_radius,
            background_intensity=background_intensity,
        )

        b64 = base64.b64encode(enhanced_bytes).decode()
        data_url = f"data:image/{services.settings.output_format};base64,{b64}"

        items.append(
            BatchEnhanceItem(
                filename=img_file.filename or "image",
                image_url=data_url,
                mood_used=mood_used,
                style_notes=adjustments.style_notes,
                intensity_used=effective_intensity,
                is_preset=is_preset,
            )
        )

    return BatchEnhanceResponse(items=items, total=len(items))
