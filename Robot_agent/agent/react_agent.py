from langchain.agents import create_agent
from model.factory import chat_model
from utils.prompt_loader import load_system_prompt
from agent.tools.agent_tools import *
from agent.tools.middleware import monitor_tools, log_before_model, prompt_switch


class ReactAgent:
    def __init__(self):
        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompt(),
            tools=[rag_summarize, fetch_tracking, get_user_location, get_weather, fill_context_for_weather],
            middleware=[monitor_tools, log_before_model, prompt_switch]
        )

    def execute_stream(self, messages):
        """
        :param messages: 完整对话历史，格式 [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
        """
        input_dict = {'messages': messages}

        last_text = ""
        for chunk in self.agent.stream(input_dict, stream_mode="values", context={"weather": False}):
            chunk_messages = chunk.get('messages', [])
            if not chunk_messages:
                continue

            last_message = chunk_messages[-1]

            # 只输出 AI 的最终回复
            if last_message.type == "ai" and last_message.content:
                content = last_message.content.strip()

                # 过滤掉 AI 复述用户问题的情况
                user_last = messages[-1].get("content", "") if messages else ""
                if content.startswith(user_last):
                    content = content[len(user_last):].strip()
                    if content and content[0] in "：:，,。.?！!":
                        content = content[1:].strip()

                if content and content != last_text:
                    last_text = content
                    yield content + '\n'


if __name__ == '__main__':
    agent = ReactAgent()
    for chunk in agent.execute_stream([{"role": "user", "content": "我是油皮，买你们家的哪款粉底液比较好呢？"}]):
        print(chunk, end="", flush=True)
