
from src.data_loader import Dataloader
from langchain_core.tools import tool
from src.visualizer import Visualizer

DATA = {"df": None, "meta": None, "filename": "", "history": [], "last_fig": None}

@tool(description="获取当前已上传数据集的概况：行列数、列名、各列类型、缺失值数量、内存占用。当用户询问数据长什么样、有哪些列、数据规模时调用")
def check_data_summary() -> str:
    meta = Dataloader.get_info(DATA["df"])   # df 从程序状态拿，不从模型拿
    return str(meta)

@tool(description="计算数值列的统计摘要：计数、均值、标准差、最小最大值、四分位数。当用户问平均值、最大最小值、数据分布时调用")
def compute_stats() -> str:
    return str(Dataloader.describe(DATA["df"]))


@tool(description="按表达式计算新列。expression 由已有列名组成，例如 语文+数学+英语。当用户要总分、平均分等数据里没有的指标时调用")
def derive_column(name: str, expression: str) -> str:
    df_new = Dataloader.derive_column(DATA["df"], {"name": name, "expression": expression})
    DATA["df"] = df_new    # 新列写回状态，这样后面的画图工具才能用"总分"这列
    return f"已创建新列 '{name}'，前3行示例：{df_new[name].head(3).tolist()}"


@tool(description="生成图表。chart_type 可选 bar/line/scatter/pie/histogram/box。当用户要看图、对比、趋势、占比时调用")
def plot_chart(chart_type: str, x_column: str, y_column: str, group_column: str = "", title: str = "") -> str:
    fig = Visualizer.create_chart(
        df=DATA["df"], chart_type=chart_type,
        x_column=x_column, y_column=y_column,
        group_column=group_column or None, title=title or "数据分析图表",
    )
    DATA["last_fig"] = fig    # 图存进状态，等界面来取
    return f"已生成{chart_type}图：x={x_column}，y={y_column}，图已展示在界面上"
