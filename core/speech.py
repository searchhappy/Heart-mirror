import os
import tempfile

import numpy as np
import sounddevice as sd
import torch
import whisper
from scipy.io.wavfile import write

# 加载 Whisper 模型（首次会自动下载，约 140MB）
# 可选：tiny / base / small / medium，越大越准但越慢
MODEL_SIZE = "base"
_model = None


def get_model():
    global _model
    if _model is None:
        print(f"Whisper {MODEL_SIZE} 模型加载中...")
        _model = whisper.load_model(MODEL_SIZE)
        print("Whisper 模型加载完成")
    return _model


def record_audio(duration: int = 15, sample_rate: int = 16000) -> np.ndarray:
    """录制音频，duration 秒"""
    print(f"开始录音，请说话（{duration}秒）...")
    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="float32"
    )
    sd.wait()
    print("录音完成")
    return audio, sample_rate


def transcribe_audio(audio: np.ndarray, sample_rate: int = 16000) -> str:
    """将音频转为文字"""
    model = get_model()

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
        write(tmp_path, sample_rate, audio)

    try:
        result = model.transcribe(tmp_path, language="zh", fp16=torch.cuda.is_available())
        return result["text"].strip()
    finally:
        os.unlink(tmp_path)


def transcribe_file(file_path: str) -> str:
    """转写上传的音频文件"""
    model = get_model()
    result = model.transcribe(file_path, language="zh", fp16=torch.cuda.is_available())
    return result["text"].strip()


def record_and_transcribe(duration: int = 5) -> str:
    """录音并直接返回识别文字"""
    audio, sr = record_audio(duration)
    return transcribe_audio(audio, sr)
