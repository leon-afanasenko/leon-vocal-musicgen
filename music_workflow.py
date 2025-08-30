import os
import time
import threading
from pathlib import Path
from audiocraft.models import MusicGen
from TTS.api import TTS
from pydub import AudioSegment
import numpy as np
from audio_utils import audio_write
from helpers import log, create_safe_filename, OUTPUT_DIR

# Загружаем модели сразу при импорте
log("🔄 Loading MusicGen model...")
musicgen = MusicGen.get_pretrained("facebook/musicgen-small")
log("✅ MusicGen loaded!")

log("🔄 Loading XTTS model...")
tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False)
log("✅ XTTS loaded!")

def generate_music_workflow(prompt, duration, track_name, progress_fn=None):
    start = time.time()
    try:
        # Этап 1: Настройка параметров
        if progress_fn:
            progress_fn(0.1, "⚙️ Настройка параметров генерации...")
        
        musicgen.set_generation_params(duration=int(duration))
        time.sleep(0.3)
        
        # Этап 2: Генерация музыки
        if progress_fn:
            progress_fn(0.15, f"🎵 Генерация музыки ({duration}с)... Это займет ~{duration*1.5:.0f} секунд")
        
        # Симуляция прогресса
        estimated_time = max(duration * 1.5, 15)
        start_gen = time.time()
        
        # Запускаем генерацию в отдельном потоке
        result_container = [None]
        def generate():
            result_container[0] = musicgen.generate([prompt])
        
        gen_thread = threading.Thread(target=generate)
        gen_thread.start()
        
        # Симулируем прогресс
        while gen_thread.is_alive():
            elapsed = time.time() - start_gen
            progress = min(0.15 + (elapsed / estimated_time) * 0.75, 0.9)
            remaining = max(0, estimated_time - elapsed)
            if progress_fn:
                progress_fn(progress, f"🎵 Генерация музыки... {progress*100:.0f}% (осталось ~{remaining:.0f}с)")
            time.sleep(0.5)
        
        gen_thread.join()
        wavs = result_container[0]
        
        # Этап 3: Сохранение
        if progress_fn:
            progress_fn(0.95, "💾 Сохранение аудио файла...")
        
        safe_name = create_safe_filename(track_name)
        wav_path = OUTPUT_DIR / f"{safe_name}.wav"
        audio_write(str(wav_path), wavs[0].cpu(), musicgen.sample_rate)
        
        if progress_fn:
            progress_fn(1.0, f"✅ Готово! Трек создан за {time.time()-start:.1f}с")
        
        elapsed = time.time() - start
        log(f"[MusicGen] Track '{track_name}' created in {elapsed:.1f} sec.")
        return str(wav_path)
        
    except Exception as e:
        log(f"[MusicGen] Error: {e}")
        if progress_fn:
            progress_fn(0, f"❌ Ошибка: {str(e)}")
        raise Exception(f"Critical error: {e}")

