import os
import sys
import time
from pathlib import Path
import gradio as gr
from pydub import AudioSegment
import numpy as np
import torch
from colorama import init, Fore, Style
from audiocraft.models import MusicGen
from TTS.api import TTS
from ffmpeg_utils import print_audio_comparison, process_existing_audio

# --- INIT ---
init(autoreset=True)
os.environ["COQUI_TOS_AGREED"] = "1"

def log(msg, color=Fore.RESET, end="\n"):
    print(color + msg + Style.RESET_ALL, end=end)

log("Starting Leon's Vibe Creator (Suno Style)", Fore.LIGHTYELLOW_EX)
OUTPUT_DIR = Path("Leon_vibe")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
VOICE_DIR = Path("Leon_voice")
VOICE_DIR.mkdir(parents=True, exist_ok=True)

start_time = time.time()
try:
    log("Loading MusicGen...", Fore.LIGHTBLUE_EX)
    musicgen = MusicGen.get_pretrained("facebook/musicgen-small")
    log("MusicGen ready.", Fore.GREEN)
except Exception as e:
    log(f"MusicGen ERROR: {e}", Fore.RED)
    sys.exit(1)

try:
    log("Loading TTS XTTS v2...", Fore.LIGHTBLUE_EX)
    tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False)
    log("XTTS v2 ready.", Fore.GREEN)
except Exception as e:
    log(f"TTS ERROR: {e}", Fore.RED)
    sys.exit(1)

total_load = time.time() - start_time
log(f"All models loaded in {total_load:.1f} sec. Go!", Fore.LIGHTYELLOW_EX)

# --- HELPERS ---
def create_safe_filename(name: str) -> str:
    safe = "".join(c for c in name if c.isalnum() or c in "_- ").rstrip()
    return safe or "track"

def audio_write(path: str, audio_tensor: torch.Tensor, sample_rate: int):
    audio_np = audio_tensor.cpu().numpy()
    if audio_np.ndim > 1: audio_np = audio_np[0]
    audio_int16 = (audio_np * 32767).astype(np.int16)
    AudioSegment(audio_int16.tobytes(), frame_rate=sample_rate, sample_width=2, channels=1).export(path, format="wav")

def list_audio_files():
    files = list(OUTPUT_DIR.glob("*.wav")) + list(OUTPUT_DIR.glob("*.mp3"))
    files.sort(key=os.path.getmtime, reverse=True)
    return [str(p.resolve()) for p in files]

def list_voice_files():
    files = list(VOICE_DIR.glob("*.wav"))
    return [str(f) for f in files]

def delete_file(path_str: str):
    try:
        if path_str and Path(path_str).exists():
            Path(path_str).unlink()
        updated_choices = gr.update(choices=list_audio_files())
        return updated_choices, updated_choices
    except Exception as e:
        log(f"Error deleting file: {e}", Fore.RED)
        return gr.update(choices=list_audio_files()), gr.update(choices=list_audio_files())

def save_uploaded_voice(voice_file):
    if not voice_file:
        raise gr.Error("Please record or upload a .wav file first!")
    if isinstance(voice_file, tuple):  # Gradio >=4 compatibility
        voice_file = voice_file[0]
    if not os.path.isfile(voice_file):
        raise gr.Error("File not found or not uploaded.")
    fname = VOICE_DIR / Path(voice_file).name
    try:
        os.rename(voice_file, fname)
    except Exception as e:
        log(f"Error saving voice: {e}", Fore.RED)
        raise gr.Error(f"Error saving: {e}")
    log(f"New voice uploaded: {fname.name}", Fore.GREEN)
    return str(fname)

def generate_music_workflow(prompt, duration, track_name, process_audio, progress=gr.Progress(track_tqdm=True)):
    start = time.time()
    try:
        musicgen.set_generation_params(duration=int(duration))
        for _ in progress.tqdm(range(30), desc="Generating music..."):
            time.sleep(max(0.1, duration / 60))
        wavs = musicgen.generate([prompt])
        progress(0.9, desc="Saving and processing...")
        safe_name = create_safe_filename(track_name)
        wav_path = OUTPUT_DIR / f"{safe_name}.wav"
        audio_write(str(wav_path), wavs[0].cpu(), musicgen.sample_rate)
        if process_audio:
            processed_path, _ = process_existing_audio(str(wav_path))
            result = processed_path or str(wav_path)
        else:
            result = str(wav_path)
        elapsed = time.time() - start
        log(f"[MusicGen] Track '{track_name}' created in {elapsed:.1f} sec.", Fore.LIGHTBLUE_EX)
        return result
    except Exception as e:
        log(f"[MusicGen] Error: {e}", Fore.RED)
        raise gr.Error(f"Critical error: {e}")

