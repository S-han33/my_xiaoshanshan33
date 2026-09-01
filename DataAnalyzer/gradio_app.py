"""
DataAnalyzer - AI 数据分析助手（Gradio 版网页界面）
====================================================
运行方法：
  1. 首次使用先安装 gradio：pip install gradio
  2. 在项目根目录执行：python gradio_app.py

"""

import os
from datetime import datetime
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv
from src.agent.react_agent import ReactAgent
from src.agent import agent_tools
# .env 放在 src 目录里，这里显式指定位置加载（否则从根目录运行时找不到）
load_dotenv(Path(__file__).parent / "src" / ".env")

from src.data_loader import Dataloader
from src.llm_engine import LLMEngine
from src.visualizer import Visualizer
from src.reporter import Reporter

agent = ReactAgent()  # Agent 模式引擎，启动时同样 fail-fast 校验
llm = LLMEngine()  # fail-fast：key / base_url / model 没配好，启动时直接报错

# 当前数据状态（Gradio 简单版：用模块级变量保存，相当于 Streamlit 的 session_state）
DATA = {"df": None, "meta": None, "filename": "", "history": []}


def load_file(file):
    """上传文件后：读数据 → 生成 meta → 刷新预览和统计"""
    meta, df = Dataloader.load_file(file, os.path.basename(file))
    DATA.update(df=df, meta=meta, filename=os.path.basename(file), history=[])
    agent_tools.DATA.update(df=df, meta=meta, filename=os.path.basename(file), history=[], last_fig=None)
    info = (
        f"✅ 已加载 {DATA['filename']}：{meta['shape'][0]} 行 × "
        f"{meta['shape'][1]} 列（{meta['memory_usage']}）"
    )
    return info, Dataloader.preview(df), Dataloader.describe(df)


def ask(query, chat_history, mode):
    """按模式分流：简单模式走 LLMEngine 出方案，Agent 模式走 ReactAgent 自己调工具"""
    df = DATA["df"]
    if df is None:
        raise gr.Error("请先上传数据文件！")
    if not query.strip():
        raise gr.Error("问题不能为空！")

    chat_history = chat_history + [
        {"role": "user", "content": query},
        {"role": "assistant", "content": ""},
    ]

    if mode == "Agent 模式":
        # 流式接收 agent 输出，AI 自己决定调哪个工具
        agent_tools.DATA["last_fig"] = None  # 清掉上一张图，防止显示旧图
        answer = ""
        for piece in agent.user_inquiry(query):
            answer += piece
            chat_history[-1]["content"] = answer  # 只更新最后那条 assistant 消息
            yield chat_history, None, None, ""
        # 流结束：把 agent 画的图取出来展示（它没画过图就是 None）
        fig = agent_tools.DATA.get("last_fig")
        DATA["history"].append({
            "query": query,
            "intent": "agent",
            "chart_type": "",
            "insight": answer,
            "time": datetime.now().strftime("%H:%M:%S"),
        })
        yield chat_history, fig, None, ""
    else:
        # 简单模式：原逻辑不动（return 改成 yield，统一流式写法）
        meta = DATA["meta"]
        analysis = llm.analyze_query(query, meta)
        derived = analysis.get("derived_column")
        if isinstance(derived, dict) and derived.get("expression"):
            df = Dataloader.derive_column(df, derived)
        fig = Visualizer.create_chart(
            df=df,
            chart_type=analysis.get("chart_type", "bar"),
            x_column=analysis.get("x_column"),
            y_column=analysis.get("y_column"),
            group_column=analysis.get("group_column"),
            title=analysis.get("title", query),
        )
        insight = llm.generate_insight(query, meta, analysis)
        DATA["history"].append({
            "query": query,
            "intent": analysis.get("intent", ""),
            "chart_type": analysis.get("chart_type", ""),
            "insight": insight,
            "time": datetime.now().strftime("%H:%M:%S"),
        })
        chat_history[-1]["content"] = (
            f"💡 {insight}\n\n"
            f"**方案**：{analysis.get('chart_type', '')} | "
            f"x={analysis.get('x_column')} | y={analysis.get('y_column')}"
        )
        yield chat_history, fig, analysis, ""


def make_report():
    """把对话历史生成 Markdown 报告并保存成文件"""
    if not DATA["history"]:
        raise gr.Error("还没有对话记录，先问几个问题吧！")
    report = Reporter.generate(DATA["df"], DATA["meta"], DATA["history"], DATA["filename"])
    path = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    Reporter.export(report, path)
    return report, path


# ============ 界面搭建（全部用 Gradio 自带组件，不用写 CSS） ============
with gr.Blocks(title="DataAnalyzer - AI 数据分析助手") as demo:
    gr.Markdown("# 📊 DataAnalyzer\nAI 数据分析助手 — 用自然语言与你的数据对话")

    # 上传区
    with gr.Row():
        mode_radio = gr.Radio(["简单模式", "Agent 模式"], value="简单模式", label="分析模式")
        file_in = gr.File(label="📁 上传数据文件", file_types=[".csv", ".xlsx", ".xls", ".json"])
        load_info = gr.Textbox(label="加载状态", interactive=False)

    # 预览 / 统计（Tab 切换）
    with gr.Tabs():
        with gr.Tab("数据预览"):
            preview_tb = gr.DataFrame(interactive=False)
        with gr.Tab("统计摘要"):
            stats_tb = gr.DataFrame(interactive=False)

    # 对话区（左：聊天，右：图表 + 方案详情）

    with gr.Row():
        with gr.Column(scale=3):
            chat = gr.Chatbot(label="💬 数据对话", height=420)  # gradio 6 默认就是 messages 格式，不用写 type 参数
            query_in = gr.Textbox(label="向你的数据提问", placeholder="例如：展示各区域销售额对比")
            ask_btn = gr.Button("🔍 分析", variant="primary")
        with gr.Column(scale=2):
            chart = gr.Plot(label="图表")
            detail = gr.JSON(label="分析详情（AI 返回的方案）")

    # 报告区
    report_btn = gr.Button("📝 生成分析报告")
    with gr.Row():
        report_md = gr.Textbox(label="报告内容（Markdown）", lines=12)
        report_file = gr.File(label="下载报告文件")

    # ---- 事件绑定：谁被点了 → 调哪个函数 → 结果填到哪几个组件 ----
    file_in.upload(load_file, file_in, [load_info, preview_tb, stats_tb])
    ask_btn.click(ask, [query_in, chat, mode_radio], [chat, chart, detail, query_in])
    query_in.submit(ask, [query_in, chat, mode_radio], [chat, chart, detail, query_in])
    report_btn.click(make_report, None, [report_md, report_file])


if __name__ == "__main__":
    demo.launch()
