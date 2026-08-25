import gradio as gr
import time
from agent.react_agent import ReactAgent

agent = ReactAgent()


def respond(message, history):
    # 1. 显示思考中
    yield "⏳ 智能客服思考中..."
    time.sleep(1)

    # 2. 把 Gradio 历史转成 Agent 需要的格式
    messages = []
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    # 3. 调用 Agent
    full_response = ""
    for chunk in agent.execute_stream(messages):
        full_response = chunk
        yield full_response


demo = gr.ChatInterface(
    fn=respond,
    title="智能客服机器人",
)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        inbrowser=True
    )