def generate_song_with_voice(lyrics, genre, duration, voice_sample_path, progress=gr.Progress(track_tqdm=True)):
    if not voice_sample_path or not os.path.isfile(voice_sample_path):
        raise gr.Error("Please select a voice file for generation (record or upload)!")
    t0 = time.time()
    try:
        progress(0.05, desc="Generating vocals...")
        vocal_path = OUTPUT_DIR / "vocal.wav"
        tts.tts_to_file(
            text=lyrics,
            speaker_wav=voice_sample_path,
            language="en",  # Можно заменить на "ru"
            file_path=str(vocal_path),
        )
        progress(0.5, desc="Generating music...")
        musicgen.set_generation_params(duration=int(duration))
        prompt = f"{genre} instrumental"
        music = musicgen.generate([prompt])
        music_path = OUTPUT_DIR / "music.wav"
        audio_np = music[0].cpu().numpy()
        if audio_np.ndim > 1: audio_np = audio_np[0]
        audio_int16 = (audio_np * 32767).astype(np.int16)
        AudioSegment(
            audio_int16.tobytes(),
            frame_rate=musicgen.sample_rate,
            sample_width=2,
            channels=1
        ).export(music_path, format="wav")
        progress(0.8, desc="Mixing...")
        vocal = AudioSegment.from_wav(vocal_path)
        instrumental = AudioSegment.from_wav(music_path)
        min_len = min(len(vocal), len(instrumental))
        out = instrumental[:min_len].overlay(vocal[:min_len])
        out_path = OUTPUT_DIR / "final_song.wav"
        out.export(out_path, format="wav")
        elapsed = time.time() - t0
        log(f"[TTS+MusicGen] Song ready in {elapsed:.1f} sec.", Fore.LIGHTBLUE_EX)
        return str(out_path)
    except Exception as e:
        log(f"[TTS+MusicGen] Error: {e}", Fore.RED)
        raise gr.Error(f"Song generation error: {e}")

def generate_tts_voice(lyrics, voice_path):
    if not voice_path or not os.path.isfile(voice_path):
        raise gr.Error("Please record or upload a voice file first!")
    t0 = time.time()
    try:
        out_path = OUTPUT_DIR / "tts_voice.wav"
        tts.tts_to_file(
            text=lyrics,
            speaker_wav=voice_path,
            language="en",  # Можно заменить на "ru"
            file_path=str(out_path),
        )
        log(f"[TTS] Voice generated in {time.time()-t0:.1f} sec.", Fore.LIGHTBLUE_EX)
        return str(out_path)
    except Exception as e:
        log(f"[TTS] Error: {e}", Fore.RED)
        raise gr.Error(f"TTS error: {e}")

