# Leon's Vibe Creator

AI-powered studio for music and vocal generation, using MusicGen and XTTS v2, with a user-friendly web interface.

---

## Features

- **Music Track Generation** by text prompt (MusicGen)
- **Vocal Synthesis** with XTTS v2 (using your own voice sample)
- **Mixing** vocals with instrumentals
- **Audio Enhancement/Normalization** (FFmpeg)
- **Record or Upload Your Voice** directly in the web UI
- **Friendly prompts** and real-time status messages

---

## Project Structure

```
leon-vibe/
├── main.py
├── helpers.py
├── audio_utils.py
├── music_workflow.py
├── ffmpeg_utils.py
├── README.md
├── Leon_vibe/         # Generated tracks
└── Leon_voice/        # Saved voice samples
```

---

## Quick Start

1. **Install dependencies**:

   ```
   pip install gradio pydub torch colorama tts audiocraft
   ```

2. **Run the app**:

   ```
   python main.py
   ```

3. **Open in browser**:  
   [http://127.0.0.1:7860](http://127.0.0.1:7860)

---

## Usage Tips & Feedback

- After recording or uploading a voice sample, you'll see a status ("Voice file loaded!").
- When saved, you'll see confirmation ("Voice saved: ...").
- You can use your microphone or upload a .wav file from your computer.
- All errors are displayed as popup messages in the interface.

---

## File Overview

- **helpers.py** — File handling, logging, status updates
- **audio_utils.py** — Saving numpy/tensor audio as .wav
- **music_workflow.py** — Music, vocal, and mix generation logic
- **main.py** — Gradio web UI (easy to extend with new tabs)
- **ffmpeg_utils.py** — Audio enhancement with ffmpeg (customize as needed)

---

## Important Notes

- You need a modern browser for microphone recording to work.
- If something isn't working, check the Python console for logs.
- To support other languages, change the `"language"` parameter in `music_workflow.py`.

---

**Have fun and make awesome music!**
