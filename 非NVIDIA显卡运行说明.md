# 非 NVIDIA 显卡运行说明

本文档说明 `heart-mirror` 项目在没有 NVIDIA 显卡，或完全没有独立显卡的机器上，是否可以运行，以及需要注意的配置项。

## 结论

可以运行，但当前项目代码默认按 CUDA 环境编写，直接启动时有较高概率在以下位置报错：

- RAG 向量模型强制使用 `cuda`
- Whisper 转写时强制使用 `fp16=True`

如果将这两处改为 CPU 兼容模式，项目在非 NVIDIA 环境下通常可以正常运行。

## 受影响的模块

### 1. RAG 检索模块

文件：`core/rag.py`

当前代码：

```python
embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={"device": "cuda"},
    encode_kwargs={"normalize_embeddings": True}
)
```

问题：

- `device="cuda"` 直接要求 PyTorch 可用 CUDA
- 如果机器没有 NVIDIA 显卡，通常会报错

建议：

- 非 NVIDIA 环境改成 `device="cpu"`
- 更好的做法是自动检测 CUDA 是否可用，不可用时回退到 CPU

影响：

- 可以运行
- 首次构建知识库和检索会比 NVIDIA GPU 慢很多

### 2. Whisper 语音转文字

文件：

- `core/speech.py`
- `main.py`

当前代码中有类似调用：

```python
result = model.transcribe(tmp_path, language="zh", fp16=True)
```

问题：

- `fp16=True` 一般用于 CUDA/GPU 推理
- 在 CPU 或非 NVIDIA 环境下，通常应关闭半精度

建议：

- 改成 `fp16=False`
- 或按运行环境自动决定是否启用 `fp16`

影响：

- 可以正常转写
- 速度会下降，尤其在纯 CPU 环境下更明显

## 哪些部分通常不受 NVIDIA 限制

以下部分通常可以正常运行：

- FastAPI Web 服务
- 用户注册、登录、JWT 鉴权
- SQLite 情绪记录存储
- 前端静态页面
- 讯飞星火对话接口
- OpenCV 图像解码

## 情绪识别模块的注意事项

文件：`core/emotion.py`

该模块使用：

- `deepface`
- `retina-face`
- `opencv-python`
- `tensorflow`

说明：

- 这部分不一定必须依赖 NVIDIA 显卡
- 但底层依赖较重，在 CPU 环境可以运行，只是速度可能较慢
- 不同机器上，`tensorflow` 的安装兼容性差异较大，比 Web 服务本身更容易成为环境问题来源

也就是说：

- “能不能运行” 往往不是逻辑问题
- 而是 “依赖能不能正确安装” 和 “运行速度能不能接受”

## 依赖安装说明

项目的 [requirements.txt](E:\Code\heart-mirror\requirements.txt) 中包含：

- `torch`
- `tensorflow`

这两个包都和硬件/平台关系很大。

在非 NVIDIA 环境下：

- 不要默认认为会自动获得 GPU 加速
- 通常应安装 CPU 版，或者安装与你机器兼容的官方版本

如果安装成功，项目大概率可以运行；如果安装失败，通常需要按你的硬件平台单独处理 `torch` 或 `tensorflow`。

## 建议的运行方式

### 方案一：纯 CPU 运行

适用场景：

- 没有 NVIDIA 显卡
- 只有集成显卡
- 只想先把项目跑起来

建议：

- `core/rag.py` 中使用 `device="cpu"`
- Whisper 使用 `fp16=False`

优点：

- 兼容性最好
- 最容易启动成功

缺点：

- RAG 建库和语音识别速度较慢

### 方案二：自动识别硬件后回退

适用场景：

- 希望同一份代码在不同机器都能跑

建议：

- 优先检测 CUDA
- 有 CUDA 就用 GPU
- 没有 CUDA 就自动切换到 CPU

优点：

- 部署更稳
- 不需要手工改代码

缺点：

- 需要额外改一点初始化逻辑

## 最终结论

非 NVIDIA 显卡环境下，这个项目不是“完全不能运行”，而是“当前代码默认假设有 CUDA”。

只要把以下两点改为 CPU 兼容模式，项目通常就可以运行：

1. `core/rag.py` 不要强制 `device="cuda"`
2. Whisper 转写不要强制 `fp16=True`

如果你希望后续部署更稳定，建议把项目改成“自动检测 GPU，没有就回退 CPU”的方式。
