from typing import Callable
from langgraph.runtime import Runtime
from langchain.agents import AgentState
from utils.prompt_loader import load_weather_prompts, load_system_prompt
from utils.logger_handler import logger
from langchain.agents.middleware import wrap_tool_call,dynamic_prompt,ModelRequest,before_model
from langchain_core.messages import ToolMessage
from langchain_protocol import Command
from langgraph.prebuilt.tool_node import ToolCallRequest


@wrap_tool_call
def monitor_tools(request,handler: Callable[[ToolCallRequest], ToolMessage | Command]) -> ToolMessage | Command:
    logger.info(f"[tool monitor]执行工具,{request.tool_call['name']}")
    logger.info(f"[tool monitor]执行参数，{request.tool_call['args']}")
    try:
        result= handler(request)
        logger.info(f"[tool monitor]工具{request.tool_call['name']}执行成功")
        if request.tool_call['name'] == "fill_context_for_weather":
            request.runtime.context["weather"] = True

        return result
    except Exception as e :
        logger.error(f"工具{request.tool_call['name']}调用失败，原因：{str(e)}")
        raise e
@before_model
def log_before_model(state:AgentState,runtime: Runtime):
    logger.info(f"[log_before_model]即将调用模型，带有{len(state['messages'])}条消息。")
    logger.debug(f"[log_before_model]{type(state['messages'][-1]).__name__} | {(state['messages'][-1]).content.strip()}")
    return  None
@dynamic_prompt
def prompt_switch(request: ModelRequest):
    is_weather = request.runtime.context.get("weather", False)
    if is_weather:
        return load_weather_prompts()

    return load_system_prompt()



