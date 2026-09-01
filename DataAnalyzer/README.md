# 📊 DataAnalyzer — AI 数据分析助手

用自然语言和你的数据对话：上传 CSV / Excel / JSON，直接提问，AI 自动出分析方案 → 画图表 → 讲人话 → 生成 Markdown 报告。支持**两种分析模式**：固定流水线的"简单模式"，和自主调工具的 **ReAct Agent 模式**。

---

## ✨ 功能特性

- **多格式数据加载**：支持 CSV / XLSX / XLS / JSON，自动识别格式、生成数据画像（行列数、列类型、缺失值、内存占用）
- **双分析模式**：
  - 🧩 **简单模式**——AI 返回严格 JSON 分析方案（图表类型、X/Y 轴列、标题），程序照方抓药执行，结果可控
  - 🤖 **Agent 模式**——ReAct 循环，AI 自主决定调哪个工具（查概况 / 算统计 / 派生列 / 画图），适合开放性问题
- **派生列计算**：数据里没有的指标（如"总分 = 语文+数学+英语"）由 AI 给出表达式，执行层先算新列再画图
- **交互式图表**：plotly 驱动，支持 line / bar / scatter / pie / heatmap / histogram / box
- **人话洞察**：AI 把分析结果翻译成 2-4 句中文结论，不懂技术也能看懂
- **Markdown 报告**：一键把对话历史生成 .md 分析报告并下载
- **双端接口**：Gradio 可视化界面 + FastAPI 标准 API（`/upload` 上传数据、`/chat` 对话分析）

---

## 🛠️ 技术栈

| 组件 | 选型 |
|---|---|
| 数据处理 | pandas（读文件、数据画像、`df.eval` 派生列计算） |
| LLM 调用 | OpenAI SDK（简单模式）+ langchain（Agent 模式） |
| Agent 框架 | langchain `create_agent`（ReAct 循环）+ `@tool` 工具注册 |
| 前端界面 | Gradio 6.x |
| 后端接口 | FastAPI + Uvicorn |
| 可视化 | Plotly |
| 大模型 | 任意 OpenAI 兼容接口（DeepSeek / 智谱 / 通义 / OpenAI 等），`.env` 三行切换 |

---

## 📁 项目结构

```
DataAnalyzer/
├── gradio_app.py           # Gradio 网页界面（总调度/"搬运工"，双模式切换）
├── api.py                  # FastAPI 接口入口（端口 8000）
├── src/
│   ├── data_loader.py      # 数据加载与加工（读文件、生成 meta、派生列计算）
│   ├── llm_engine.py       # 简单模式 AI 引擎（出 JSON 分析方案 + 生成洞察）
│   ├── visualizer.py       # 可视化（按方案生成 plotly 图表）
│   ├── reporter.py         # 报告生成（拼 Markdown + 写文件）
│   ├── prompt/
│   │   └── prompt.txt      # 简单模式系统提示词（外置，改提示词不用动代码）
│   └── agent/
│       ├── react_agent.py  # Agent 模式主智能体（ChatOpenAI + create_agent，流式输出）
│       ├── agent_tools.py  # 4 个 @tool 工具 + 共享数据状态 DATA
│       └── agent_prompt.txt# Agent 模式系统提示词（工具说明书 + 使用规则）
├── test_sales.csv          # 测试数据：销售数据（15 行 × 6 列）
└── README.md
```

### Agent 的 4 个工具（agent_tools.py）

| 工具 | 干什么 | 何时被调 |
|---|---|---|
| `check_data_summary` | 数据概况（行列数、列名、类型、缺失值） | 用户问数据长什么样 |
| `compute_stats` | 数值列统计摘要（均值、最值、分位数） | 用户问平均/最大最小 |
| `derive_column` | 按表达式建新列（如 语文+数学+英语） | 用户要总分等数据里没有的指标 |
| `plot_chart` | 生成 7 种 plotly 图表 | 用户要看图/对比/趋势 |

**核心设计——数字永远不由 AI 编造**：模型只传参数（JSON 标量），DataFrame 从程序状态 `DATA["df"]` 里拿，所有数字都由 pandas 算出来，AI 只负责"说人话"。

---

## 🔗 两条数据流水线

**简单模式**（AI 出方案，程序执行）：

```
data_loader（读数据/造 meta）
        ↓ df, meta
llm_engine.analyze_query → AI 出 JSON 方案
        ↓
data_loader.derive_column → 需要时先算新列（如总分）
        ↓
visualizer.create_chart → 画 plotly 图
        ↓
llm_engine.generate_insight → AI 说人话
        ↓
reporter.generate/export → 生成 .md 报告
```

**Agent 模式**（AI 自己调工具）：

