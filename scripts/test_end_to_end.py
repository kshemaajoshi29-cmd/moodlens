#!/usr/bin/env python3
"""
MoodLens end-to-end smoke test.

Usage:
    python scripts/test_end_to_end.py sample.jpg
    python scripts/test_end_to_end.py sample.jpg --mood "dreamy pastel anime"
    python scripts/test_end_to_end.py sample.jpg --mood vintage --host http://localhost:8000

Prerequisites:
    1. Copy .env.example → .env and fill in real API keys
    2. Start the API:  uvicorn moodlens.api.app:app --reload
    3. Run this script from the project root
"""
import argparse
import base64
import sys
import time
from pathlib import Path

import httpx


def check_health(base_url: str) -> None:
    print(f"[1/3] Health check → {base_url}/health")
    resp = httpx.get(f"{base_url}/health", timeout=10.0)
    resp.raise_for_status()
    body = resp.json()
    print(f"      status={body['status']}  version={body['version']}")


def enhance_image(base_url: str, image_path: Path, mood: str) -> dict:
    print(f"[2/3] POST /api/v1/enhance")
    print(f"      image={image_path.name}  mood={mood!r}")
    t0 = time.perf_counter()

    with image_path.open("rb") as fh:
        content_type = "image/jpeg"
        suffix = image_path.suffix.lower()
        if suffix == ".png":
            content_type = "image/png"
        elif suffix in {".webp"}:
            content_type = "image/webp"

        resp = httpx.post(
            f"{base_url}/api/v1/enhance",
            files={"image": (image_path.name, fh, content_type)},
            data={"mood": mood},
            timeout=180.0,
        )

    elapsed = time.perf_counter() - t0
    resp.raise_for_status()
    body = resp.json()
    print(f"      done in {elapsed:.1f}s  is_preset={body['is_preset']}")
    print(f"      intensity={body['intensity_used']:.2f}")
    print(f"      style: {body['style_notes'][:80]}")
    return body


def save_result(body: dict, mood: str) -> Path:
    data_url: str = body["image_url"]
    # data:image/webp;base64,<data>
    header, b64_data = data_url.split(",", 1)
    ext = header.split("/")[1].split(";")[0]
    slug = mood.replace(" ", "_")[:30].strip("_")
    output_path = Path(f"output_{slug}.{ext}")
    output_path.write_bytes(base64.b64decode(b64_data))
    size_kb = output_path.stat().st_size / 1024
    print(f"[3/3] Saved → {output_path}  ({size_kb:.1f} KB)")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="MoodLens end-to-end smoke test")
    parser.add_argument("image", help="Path to an input JPEG/PNG image")
    parser.add_argument(
        "--mood",
        default="dreamy pastel anime",
        help="Mood preset name or free-text description (default: 'dreamy pastel anime')",
    )
    parser.add_argument(
        "--host",
        default="http://localhost:8000",
        help="MoodLens API base URL (default: http://localhost:8000)",
    )
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"Error: image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("MoodLens End-to-End Smoke Test")
    print("=" * 60)

    try:
        check_health(args.host)
        body = enhance_image(args.host, image_path, args.mood)
        save_result(body, args.mood)
        print("\n✓ All checks passed!")
    except httpx.HTTPStatusError as exc:
        print(f"\nHTTP {exc.response.status_code}: {exc.response.text}", file=sys.stderr)
        sys.exit(1)
    except httpx.ConnectError:
        print(
            f"\nCould not connect to {args.host}. Is the server running?\n"
            "  uvicorn moodlens.api.app:app --reload",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
