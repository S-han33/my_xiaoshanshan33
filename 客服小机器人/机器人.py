import re
from unittest.mock import patch, Mock
from dotenv import load_dotenv
import os
from cozepy import Coze, TokenAuth, COZE_CN_BASE_URL

load_dotenv("") # 这里输入你的cozeAPI的密钥文件名字进去


# ========== Coze 配置 ==========
def get_coze_client():
    token = os.getenv("COZE_API_TOKEN")
    return Coze(auth=TokenAuth(token=token), base_url=COZE_CN_BASE_URL)


def call_coze_workflow(user_input: str) -> str:
    workflow_id = os.getenv("WORKFLOW_ID")
    if not workflow_id:
        return "❌ 工作流ID未配置"

    # 提取快递单号（假设是11位数字）
    match = re.search(r'\d{11}', user_input)
    快递单号 = match.group() if match else ""

    try:
        coze = get_coze_client()
        result = coze.workflows.runs.create(
            workflow_id=workflow_id,
            parameters={
                "input": user_input,      # 可以查看coze里面开始的变量名，然后进行修改，这里一般都是input。
                "logistic_code": 快递单号      # 提取出来的单号
            }
        )
        return result.data if result else "无返回结果"
    except Exception as e:
        return f"调用失败：{str(e)}"
# 方式一：直接 Mock 一个函数
def call_platform_api(order_no, platform):
    """这是商家要替换的 API 调用函数"""
    # 商家自己在这里写真实的 API 调用
    pass


# 你用 Mock 来模拟这个函数的行为
def test_with_mock():
    # 创建 Mock 对象，设置返回值
    mock_api = Mock()
    mock_api.return_value = {
        "status": "success",
        "order_exists": True,
        "platform": "taobao",
        "order_info": {
            "order_no": "TP123456",
            "product": "测试商品",
            "amount": 29.9,
            "order_date": "2026-01-01"
        }
    }

    # 用 Mock 替换真实函数
    with patch('__main__.call_platform_api', mock_api):
        # 现在调用 call_platform_api 会返回 Mock 数据，不会真的请求网络
        result = call_platform_api("TP123456", "taobao")
        print(result)  # 输出上面定义的假数据

        # 你的业务逻辑写在这里
        if result["order_exists"]:
            print(f"订单存在！商品：{result['order_info']['product']}")
        else:
            print("订单不存在")


# 运行测试
test_with_mock()

def fetch_orders_by_user(open_id):
    """
    根据 open_id 调用电商平台API，获取该用户的订单列表
    返回订单对象列表
    商家需要根据实际对接的电商平台实现
    """
    # TODO: 商家替换成真实的 API 调用
    # 这里是模拟数据，让代码先跑通

    # ===== 加这段模拟数据 =====
    模拟订单 = 模拟商品(
        名称="测试商品",
        品类="测试品类",
        退货政策="具体看详细页面",
        发货地="河北",
        商品描述="这是一个测试商品",
        快递="马上就到快递")
    return [模拟订单]


# 主程序
class 模拟商品:
    def __init__(self, 名称, 品类, 退货政策,发货地,商品描述,快递):
        self.名称 = 名称
        self.品类 = 品类
        self.退货政策 = 退货政策
        self.发货地 = 发货地
        self.商品描述 = 商品描述
        self.快递 = 快递



# 真实代码示例（商家自己写）：
# import requests
# response = requests.post(
#     "https://商家自己的API.com/orders",
#     headers={"Authorization": "Bearer 商家的API_KEY"},
#     json={"open_id": open_id}
# )
# orders_data = response.json()
# return [商品(**order) for order in orders_data]


def 识别意图(用户输入):
    """简单的关键词识别"""
    if  "质量" in 用户输入 or "哪里发货" in 用户输入 or "什么快递" in 用户输入 :
        return "售前"
    elif  "什么时候到" in 用户输入 or "停止不动" in  用户输入 or "到哪了" in 用户输入 or "快递" in 用户输入 :
        return "售中"
    elif "退货" in 用户输入 or "退款" in 用户输入 or "坏了" in 用户输入  :
        return "售后"
    else:
        return "转人工"  # 机器人都解决不了情况下转人工


