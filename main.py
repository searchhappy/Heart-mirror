from collections import defaultdict
from threading import Lock
import os
import tempfile

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core.auth import create_token, decode_token, hash_password, verify_password
from core.config import MODEL_PROVIDER, XF_API_KEY, XF_API_SECRET, XF_APP_ID
from core.emotion import analyze_emotion_from_base64_list
from core.llm import chat as ollama_chat
from core.llm import chat_stream as ollama_chat_stream
from core.llm_xf import chat as xf_chat
from core.llm_xf import chat_stream as xf_chat_stream
from core.rag import init_vectorstore
from core.speech import record_and_transcribe, transcribe_file
from database.db import (
    create_user,
    get_emotion_stats,
    get_emotion_stats_by_range,
    get_recent_emotions,
    get_user,
    init_db,
    save_emotion,
)

app = FastAPI(title="心语镜像", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

security = HTTPBearer(auto_error=False)
conversation_history: dict[str, list] = defaultdict(list)
conversation_lock = Lock()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


class EmotionRequest(BaseModel):
    image: str
    frames: list[str] = Field(default_factory=list)


class SpeechRequest(BaseModel):
    duration: int = 15


class EmotionRecordRequest(BaseModel):
    dominant_emotion: str
    stress_score: int
    emotions: dict
    speech_text: str = ""
    chat_message: str = ""
    source: str = "manual"


class AuthRequest(BaseModel):
    username: str
    password: str


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    if not credentials:
        raise HTTPException(status_code=401, detail="未登录")
    username = decode_token(credentials.credentials)
    if not username:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")
    return username


def _xf_available() -> bool:
    return all([XF_APP_ID, XF_API_KEY, XF_API_SECRET])


def _provider_order() -> list[str]:
    if MODEL_PROVIDER == "xf":
        return ["xf"]
    if MODEL_PROVIDER == "ollama":
        return ["ollama"]
    return ["xf", "ollama"]


def _chat_with_fallback(message: str, history: list) -> str:
    errors = []
    for provider in _provider_order():
        if provider == "xf":
            if not _xf_available():
                errors.append("讯飞未配置")
                continue
            try:
                return xf_chat(message, history)
            except Exception as exc:
                errors.append(f"讯飞模型调用失败: {exc}")
        elif provider == "ollama":
            try:
                return ollama_chat(message, history)
            except Exception as exc:
                errors.append(f"Ollama 模型调用失败: {exc}")
    raise HTTPException(status_code=503, detail="；".join(errors) or "没有可用的大模型服务")


def _chat_stream_with_fallback(message: str, history: list):
    errors = []
    for provider in _provider_order():
        if provider == "xf":
            if not _xf_available():
                errors.append("讯飞未配置")
                continue
            try:
                for token in xf_chat_stream(message, history):
                    yield token
                return
            except Exception as exc:
                errors.append(f"讯飞模型调用失败: {exc}")
        elif provider == "ollama":
            try:
                for token in ollama_chat_stream(message, history):
                    yield token
                return
            except Exception as exc:
                errors.append(f"Ollama 模型调用失败: {exc}")
    yield "[系统提示] 当前没有可用的大模型服务。"
    if errors:
        yield " " + "；".join(errors)


@app.on_event("startup")
async def startup():
    init_db()
    init_vectorstore()


@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/health")
async def health():
    return {"status": "ok", "message": "服务正常运行", "provider": MODEL_PROVIDER}


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, username: str = Depends(get_current_user)):
    with conversation_lock:
        history = list(conversation_history[username])
    reply = _chat_with_fallback(request.message, history)
    with conversation_lock:
        user_history = conversation_history[username]
        user_history.append({"role": "user", "content": request.message})
        user_history.append({"role": "assistant", "content": reply})
        if len(user_history) > 20:
            conversation_history[username] = user_history[-20:]
    return ChatResponse(reply=reply)


@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest, username: str = Depends(get_current_user)):
    with conversation_lock:
        history = list(conversation_history[username])

    def generate():
        full_reply = ""
        for token in _chat_stream_with_fallback(request.message, history):
            full_reply += token
            yield token
        with conversation_lock:
            user_history = conversation_history[username]
            user_history.append({"role": "user", "content": request.message})
            user_history.append({"role": "assistant", "content": full_reply})
            if len(user_history) > 20:
                conversation_history[username] = user_history[-20:]

    return StreamingResponse(generate(), media_type="text/plain")


@app.delete("/chat/history")
async def clear_history(username: str = Depends(get_current_user)):
    with conversation_lock:
        conversation_history.pop(username, None)
    return {"message": "对话历史已清空"}


@app.post("/analyze/emotion")
async def analyze_emotion(request: EmotionRequest, _: str = Depends(get_current_user)):
    frames = request.frames if request.frames else [request.image]
    return analyze_emotion_from_base64_list(frames)


@app.post("/analyze/speech")
async def speech_to_text(request: SpeechRequest, _: str = Depends(get_current_user)):
    text = record_and_transcribe(request.duration)
    return {"text": text}


@app.post("/analyze/speech/upload")
async def speech_upload(file: UploadFile = File(...), _: str = Depends(get_current_user)):
    suffix = os.path.splitext(file.filename or "upload.webm")[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        return {"text": transcribe_file(tmp_path)}
    except Exception as e:
        return {"text": "", "error": str(e)}
    finally:
        os.unlink(tmp_path)


@app.post("/emotions/save")
async def save_emotion_record(request: EmotionRecordRequest, username: str = Depends(get_current_user)):
    save_emotion(username, request.dominant_emotion, request.stress_score, request.emotions, request.speech_text, request.chat_message, request.source)
    return {"message": "情绪记录已保存"}


@app.get("/emotions/recent")
async def get_recent(days: int = 7, username: str = Depends(get_current_user)):
    return get_recent_emotions(username, days)


@app.get("/emotions/stats")
async def get_stats(days: int = 7, username: str = Depends(get_current_user)):
    return get_emotion_stats(username, days)


@app.get("/emotions/trend")
async def get_trend(days: int = 7, username: str = Depends(get_current_user)):
    return get_emotion_stats_by_range(username, days)


@app.post("/auth/register")
async def register(request: AuthRequest):
    if len(request.username) < 2:
        raise HTTPException(status_code=400, detail="用户名至少2个字符")
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少6位")
    if get_user(request.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    success = create_user(request.username, hash_password(request.password))
    if not success:
        raise HTTPException(status_code=500, detail="注册失败")
    token = create_token(request.username)
    return {"token": token, "username": request.username}


@app.post("/auth/login")
async def login(request: AuthRequest):
    user = get_user(request.username)
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_token(request.username)
    return {"token": token, "username": request.username}


@app.get("/auth/me")
async def me(username: str = Depends(get_current_user)):
    return {"username": username}
