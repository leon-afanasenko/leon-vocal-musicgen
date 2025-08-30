import os
from pathlib import Path
from colorama import Fore, Style
import shutil
import uuid
import time

OUTPUT_DIR = Path("Leon_vibe")
VOICE_DIR = Path("Leon_voice")

# Создаем папки если их нет
OUTPUT_DIR.mkdir(exist_ok=True)
VOICE_DIR.mkdir(exist_ok=True)

def log(msg, color=Fore.RESET, end="\n"):
    print(color + msg + Style.RESET_ALL, end=end)

def create_safe_filename(name: str) -> str:
    safe = "".join(c for c in name if c.isalnum() or c in "_- ").rstrip()
    return safe or "track"

def get_filename_only(file_path: str) -> str:
    """Возвращает только имя файла без пути"""
    return Path(file_path).name

def list_audio_files():
    """Возвращает список полных путей к аудио файлам"""
    files = list(OUTPUT_DIR.glob("*.wav")) + list(OUTPUT_DIR.glob("*.mp3"))
    files.sort(key=os.path.getmtime, reverse=True)
    return [str(p.resolve()) for p in files]

def list_voice_files():
    """Возвращает список полных путей к голосовым файлам"""
    files = list(VOICE_DIR.glob("*.wav"))
    files.sort(key=os.path.getmtime, reverse=True)
    return [str(f.resolve()) for f in files]

def delete_file(path_str: str):
    """Удаляет файл по пути"""
    try:
        if path_str and Path(path_str).exists():
            Path(path_str).unlink()
            log(f"File deleted: {get_filename_only(path_str)}", Fore.YELLOW)
        return True
    except Exception as e:
        log(f"Error deleting file: {e}", Fore.RED)
        return False

def save_voice_to_voice_dir(src_path, custom_name=None):
    """
    Сохраняет голосовой файл в VOICE_DIR с пользовательским названием.
    
    Args:
        src_path: путь к исходному файлу
        custom_name: пользовательское название (без расширения)
    
    Returns:
        str: путь к сохраненному файлу
    """
    if not src_path or not os.path.isfile(src_path):
        raise Exception("Файл не найден")
    
    ext = os.path.splitext(src_path)[1]
    
    if custom_name:
        # Используем пользовательское название
        safe_name = create_safe_filename(custom_name)
        new_name = f"{safe_name}{ext}"
    else:
        # Используем случайное название
        new_name = f"user_voice_{uuid.uuid4().hex[:8]}{ext}"
    
    dst_path = VOICE_DIR / new_name
    
    # Проверяем, не существует ли уже файл с таким именем
    counter = 1
    original_dst_path = dst_path
    while dst_path.exists():
        name_part = original_dst_path.stem
        dst_path = VOICE_DIR / f"{name_part}_{counter}{ext}"
        counter += 1
    
    try:
        shutil.copy(src_path, dst_path)
        log(f"Voice saved as: {dst_path.name}", Fore.GREEN)
        return str(dst_path)
    except Exception as e:
        log(f"Error saving voice: {e}", Fore.RED)
        raise Exception(f"Ошибка сохранения: {e}")

# Оставляем старую функцию для совместимости
def save_uploaded_voice(voice_file):
    import gradio as gr
    if not voice_file:
        raise gr.Error("Please record or upload a .wav file first!")
    if isinstance(voice_file, tuple):
        voice_file = voice_file[0]
    if not os.path.isfile(voice_file):
        raise gr.Error("File not found or not uploaded.")
    
    return save_voice_to_voice_dir(voice_file)