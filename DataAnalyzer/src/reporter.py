import pandas as pd
from datetime import  datetime

class Reporter:
    @staticmethod
    def generate(df:pd.DataFrame,
                 df_meta:dict,
                 analysis,filename: str = ""):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [ f"# 📊 DataWhisper 数据分析报告",
            f"",
            f"**生成时间**: {now}  ",]
        if filename:
            lines.append(f"**数据文件**:{filename}")
        lines.extend([f"**数据规模**: {df_meta['shape'][0]} 行 × {df_meta['shape'][1]} 列  ",
                      f"**内存占用**:{df_meta.get('memory_usage', 'N/A')}",
                      "",
                      "---",
                      "",
                      "## 📋 数据概览",
                      "",])
        lines.append("| 列名 | 数据类型 | 缺失数 | 缺失率 |")
        lines.append("|------|----------|--------|--------|")
        for col in df_meta["columns"]:
            dtype = df_meta["dtypes"].get(col,"unknown")
            missing_count = df_meta["missing_count"].get(col,0)
            missing_pct = df_meta["missing_pct"].get(col,0)
            lines.append(f"| {col} | {dtype} | {missing_count} | {missing_pct:.1f}% |")
        lines.extend(["", "## 📈 数据统计摘要", ""])
        numeric = df.describe()
        if not numeric.empty:
            lines.append("```")
            lines.append(numeric.to_string())
            lines.append("```")


        if analysis:
            lines.extend(["", "---", "", "## 💬 分析对话记录", ""])
            for i ,x in enumerate(analysis[-10:],1):# 最近10条
                lines.append(f"### Q{i}: {x.get('query', '')}")
                lines.append(f"**分析意图**: {x.get('intent', 'N/A')}  ")
                lines.append(f"**图表类型**: {x.get('chart_type', 'N/A')}  ")
                if x.get("insight"):
                    lines.append(f"**洞察**: {x['insight']}")
                lines.append("")

            lines.extend(
                [
                    "---",
                    "",
                    f"*报告由 [DataWhisper](https://github.com/S-han33/my_xiaoshanshan33/DataWhisper) 自动生成*",
                ])

        return "\n".join(lines)
    @staticmethod
    def export(report_text: str, filepath: str):
        with open(filepath,"w",encoding='utf-8')as f:
            f.write(report_text)
