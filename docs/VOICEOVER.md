# Narrated demonstration

The user selected **Liam**, American English (`am_liam`). The narration and captions do not mention the voice-generation tool, as requested. No background music or third-party media was added.

## Delivered files

- `demo/assets/video/final_demo.mp4`: final 1920×1080 H.264 video, 48 kHz AAC speech, burned captions in a dedicated bottom band, and a selectable English subtitle track.
- `demo/assets/audio/kokoro_voiceover.wav`: full-length aligned narration, 48 kHz mono PCM.
- `demo/assets/audio/subtitles.srt`: 29 time-aligned English cues derived from the model's word durations.
- `demo/assets/audio/subtitles.ass`: caption layout for the dedicated band; the original app recording is scaled to fit above it so controls are not obscured.
- `demo/assets/audio/narration_script.md` and `narration_timeline.json`: spoken script and scene placement.
- `demo/assets/audio/voiceover-evidence.json`: actual model, voice, hashes, versions, and per-scene timing.
- `demo/assets/audio/final-verification.json`: measured final-file checks.

Absolute final video path: `G:\Hacktoberfest-2026-Week3\03-AccessPath\demo\assets\video\final_demo.mp4`.

## Verified result

The final audio and video tracks both last **114.92 seconds**. The complete MP4 decoded successfully. All caption words match the spoken script, with no overlapping cues or punctuation-only cues. Final audio measured **-16.16 LUFS** integrated and **-1.43 dBTP** true peak; the PCM narration contains zero clipped samples. Representative frames were inspected for readable captions and unobstructed controls.

The speech is genuine local Kokoro-82M inference, package version 0.9.4, with the actual `am_liam.pt` voice from pinned model revision `f3ff3571791e39611d31c381e3a41a3af07b4987`. This technical record preserves reproducibility; the engine is not named in the spoken narration or video captions. A phoneme override corrects the model name Qwen while leaving the displayed word unchanged.

The runtime is separate from the application at `.tools/kokoro`. It uses CPU-only PyTorch with two threads and a project-local model/cache/temp folder. The shared Ollama service, app ports, and other projects are not restarted or reconfigured. Source weights and runtime files are ignored by Git.

## Reproduce

Create a separate Python 3.12 environment, install CPU PyTorch from its official index, and install the voice dependency lock:

```powershell
python -m venv .tools\kokoro
$env:UV_CACHE_DIR=Join-Path (Get-Location) '.tools\uv-cache'
uv pip install --python .tools\kokoro\Scripts\python.exe --index-url https://download.pytorch.org/whl/cpu torch==2.8.0
uv pip install --python .tools\kokoro\Scripts\python.exe -r demo\requirements-voice.lock.txt
.\.tools\kokoro\Scripts\python.exe demo\narrate_demo.py --voice am_liam
.\.venv\Scripts\python.exe demo\verify_voiceover.py
```

FFmpeg/FFprobe must be on PATH. The renderer downloads the pinned official model/voice when absent, caches raw scene audio locally, normalizes loudness, places each clip within its scene window, writes SRT/ASS, exports the MP4, and fully decodes it. It rejects a voice that differs from the recorded user selection. Updating the final voice requires a new explicit user selection and timeline update.

No YouTube upload or external publication was performed.