# --- UI ---
with gr.Blocks(theme=gr.themes.Monochrome()) as demo:
    gr.Markdown("""
<h1 style='font-family:sans-serif; letter-spacing:2px; color:#222; text-align:center;'>
  <span style="color:#f15a24;">L</span><span style="color:#ff6600;">e</span><span style="color:#ffb347;">o</span><span style="color:#ffcc00;">n</span>
  <span style="color:#f15a24;"> </span>
  <span style="color:#ff6600;">V</span><span style="color:#ffb347;">i</span><span style="color:#ffcc00;">b</span><span style="color:#f15a24;">e</span>
  <span style="color:#222;"> Creator </span>
  <span style="color:#f15a24;">b</span><span style="color:#ff6600;">y</span>
  <span style="color:#ffcc00;"> S</span><span style="color:#ffb347;">u</span><span style="color:#ff6600;">n</span><span style="color:#f15a24;">o</span>
  <span style="color:#ffcc00;">-</span>
  <span style="color:#f15a24;">s</span><span style="color:#ff6600;">t</span><span style="color:#ffb347;">y</span><span style="color:#ffcc00;">l</span><span style="color:#f15a24;">e</span>
</h1>
""")
    with gr.Tab("Create / Enhance Track"):
        gr.Markdown("### Step 1: Create new track")
        with gr.Row():
            prompt_input = gr.Textbox(label="Prompt (e.g.: happy jazz, lofi, etc.)", lines=2, value="lofi relaxing piano")
            with gr.Column():
                track_name_input = gr.Textbox(label="Track name", value="Leon_music")
                duration_input = gr.Slider(minimum=5, maximum=60, value=20, step=1, label="Duration (sec)")
        process_checkbox = gr.Checkbox(label="Enhance audio (ffmpeg)", value=True)
        generate_button = gr.Button("Generate", variant="primary")
        generated_audio_output = gr.Audio(label="Result", type="filepath")

        gr.Markdown("--- \n### Enhance existing track")
        files_list_process = gr.Dropdown(label="Select file", choices=list_audio_files(), interactive=True)
        process_button = gr.Button("Enhance selected")
        processed_audio_output = gr.Audio(label="Enhanced result", type="filepath")
        status_text = gr.Textbox(label="Status", interactive=False)

    with gr.Tab("File Manager"):
        files_list_manage = gr.Dropdown(label="Files list", choices=list_audio_files(), interactive=True)
        with gr.Row():
            play_button = gr.Button("Play")
            delete_button = gr.Button("Delete")
        audio_player = gr.Audio(label="Player", type="filepath")

    with gr.Tab("Sing like Leon!"):
        gr.Markdown("#### 1. Record or upload your voice (.wav, ~10 sec, no music):")
        with gr.Row():
            voice_input = gr.Audio(label="Your voice (record or upload)", type="filepath", source="microphone")
            save_voice_btn = gr.Button("Save voice")
        saved_voice_path = gr.Textbox(label="Saved voice path (hidden)", visible=False)

        gr.Markdown("#### 2. Enter lyrics and generate TTS voice (without music):")
        lyrics_input = gr.Textbox(label="Lyrics/text for TTS")
        generate_tts_btn = gr.Button("Generate TTS Voice")
        tts_result_audio = gr.Audio(label="Synthesized voice", type="filepath")

        # Save voice file (recorded or uploaded) to VOICE_DIR
        save_voice_btn.click(save_uploaded_voice, inputs=voice_input, outputs=saved_voice_path)

        # Generate TTS output (not mixed with music)
        generate_tts_btn.click(
            generate_tts_voice,
            inputs=[lyrics_input, saved_voice_path],
            outputs=tts_result_audio
        )

    with gr.Tab("Sing + Instrumental"):
        gr.Markdown("#### 1. Select voice, enter lyrics, genre and duration to generate full song:")
        voice_files_dropdown = gr.Dropdown(label="Select voice", choices=list_voice_files())
        lyrics_song_input = gr.Textbox(label="Lyrics")
        genre_input = gr.Dropdown(["pop", "rock", "rap", "jazz", "lofi", "electronic"], label="Genre", value="pop")
        duration_input2 = gr.Slider(minimum=10, maximum=60, value=30, step=1, label="Duration (sec)")
        generate_song_btn = gr.Button("Generate Song")
        song_output = gr.Audio(label="Your song", type="filepath")

        generate_song_btn.click(
            generate_song_with_voice,
            inputs=[lyrics_song_input, genre_input, duration_input2, voice_files_dropdown],
            outputs=song_output,
        )

    def on_generate_and_update(prompt, duration, track_name, process_audio):
        result = generate_music_workflow(prompt, duration, track_name, process_audio)
        files = list_audio_files()
        return result, gr.update(choices=files), gr.update(choices=files)

    def on_process_and_update(filepath):
        path, status = process_existing_audio(filepath)
        files = list_audio_files()
        return path, status, gr.update(choices=files), gr.update(choices=files)

    generate_button.click(
        on_generate_and_update,
        inputs=[prompt_input, duration_input, track_name_input, process_checkbox],
        outputs=[generated_audio_output, files_list_process, files_list_manage]
    )
    process_button.click(
        on_process_and_update,
        inputs=[files_list_process],
        outputs=[processed_audio_output, status_text, files_list_process, files_list_manage]
    )
    play_button.click(lambda p: p, inputs=[files_list_manage], outputs=[audio_player])
    delete_button.click(delete_file, inputs=[files_list_manage], outputs=[files_list_process, files_list_manage])

if __name__ == "__main__":
    log("===> Interface loaded! Open in browser: http://127.0.0.1:7860", Fore.LIGHTGREEN_EX)
    demo.queue()
    demo.launch()