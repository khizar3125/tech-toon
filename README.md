# 🎬 Tech Toon — "Free iPhone Ka Chakkar 🤣"

A **fully code-driven, rigged 2D cartoon** comedy short for YouTube — not a slideshow.
Every frame is generated in Python with a character rig:

- 👄 **Jaw-morph lip-sync** — the mouth opens/closes with the actual voice amplitude
- 😉 **Blinking** eyes on randomized timing
- 🙆 **6 full-body pose swaps** + idle bob/sway for gestures
- 🏞️ **Parallax backgrounds** with slow zoom/pan
- 💥 **Meme sticker pops** (WOW / LOL / BOOM / HAHA) with overshoot + shake
- 🎥 **Camera FX** — zoom punch, shake, flash
- 💬 Hinglish speech bubble + "Wait for End" pill
- 🎙️ **3 distinct AI voices** (Khizar / Mom / Robot-scammer) with comic timing

Rendered at **1080×1920, 24 fps** — fully editable from source.

## ▶️ Watch / Download

Download the finished MP4 from the **[GitHub Release →](../../releases)** (asset: `tech_cartoon_final.mp4`).

## ✏️ How to edit (anyone can)

Everything that matters is in **`story.json`** — no Python needed to change the content:

| Field | What it does |
|-------|--------------|
| `text` | Dialogue line (Hinglish) |
| `voice` | `hi-IN-MadhurNeural` (Khizar), `hi-IN-SwaraNeural` (Mom) — run `edge-tts --list-voices` for more |
| `rate` / `pitch` | Comic voice tweaks, e.g. `+15%` / `+40Hz` |
| `face` | Expression head: `face2_happy`, `face2_sad`, `face2_angry`, `face2_shock`, `face2_think`, `face_laugh` … |
| `body` | Full-body pose: `body_1` … `body_6` |
| `bg` | `living`, `street`, `garden`, `school` |
| `meme` | `wow`, `lol`, `boom`, `haha`, or `null` |
| `fx` | `pop`, `zoom`, `flash`, `shake`, `punch` |

### Regenerate locally
```bash
pip install edge-tts pillow numpy
# 1) voices + timing
python scripts/voice.py
python scripts/amplitude.py
# 2) render frames + encode
python scripts/render.py
# 3) audio + mux
python scripts/mix_audio.py
ffmpeg -i output/tech_cartoon.mp4 -i output/voice.wav \
  -c:v copy -c:a aac -shortest output/tech_cartoon_final.mp4
```

### Regenerate with one click
Push a change to `story.json` (or manually run the **"Render Tech Cartoon & Release"** GitHub Action).
CI re-renders the MP4, muxes audio, and uploads it to the Release automatically.

## 📁 Project layout
```
story.json              # ← EDIT THIS (script, voices, expressions, FX)
scripts/
  voice.py              # edge-tts voice synthesis + durations
  amplitude.py          # per-frame loudness for lip-sync
  animate.py            # rig: jaw morph, blink, bob, parallax, memes, FX
  render.py             # frame loop + H.264 encode
  mix_audio.py          # frame-aligned audio track
  extract_sprites.py    # re-cut sprites from source sheets (rembg)
assets/
  source/               # original 7 cartoon asset sheets
  sprites/              # transparent character/face/bg/meme PNGs
  audio/                # generated per-line voice lines
.github/workflows/      # GitHub Actions auto-render + release
```

Built from the shared cartoon family asset pack. All audio is synthetic (edge-tts), all visuals are programmatic compositions over the provided sprites.
