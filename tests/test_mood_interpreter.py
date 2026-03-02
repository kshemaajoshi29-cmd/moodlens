import json
from unittest.mock import MagicMock, patch

import pytest

from moodlens.models import PhotoAdjustments


def _make_tool_response(data: dict) -> MagicMock:
    """Build a fake OpenAI chat.completions.create response with a tool_call."""
    tool_call = MagicMock()
    tool_call.function.arguments = json.dumps(data)
    message = MagicMock()
    message.tool_calls = [tool_call]
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


_VALID_ADJ = {
    "temperature": 0.3,
    "tint": 0.0,
    "saturation": 1.2,
    "brightness": 1.05,
    "contrast": 1.1,
    "shadows_lift": 0.0,
    "shadows_tint": [5, 2, -3],
    "highlights_tint": [8, 2, -5],
    "vignette": 0.2,
    "grain": 0.0,
    "sharpness": 1.1,
    "style_notes": "Warm golden hour glow",
}


def test_interpret_returns_photo_adjustments(mock_settings):
    with patch("moodlens.services.mood_interpreter.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_tool_response(_VALID_ADJ)

        from moodlens.services.mood_interpreter import MoodInterpreter

        result = MoodInterpreter(mock_settings).interpret("warm golden hour")

    assert isinstance(result, PhotoAdjustments)
    assert result.temperature == pytest.approx(0.3)
    assert result.saturation == pytest.approx(1.2)
    assert result.style_notes == "Warm golden hour glow"


def test_interpret_calls_openrouter_with_correct_model(mock_settings):
    with patch("moodlens.services.mood_interpreter.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_tool_response(_VALID_ADJ)

        from moodlens.services.mood_interpreter import MoodInterpreter

        MoodInterpreter(mock_settings).interpret("moody noir")

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == mock_settings.openrouter_model


def test_interpret_uses_tool_choice(mock_settings):
    with patch("moodlens.services.mood_interpreter.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_tool_response(_VALID_ADJ)

        from moodlens.services.mood_interpreter import MoodInterpreter

        MoodInterpreter(mock_settings).interpret("dreamy pastel")

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["tool_choice"] == {
            "type": "function",
            "function": {"name": "photo_adjustments"},
        }


def test_interpret_passes_mood_in_user_message(mock_settings):
    with patch("moodlens.services.mood_interpreter.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_tool_response(_VALID_ADJ)

        from moodlens.services.mood_interpreter import MoodInterpreter

        MoodInterpreter(mock_settings).interpret("cyberpunk neon rain")

        messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
        assert any("cyberpunk neon rain" in str(m) for m in messages)


def test_interpret_connects_to_openrouter_base_url(mock_settings):
    with patch("moodlens.services.mood_interpreter.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_tool_response(_VALID_ADJ)

        from moodlens.services.mood_interpreter import MoodInterpreter

        MoodInterpreter(mock_settings)

        call_kwargs = mock_cls.call_args.kwargs
        assert call_kwargs["base_url"] == "https://openrouter.ai/api/v1"
