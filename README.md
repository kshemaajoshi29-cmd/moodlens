# MoodLens

Travel photo enhancement powered by AI colour grading. Pick a preset — or describe any vibe in plain English — and MoodLens transforms your photo's mood using **Claude Haiku** (mood → parameters) and **Pillow** (colour grading). Faces and composition are never touched.

---

## How It Works

```
Your photo + mood description
        │
        ├─ Preset mood? → apply colour grade directly (zero LLM cost)
        │
        └─ Free-text mood → Claude Haiku → 12 colour parameters → Pillow grade
```

No generative AI rewrites your image. MoodLens only adjusts tone: white balance, saturation, contrast, shadows, highlights, vignette, and grain.

---

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/yourname/moodlens
cd moodlens
pip install -e ".[dev]"

# 2. Configure API key
cp .env.example .env
# Edit .env — add your OPENROUTER_API_KEY
# Get a free key at https://openrouter.ai

# 3. Enhance a photo
moodlens enhance photo.jpg --mood vintage
moodlens enhance photo.jpg --mood "california coastal afternoon"

# 4. List all presets
moodlens list-presets
```

---

## Presets

10 built-in moods — no API call required.

| Preset | Vibe |
|--------|------|
| `vintage` | Warm sepia film with grain and vignette |
| `hawaii` | Vibrant tropical paradise with golden hour warmth |
| `cinematic` | Hollywood teal-orange grade with deep shadows |
| `moody_rainy` | Desaturated blues with rain and fog atmosphere |
| `california_coastal` | Hazy Pacific light — sun-bleached, airy, cool blues |
| `golden_hour` | Rich amber sunset — warm, golden, romantic dusk |
| `nordic` | Pale overcast Scandinavian — cool, minimal, clean |
| `desert_sun` | Harsh desert sun — dusty orange, high contrast, arid |
| `jungle_green` | Lush tropical forest — vivid green, humid, dense |
| `new_york` | Gritty urban street — muted, high contrast, film grain |

---

## CLI

```bash
# Preset mood (no API cost)
moodlens enhance photo.jpg --mood vintage

# Free-text mood (calls Claude Haiku via OpenRouter)
moodlens enhance photo.jpg --mood "dreamy pastel anime sunset"

# Custom intensity and output path
moodlens enhance photo.jpg --mood golden_hour --intensity 0.7 --output result.webp

# List all presets with parameters
moodlens list-presets
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--mood`, `-m` | required | Preset name or free-text description |
| `--intensity`, `-i` | `1.0` | Effect strength (0 = no change, 1 = full) |
| `--output`, `-o` | auto | Output file path |

---

## Web UI

Start the server and open `http://localhost:8000` in your browser:

```bash
uvicorn moodlens.api.app:app --reload
```

The UI supports drag-and-drop upload, preset selection, intensity slider, and before/after comparison.

---

## REST API

### `POST /api/v1/enhance`

Multipart form upload.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image` | file | ✓ | JPEG, PNG, WebP, or HEIC (max 10 MB) |
| `mood` | string | ✓ | Preset name or free-text mood |
| `intensity` | float | — | Effect strength 0–1 (default: 1.0) |

**Response:**
```json
{
  "image_url": "data:image/webp;base64,…",
  "mood_used": "vintage",
  "style_notes": "Warm sepia film with grain and vignette",
  "intensity_used": 1.0,
  "is_preset": true
}
```

### `GET /health`

```json
{"status": "ok", "version": "0.1.0"}
```

### Example — curl

```bash
curl -X POST http://localhost:8000/api/v1/enhance \
  -F "image=@photo.jpg" \
  -F "mood=cinematic" \
  | python3 -c "
import sys, json, base64
body = json.load(sys.stdin)
data = body['image_url'].split(',')[1]
open('enhanced.webp','wb').write(base64.b64decode(data))
print('saved enhanced.webp')
"
```

---

## Running Tests

```bash
pytest tests/ -v
```

All unit tests are fully mocked — no real API calls or images required.

---

## End-to-End Smoke Test

```bash
# Start server in another terminal
uvicorn moodlens.api.app:app --reload

# Run with a real image
python scripts/test_end_to_end.py photo.jpg --mood "dreamy pastel anime"
python scripts/test_end_to_end.py photo.jpg --mood vintage
```

---

## Project Structure

```
moodlens/
├── pyproject.toml            # Package config and dependencies
├── requirements.txt          # Pinned dependencies
├── .env.example              # Environment variable template
├── start.sh                  # One-shot startup script
├── moodlens/
│   ├── config.py             # Pydantic settings (loads .env)
│   ├── models.py             # Pydantic schemas
│   ├── presets.py            # 10 built-in mood presets
│   ├── services/
│   │   ├── mood_interpreter.py   # Claude Haiku → PhotoAdjustments
│   │   └── image_enhancer.py     # Pillow + NumPy colour grading
│   ├── api/
│   │   ├── app.py                # FastAPI app factory + CORS
│   │   ├── dependencies.py       # lru_cache service singletons
│   │   └── routes/
│   │       ├── enhance.py        # POST /api/v1/enhance
│   │       └── health.py         # GET /health
│   ├── cli/
│   │   └── main.py               # Typer CLI (enhance, list-presets)
│   └── static/
│       └── index.html            # Web UI (single-page app)
├── tests/                    # Fully mocked unit tests
└── scripts/
    └── test_end_to_end.py    # Real API smoke test
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your key:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | — | Required for free-text moods. Get one free at [openrouter.ai](https://openrouter.ai) |
| `OPENROUTER_MODEL` | `anthropic/claude-haiku-4-5` | Claude model used for mood interpretation |
| `MAX_IMAGE_SIZE_MB` | `10` | Maximum upload size |
| `OUTPUT_FORMAT` | `webp` | Output image format (`webp`, `jpeg`, `png`) |

Preset moods bypass Claude entirely — no API key needed for those.

---

## Colour Grading Parameters

Claude generates (or presets define) 12 parameters applied purely via Pillow:

| Parameter | Range | Effect |
|-----------|-------|--------|
| `temperature` | −1 to +1 | Cool blue → warm gold |
| `tint` | −1 to +1 | Green → magenta |
| `saturation` | 0.5 to 2.5 | Near B&W → vivid |
| `brightness` | 0.5 to 1.5 | Dark → bright |
| `contrast` | 0.5 to 2.0 | Flat → punchy |
| `shadows_lift` | 0 to 0.3 | Deep blacks → faded matte |
| `shadows_tint` | RGB offset | Split-tone colour in darks |
| `highlights_tint` | RGB offset | Split-tone colour in brights |
| `vignette` | 0 to 1 | None → heavy dark edges |
| `grain` | 0 to 0.3 | Clean → heavy film grain |
| `sharpness` | 0 to 2.0 | Soft → crisp |
