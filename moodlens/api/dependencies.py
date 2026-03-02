from dataclasses import dataclass
from functools import lru_cache

from ..config import Settings
from ..services.image_enhancer import ImageEnhancer
from ..services.mood_interpreter import MoodInterpreter


@dataclass
class Services:
    settings: Settings
    mood_interpreter: MoodInterpreter
    image_enhancer: ImageEnhancer


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_services() -> Services:
    settings = get_settings()
    return Services(
        settings=settings,
        mood_interpreter=MoodInterpreter(settings),
        image_enhancer=ImageEnhancer(),  # pure Pillow — no API credentials needed
    )
