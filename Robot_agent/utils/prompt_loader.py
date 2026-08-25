from utils.path_tool import get_abs_path
from utils.config_handler import prompt_conf
from utils.logger_handler import logger
def load_system_prompt():
    try:
        system_prompt_path = get_abs_path(prompt_conf["main_prompt_path"])
    except KeyError as e :
        logger.error(f"[load_system_prompt]在yaml配置项中没有main_prompt_path配置项")
        return e
    try:
        content = open(system_prompt_path, "r", encoding='utf-8').read()         #打印读取到的内容
        return content
    except Exception as e :
        logger.error(f"[load_system_prompt]解析系统提示词出错，{str(e)}")
        return e
def load_rag_prompt():
    try:
        rag_prompt_path = get_abs_path(prompt_conf["rag_summarize_path"])
    except KeyError as e:
        logger.error(f"[rag_prompt_path]在yaml配置项中没有rag_summarize_path配置项")
        return e
    try:
        content = open(rag_prompt_path, "r", encoding='utf-8').read()
        return content
    except Exception as e:
        logger.error(f"[rag_prompt_path]解析系统提示词出错，{str(e)}")
        return e
def load_weather_prompts():
    try:
        weather_prompt_path = get_abs_path(prompt_conf["weather_prompt_path"])
    except KeyError as e:
        logger.error(f"[load_weather_prompts]在yaml配置项中没有weather_prompt_path配置项")
        raise  e

    try:
        return  open(weather_prompt_path,"r",encoding="utf-8").read()
    except Exception as e:
        logger.error(f"[load_weather_prompts]解析天气生成提示词出错，{str(e)}")
        raise  e
if __name__ == '__main__':
    print(load_system_prompt())