import ollama

from core.config import ENABLE_RAG, OLLAMA_MODEL
from core.rag import retrieve_context

SYSTEM_PROMPT = """你是"心语镜像"，一个专业、温暖的心理陪伴助手。
你的职责是：
1. 倾听用户的情绪与困扰，给予共情和支持
2. 基于专业心理学知识提供建议
3. 不做医疗诊断，但可以引导用户进行自我觉察
4. 语气温和、不评判，像一个值得信赖的朋友

如果提供了参考资料，请优先基于参考资料回答，但要用自然的语言表达，不要生硬引用。
请用中文回复，语言自然亲切。"""


def _build_augmented_message(user_message: str) -> str:
    context = retrieve_context(user_message) if ENABLE_RAG else ""
    if context:
        return f"""参考资料：
{context}

用户说：{user_message}"""
    return user_message


def chat(user_message: str, history: list | None = None) -> str:
    if history is None:
        history = []
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": _build_augmented_message(user_message)})

    response = ollama.chat(model=OLLAMA_MODEL, messages=messages)
    return response['message']['content']


def chat_stream(user_message: str, history: list | None = None):
    if history is None:
        history = []
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": _build_augmented_message(user_message)})

    stream = ollama.chat(model=OLLAMA_MODEL, messages=messages, stream=True)
    for chunk in stream:
        token = chunk['message']['content']
        if token:
            yield token
