import base64
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from ...models import EnhanceResponse
from ...presets import PRESETS
from ..dependencies import Services, get_services

router = APIRouter()

_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}


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
    services: Services = Depends(get_services),
) -> EnhanceResponse:
    # Validate content type
    if image.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{image.content_type}'. "
                "Allowed: image/jpeg, image/png, image/webp, image/heic"
            ),
        )

    # Read and validate file size
    image_bytes = await image.read()
    max_bytes = services.settings.max_image_size_mb * 1024 * 1024
    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Image too large. Maximum allowed size: {services.settings.max_image_size_mb} MB",
        )

    # Resolve mood — presets bypass Claude entirely (zero LLM cost)
    mood_key = mood.lower().strip()
    if mood_key in PRESETS:
        adjustments = PRESETS[mood_key]
        is_preset = True
    else:
        adjustments = services.mood_interpreter.interpret(mood)
        is_preset = False

    # Apply colour-grading pipeline (pure Pillow — no generative AI)
    enhanced_bytes = services.image_enhancer.enhance(
        image_bytes=image_bytes,
        adjustments=adjustments,
        intensity=intensity if intensity is not None else 1.0,
        output_format=services.settings.output_format,
    )

    b64 = base64.b64encode(enhanced_bytes).decode()
    data_url = f"data:image/{services.settings.output_format};base64,{b64}"

    return EnhanceResponse(
        image_url=data_url,
        mood_used=mood,
        style_notes=adjustments.style_notes,
        intensity_used=intensity if intensity is not None else 1.0,
        is_preset=is_preset,
    )
