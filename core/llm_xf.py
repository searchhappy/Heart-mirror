from sparkai.core.messages import ChatMessage
from sparkai.llm.llm import ChatSparkLLM

from core.config import ENABLE_RAG, OLLAMA_MODEL, XF_API_KEY, XF_API_SECRET, XF_APP_ID, XF_DOMAIN, XF_URL

SYSTEM_PROMPT = """你是"心语镜像"，一个专业、温暖的心理陪伴助手。
你的职责是：
1. 倾听用户的情绪与困扰，给予共情和支持
2. 基于专业心理学知识提供建议
3. 不做医疗诊断，但可以引导用户进行自我觉察
4. 语气温和、不评判，像一个值得信赖的朋友

如果提供了参考资料，请优先基于参考资料回答，但要用自然的语言表达，不要生硬引用。
请用中文回复，语言自然亲切。"""

_xf_llm = None
_xf_llm_stream = None


def _ensure_credentials():
    if not all([XF_APP_ID, XF_API_KEY, XF_API_SECRET]):
        raise RuntimeError("Missing XF credentials. Set XF_APP_ID, XF_API_KEY and XF_API_SECRET.")


def _build_augmented_message(user_message: str) -> str:
    if not ENABLE_RAG:
        return user_message
    try:
        from core.rag import retrieve_context
        context = retrieve_context(user_message)
    except Exception:
        context = ""
    if context:
        return f"""参考资料：
{context}

用户说：{user_message}"""
    return user_message


def _get_xf_llm():
    global _xf_llm
    if _xf_llm is None:
        _ensure_credentials()
        _xf_llm = ChatSparkLLM(
            spark_api_url=XF_URL,
            spark_app_id=XF_APP_ID,
            spark_api_key=XF_API_KEY,
            spark_api_secret=XF_API_SECRET,
            spark_llm_domain=XF_DOMAIN,
            streaming=False,
        )
    return _xf_llm


def _get_xf_llm_stream():
    global _xf_llm_stream
    if _xf_llm_stream is None:
        _ensure_credentials()
        _xf_llm_stream = ChatSparkLLM(
            spark_api_url=XF_URL,
            spark_app_id=XF_APP_ID,
            spark_api_key=XF_API_KEY,
            spark_api_secret=XF_API_SECRET,
            spark_llm_domain=XF_DOMAIN,
            streaming=True,
        )
    return _xf_llm_stream


def chat(user_message: str, history: list | None = None) -> str:
    if history is None:
        history = []
    messages = [ChatMessage(role="system", content=SYSTEM_PROMPT)]
    for msg in history:
        messages.append(ChatMessage(role=msg.get("role", "user"), content=msg.get("content", "")))
    messages.append(ChatMessage(role="user", content=_build_augmented_message(user_message)))
    response = _get_xf_llm().generate([messages])
    return response.generations[0][0].text


def chat_stream(user_message: str, history: list | None = None):
    if history is None:
        history = []
    messages = [ChatMessage(role="system", content=SYSTEM_PROMPT)]
    for msg in history:
        messages.append(ChatMessage(role=msg.get("role", "user"), content=msg.get("content", "")))
    messages.append(ChatMessage(role="user", content=_build_augmented_message(user_message)))
    stream = _get_xf_llm_stream().stream(messages)
    for chunk in stream:
        if chunk.content:
            yield chunk.content
