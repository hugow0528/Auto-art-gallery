#!/usr/bin/env python3
"""
Auto Art Gallery - Artwork Generator
Generates AI artwork every 30 minutes from 4:00 AM to 11:00 PM HKT using Pollinations AI API.
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

# Text models to randomly choose from (with fallback order)
TEXT_MODELS = [
    "gemini-fast",
    "gemini-search",
    "openai",
    "perplexity-fast",
    "minimax",
    "deepseek",
]

# Image models to randomly choose from (with fallback order)
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

# Topics for artwork generation
TOPICS = [
    "future of human civilization and technology",
    "artificial intelligence reshaping society",
    "health and medicine breakthroughs",
    "revolution in education through technology",
    "social media culture and human connection",
    "Hong Kong city life and culture",
    "global climate crisis and environmental solutions",
    "space exploration and the cosmos",
    "urban architecture of the future",
    "traditional vs modern culture clash in Asia",
    "mental health awareness in the digital age",
    "renewable energy and sustainable living",
    "cybersecurity and privacy in the digital world",
    "cultural diversity and global harmony",
    "economic inequality and social justice",
    "Hong Kong protest art and resilience",
    "ocean conservation and marine life",
    "quantum computing and the future",
    "biotechnology and genetic engineering",
    "virtual reality and the metaverse",
    "street food culture in Hong Kong",
    "news headlines of tomorrow",
    "post-pandemic world transformation",
    "sports and human physical achievement",
    "music and the evolution of sound",
    "fashion meets technology",
    "animals and nature conservation",
    "blockchain and decentralized future",
    "human migration and global nomadism",
    "ancient traditions meeting the modern world",
]

MAX_SEED = 2**31 - 1

ART_STYLES = [
    "photorealistic",
    "digital art",
    "oil painting",
    "watercolor",
    "cyberpunk",
    "surrealist",
    "impressionist",
    "abstract expressionist",
    "concept art",
    "cinematic",
    "anime-inspired",
    "noir",
    "baroque",
    "minimalist",
    "pop art",
]

MOODS = [
    "dramatic and intense",
    "peaceful and serene",
    "mysterious and ethereal",
    "vibrant and energetic",
    "melancholic and reflective",
    "hopeful and uplifting",
    "dark and dystopian",
    "whimsical and dreamlike",
    "powerful and monumental",
    "intimate and human",
]

LIGHTING = [
    "golden hour sunlight",
    "dramatic studio lighting",
    "moonlight and shadows",
    "neon city glow",
    "soft diffused daylight",
    "candlelight ambiance",
    "bioluminescent glow",
    "stormy overcast light",
    "arctic aurora borealis",
    "dappled forest light",
]

COLOR_PALETTES = [
    "warm amber and orange tones",
    "cool blues and purples",
    "vibrant neon colors",
    "monochromatic black and white",
    "soft pastel hues",
    "high contrast black and gold",
    "earth tones and terracotta",
    "emerald and deep forest green",
    "crimson and deep red",
    "holographic iridescent",
]


def is_english(text):
    """Return True if the text is predominantly English (≤15% non-ASCII characters).

    This heuristic specifically catches CJK (Chinese, Japanese, Korean), Arabic,
    Cyrillic, and other non-Latin-script languages, which are the primary concern
    for this gallery's prompt generation.
    """
    if not text:
        return False
    non_ascii = sum(1 for c in text if ord(c) > 127)
    return (non_ascii / len(text)) < 0.15


def get_shuffled_models(models, preferred=None):
    """Return models list starting from a random one, optionally starting with preferred."""
    shuffled = models.copy()
    random.shuffle(shuffled)
    if preferred and preferred in shuffled:
        shuffled.remove(preferred)
        shuffled.insert(0, preferred)
    return shuffled


def generate_text_prompt(topic):
    """Generate an image prompt using a random text model with fallback."""
    art_style = random.choice(ART_STYLES)
    mood = random.choice(MOODS)
    lighting = random.choice(LIGHTING)
    color_palette = random.choice(COLOR_PALETTES)

    system_message = (
        "You are a world-class creative director and AI artist. "
        "Your task is to craft a single, vivid, detailed image generation prompt. "
        "The prompt should be descriptive, rich in visual detail, and mention artistic style, "
        "mood, lighting, color palette, and specific visual elements. "
        "Respond with ONLY the image prompt itself — no explanations, no titles, no markdown. "
        "You MUST write your response exclusively in English. Do not use any other language."
    )

    user_message = (
        f"Create a unique, detailed image generation prompt about: {topic}\n\n"
        f"Required elements to incorporate naturally:\n"
        f"- Art style: {art_style}\n"
        f"- Mood: {mood}\n"
        f"- Lighting: {lighting}\n"
        f"- Color palette: {color_palette}\n\n"
        "Make it visually stunning, award-winning, and highly detailed. "
        "The prompt should be 2-4 sentences long and paint a clear mental picture. "
        "Write in English only."
    )

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    model_order = get_shuffled_models(TEXT_MODELS)
    for model in model_order:
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
                    "max_tokens": 400,
                    "temperature": 1.1,
                },
                timeout=45,
            )
            resp.raise_for_status()
            data = resp.json()
            prompt = data["choices"][0]["message"]["content"].strip()
            # Remove any surrounding quotes if present
            prompt = prompt.strip('"').strip("'")
            if not is_english(prompt):
                print(f"  ✗ Model {model} returned non-English response, skipping")
                time.sleep(2)
                continue
            print(f"  ✓ Text generated with {model}")
            return prompt, model
        except Exception as exc:
            print(f"  ✗ Text model {model} failed: {exc}")
            time.sleep(2)
            continue

    # Fallback prompt if all models fail
    fallback = (
        f"A breathtaking {art_style} artwork depicting {topic}, "
        f"with {mood} atmosphere, {lighting}, and {color_palette}. "
        "Ultra-detailed, 8K resolution, award-winning composition."
    )
    print("  Using fallback prompt")
    return fallback, "fallback"


def generate_image(prompt, seed=None):
    """Generate an image using a random image model with fallback."""
    if seed is None:
        seed = random.randint(1, MAX_SEED)

    encoded_prompt = urllib.parse.quote(prompt)
    headers = {"Authorization": f"Bearer {API_KEY}"}

    model_order = get_shuffled_models(IMAGE_MODELS)
    for model in model_order:
        try:
            print(f"  Trying image model: {model}")
            url = (
                f"{API_BASE}/image/{encoded_prompt}"
                f"?model={model}&width=768&height=768&seed={seed}&nologo=true"
            )
            resp = requests.get(url, headers=headers, timeout=120)
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            if "image" in content_type:
                print(f"  ✓ Image generated with {model}")
                return resp.content, model, seed
            else:
                print(f"  ✗ Model {model} returned non-image content: {content_type}")
        except Exception as exc:
            print(f"  ✗ Image model {model} failed: {exc}")
            time.sleep(2)
            continue

    return None, None, seed


def load_gallery(gallery_file):
    """Load existing gallery or return empty structure."""
    if os.path.exists(gallery_file):
        try:
            with open(gallery_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as exc:
            print(f"Warning: Could not load gallery.json: {exc}")
    return {"artworks": []}


def save_gallery(gallery, gallery_file):
    """Save gallery to JSON file."""
    with open(gallery_file, "w", encoding="utf-8") as f:
        json.dump(gallery, f, indent=2, ensure_ascii=False)


def main():
    print("=" * 60)
    print("Auto Art Gallery - Artwork Generator")
    print("=" * 60)

    if not API_KEY:
        print("ERROR: POLLINATIONS_API_KEY environment variable not set")
        raise SystemExit(1)

    # Set up directories
    images_dir = "images"
    gallery_file = "gallery.json"
    os.makedirs(images_dir, exist_ok=True)

    # Pick a random topic
    topic = random.choice(TOPICS)
    print(f"\nTopic: {topic}")

    # Generate the image prompt
    print("\nGenerating image prompt...")
    prompt, text_model = generate_text_prompt(topic)
    print(f"Prompt: {prompt[:120]}{'...' if len(prompt) > 120 else ''}")

    # Generate a random seed for reproducibility + uniqueness
    seed = random.randint(1, MAX_SEED)
    print(f"\nGenerating image (seed: {seed})...")
    image_data, image_model, used_seed = generate_image(prompt, seed)

    if image_data is None:
        print("ERROR: Failed to generate image with all models")
        raise SystemExit(1)

    # Save the image with JPEG optimization for smaller file size
    timestamp = datetime.now(HKT).strftime("%Y%m%d_%H%M%S")
    filename = f"{images_dir}/artwork_{timestamp}.jpg"
    try:
        img = Image.open(io.BytesIO(image_data))
        img.save(filename, format="JPEG", quality=85, optimize=True)
        saved_size = os.path.getsize(filename)
    except Exception as exc:
        print(f"  Warning: Pillow optimization failed ({exc}), saving raw bytes")
        with open(filename, "wb") as f:
            f.write(image_data)
        saved_size = len(image_data)
    print(f"\nSaved image: {filename} ({saved_size:,} bytes)")

    # Update gallery metadata
    gallery = load_gallery(gallery_file)
    artwork = {
        "id": timestamp,
        "filename": filename,
        "topic": topic,
        "prompt": prompt,
        "text_model": text_model,
        "image_model": image_model,
        "seed": used_seed,
        "created_at": datetime.now(HKT).isoformat(),
    }
    gallery["artworks"].insert(0, artwork)
    save_gallery(gallery, gallery_file)
    print(f"Updated {gallery_file} ({len(gallery['artworks'])} artworks total)")

    print("\n✓ Artwork generation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
