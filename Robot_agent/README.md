# 客服Agent（YunYunBot）

> 基于 **RAG + ReAct Agent** 的企业级智能客服系统 —— 用商品知识库回答顾客问题，让回答有依据、不瞎编。

云云客服是一个完整的 AI 客服 Agent 项目：顾客提问 → Agent 判断是否需要检索 → 调用 `rag_summarize` 工具从向量库检索化妆品/商品资料 → 结合工具结果生成专业回答。覆盖 **RAG 检索增强、ReAct 工具调用、混合格式文档处理、双端接口、Docker 容器化部署** 全链路。

---

## ✨ 功能特性

- 🧠 **RAG 知识库问答**：基于 LangChain + Chroma 向量库，回答价格/规格/物流/退换货等商品问题，回答可溯源
- 🔄 **ReAct Agent 循环**：思考 → 调用工具 → 观察结果 → 再思考，自主决定何时检索、何时直接回答
- 📄 **混合格式文档支持**：txt / PDF / Word（docx）自动识别加载
- 💬 **多轮对话**：上下文连贯，支持追问
- 🎨 **双端接口**：Gradio 可视化聊天界面 + FastAPI 标准 API
- 🐳 **Docker Compose 一键部署**：App 与 Ollama 双容器，模型持久化，开箱即用
- ⚡ **MD5 去重增量灌库**：修改资料后秒级增量更新向量库，不重复灌入
- 🔌 **模型可插拔**：本地 Ollama 或云端 API 一键切换（环境变量控制）

---

## 🛠 技术栈

| 组件 | 选型 |
|---|---|
| AI 框架 | LangChain 1.x（langchain-core / community / chroma / ollama） |
| Agent 框架 | langgraph（create_agent + 中间件） |
| 向量库 | ChromaDB + bge-m3 向量模型 |
| 大模型 | Ollama（qwen2.5:7b），可切换 DeepSeek 等云端 API |
| 前端界面 | Gradio 6.x |
| 后端接口 | FastAPI + Uvicorn |
| 部署 | Docker Compose（App + Ollama 双容器） |

---

## 📁 项目结构

```
客服Agent/
├── app.py                  # Gradio 聊天界面入口（端口 7860）
├── api.py                  # FastAPI 接口入口（端口 8000）
├── Dockerfile              # App 容器镜像
├── docker-compose.yml      # 双容器编排（App + Ollama）
├── requirements.txt        # 项目依赖
├── config/                 # YAML 配置（模型 / 向量库 / 提示词路径）
│   ├── rag.yml             #   模型名、Ollama 地址
│   ├── chroma.yml          #   向量库参数、切分参数
│   ├── prompts.yml         #   提示词文件路径
│   └── agent.yml           #   Agent 外部数据配置
├── data/                   # 📚 商品知识库资料（txt / pdf / docx）
├── prompts/                # 提示词模板（系统提示词 / RAG 总结提示词）
├── model/
│   └── factory.py          # 模型工厂（聊天模型 + 向量模型，可插拔）
├── rag/
│   ├── vector_store.py     # 向量库服务（加载→MD5去重→切分→入库→检索）
│   └── rag_service.py      # RAG 总结服务（检索→拼参考资料→生成回答）
├── agent/
│   ├── react_agent.py      # ReAct 主智能体（流式输出）
│   └── tools/              # 工具定义 + 中间件
└── utils/                  # 公共工具（配置/文件/日志/路径/提示词加载）
```

**请求链路**：`app.py / api.py` → `ReactAgent`（ReAct 思考）→ 需要资料时调用 `rag_summarize` 工具 → `rag_service` 检索向量库 → 返回资料 → Agent 生成回答

---

## 🚀 快速开始（Docker 部署）

### 前置条件
- 安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- 至少 16GB 内存（qwen2.5:7b + bge-m3 模型约 6GB）

### 一键启动

```bash
# 1. 构建并启动（App + Ollama 两个容器）
docker compose up -d --build

# 2. 拉取模型（只需一次，约 6GB）
docker compose exec ollama ollama pull qwen2.5:7b
docker compose exec ollama ollama pull bge-m3

# 3. 首次建向量库（把 data/ 资料灌入 Chroma）
docker compose exec app python -m rag.vector_store
```

完成后浏览器打开 **http://localhost:7860** 开始聊天。

### 日常使用

```bash
docker compose up -d        # 启动（模型已持久化，无需重复拉取）
docker compose down         # 停止
```

---

## 📚 数据管理（改资料 / 更新知识库）

`data/` 目录已挂载（bind mount）到容器，**改本地文件立即生效，无需重建镜像**：

```bash
# 修改 data/ 下的资料后，增量更新向量库（MD5 去重，只处理改动过的文件）
docker compose exec app python -m rag.vector_store
```

如果检索结果混乱（旧数据残留）：

```bash
docker compose down
docker volume rm 客服agent_app_chroma    # 删除旧向量库
docker compose up -d
docker compose exec app python -m rag.vector_store    # 重新建库
```

---

## ⚙️ 配置说明

### 模型配置（`config/rag.yml`）

```yaml
chat_model_name : qwen2.5:7b          # 聊天模型
embedding_model_name : bge-m3         # 向量模型
base_url : http://localhost:11434     # Ollama 地址（容器内由环境变量覆盖）
```

### 切换模型（本地 ↔ 云端）

- **本地 Ollama**（默认）：直接使用 qwen2.5:7b + bge-m3，免费、离线可用
- **云端 API**（如 DeepSeek）：设置环境变量 `OLLAMA_BASE_URL` 指向云端兼容接口，或调整 `model/factory.py`

---

## 📡 API 接口（FastAPI）

默认入口为 Gradio（`app.py`）。如需启用 FastAPI：

```bash
docker compose exec app python api.py   # 启动 API（端口 8000）
```

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/chat` | 发送消息，返回客服回答 |

请求示例：

```json
{ "message": "油皮适合哪款粉底液？" }
```

响应示例：

```json
{ "status": 200, "reply": "亲，油皮建议选择清爽控油款..." }
```

---

## 📝 更新记录

| 日期 | 内容 |
|---|---|
| 2026-08-25 | M6 完成：Docker Compose 双容器部署（App + Ollama），模型持久化，data 目录 bind mount 挂载 |
| 2026-08-17 | M3-M5 完成：RAG 核心链路、Gradio 界面、FastAPI 封装 |
| 2026-08-07 | M1-M2 完成：环境搭建、化妆品知识库资料整理（混合格式） |

---

## 📄 许可证

本项目仅供学习交流使用，数据中的品牌均为虚构。
