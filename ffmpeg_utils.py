import subprocess
from colorama import Fore, Style
from pathlib import Path
import sys

FFPROBE_PATH = "ffprobe"

def get_audio_info(filename_str: str):
    filename = Path(filename_str)
    if not filename.exists():
        return None
    cmd = [
        FFPROBE_PATH, "-v", "error", "-select_streams", "a:0",
        "-show_entries", "stream=sample_rate,channels,bit_rate,codec_name",
        "-show_entries", "format=duration,size",
        "-of", "default=noprint_wrappers=1:nokey=1", str(filename)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    try:
        lines = result.stdout.strip().split('\n')
        return {
            "path": filename,
            "codec": lines[0],
            "sample_rate": int(lines[1]),
            "channels": int(lines[2]),
            "bit_rate": int(lines[3]) if lines[3].isdigit() else 0,
            "duration": float(lines[4]),
            "size": int(lines[5])
        }
    except Exception as e:
        print(Fore.RED + f"ffprobe data parse error: {e}")
        return None

def format_size(size_bytes):
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def print_audio_comparison(orig_info, proc_info, actions_applied):
    if not orig_info or not proc_info:
        print(Fore.YELLOW + "Unable to get audio info for comparison.")
        return
    print(Style.BRIGHT + Fore.CYAN + "\n" + "="*50)
    print(" " * 15 + "STUDIO REPORT")
    print("="*50)
    print(Fore.WHITE + "\nBEFORE PROCESSING (Original file):")
    print(f"  File:        {orig_info['path'].name}")
    print(f"  Format:      {orig_info['codec'].upper()}")
    print(f"  Size:        {format_size(orig_info['size'])}")
    print(f"  Bitrate:     {orig_info['bit_rate'] // 1000} kbps" if orig_info["bit_rate"] else "  Bitrate:     unknown")
    print(f"  Duration:    {orig_info['duration']:.2f} sec")
    print(Fore.GREEN + "\nAFTER PROCESSING (Enhanced file):")
    print(f"  File:        {proc_info['path'].name}")
    print(f"  Format:      {proc_info['codec'].upper()}")
    print(f"  Size:        {format_size(proc_info['size'])}")
    print(f"  Bitrate:     {proc_info['bit_rate'] // 1000} kbps" if proc_info["bit_rate"] else "  Bitrate:     unknown")
    print(f"  Duration:    {proc_info['duration']:.2f} sec")
    print(Fore.YELLOW + "\nApplied enhancements:")
    for action in actions_applied:
        print(f"  - {action}")
    print(Style.BRIGHT + Fore.CYAN + "="*50 + "\n")

def analyze_track_for_enhancement(info):
    """
    Decide which enhancements to apply based on audio properties.
    Returns:
        - filter_chain: str
        - actions: list of str
        - out_fmt: str (file extension, e.g. '.wav' or '.mp3')
    """
    actions = []
    filters = []
    # 1. Dynamic normalization if dynamic range is likely too wide (always safe for AI vocals)
    filters.append("dynaudnorm=f=200:g=15")
    actions.append("Dynamic normalization (dynaudnorm)")
    # 2. Increase volume only if not already close to 0 dBFS (very loud)
    # Empirically, AI tracks are often at -10 to -6 dBFS. If bit_rate high, skip gain.
    gain_db = 0
    # Heuristic: skip gain if bitrate >= 300000 or file is already loud
    if info:
        if info.get("bit_rate", 0) < 300000:
            gain_db = 6
            filters.append(f"volume={gain_db}dB")
            actions.append("Volume increased by +6 dB")
        else:
            actions.append("Volume unchanged (already loud)")
    # 3. Output as WAV for no loss, but allow mp3 if small size is preferred
    out_fmt = ".wav"
    actions.append("Exported as lossless WAV (pcm_s16le)")
    filter_chain = ",".join(filters)
    return filter_chain, actions, out_fmt

def process_existing_audio(input_path_str: str, progress=None):
    if not input_path_str:
        return None, "No file selected."
    input_path = Path(input_path_str)
    if not input_path.exists():
        return None, f"Error: File not found: {input_path.name}"

    # Gather original info
    orig_info = get_audio_info(str(input_path))
    if not orig_info:
        return None, "Could not get audio info!"

    if progress:
        progress(0.1, desc=f"Analyzing {input_path.name} ...")

    # Decide enhancements dynamically
    filter_chain, actions, out_fmt = analyze_track_for_enhancement(orig_info)
    output_path = input_path.with_name(f"{input_path.stem}_ENHANCED{out_fmt}")

    print(Fore.CYAN + f"-> FFmpeg: enhancing {input_path.name} -> {output_path.name}")
    try:
        ffmpeg_codec = "pcm_s16le" if out_fmt == ".wav" else "libmp3lame"
        ffmpeg_args = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(input_path),
            "-af", filter_chain, "-c:a", ffmpeg_codec
        ]
        if ffmpeg_codec == "libmp3lame":
            ffmpeg_args += ["-b:a", "320k"]
        ffmpeg_args += [str(output_path), "-y"]

        if progress:
            progress(0.6, desc="Enhancing track...")
        subprocess.run(ffmpeg_args, check=True, capture_output=True, text=True)
        if progress:
            progress(1, desc="Done!")

        proc_info = get_audio_info(str(output_path))
        print_audio_comparison(orig_info, proc_info, actions)
        return str(output_path.resolve()), "Track successfully enhanced!"
    except subprocess.CalledProcessError as e:
        error_msg = f"-> FFmpeg ERROR:\n{e.stderr or e.stdout}"
        print(Fore.RED + error_msg, file=sys.stderr)
        return None, error_msg