def generate_song_with_voice(lyrics, genre, duration, voice_sample_path, progress_fn=None):
    if not voice_sample_path or not os.path.isfile(voice_sample_path):
        raise Exception("Please select a voice file for generation (record or upload)!")
    
    t0 = time.time()
    try:
        # Этап 1: Генерация вокала
        if progress_fn: 
            progress_fn(0.1, f"🎤 Синтез голоса (~{len(lyrics)*0.3:.0f}с)...")
        
        vocal_path = OUTPUT_DIR / "vocal.wav"
        
        # TTS в отдельном потоке
        tts_start = time.time()
        estimated_tts_time = len(lyrics) * 0.3
        
        result_container = [None]
        def generate_tts():
            tts.tts_to_file(
                text=lyrics,
                speaker_wav=voice_sample_path,
                language="en",
                file_path=str(vocal_path),
            )
            result_container[0] = True
        
        tts_thread = threading.Thread(target=generate_tts)
        tts_thread.start()
        
        while tts_thread.is_alive():
            elapsed = time.time() - tts_start
            progress = min(0.1 + (elapsed / estimated_tts_time) * 0.3, 0.4)
            remaining = max(0, estimated_tts_time - elapsed)
            if progress_fn:
                progress_fn(progress, f"🎤 Синтез голоса... {progress*100:.0f}% (осталось ~{remaining:.0f}с)")
            time.sleep(0.3)
        
        tts_thread.join()
        
        # Этап 2: Генерация музыки
        if progress_fn: 
            progress_fn(0.45, f"🎵 Генерация {genre} инструментала ({duration}с)...")
        
        musicgen.set_generation_params(duration=int(duration))
        prompt = f"{genre} instrumental"
        
        music_start = time.time()
        estimated_music_time = duration * 1.2
        
        music_container = [None]
        def generate_music():
            music_container[0] = musicgen.generate([prompt])
        
        music_thread = threading.Thread(target=generate_music)
        music_thread.start()
        
        while music_thread.is_alive():
            elapsed = time.time() - music_start
            progress = min(0.45 + (elapsed / estimated_music_time) * 0.35, 0.8)
            remaining = max(0, estimated_music_time - elapsed)
            if progress_fn:
                progress_fn(progress, f"🎵 Создание инструментала... {progress*100:.0f}% (осталось ~{remaining:.0f}с)")
            time.sleep(0.5)
        
        music_thread.join()
        music = music_container[0]
        
        # Этап 3: Сохранение музыки
        if progress_fn: 
            progress_fn(0.85, "💾 Сохранение инструментала...")
        
        music_path = OUTPUT_DIR / "music.wav"
        audio_np = music[0].cpu().numpy()
        if audio_np.ndim > 1: 
            audio_np = audio_np[0]
        audio_int16 = (audio_np * 32767).astype(np.int16)
        AudioSegment(
            audio_int16.tobytes(),
            frame_rate=musicgen.sample_rate,
            sample_width=2,
            channels=1
        ).export(music_path, format="wav")
        
        # Этап 4: Сведение треков
        if progress_fn: 
            progress_fn(0.9, "🎚️ Сведение вокала и инструментала...")
        
        vocal = AudioSegment.from_wav(vocal_path)
        instrumental = AudioSegment.from_wav(music_path)
        min_len = min(len(vocal), len(instrumental))
        out = instrumental[:min_len].overlay(vocal[:min_len])
        
        out_path = OUTPUT_DIR / "final_song.wav"
        out.export(out_path, format="wav")
        
        if progress_fn: 
            progress_fn(1.0, f"✅ Песня готова за {time.time()-t0:.1f}с!")
        
        elapsed = time.time() - t0
        log(f"[TTS+MusicGen] Song ready in {elapsed:.1f} sec.")
        return str(out_path)
        
    except Exception as e:
        log(f"[TTS+MusicGen] Error: {e}")
        if progress_fn:
            progress_fn(0, f"❌ Ошибка: {str(e)}")
        raise Exception(f"Song generation error: {e}")

def generate_tts_voice(lyrics, voice_path, progress_fn=None):
    if not voice_path or not os.path.isfile(voice_path):
        raise Exception("Please record or upload a voice file first!")
    
    t0 = time.time()
    try:
        if progress_fn:
            progress_fn(0.1, f"🎤 Подготовка синтеза голоса (~{len(lyrics)*0.2:.0f}с)...")
        
        out_path = OUTPUT_DIR / "tts_voice.wav"
        
        # TTS с прогрессом
        tts_start = time.time()
        estimated_time = len(lyrics) * 0.2
        
        result_container = [None]
        def generate_tts():
            tts.tts_to_file(
                text=lyrics,
                speaker_wav=voice_path,
                language="en",
                file_path=str(out_path),
            )
            result_container[0] = True
        
        tts_thread = threading.Thread(target=generate_tts)
        tts_thread.start()
        
        while tts_thread.is_alive():
            elapsed = time.time() - tts_start
            progress = min(0.1 + (elapsed / estimated_time) * 0.8, 0.9)
            remaining = max(0, estimated_time - elapsed)
            if progress_fn:
                progress_fn(progress, f"🎤 Синтез голоса... {progress*100:.0f}% (осталось ~{remaining:.0f}с)")
            time.sleep(0.3)
        
        tts_thread.join()
        
        if progress_fn:
            progress_fn(1.0, f"✅ Голос синтезирован за {time.time()-t0:.1f}с!")
        
        log(f"[TTS] Voice generated in {time.time()-t0:.1f} sec.")
        return str(out_path)
        
    except Exception as e:
        log(f"[TTS] Error: {e}")
        if progress_fn:
            progress_fn(0, f"❌ Ошибка: {str(e)}")
        raise Exception(f"TTS error: {e}")