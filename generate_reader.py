#!/usr/bin/env python3
"""
Book Reader Generator
Reads sequentially from book/source.txt, extracts ~20-word segments (completing
at the next sentence-ending punctuation mark), generates a paired AI image, and
saves progress so the next run continues from where it left off.
Runs until the whole book has been processed.
"""

import io
import os
import json
import random
import time
import urllib.parse
from datetime import datetime, timezone, timedelta

import requests
from PIL import Image

API_KEY = os.environ.get("POLLINATIONS_API_KEY", "")

HKT = timezone(timedelta(hours=8))
API_BASE = "https://gen.pollinations.ai"

BOOK_FILE = "book/source.txt"
PROGRESS_FILE = "book/reader_progress.json"
ENTRIES_FILE = "book/reader_entries.json"
IMAGES_DIR = "book/reader_images"        # filesystem path for saving images
IMAGES_WEB_PREFIX = "reader_images"      # path relative to book/reader.html for use in HTML

# ~20 Chinese words ≈ 40-80 characters; we read at least this many chars then
# advance to the next sentence-ending punctuation mark.
TARGET_CHARS = 60

# Sentence-ending punctuation (Chinese + Western)
SENTENCE_END_PUNCT = set("。！？!?")

MAX_SEED = 2**31 - 1

TEXT_MODELS = [
    "gemini-fast",
    "gemini-search",
    "openai",
    "perplexity-fast",
    "minimax",
    "deepseek",
]

IMAGE_MODELS = [
    "flux",
    "zimage",
    "flux-2-dev",
    "imagen-4",
    "grok-imagine",
    "klein",
    "klein-large",
    "gptimage",
]


def get_shuffled_models(models):
    """Return a randomly-shuffled copy of the models list."""
    shuffled = models.copy()
    random.shuffle(shuffled)
    return shuffled


