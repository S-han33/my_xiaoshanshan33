# langchain客服.py
# 用LangChain增强客服机器人意图识别
# 每行都有详细注释

# ========== 导入部分 ==========
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_classic.chains import LLMChain
from langchain_classic.prompts import PromptTemplate
from langchain_community.llms import Ollama

# ========== 创建模型 ==========
# 使用本地Ollama模型（qwen2.5:0.5b）
llm = Ollama(model="qwen2.5:0.5b")

# ========== 对话记忆 ==========
# 保存最近10轮对话
memory = ConversationBufferWindowMemory(k=10)

# ========== 意图识别模板 ==========
意图模板 = """你是客服意图识别助手。根据用户输入判断意图。

意图分类：
- 售前：问价格、功能、库存、优惠、怎么买
- 售中：问发货、物流、到货时间、快递
- 售后：退货、换货、维修、退款、质量问题
- 转人工：闲聊、天气、其他问题

只回答一个词：售前、售中、售后、转人工

用户输入：{input}
意图："""

# ========== 创建意图识别链 ==========
意图链 = LLMChain(
    llm=llm,
    prompt=PromptTemplate.from_template(意图模板),
    memory=memory,
    verbose=False  # 关闭详细输出，减少乱码
)

# ========== 关键词兜底 ==========
# 小模型可能识别不准，用关键词补充判断
关键词规则 = {
    "售后": ["退货", "换货", "维修", "退款", "质量", "坏了", "破损", "投诉", "差评", "处理"],
    "售中": ["发货", "物流", "快递", "到货", "什么时候到", "几天到"],
    "售前": ["多少钱", "价格", "怎么买", "购买", "库存", "有货"],
}

def 关键词判断(用户输入):
    """用关键词快速判断意图（兜底方案）"""
    for 意图, 词列表 in 关键词规则.items():
        for 词 in 词列表:
            if 词 in 用户输入:
                return 意图
    return None  # 没匹配到关键词

# ========== 意图识别函数 ==========
def 识别意图(用户输入):
    """
    识别用户意图
    先用AI识别，识别不准时用关键词兜底
    """
    try:
        # 1. 先用关键词快速判断
        关键词结果 = 关键词判断(用户输入)
        if 关键词结果:
            return 关键词结果
        
        # 2. 关键词没匹配到，用AI识别
        result = 意图链.invoke({"input": 用户输入})
        意图 = result["text"].strip()
        
        # 3. 验证意图是否有效
        if 意图 in ["售前", "售中", "售后", "转人工"]:
            return 意图
        else:
            return "转人工"
    except Exception as e:
        print(f"AI识别出错：{e}")
        return "转人工"

# ========== 测试 ==========
if __name__ == "__main__":
    print("=" * 50)
    print("测试意图识别：")
    print("=" * 50)
    
    test_cases = [
        "这个多少钱？",
        "什么时候到？",
        "我想退货",
        "今天天气真好",
        "质量有问题",
        "怎么购买",
    ]
    
    for 输入 in test_cases:
        结果 = 识别意图(输入)
        print(f"输入：{输入} → 意图：{结果}")
    
    print("=" * 50)

# ========== 闲聊回复模板 ==========
闲聊模板 = """你是一个友好的客服助手。用户在和你闲聊，请用简洁友好的方式回复。
不要超过20个字。

用户说：{input}
回复："""

# 创建闲聊回复链
闲聊链 = LLMChain(
    llm=llm,
    prompt=PromptTemplate.from_template(闲聊模板),
    verbose=False
)

# ========== 闲聊回复函数 ==========
def 闲聊回复(用户输入):
    """
    用Ollama小模型回复闲聊问题
    比如"你好"、"你是谁"、"今天天气真好"等
    """
    try:
        result = 闲聊链.invoke({"input": 用户输入})
        回复 = result["text"].strip()
        return 回复
    except Exception as e:
        return "您好！请问有什么可以帮您的吗？"
