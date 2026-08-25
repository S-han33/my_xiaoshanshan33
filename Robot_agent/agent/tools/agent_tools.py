from langchain_core.tools import tool
import random
from rag.rag_service import RagSummarize


rag = RagSummarize()
order_progress = {}
mock_data = [
    {"status": "到达当地中转站", "time": "2025-08-21 22:00"},
    {"status": "配送中", "time": "2025-08-22 10:15"},
    {"status": "已签收", "time": "2025-08-22 14:30"},
]
@tool(description="从向量存储中检索参考资料")
def rag_summarize(query: str):
    return rag.rag_summarize(query)


@tool(description="根据运单号查询最新的物流状态")
def fetch_tracking(tracking_number: str):
    # 首次查询该订单 → 从第一步开始允许选择
    if tracking_number not in order_progress:
        order_progress[tracking_number] = 0  # 初始阶段为0

    # 下次可选的最小阶段就是当前已记录的阶段
    min_stage = order_progress[tracking_number]

    # 只从 >= min_stage 的选项里随机挑
    available = mock_data[min_stage:]
    record = random.choice(available)

    # 如果抽到了更新的阶段,就更新记录
    stage_index = mock_data.index(record)
    order_progress[tracking_number] = stage_index

    return f"您订单{tracking_number}的最新进度：{record['status']} - {record['time']}"

@tool(description="获取用户所在城市的名称，以纯字符串形式返回")
def get_user_location() -> str:
    return random.choice(["深圳", "合肥", "杭州","北京","上海","浙江"])

@tool(description="获取指定城市的天气，以消息字符串的形式返回")
def get_weather(city: str) -> str:
    return f"城市{city}天气为晴天，气温26摄氏度，空气湿度50%，南风1级，AQI21，最近6小时降雨概率极低"

@tool(description="无入参，无返回值，调用后触发中间件自动为报告生成的场景动态注入上下文信息，为后续提示词切换提供上下文信息")
def fill_context_for_weather():
    return "fill_context_for_weather已调用"


if __name__ == '__main__':
    result = fetch_tracking.func("7811293942888")  # ← 用 .func 访问原始函数
    print(result)

    result2 = fetch_tracking.func("7811293942888")
    print(result2)  # 同一单再查,看状态机是否前进