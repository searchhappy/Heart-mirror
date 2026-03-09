# 心语镜像

心语镜像是一套基于多模态大模型的心理干预与陪伴系统，面向大学生、职场人士和关注心理健康的日常用户，提供文字对话、表情识别、语音转写、RAG 知识增强回复和情绪趋势可视化能力。

项目最初用于 2026 年中国大学生计算机设计大赛人工智能实践赛。当前仓库版本以代码实际实现为准，包含用户鉴权、按用户隔离的会话与情绪记录，以及基于浏览器录音上传的语音识别流程。

## 项目亮点

- 多模态输入：支持文本、摄像头表情和语音输入。
- 专业知识增强：基于心理学知识库构建 RAG 检索，提升回复的专业性与可解释性。
- 实时陪伴对话：支持流式输出，前端以打字机效果展示回复。
- 情绪数据沉淀：记录主要情绪、压力值和情绪分布，用图表展示近 7/30/90 天趋势。
- 隐私与隔离：支持注册登录，聊天上下文和情绪数据按用户隔离存储。

## 典型场景

- 情绪低落、焦虑、失眠时的即时倾诉与陪伴。
- 每日情绪打卡与压力监测。
- 考试、项目冲刺、社交冲突等高压阶段的情绪跟踪。
- CBT、压力管理、情绪调节等心理知识的日常学习。

## 系统架构

项目采用前后端分离的轻量架构：

- 感知层：OpenCV + DeepFace 进行多帧表情识别；Whisper 进行语音转写；浏览器提供文本和多媒体输入。
- 理解层：LangChain + ChromaDB + HuggingFace Embeddings 构建 RAG 知识库。
- 响应层：讯飞星火或本地 Ollama 模型生成心理陪伴回复，支持流式输出。
- 记录层：SQLite 持久化情绪记录，ECharts 展示雷达图和趋势图。

## 当前功能

- 用户注册、登录、登录态校验。
- 文本对话与流式对话。
- 摄像头连拍 5 帧后做表情识别，并生成压力值。
- 浏览器录音上传到后端后进行 Whisper 中文转写。
- 情绪记录保存、最近记录查询、情绪雷达统计、压力趋势统计。
- 心理知识库检索增强回复。

## 技术栈

### 后端

- FastAPI
- SQLite
- python-jose / passlib
- LangChain / ChromaDB / sentence-transformers
- DeepFace / OpenCV
- Whisper
- 讯飞星火 SDK 或 Ollama

### 前端

- 原生 HTML / CSS / JavaScript
- ECharts 5.x

## 项目结构

```text
heart-mirror/
├── main.py                 # FastAPI 主入口
├── requirements.txt        # Python 依赖
├── core/
│   ├── auth.py             # JWT 与密码校验
│   ├── config.py           # 模型与接口配置
│   ├── emotion.py          # 多帧表情识别
│   ├── llm.py              # Ollama 对话实现
│   ├── llm_xf.py           # 讯飞星火对话实现
│   ├── rag.py              # 向量库构建与检索
│   └── speech.py           # Whisper 语音转写
├── database/
│   ├── db.py               # 数据库初始化与读写
│   └── emotion.db          # SQLite 数据库文件
├── knowledge/
│   ├── cbt.txt
│   ├── emotions.txt
│   └── stress.txt
├── static/
│   └── index.html          # 前端页面
├── uploads/                # 上传文件目录
└── test_*.py               # 简单测试脚本
```

## 环境要求

- Windows 10/11 64 位优先
- Python 3.10 或 3.11
- 摄像头与麦克风
- 推荐 16GB 内存
- 如使用 GPU 推理，建议具备可用 CUDA 环境

## 安装与启动

### 1. 创建虚拟环境

```powershell
python -m venv venv
venv\Scripts\activate
```

### 2. 安装依赖

```powershell
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 配置环境变量

项目当前通过环境变量读取鉴权和讯飞配置。你可以在系统环境变量中设置，或在项目根目录放置 `.env` 文件。

```env
JWT_SECRET_KEY=your_jwt_secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=7

