import os
import threading

from core.config import ENABLE_RAG, HF_ENDPOINT

if HF_ENDPOINT:
    os.environ["HF_ENDPOINT"] = HF_ENDPOINT

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

CHROMA_PATH = "database/chroma"
KNOWLEDGE_PATH = "knowledge"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

_vectorstore = None
_loading = False
_loaded = False
_vectorstore_lock = threading.Lock()
_vectorstore_ready = threading.Event()


def _load_vectorstore_async():
    global _vectorstore, _loaded, _loading
    try:
        print("[RAG] 加载 embedding 模型...")
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        print("[RAG] embedding 模型加载成功")

        if os.path.exists(CHROMA_PATH):
            print("[RAG] 加载已有知识库...")
            _vectorstore = Chroma(
                persist_directory=CHROMA_PATH,
                embedding_function=embeddings
            )
        else:
            print("[RAG] 首次构建知识库...")
            _vectorstore = _build_vectorstore(embeddings)
        print("[RAG] 知识库加载完成")
    except Exception as e:
        print(f"[RAG] 知识库加载失败: {e}")
    finally:
        _loading = False
        _loaded = True
        _vectorstore_ready.set()


def _build_vectorstore(embeddings):
    loader = DirectoryLoader(
        KNOWLEDGE_PATH,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    documents = loader.load()
    print(f"[RAG] 加载了 {len(documents)} 个文档")

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(documents)
    print(f"[RAG] 分割为 {len(chunks)} 个文本块")

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )
    print("[RAG] 知识库构建完成")
    return vectorstore


def init_vectorstore():
    global _loading, _loaded
    if not ENABLE_RAG:
        _loaded = True
        _vectorstore_ready.set()
        print("[RAG] 已禁用")
        return
    with _vectorstore_lock:
        if _loaded or _loading:
            return
        _loading = True
        _vectorstore_ready.clear()
        thread = threading.Thread(target=_load_vectorstore_async, daemon=True)
        thread.start()
    print("[RAG] 知识库后台加载已启动")


def get_vectorstore():
    global _vectorstore, _loaded, _loading
    if not ENABLE_RAG:
        return None
    if _vectorstore is not None:
        return _vectorstore
    if _loading:
        print("[RAG] 等待知识库后台加载完成...")
        _vectorstore_ready.wait()
        return _vectorstore
    if not _loaded:
        with _vectorstore_lock:
            if _vectorstore is None and not _loading and not _loaded:
                print("[RAG] 同步加载知识库...")
                _loading = True
                _vectorstore_ready.clear()
                _load_vectorstore_async()
    return _vectorstore


def retrieve_context(query: str, k: int = 3) -> str:
    vectorstore = get_vectorstore()
    if vectorstore is None:
        return ""
    docs = vectorstore.similarity_search(query, k=k)
    if not docs:
        return ""
    return "\n\n---\n\n".join(doc.page_content for doc in docs)