def 售前处理(商品对象,用户输入):
    if "质量" in 用户输入:
        print("亲，每个人的感受都是不一样呢，咱家这家款式是最多人喜欢的哦，您可以买回去试试看哈")
    elif "哪里发货" in 用户输入:
        print(f"亲，我们是{商品对象.发货地}发货的哦~尽快拍下才能尽快收到商品哈")
    elif "什么快递" in 用户输入:
        print(f"亲，我们这边发的是{商品对象.快递}，会按照亲亲的地址选择就近安排的哦")
    else:
        reply = call_coze_workflow(用户输入)
        # 第三层：如果 Coze 也处理不了，它应该返回"转人工"
        if "转人工" in reply:
            print("很抱歉呢~这个问题有点复杂，正在为您'转接人工'客服，请稍等...")
            # TODO: 调用转人工 API


def 售中处理(商品对象,用户输入):
    if  "物流" in 用户输入 or "什么时候到" in 用户输入:
        print(f"亲亲，查到您的{商品对象.名称}订单已发货，预计3~5天内的呢，具体要看运输流程为准哈")
    elif "停止不动" in 用户输入:
        print("亲亲，若是物流一直停止不动5天以上，建议这边‘转人工’反馈给快递公司哦~")
    else:
        reply = call_coze_workflow(用户输入)
        # 第三层：如果 Coze 也处理不了，它应该返回"转人工"
        if "转人工" in reply:
            print("这个问题有点复杂，正在为您转接人工客服，请稍等...")
            # TODO: 调用转人工 API
        else:
            print(f"{reply}")
def 售后处理(商品对象,用户输入):
    if "退货" in 用户输入:
        print(f"亲亲~{商品对象.退货政策}。如果还需要售后，请提供订单截图并输入‘转人工’哦~")
    else:
        print("亲亲~售后问题需要人工处理，请您输入【转人工】，我们会第一时间为您对接专员~")
        # TODO: 调用转人工 API


# ========== 正式程序：给用户用的客服机器人（有交互）==========
def main():
    """用户交互的主程序"""
    print("\n=== 客服机器人 ===")


    # ===== 第一步：获取用户身份 =====
    # 商家需要实现这个函数，从登录态获取 open_id
    # 这里先用模拟数据，商家拿到代码后替换成真实的
    user_open_id = "模拟的用户ID_123456"  # TODO: 商家替换成真实的 open_id

    # ===== 第二步：查询订单（核心测试点）=====
    order_list = fetch_orders_by_user(user_open_id)
    # TODO: 商家需替换为真实订单API，并换成自己的商品类

    # 测试：订单是否存在？
    if not order_list:
        print("亲亲~您好，暂时查询不到您的订单。")
        print("可能的原因：1）您还没有下过单；2）账号绑定有误")
        print("如需进一步帮助，请‘转人工’客服。")

        # 订单不存在时，也可以继续让用户咨询售前问题
        print("\n不过，您也可以先咨询商品问题：")
        current_order = None  # 订单不存在，没有商品对象
    else:
        # 订单存在，取第一个（最新的）
        current_order = order_list[0]
        print(f"亲亲~查到您的订单【{current_order.名称}】，有什么可以帮您？")
    # 进入对话循环
    while True:
        用户问题 = input("\n您想问什么：")

        if 用户问题 == "quit":
            print("感谢光临，再见~")
            break

        意图 = 识别意图(用户问题)

        if 意图 == "售前":
            if current_order is None:
                售前处理(模拟商品("测试商品", "测试品类", "具体看详细页面", "河北", "这是一个测试商品", "马上就到快递"), 用户问题)
            else:
                售前处理(current_order, 用户问题)

        elif 意图 == "售中":
            售中处理(current_order, 用户问题)


        elif 意图 == "售后":
            售后处理(current_order, 用户问题)

        elif 意图 == "转人工":
            print("客服：正在为您转接人工...")
            # TODO: 商家自行接入转人工API
            # 示例：requests.post("https://商家自己的客服系统.com/transfer", json={"user_id": user_open_id})
        print("\n--- 回到订单查询 ---\n")  # 对话结束，重新查订单


# ========== 运行 ==========
if __name__ == "__main__":
    # test_with_mock()   # 已废弃
    main()