XF_APP_ID=your_xf_app_id
XF_API_KEY=your_xf_api_key
XF_API_SECRET=your_xf_api_secret
XF_URL=wss://spark-api.xf-yun.com/v4.0/chat
XF_DOMAIN=4.0Ultra
```

如果你想改用本地 Ollama 模型：

- 安装并启动 Ollama
- 拉取模型，例如 `ollama pull qwen2.5:7b`
- 在 [main.py](/E:/Code/heart-mirror/main.py) 中把 `from core.llm_xf import chat, chat_stream` 改为 `from core.llm import chat, chat_stream`

### 4. 启动服务

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问系统

浏览器打开：

- [http://localhost:8000](http://localhost:8000)

## 使用说明

### 文字对话

- 注册或登录后，在页面底部输入文字。
- 点击“发送”或按 `Enter` 发起对话。
- 系统会结合心理知识库进行增强回复。

### 表情识别

- 点击“拍照分析”并授权摄像头。
- 系统自动连拍 5 帧，输出主要情绪和压力值。
- 分析结果可自动写入情绪记录，并用于触发后续对话。

### 语音输入

- 点击“语音输入”并授权麦克风。
- 浏览器录音后会上传到后端，由 Whisper 转写为中文文本。
- 识别结果会自动填入输入框。

### 情绪可视化

- 右侧面板展示情绪雷达图和压力趋势图。
- 支持查看近 7 天、30 天、90 天数据。
- 情绪数据按登录用户隔离存储。

## 主要接口

### 认证

- `POST /auth/register` 注册
- `POST /auth/login` 登录
- `GET /auth/me` 获取当前用户

### 对话

- `POST /chat` 普通对话
- `POST /chat/stream` 流式对话
- `DELETE /chat/history` 清空当前用户会话

### 分析

- `POST /analyze/emotion` 表情识别
- `POST /analyze/speech` 服务端本机录音转写
- `POST /analyze/speech/upload` 上传音频转写

### 情绪记录

- `POST /emotions/save` 保存记录
- `GET /emotions/recent` 最近记录
- `GET /emotions/stats` 情绪统计
- `GET /emotions/trend` 压力趋势

说明：除注册、登录、健康检查外，核心接口均需要 `Bearer Token`。

## 知识库说明

知识库文本位于 `knowledge/` 目录，当前包含：

- `cbt.txt`：认知行为疗法相关内容
- `stress.txt`：压力与焦虑管理
- `emotions.txt`：情绪识别与调节

启动时系统会初始化向量库，首次运行可能需要下载 embedding 模型并建立本地索引。

## 测试脚本

仓库中包含若干简单脚本用于本地验证：

- [test_db.py](/E:/Code/heart-mirror/test_db.py)
- [test_emotion.py](/E:/Code/heart-mirror/test_emotion.py)
- [test_camera.py](/E:/Code/heart-mirror/test_camera.py)
- [test_speech.py](/E:/Code/heart-mirror/test_speech.py)
- [test_rag.py](/E:/Code/heart-mirror/test_rag.py)

这些脚本更接近手工验证，不是完整的自动化测试套件。

## 注意事项

- 首次运行可能需要下载 Whisper 或 embedding 模型，耗时取决于网络环境。
- 若使用讯飞星火，必须正确配置 `XF_APP_ID`、`XF_API_KEY`、`XF_API_SECRET`。
- 若使用 Ollama，本地模型需要提前拉取。
- `POST /analyze/speech` 仍是服务端本机录音接口，部署场景下推荐使用 `/analyze/speech/upload`。

## 未来可扩展方向

- 接入更强的情绪识别和语音情感分析模型。
- 引入移动端应用或 PWA 版本。
- 扩充知识库来源，提高建议的专业性和覆盖面。
- 增加危机预警和长期干预策略。
- 提供 Docker 化部署方案。

## 参考来源

本 README 主要依据以下材料整理：

- [心语镜像_参赛文档.docx](/E:/Code/heart-mirror/心语镜像_参赛文档.docx)
- 当前仓库实现代码
