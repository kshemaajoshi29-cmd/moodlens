from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ...models import SceneInfo
from ..dependencies import Services, get_services

router = APIRouter()

_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}


@router.post("/detect-scene", response_model=SceneInfo)
async def detect_scene(
    image: UploadFile = File(..., description="Photo to analyse for scene detection"),
    services: Services = Depends(get_services),
) -> SceneInfo:
    if image.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{image.content_type}'. "
                "Allowed: image/jpeg, image/png, image/webp, image/heic"
            ),
        )

    image_bytes = await image.read()
    max_bytes = services.settings.max_image_size_mb * 1024 * 1024
    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Image too large. Maximum allowed size: {services.settings.max_image_size_mb} MB",
        )

    return services.scene_detector.detect_scene(image_bytes)
