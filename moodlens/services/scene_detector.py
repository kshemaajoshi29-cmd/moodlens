"""
Scene detection and style description using Claude vision via OpenRouter.

detect_scene  — forced tool call → SceneInfo (structured)
describe_style — free-text      → colorist brief string for MoodInterpreter
"""

import base64
import json

from openai import OpenAI

from ..config import Settings

_SCENE_TOOL = {
    "type": "function",
    "function": {
        "name": "detect_scene",
        "description": "Detect the scene type in a photo and suggest matching colour-grading presets",
        "parameters": {
            "type": "object",
            "properties": {
                "scene_type": {
                    "type": "string",
                    "description": (
                        "Scene category — e.g. 'wedding', 'beach', 'portrait', "
                        "'urban', 'nature', 'landscape', 'indoor', 'food', 'architecture'"
                    ),
                },
                "description": {
                    "type": "string",
                    "description": "One-sentence description of what is in the photo",
                },
                "suggested_presets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 3,
                    "description": (
                        "Up to 3 preset names chosen from: vintage, hawaii, cinematic, "
                        "moody_rainy, california_coastal, golden_hour, nordic, "
                        "desert_sun, jungle_green, new_york"
                    ),
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence in the scene detection, 0.0 (low) to 1.0 (high)",
                },
            },
            "required": ["scene_type", "description", "suggested_presets", "confidence"],
            "additionalProperties": False,
        },
    },
}

_STYLE_SYSTEM = (
    "You are a professional photo colorist. Describe the colour aesthetic of the reference image "
    "in detail: colour temperature, tones, mood, contrast, saturation, any split toning, and "
    "overall feel. Your description will be used to recreate this aesthetic on another photo. "
    "Respond with a single paragraph of 2–4 sentences written as a concise colorist brief."
)


class SceneDetector:
    def __init__(self, settings: Settings) -> None:
        self._client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        self._model = settings.openrouter_model

    def detect_scene(self, image_bytes: bytes) -> "SceneInfo":  # noqa: F821
        from ..models import SceneInfo

        media_type = self._infer_media_type(image_bytes)
        data_url = self._encode_image(image_bytes, media_type)

        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=256,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_url}},
                        {
                            "type": "text",
                            "text": (
                                "Analyse this photo. Detect the scene type and "
                                "suggest up to 3 colour-grading presets from: "
                                "vintage, hawaii, cinematic, moody_rainy, "
                                "california_coastal, golden_hour, nordic, "
                                "desert_sun, jungle_green, new_york."
                            ),
                        },
                    ],
                }
            ],
            tools=[_SCENE_TOOL],
            tool_choice={"type": "function", "function": {"name": "detect_scene"}},
        )
        tool_call = response.choices[0].message.tool_calls[0]
        data = json.loads(tool_call.function.arguments)
        return SceneInfo(**data)

    def describe_style(self, reference_image_bytes: bytes) -> str:
        media_type = self._infer_media_type(reference_image_bytes)
        data_url = self._encode_image(reference_image_bytes, media_type)

        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=256,
            messages=[
                {"role": "system", "content": _STYLE_SYSTEM},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_url}},
                        {
                            "type": "text",
                            "text": "Describe the colour aesthetic of this reference image as a concise colorist brief.",
                        },
                    ],
                },
            ],
        )
        return response.choices[0].message.content.strip()

    @staticmethod
    def _encode_image(image_bytes: bytes, media_type: str) -> str:
        b64 = base64.b64encode(image_bytes).decode()
        return f"data:{media_type};base64,{b64}"

    @staticmethod
    def _infer_media_type(image_bytes: bytes) -> str:
        if image_bytes[:3] == b"\xff\xd8\xff":
            return "image/jpeg"
        if image_bytes[:4] == b"\x89PNG":
            return "image/png"
        if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
            return "image/webp"
        return "image/jpeg"