```
react_agent（ReAct 循环：思考 → 调工具 → 观察 → 再思考）
        ↓
agent_tools（@tool 工具从 DATA 状态拿 df，pandas 算真数据）
        ↓
流式输出回答 + 图表（DATA["last_fig"] 交还界面展示）
```

模块之间靠函数参数传数据，互不 import；串起它们的是 gradio_app 这个"搬运工"。

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install pandas openai python-dotenv gradio plotly langchain langchain-openai fastapi uvicorn python-multipart
```

### 2. 配置 `.env`

在 `src/` 目录下创建 `.env`：

```ini
LLM_API_KEY=你的key
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

支持所有 OpenAI 兼容接口的模型，改 `base_url` + `key` + `model` 三行即可切换。

### 3. 启动

```bash
# 方式一：Gradio 网页界面（推荐）
python gradio_app.py

# 方式二：FastAPI 接口
python api.py
```

Gradio 启动后浏览器打开 `http://127.0.0.1:7860`，上传 `test_sales.csv`，右上角选模式开聊。

---

## 📡 API 接口（FastAPI）

启动 `python api.py` 后，浏览器打开 `http://127.0.0.1:8000/docs` 可视化调试。

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/upload` | 上传数据文件（csv/xlsx/json），加载进分析引擎 |
| POST | `/chat` | 发送自然语言问题，Agent 调工具分析后返回回答 |

**必须先 `/upload` 再 `/chat`**（工具要有数据可算）。

请求示例（/chat）：

```json
{ "message": "这份数据有哪些列？一共多少行？" }
```

响应示例：

```json
{ "status": 200, "reply": "这份数据共 5 行、4 列：name / Chinese / Math / English ..." }
```

**上传的技术细节**：HTTP 传上来的文件在内存里不在磁盘上，`/upload` 先用 `tempfile.NamedTemporaryFile` 落成临时文件（保留原后缀），再把路径交给 pandas 读取——这是"前端上传 → 后端 pandas"衔接的关键一环。

---

## 💬 使用示例

上传 `test_sales.csv` 后可以问：

| 问题 | 简单模式 | Agent 模式 |
|---|---|---|
| "各区域销售额对比" | 出 bar 图方案 + 画图 | 自主调 plot_chart |
| "把每个人的总分算出来再排名" | 派生列 + bar 图 | 先 derive_column 再画图 |
| "这份数据有什么规律" | 只能按方案画图 | 自由组合多工具，开放性回答 |

---

## 🧠 设计决策（差异性）

| 决策 | 理由 |
|---|---|
| fail-fast 启动校验 | `api_key` / `base_url` / `model` 缺哪个启动就报哪个，错误不拖到运行时 |
| client 在 `__init__` 直接创建 | 不搞延迟初始化，少一层间接 |
| prompt 外置到 txt | 改提示词不用碰代码，简单模式和 Agent 模式各一份 |
| `model` 不写默认值 | 配置是使用者自己的事，.env 自己填 |
| 双模式并存 | 简单模式结果可控适合固定报表；Agent 模式灵活适合探索性分析 |
| 数字必须来自工具 | 模型只传参数不碰数据，所有数字由 pandas 计算，杜绝 AI 幻觉编数 |
| Gradio + FastAPI 双端 | 界面给人用，API 给程序用，同一套分析引擎 |

---

## 📅 修改日期与更新详情

- **2026-09-01**
  - 新增 **Agent 模式**：`src/agent/react_agent.py`（langchain `create_agent` + `ChatOpenAI`，环境变量 fail-fast 校验，流式输出）
  - 新增 `src/agent/agent_tools.py`：4 个 `@tool` 工具（查概况/算统计/派生列/画图）+ 共享数据状态 `DATA`，数字全部由 pandas 计算
  - 新增 `src/agent/agent_prompt.txt`：Agent 专属系统提示词（工具说明 + 调用规则）
  - `gradio_app.py` 增加模式切换（Radio：简单模式 / Agent 模式），Agent 分支流式渲染 + 取回图表
  - 新增 `api.py`：FastAPI 双接口（`/upload` 用 UploadFile + tempfile 落盘加载、`/chat` Agent 对话），已全链路实测通过
- **2026-08-31**
  - 新建 Gradio 版界面 `gradio_app.py`，替代 Streamlit 版 `app.py`
  - 修复 `data_loader.py` 5 处 bug（误导入、xlsx 分支永不成立、dtypes 生成错误、df.df 笔误）
  - 新增派生列支持：prompt 加 `derived_column` 字段 + `Dataloader.derive_column` 方法 + 画图前计算
  - 适配 gradio 6.x（移除 `Chatbot` 的 `type` 参数旧写法）
  - 新增测试数据 `test_sales.csv`

## 📄 License

仅供学习交流使用。
