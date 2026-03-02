import json

from openai import OpenAI

from ..config import Settings
from ..models import PhotoAdjustments

SYSTEM_PROMPT = """You are a professional photo colorist and editor.
Convert mood descriptions into precise photo adjustment parameters.
These adjust ONLY colour grading, lighting, and atmosphere — image content (faces, objects) is NEVER changed.

Parameter ranges and meaning:
- temperature: -1.0 (icy blue) to 1.0 (golden warm). 0 = neutral
- tint:        -1.0 (green)    to 1.0 (magenta).     0 = neutral
- saturation:  0.5 (near B&W)  to 1.8 (vivid).       1.0 = unchanged
- brightness:  0.7 (darker)    to 1.3 (brighter).     1.0 = unchanged
- contrast:    0.6 (flat/matte) to 1.8 (punchy).      1.0 = unchanged
- shadows_lift: 0.0 (deep blacks) to 0.25 (faded matte)
- shadows_tint:    [R, G, B] colour added to dark areas  (each -25 to 25)
- highlights_tint: [R, G, B] colour added to bright areas (each -20 to 20)
- vignette:    0.0 (none) to 0.8 (strong dark edges)
- grain:       0.0 (clean) to 0.12 (heavy film grain)
- sharpness:   0.6 (soft)  to 1.6 (crisp).  1.0 = unchanged
- style_notes: one-line UI label, max 55 chars

Calibration examples:
- "warm golden hour"   → temperature=0.4, saturation=1.2, highlights_tint=[8,2,-5], brightness=1.05, vignette=0.2
- "dark noir"          → temperature=-0.2, saturation=0.5, contrast=1.5, vignette=0.65, brightness=0.82
- "dreamy pastel"      → saturation=0.78, brightness=1.08, contrast=0.82, shadows_lift=0.1, grain=0.03, sharpness=0.8
- "punchy street photo"→ contrast=1.4, sharpness=1.35, saturation=1.15, vignette=0.3
- "cool arctic"        → temperature=-0.6, saturation=0.7, brightness=1.05, shadows_tint=[-5,-2,14]"""

_TOOL = {
    "type": "function",
    "function": {
        "name": "photo_adjustments",
        "description": "Return colour grading and photo adjustment parameters for the given mood",
        "parameters": {
            "type": "object",
            "properties": {
                "temperature":     {"type": "number"},
                "tint":            {"type": "number"},
                "saturation":      {"type": "number"},
                "brightness":      {"type": "number"},
                "contrast":        {"type": "number"},
                "shadows_lift":    {"type": "number"},
                "shadows_tint":    {"type": "array", "items": {"type": "integer"},
                                    "minItems": 3, "maxItems": 3},
                "highlights_tint": {"type": "array", "items": {"type": "integer"},
                                    "minItems": 3, "maxItems": 3},
                "vignette":        {"type": "number"},
                "grain":           {"type": "number"},
                "sharpness":       {"type": "number"},
                "style_notes":     {"type": "string"},
            },
            "required": [
                "temperature", "tint", "saturation", "brightness", "contrast",
                "shadows_lift", "shadows_tint", "highlights_tint",
                "vignette", "grain", "sharpness", "style_notes",
            ],
            "additionalProperties": False,
        },
    },
}


class MoodInterpreter:
    def __init__(self, settings: Settings) -> None:
        self._client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        self._model = settings.openrouter_model

    def interpret(self, mood_text: str) -> PhotoAdjustments:
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=512,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Generate photo adjustments for this mood: {mood_text}",
                },
            ],
            tools=[_TOOL],
            tool_choice={"type": "function", "function": {"name": "photo_adjustments"}},
        )
        tool_call = response.choices[0].message.tool_calls[0]
        data = json.loads(tool_call.function.arguments)
        return PhotoAdjustments(**data)
