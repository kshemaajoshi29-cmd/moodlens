import pytest
from moodlens.models import PhotoAdjustments
from moodlens.presets import PRESETS


def test_four_presets_exist():
    assert len(PRESETS) == 4


def test_all_expected_keys_present():
    assert set(PRESETS.keys()) == {"vintage", "hawaii", "cinematic", "moody_rainy"}


@pytest.mark.parametrize("name", ["vintage", "hawaii", "cinematic", "moody_rainy"])
def test_preset_is_photo_adjustments(name):
    assert isinstance(PRESETS[name], PhotoAdjustments)


@pytest.mark.parametrize("name", ["vintage", "hawaii", "cinematic", "moody_rainy"])
def test_preset_is_immutable(name):
    """PhotoAdjustments is frozen — mutation must raise."""
    with pytest.raises(Exception):
        PRESETS[name].temperature = 0.99  # type: ignore[misc]


@pytest.mark.parametrize("name", ["vintage", "hawaii", "cinematic", "moody_rainy"])
def test_preset_values_in_range(name):
    adj = PRESETS[name]
    assert -1.0 <= adj.temperature <= 1.0
    assert -1.0 <= adj.tint <= 1.0
    assert 0.0 <= adj.saturation <= 2.5
    assert 0.5 <= adj.brightness <= 1.5
    assert 0.5 <= adj.contrast <= 2.0
    assert 0.0 <= adj.shadows_lift <= 0.3
    assert 0.0 <= adj.vignette <= 1.0
    assert 0.0 <= adj.grain <= 0.3


@pytest.mark.parametrize("name", ["vintage", "hawaii", "cinematic", "moody_rainy"])
def test_preset_shadows_tint_has_3_channels(name):
    adj = PRESETS[name]
    assert len(adj.shadows_tint) == 3
    assert len(adj.highlights_tint) == 3


@pytest.mark.parametrize("name", ["vintage", "hawaii", "cinematic", "moody_rainy"])
def test_preset_has_style_notes(name):
    assert PRESETS[name].style_notes.strip()


def test_vintage_is_warm():
    assert PRESETS["vintage"].temperature > 0


def test_hawaii_is_vibrant():
    assert PRESETS["hawaii"].saturation > 1.2


def test_cinematic_has_split_tone():
    adj = PRESETS["cinematic"]
    # teal shadows: blue channel positive, red negative
    assert adj.shadows_tint[2] > 0   # blue up in shadows
    assert adj.highlights_tint[0] > 0  # red up in highlights


def test_moody_rainy_is_desaturated_and_cool():
    adj = PRESETS["moody_rainy"]
    assert adj.saturation < 0.8
    assert adj.temperature < 0
