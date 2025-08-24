import os
from pathlib import Path
from colorama import Fore, Style
import shutil
import uuid

OUTPUT_DIR = Path("Leon_vibe")
VOICE_DIR = Path("Leon_voice")

def log(msg, color=Fore.RESET, end="\n"):
    print(color + msg + Style.RESET_ALL, end=end)

def create_safe_filename(name: str) -> str:
    safe = "".join(c for c in name if c.isalnum() or c in "_- ").rstrip()
    return safe or "track"

def list_audio_files():
    files = list(OUTPUT_DIR.glob("*.wav")) + list(OUTPUT_DIR.glob("*.mp3"))
    files.sort(key=os.path.getmtime, reverse=True)
    return [str(p.resolve()) for p in files]

def list_voice_files():
    files = list(VOICE_DIR.glob("*.wav"))
    return [str(f.resolve()) for f in files]

def delete_file(path_str: str):
    import gradio as gr
    try:
        if path_str and Path(path_str).exists():
            Path(path_str).unlink()
        updated_choices = gr.update(choices=list_audio_files())
        return updated_choices, updated_choices
    except Exception as e:
        log(f"Error deleting file: {e}", Fore.RED)
        return gr.update(choices=list_audio_files()), gr.update(choices=list_audio_files())

def save_uploaded_voice(voice_file):
    import gradio as gr
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

def save_voice_to_voice_dir(src_path):
    """
    Сохраняет файл (upload или record) из временной папки в VOICE_DIR с уникальным именем.
    """
    if not src_path or not os.path.isfile(src_path):
        return None
    ext = os.path.splitext(src_path)[1]
    new_name = f"user_voice_{uuid.uuid4().hex[:8]}{ext}"
    dst_path = VOICE_DIR / new_name
    shutil.copy(src_path, dst_path)
    log(f"Voice saved as {dst_path.name} in VOICE_DIR", Fore.GREEN)
    return str(dst_path)