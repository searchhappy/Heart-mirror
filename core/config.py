import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

XF_APP_ID = os.getenv("XF_APP_ID", "")
XF_API_KEY = os.getenv("XF_API_KEY", "")
XF_API_SECRET = os.getenv("XF_API_SECRET", "")
XF_URL = os.getenv("XF_URL", "wss://spark-api.xf-yun.com/v4.0/chat")
XF_DOMAIN = os.getenv("XF_DOMAIN", "4.0Ultra")

MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "auto").lower()
ENABLE_RAG = os.getenv("ENABLE_RAG", "true").lower() in {"1", "true", "yes", "on"}
HF_ENDPOINT = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
