# 🎨 Auto Art Gallery

> An autonomous AI-powered art gallery that generates brand-new artworks throughout the day and publishes them to a beautiful GitHub Pages website — automatically.

[![Generate Artwork](https://github.com/kychugo/Auto-art-gallery/actions/workflows/generate.yml/badge.svg)](https://github.com/kychugo/Auto-art-gallery/actions/workflows/generate.yml)
[![Deploy to GitHub Pages](https://github.com/kychugo/Auto-art-gallery/actions/workflows/deploy.yml/badge.svg)](https://github.com/kychugo/Auto-art-gallery/actions/workflows/deploy.yml)

---

## ✨ Features

| Feature | Detail |
|---|---|
| ⏰ Auto-generation | New artwork at scheduled times daily via GitHub Actions |
| 🎲 Always unique | Random topic, art style, mood, lighting & seed every time |
| 🤖 Multi-model AI | Randomly picks from **6 text models** + **8 image models** with auto-fallback |
| 🌍 Diverse topics | 30+ topics: AI, Hong Kong, global news, climate, health, culture … |
| 🖼️ Beautiful gallery | Responsive masonry grid, lightbox, search, filter, download |
| 🔁 Manual trigger | Run generation on-demand from the Actions tab |

---

## 🚀 Setup Guide

Follow these steps **once** after forking / cloning the repository.

---

### Step 1 — Add the API Key Secret

The generator uses [Pollinations AI](https://pollinations.ai). You need to store the API key as a **GitHub Actions Repository Secret** so it is never exposed in source code.

1. Go to your repository on GitHub.
2. Click **Settings** (top menu).
3. In the left sidebar, expand **Secrets and variables** → click **Actions**.
4. Under **Repository secrets**, click **New repository secret**.
5. Fill in the form:

   | Field | Value |
   |---|---|
   | **Name** | `POLLINATIONS_API_KEY` |
   | **Secret** | `sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` ← paste your key here |

6. Click **Add secret**.

> ⚠️ **Never** commit the API key directly into any file. The workflow reads it from the secret automatically via `${{ secrets.POLLINATIONS_API_KEY }}`.

---

### Step 2 — Enable GitHub Pages

1. Go to **Settings** → **Pages** (left sidebar).
2. Under **Source**, select **GitHub Actions**.
3. Click **Save**.

That's it. The Pages deploy workflow will trigger automatically whenever new artwork is committed to `main`.

---

### Step 3 — Trigger Your First Artwork (Manual)

You don't have to wait for the next scheduled run!

1. Go to the **Actions** tab in your repository.
2. Click **Generate Artwork** in the left sidebar.
3. Click the **Run workflow** button (top-right of the runs list).
4. Select branch `main` → click **Run workflow**.

The workflow will:
- Pick a random topic, art style, mood, lighting, and color palette
- Call a random text model to craft a rich image prompt
- Call a random image model to generate the artwork
- Commit the image + update `gallery.json`
- Automatically trigger the Pages deploy

Your gallery will be live at:
```
https://<your-github-username>.github.io/Auto-art-gallery/
```

---

## 🔄 How It Works

```
At scheduled times (or on-demand)
        │
        ▼
┌───────────────────────────┐
│   Generate Artwork CI     │
│                           │
│  1. Pick random topic     │
│  2. Pick random text      │
│     model (6 options)     │
│  3. Generate image prompt │
│     via Pollinations AI   │
│  4. Pick random image     │
│     model (8 options)     │
│  5. Generate image        │
│  6. Save to images/       │
│  7. Update gallery.json   │
│  8. Commit & push → main  │
└───────────┬───────────────┘
            │ push to main triggers
            ▼
┌───────────────────────────┐
│   Deploy to Pages CI      │
│                           │
│  Deploys entire repo to   │
│  GitHub Pages             │
└───────────────────────────┘
```

---

## 🤖 AI Models Used

### Text Models (prompt generation)
One is chosen randomly each run; the next is tried automatically if one fails.

| Model ID | Provider |
|---|---|
| `gemini-fast` | Google Gemini 2.5 Flash Lite |
| `gemini-search` | Google Gemini 2.5 Flash Lite (search) |
| `openai` | OpenAI GPT-5 Mini |
| `perplexity-fast` | Perplexity Sonar |
| `minimax` | MiniMax M2.5 |
| `deepseek` | DeepSeek V3.2 |

### Image Models (artwork generation)
One is chosen randomly each run; the next is tried automatically if one fails.

| Model ID | Provider |
|---|---|
| `flux` | Flux Schnell |
| `zimage` | Z-Image Turbo |
| `flux-2-dev` | FLUX.2 Dev (api.airforce) |
| `imagen-4` | Imagen 4 (api.airforce) |
| `grok-imagine` | Grok Imagine (api.airforce) |
| `klein` | FLUX.2 Klein 4B |
| `klein-large` | FLUX.2 Klein 9B |
| `gptimage` | GPT Image 1 Mini |

---

## 📁 Project Structure

```
Auto-art-gallery/
├── .github/
│   └── workflows/
│       ├── generate.yml    # Scheduled + manual artwork generation
│       ├── reader.yml      # Scheduled + manual book reader generation
│       └── deploy.yml      # Auto-deploys to GitHub Pages on push to main
├── images/                 # Generated artwork images (auto-populated)
├── book/                   # Book reader files (see Book section below)
├── index.html              # Gallery web page (GitHub Pages)
├── gallery.json            # Artwork metadata (auto-updated)
├── generate_artwork.py     # Core artwork generation script
├── generate_reader.py      # Book reader generation script
└── README.md               # This file
```

---

## 🎨 Customisation

### Add more topics
Edit the `TOPICS` list in `generate_artwork.py`:
```python
TOPICS = [
    "your custom topic here",
    ...
]
```

### Change the generation schedule
Edit `.github/workflows/generate.yml` and add or remove cron entries:
```yaml
schedule:
  - cron: '0 20 * * *'   # 4:00 AM HKT — add or remove lines to taste
```
Use [crontab.guru](https://crontab.guru) to build a cron expression.

### Change image dimensions
In `generate_artwork.py`, find the `generate_image` function and update:
```python
f"?model={model}&width=1024&height=1024&seed={seed}&nologo=true"
#                 ^^^^^^^^^^   ^^^^^^^^^^^
```

---

## 🔑 Environment Variables Reference

| Variable | Where to set | Description |
|---|---|---|
| `POLLINATIONS_API_KEY` | GitHub → Settings → Secrets and variables → Actions → Repository secrets | Your Pollinations AI secret key |

> **Only repository secrets are used.** No `.env` files are needed — everything runs inside GitHub Actions.

---

---

# 📖 Book Reader

> An AI-illustrated reading experience that publishes a new passage from a Chinese literary memoir on a daily schedule, each paired with an AI-generated illustration.

[![Book Reader Generator](https://github.com/kychugo/Auto-art-gallery/actions/workflows/reader.yml/badge.svg)](https://github.com/kychugo/Auto-art-gallery/actions/workflows/reader.yml)

The Book Reader is available at:
```
https://<your-github-username>.github.io/Auto-art-gallery/book/reader.html
```

The interface is in **Traditional Chinese (繁體中文)**.

---

## ✨ Book Reader Features

| Feature | Detail |
|---|---|
| ⏰ Auto-generation | New illustrated passage **every 5 minutes**, all day |
| 📚 Sequential reading | Passages are extracted in order from `book/source.txt` |
| 🎨 AI illustrations | Each passage is paired with a matching AI-generated image |
| 📊 Progress tracking | Reading progress bar shows how far through the book you are |
| 🌙 Dark / light mode | Theme toggle stored in browser preferences |
| 🔁 Manual trigger | Run generation on-demand from the Actions tab |

---

## 🔄 How It Works

```
Every 5 minutes (or on-demand)
        │
        ▼
┌───────────────────────────────┐
│   Book Reader Generator CI    │
│                               │
│  1. Read next ~60-char        │
│     segment from source.txt   │
│  2. Convert Simplified →      │
│     Traditional Chinese       │
│  3. Generate English image    │
│     prompt via text model     │
│  4. Generate illustration     │
│     via image model           │
│  5. Save image to             │
│     book/reader_images/       │
│  6. Append to                 │
│     reader_entries.json       │
│  7. Update reader_progress    │
│  8. Commit & push → main      │
└───────────┬───────────────────┘
            │ push to main triggers
            ▼
┌───────────────────────────────┐
│   Deploy to Pages CI          │
│                               │
│  Deploys entire repo to       │
│  GitHub Pages                 │
└───────────────────────────────┘
```

---

## 📁 Book Structure

```
book/
├── source.txt              # Full book text in Simplified Chinese (UTF-8)
├── reader.html             # Reader web page (Traditional Chinese UI)
├── reader_entries.json     # All generated passages + image metadata (Traditional Chinese)
├── reader_progress.json    # Current reading offset
└── reader_images/          # AI-generated illustrations (auto-populated)
```

---

## ⚙️ Customisation

### Change the book source
Replace `book/source.txt` with any UTF-8 text file and reset the progress:
```bash
echo '{"offset": 0, "completed": false}' > book/reader_progress.json
echo '{"entries": [], "book_total_chars": 0, "completed": false}' > book/reader_entries.json
```

### Change the generation schedule
Edit `.github/workflows/reader.yml`:
```yaml
schedule:
  - cron: '*/5 * * * *'   # currently every 5 minutes — adjust to taste
```

### Change passage length
In `generate_reader.py`, adjust the `TARGET_CHARS` constant:
```python
TARGET_CHARS = 60   # target number of Chinese characters per passage
```

---

## 📄 License

MIT — do whatever you like with it.

