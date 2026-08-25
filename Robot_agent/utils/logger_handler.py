from datetime import datetime
import os ,logging

from utils.path_tool import get_abs_path

log_root = get_abs_path("logs")

os.makedirs(log_root, exist_ok = True)

log_time = logging.Formatter("%(asctime)s - %(filename)s - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s")

def get_logging(
        name:str = "agent" , console_level:str = logging.INFO , file_level:str = logging.DEBUG ,log_file = None
)-> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if logger.handlers:
        return logger

    processor_content = logging.StreamHandler()
    processor_content.setLevel(console_level)
    processor_content.setFormatter(log_time)
    logger.addHandler(processor_content)
    if not log_file:
        log_file = os.path.join(log_root,f"{name}_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler =logging.FileHandler(log_file,encoding= "utf-8")
    file_handler.setLevel(file_level)
    file_handler.setFormatter(log_time)
    logger.addHandler(file_handler)
    return logger

logger = get_logging()


if __name__ == '__main__':
    logger.info("信息日志")
    logger.error("错误日志")
    logger.warning("警告日志")
    logger.debug("调试日志")
