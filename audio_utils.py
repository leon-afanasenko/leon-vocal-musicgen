import numpy as np
from pydub import AudioSegment

def audio_write(path: str, audio_tensor, sample_rate: int):
    audio_np = audio_tensor.cpu().numpy()
    if audio_np.ndim > 1:
        audio_np = audio_np[0]
    audio_int16 = (audio_np * 32767).astype(np.int16)
    AudioSegment(audio_int16.tobytes(), frame_rate=sample_rate, sample_width=2, channels=1).export(path, format="wav")