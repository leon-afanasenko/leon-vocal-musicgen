import os
import time
from pathlib import Path
from audiocraft.models import MusicGen
from TTS.api import TTS
from pydub import AudioSegment
from audio_utils import audio_write
from helpers import log, create_safe_filename, OUTPUT_DIR
from ffmpeg_utils import process_existing_audio

musicgen = MusicGen.get_pretrained("facebook/musicgen-small")
tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False)

def generate_music_workflow(prompt, duration, track_name, process_audio, progress=None):
    start = time.time()
    try:
        musicgen.set_generation_params(duration=int(duration))
        if progress:
            for _ in progress.tqdm(range(30), desc="Generating music..."):
                time.sleep(max(0.1, duration / 60))
        wavs = musicgen.generate([prompt])
        if progress:
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
        log(f"[MusicGen] Track '{track_name}' created in {elapsed:.1f} sec.")
        return result
    except Exception as e:
        log(f"[MusicGen] Error: {e}")
        raise Exception(f"Critical error: {e}")

def generate_song_with_voice(lyrics, genre, duration, voice_sample_path, progress=None):
    if not voice_sample_path or not os.path.isfile(voice_sample_path):
        raise Exception("Please select a voice file for generation (record or upload)!")
    t0 = time.time()
    try:
        if progress: progress(0.05, desc="Generating vocals...")
        vocal_path = OUTPUT_DIR / "vocal.wav"
        tts.tts_to_file(
            text=lyrics,
            speaker_wav=voice_sample_path,
            language="en",  # Можно заменить на "ru"
            file_path=str(vocal_path),
        )
        if progress: progress(0.5, desc="Generating music...")
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
        if progress: progress(0.8, desc="Mixing...")
        vocal = AudioSegment.from_wav(vocal_path)
        instrumental = AudioSegment.from_wav(music_path)
        min_len = min(len(vocal), len(instrumental))
        out = instrumental[:min_len].overlay(vocal[:min_len])
        out_path = OUTPUT_DIR / "final_song.wav"
        out.export(out_path, format="wav")
        elapsed = time.time() - t0
        log(f"[TTS+MusicGen] Song ready in {elapsed:.1f} sec.")
        return str(out_path)
    except Exception as e:
        log(f"[TTS+MusicGen] Error: {e}")
        raise Exception(f"Song generation error: {e}")

def generate_tts_voice(lyrics, voice_path):
    if not voice_path or not os.path.isfile(voice_path):
        raise Exception("Please record or upload a voice file first!")
    t0 = time.time()
    try:
        out_path = OUTPUT_DIR / "tts_voice.wav"
        tts.tts_to_file(
            text=lyrics,
            speaker_wav=voice_path,
            language="en",  # Можно заменить на "ru"
            file_path=str(out_path),
        )
        log(f"[TTS] Voice generated in {time.time()-t0:.1f} sec.")
        return str(out_path)
    except Exception as e:
        log(f"[TTS] Error: {e}")
        raise Exception(f"TTS error: {e}")