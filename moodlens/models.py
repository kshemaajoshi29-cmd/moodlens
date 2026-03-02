from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PhotoAdjustments(BaseModel):
    """Colour-grading parameters applied purely via Pillow — no generative AI touches the image."""

    model_config = ConfigDict(frozen=True)

    temperature: float = Field(default=0.0, ge=-1.0, le=1.0,
                               description="-1 = icy blue, +1 = golden warm")
    tint: float = Field(default=0.0, ge=-1.0, le=1.0,
                        description="-1 = green, +1 = magenta")
    saturation: float = Field(default=1.0, ge=0.0, le=2.5,
                              description="0.5 = near B&W, 1.0 = unchanged, 1.8 = vivid")
    brightness: float = Field(default=1.0, ge=0.5, le=1.5,
                              description="0.7 = dark, 1.0 = unchanged, 1.3 = bright")
    contrast: float = Field(default=1.0, ge=0.5, le=2.0,
                            description="0.6 = flat, 1.0 = unchanged, 1.8 = punchy")
    shadows_lift: float = Field(default=0.0, ge=0.0, le=0.3,
                                description="Lift blacks (0 = deep, 0.25 = faded matte)")
    shadows_tint: list[int] = Field(default=[0, 0, 0],
                                    description="RGB offset added to dark areas (±25 each)")
    highlights_tint: list[int] = Field(default=[0, 0, 0],
                                       description="RGB offset added to bright areas (±20 each)")
    vignette: float = Field(default=0.0, ge=0.0, le=1.0,
                            description="0 = none, 0.8 = heavy dark edges")
    grain: float = Field(default=0.0, ge=0.0, le=0.3,
                         description="0 = clean, 0.12 = heavy film grain")
    sharpness: float = Field(default=1.0, ge=0.0, le=2.0,
                             description="0.6 = soft, 1.0 = unchanged, 1.6 = crisp")
    style_notes: str = Field(default="", description="One-line UI label (max 55 chars)")


class EnhanceResponse(BaseModel):
    image_url: str = Field(description="Base64 data URL of enhanced image")
    mood_used: str = Field(description="Mood name or free-text that was applied")
    style_notes: str = Field(description="Human-readable description of the style")
    intensity_used: float = Field(description="Intensity factor applied (0–1)")
    is_preset: bool = Field(description="Whether a built-in preset was used")


class HealthResponse(BaseModel):
    status: str
    version: str
