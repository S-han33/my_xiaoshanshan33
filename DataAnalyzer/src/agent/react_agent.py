from langchain.agents import create_agent
from src.agent.agent_tools import *
import os
from pathlib import Path
from langchain_openai import ChatOpenAI




class ReactAgent:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL")
        self.model = os.getenv("LLM_MODEL")

        if not self.api_key or self.api_key == "your-api-key-here":
            raise ValueError("LLM_API_KEY 未配置或仍为占位符，请检查 .env 文件")
        if not self.base_url:
            raise ValueError("LLM_BASE_URL 未配置，请检查 .env 文件")
        if not self.model:
            raise ValueError("LLM_MODEL 未配置，请检查 .env 文件")
        self.llm = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
        )
        self.prompt_path = Path(__file__).parent / "agent_prompt.txt"  # prompt 就在本文件所在文件夹 src/agent/ 里
        self.system_prompt = self.prompt_path.read_text(encoding="utf-8")

        # 然后 create_agent 改成：
        self.agent = create_agent(
            model=self.llm,  # ← 传刚才建的"对象"，不是 self.model 字符串
            system_prompt=self.system_prompt,
            tools=[check_data_summary, compute_stats, derive_column, plot_chart],
        )
    def user_inquiry(self, query):
        input_dict = {
            "messages": [{
                "role": "user",
                "content": query,
            }]
        }
        for chunk in self.agent.stream(input_dict, stream_mode="values"):
            latest_message = chunk["messages"][-1]
            if latest_message.content:
                yield latest_message.content.strip() + "\n"