def load_progress():
    """Return (offset, completed) from the progress file."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("offset", 0), data.get("completed", False)
        except (json.JSONDecodeError, IOError):
            pass
    return 0, False


def save_progress(offset, completed=False):
    """Persist the current reading position."""
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump({"offset": offset, "completed": completed}, f)


def load_entries():
    """Load existing reader entries or return an empty structure."""
    if os.path.exists(ENTRIES_FILE):
        try:
            with open(ENTRIES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"entries": [], "book_total_chars": 0, "completed": False}


def save_entries(data):
    """Save reader entries to JSON."""
    with open(ENTRIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def extract_segment(text, offset):
    """
    Extract ~TARGET_CHARS characters from *offset*, extending to the next
    sentence-ending punctuation mark so that segments are always complete
    sentences.  Returns (segment_text, new_offset).
    """
    if offset >= len(text):
        return None, offset

    # Skip leading whitespace / blank lines
    while offset < len(text) and text[offset] in " \t\r\n":
        offset += 1

    if offset >= len(text):
        return None, offset

    target_end = min(offset + TARGET_CHARS, len(text))

    # Extend past the target until we hit a sentence-ending punctuation mark
    pos = target_end
    while pos < len(text) and text[pos] not in SENTENCE_END_PUNCT:
        pos += 1

    # Include the punctuation character itself
    if pos < len(text):
        pos += 1

    segment = text[offset:pos].strip()
    if not segment:
        return None, pos

    return segment, pos


def generate_image_prompt(chinese_text):
    """Use an AI text model to craft an English image-generation prompt
    that captures the visual essence of the provided Chinese literary passage."""
    system_message = (
        "You are a creative visual artist. Given a segment of Chinese literary text, "
        "craft a vivid, detailed English image-generation prompt that captures the "
        "scene, atmosphere, characters, and visual essence of the passage. "
        "Include artistic style, mood, lighting, and specific visual elements. "
        "Respond ONLY with the image prompt in English — no explanations, no "
        "translations, no markdown."
    )
    user_message = (
        f"Create an image-generation prompt based on this Chinese literary passage:\n\n"
        f"{chinese_text}\n\n"
        "Describe a specific visual scene in English, suitable for AI image generation. "
        "Include setting, atmosphere, any characters present, and artistic style. "
        "2–4 sentences only. English only."
    )

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    for model in get_shuffled_models(TEXT_MODELS):
        try:
            print(f"  Trying text model: {model}")
            resp = requests.post(
                f"{API_BASE}/v1/chat/completions",
                headers=headers,
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message},
                    ],
                    "max_tokens": 300,
                    "temperature": 0.9,
                },
                timeout=45,
            )
            resp.raise_for_status()
            data = resp.json()
            prompt = data["choices"][0]["message"]["content"].strip().strip("\"'\u201c\u201d\u2018\u2019")
            # Reject responses that are still mostly non-ASCII (non-English)
            non_ascii = sum(1 for c in prompt if ord(c) > 127)
            if len(prompt) > 0 and (non_ascii / len(prompt)) < 0.15:
                print(f"  ✓ Prompt generated with {model}")
                return prompt, model
            print(f"  ✗ Model {model} returned non-English response, skipping")
            time.sleep(2)
        except Exception as exc:
            print(f"  ✗ Text model {model} failed: {exc}")
            time.sleep(2)

    # Fallback prompt when all models fail
    fallback = (
        "A poignant scene from a Chinese literary memoir, traditional Chinese setting, "
        "warm candlelight, ink-wash painting style, melancholic and reflective atmosphere, "
        "soft diffused light, muted earth tones."
    )
    print("  Using fallback prompt")
    return fallback, "fallback"


def generate_image(prompt, seed=None):
    """Generate an image using a randomly-chosen image model with fallback."""
    if seed is None:
        seed = random.randint(1, MAX_SEED)

    encoded_prompt = urllib.parse.quote(prompt)
    headers = {"Authorization": f"Bearer {API_KEY}"}

    for model in get_shuffled_models(IMAGE_MODELS):
        try:
            print(f"  Trying image model: {model}")
            url = (
                f"{API_BASE}/image/{encoded_prompt}"
                f"?model={model}&width=768&height=768&seed={seed}&nologo=true"
            )
            resp = requests.get(url, headers=headers, timeout=120)
            resp.raise_for_status()
            if "image" in resp.headers.get("Content-Type", ""):
                print(f"  ✓ Image generated with {model}")
                return resp.content, model, seed
            print(f"  ✗ Model {model} returned non-image content")
        except Exception as exc:
            print(f"  ✗ Image model {model} failed: {exc}")
            time.sleep(2)

    return None, None, seed


def main():
    print("=" * 60)
    print("Book Reader Generator")
    print("=" * 60)

    if not API_KEY:
        print("ERROR: POLLINATIONS_API_KEY environment variable not set")
        raise SystemExit(1)

    # Load the full book text
    with open(BOOK_FILE, "r", encoding="utf-8") as f:
        book_text = f.read()
    total_chars = len(book_text)
    print(f"Book loaded: {total_chars:,} characters")

    # Load previous progress
    offset, completed = load_progress()
    if completed:
        print("✓ Book already fully processed. Nothing to do.")
        return

    pct = 100.0 * offset / total_chars if total_chars else 0
    print(f"Current offset: {offset:,} / {total_chars:,} ({pct:.1f}%)")

    # Extract the next segment
    segment, new_offset = extract_segment(book_text, offset)
    if segment is None:
        print("✓ Book fully processed — marking as complete.")
        entries = load_entries()
        entries["completed"] = True
        save_entries(entries)
        save_progress(new_offset, completed=True)
        return

    seg_len = new_offset - offset
    print(f"\nExtracted segment ({seg_len} chars):")
    preview = segment.replace("\n", " ")
    print(f"  {preview[:100]}{'...' if len(preview) > 100 else ''}")

    # Generate an image prompt from the extracted text
    print("\nGenerating image prompt from text...")
    prompt, text_model = generate_image_prompt(segment)
    print(f"Prompt: {prompt[:120]}{'...' if len(prompt) > 120 else ''}")

    # Generate the image
    seed = random.randint(1, MAX_SEED)
    print(f"\nGenerating image (seed: {seed})...")
    image_data, image_model, used_seed = generate_image(prompt, seed)

    if image_data is None:
        print("ERROR: Failed to generate image with all models")
        raise SystemExit(1)

    # Save the image with JPEG optimisation
    os.makedirs(IMAGES_DIR, exist_ok=True)
    timestamp = datetime.now(HKT).strftime("%Y%m%d_%H%M%S")
    img_filename = f"reader_{timestamp}.jpg"
    fs_filename = f"{IMAGES_DIR}/{img_filename}"      # filesystem path for saving
    web_filename = f"{IMAGES_WEB_PREFIX}/{img_filename}"  # relative path for HTML (relative to book/)
    try:
        img = Image.open(io.BytesIO(image_data))
        img.save(fs_filename, format="JPEG", quality=85, optimize=True)
        saved_size = os.path.getsize(fs_filename)
    except Exception as exc:
        print(f"  Warning: Pillow optimisation failed ({exc}), saving raw bytes")
        with open(fs_filename, "wb") as f:
            f.write(image_data)
        saved_size = len(image_data)
    print(f"\nSaved image: {fs_filename} ({saved_size:,} bytes)")

    # Update entries file
    entries = load_entries()
    entries["book_total_chars"] = total_chars
    is_complete = new_offset >= total_chars
    entries["completed"] = is_complete
    entries["entries"].append(
        {
            "id": timestamp,
            "offset_start": offset,
            "offset_end": new_offset,
            "text": segment,
            "prompt": prompt,
            "image": web_filename,
            "text_model": text_model,
            "image_model": image_model,
            "seed": used_seed,
            "created_at": datetime.now(HKT).isoformat(),
        }
    )
    save_entries(entries)
    print(f"Updated {ENTRIES_FILE} ({len(entries['entries'])} entries total)")

    # Persist the new reading position
    save_progress(new_offset, completed=is_complete)

    if is_complete:
        print("\n🎉 Book fully processed!")
    else:
        remaining = total_chars - new_offset
        print(f"\n✓ Segment complete! {remaining:,} characters remaining.")

    print("=" * 60)


if __name__ == "__main__":
    main()
