from .models import PhotoAdjustments

# Presets define pure colour-grading adjustments.
# No Stable Diffusion, no generative AI — faces and composition are never touched.
PRESETS: dict[str, PhotoAdjustments] = {
    "vintage": PhotoAdjustments(
        temperature=0.35,
        tint=0.10,
        saturation=0.72,
        brightness=0.96,
        contrast=0.88,
        shadows_lift=0.12,        # lifted blacks → classic faded film look
        shadows_tint=[10, 5, -5],  # warm brown in shadows
        highlights_tint=[8, 3, -10],  # amber highlights
        vignette=0.55,
        grain=0.08,
        sharpness=0.85,
        style_notes="Warm sepia film with grain and vignette",
    ),
    "hawaii": PhotoAdjustments(
        temperature=0.40,
        tint=-0.10,
        saturation=1.45,
        brightness=1.08,
        contrast=1.12,
        shadows_lift=0.0,
        shadows_tint=[-5, 5, 10],   # teal in shadows
        highlights_tint=[10, 4, -5],  # golden highlights
        vignette=0.15,
        grain=0.0,
        sharpness=1.20,
        style_notes="Vibrant tropical paradise with golden hour warmth",
    ),
    "cinematic": PhotoAdjustments(
        temperature=0.05,
        tint=0.05,
        saturation=0.88,
        brightness=0.93,
        contrast=1.35,
        shadows_lift=0.0,
        shadows_tint=[-10, 5, 15],   # teal shadows (the Hollywood look)
        highlights_tint=[15, 3, -10],  # orange highlights
        vignette=0.55,
        grain=0.02,
        sharpness=1.10,
        style_notes="Hollywood teal-orange grade with deep shadows",
    ),
    "moody_rainy": PhotoAdjustments(
        temperature=-0.45,
        tint=0.10,
        saturation=0.58,
        brightness=0.83,
        contrast=0.92,
        shadows_lift=0.04,
        shadows_tint=[-5, -3, 15],   # blue-grey shadows
        highlights_tint=[-3, -2, 10],  # cool highlights
        vignette=0.65,
        grain=0.06,
        sharpness=0.85,
        style_notes="Desaturated blues with rain and fog atmosphere",
    ),
    "california_coastal": PhotoAdjustments(
        temperature=-0.15,
        tint=-0.08,
        saturation=1.10,
        brightness=1.12,
        contrast=0.95,
        shadows_lift=0.10,           # lifted blacks — hazy beach light
        shadows_tint=[-8, 2, 18],    # blue-teal shadows (ocean reflection)
        highlights_tint=[12, 8, -5],  # warm sun-bleached highlights
        vignette=0.10,
        grain=0.02,
        sharpness=1.05,
        style_notes="Hazy Pacific light — sun-bleached, airy, cool blues",
    ),
    "golden_hour": PhotoAdjustments(
        temperature=0.60,
        tint=0.05,
        saturation=1.30,
        brightness=1.05,
        contrast=1.18,
        shadows_lift=0.05,
        shadows_tint=[15, 5, -8],    # warm amber in shadows
        highlights_tint=[20, 8, -12],  # rich golden highlights
        vignette=0.30,
        grain=0.01,
        sharpness=1.15,
        style_notes="Rich amber sunset — warm, golden, romantic dusk",
    ),
    "nordic": PhotoAdjustments(
        temperature=-0.50,
        tint=0.05,
        saturation=0.65,
        brightness=1.05,
        contrast=0.85,
        shadows_lift=0.08,           # lifted blacks — overcast Nordic light
        shadows_tint=[-8, -4, 12],   # pale blue shadows
        highlights_tint=[-5, -2, 8],  # cool white highlights
        vignette=0.20,
        grain=0.04,
        sharpness=0.90,
        style_notes="Pale overcast Scandinavian — cool, minimal, clean",
    ),
    "desert_sun": PhotoAdjustments(
        temperature=0.55,
        tint=0.08,
        saturation=1.15,
        brightness=1.03,
        contrast=1.30,
        shadows_lift=0.0,
        shadows_tint=[12, 4, -10],   # warm rust-orange in shadows
        highlights_tint=[18, 6, -14],  # scorched amber highlights
        vignette=0.25,
        grain=0.03,
        sharpness=1.25,
        style_notes="Harsh desert sun — dusty orange, high contrast, arid",
    ),
    "jungle_green": PhotoAdjustments(
        temperature=-0.05,
        tint=-0.20,
        saturation=1.50,
        brightness=0.95,
        contrast=1.15,
        shadows_lift=0.02,
        shadows_tint=[-10, 12, -5],  # deep green in shadows
        highlights_tint=[-5, 10, -8],  # lush green highlights
        vignette=0.35,
        grain=0.02,
        sharpness=1.10,
        style_notes="Lush tropical forest — vivid green, humid, dense",
    ),
    "new_york": PhotoAdjustments(
        temperature=-0.10,
        tint=0.05,
        saturation=0.80,
        brightness=0.90,
        contrast=1.25,
        shadows_lift=0.0,
        shadows_tint=[-5, -3, 10],   # cool blue urban shadows
        highlights_tint=[8, 5, -5],   # slightly warm streetlight glow
        vignette=0.50,
        grain=0.07,
        sharpness=1.20,
        style_notes="Gritty urban street — muted, high contrast, film grain",
    ),
}
