import cv2
import base64
import numpy as np
from deepface import DeepFace

EMOTION_MAP = {
    "happy": "开心", "sad": "悲伤", "angry": "愤怒",
    "fear": "恐惧", "surprise": "惊讶", "disgust": "厌恶", "neutral": "平静"
}

STRESS_WEIGHT = {
    "happy": 0, "neutral": 20, "surprise": 30,
    "sad": 60, "fear": 75, "disgust": 70, "angry": 80
}

def _analyze_single(img) -> dict | None:
    """分析单帧图片，返回原始情绪数据"""
    try:
        img = cv2.convertScaleAbs(img, alpha=1.2, beta=15)

        result = DeepFace.analyze(
            img,
            actions=["emotion"],
            enforce_detection=False,
            silent=True,
            detector_backend="retinaface"  # 更精准的人脸检测器
                   # 更准确的情绪模型
        )
        if not result:
            return None
        return result[0]["emotion"]
    except Exception:
        return None

def analyze_emotion_from_base64_list(image_base64_list: list) -> dict:
    """
    分析多帧 base64 图片，取平均值后返回结果
    image_base64_list: 最多5帧的 base64 图片列表
    """
    all_emotions = []

    for b64 in image_base64_list:
        try:
            img_data = base64.b64decode(b64)
            np_arr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if img is None:
                continue
            emotions = _analyze_single(img)
            if emotions:
                all_emotions.append(emotions)
        except Exception:
            continue

    if not all_emotions:
        return {"error": "未能识别到有效表情"}

    # 取所有帧的平均值
   # 取所有帧的平均值（强制转为 Python float，避免 numpy.float32 序列化错误）
    avg_emotions = {}
    for key in all_emotions[0].keys():
        avg_emotions[key] = round(
            float(sum(float(e.get(key, 0)) for e in all_emotions) / len(all_emotions)), 1
        )

    # 找主要情绪
    dominant = max(avg_emotions, key=avg_emotions.get)

    # 计算压力值
    stress_score = int(sum(
        float(avg_emotions.get(e, 0)) * STRESS_WEIGHT.get(e, 0) / 100
        for e in STRESS_WEIGHT
    ))

    return {
        "dominant_emotion": dominant,
        "dominant_emotion_cn": EMOTION_MAP.get(dominant, dominant),
        "stress_score": stress_score,
        "emotions": {
            EMOTION_MAP.get(k, k): round(v, 1)
            for k, v in avg_emotions.items()
        },
        "frames_analyzed": len(all_emotions)  # 实际分析的帧数
    }

# 保留单帧兼容接口
def analyze_emotion_from_base64(image_base64: str) -> dict:
    return analyze_emotion_from_base64_list([image_base64])