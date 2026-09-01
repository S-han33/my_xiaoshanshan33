"""
LLM 智能分析引擎
将用户的自然语言问题转化为数据分析操作
"""

import json
import os
import re
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
load_dotenv()

class LLMEngine:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        if not self.api_key or self.api_key == "your-api-key-here":
            raise ValueError("LLM_API_KEY 未配置或仍为占位符，请检查 .env 文件")
        self.base_url = os.getenv("LLM_BASE_URL")
        if not self.base_url:
            raise ValueError("LLM_BASE_URL 未配置，请检查 .env 文件")
        self.model = os.getenv("LLM_MODEL")
        if not self.model:
            raise ValueError("LLM_MODEL 未配置，请检查 .env 文件")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.prompt_path = Path(__file__).parent / "prompt" / "prompt.txt"
    def _data_context(self, df_meta: dict) -> str:
        lines = [
            f"数据集形状: {df_meta['shape'][0]} 行 × {df_meta['shape'][1]} 列",
            f"列名列表: {', '.join(df_meta.get('columns',[ ]))}",
            f"数值列: {', '.join(df_meta.get('numeric_columns', []))}",
            f"类别列: {', '.join(df_meta.get('categorical_columns', []))}",
            "",
            "各列数据类型:",
        ]
        for x, y in df_meta.get("dtypes", {}).items():
            lines.append(f"  - {x}: {y}")
        return "\n".join(lines)
    def analyze_query(self, query: str, df_meta: dict):
        data_context = self._data_context(df_meta)
        system_prompt = self.prompt_path.read_text(encoding="utf-8").replace("{data_context}", data_context)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[ # type: ignore
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                temperature=0.1,
                max_tokens=500,
            )

            content = response.choices[0].message.content.strip()
            # 尝试提取 JSON（处理可能包含 markdown 代码块的情况）
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                result["_raw_response"] = content
                return result
            else:
                raise ValueError(f"模型未返回有效 JSON，原始回复: {content}")

        except Exception as e:
            raise ValueError(f"LLM 调用失败: {e}")

    def generate_insight(self, query: str, df_meta: dict, analysis_result: dict):
        data_context = self._data_context(df_meta)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[# type: ignore
                    {
                        "role": "system",
                        "content": f"你是一个数据分析专家。根据分析结果，用中文给出简洁的数据洞察（2-4句话），指出关键发现和趋势。\n\n数据集信息:\n{data_context}",
                    },
                    {
                        "role": "user",
                        "content": f"用户问题: {query}\n分析结果: {json.dumps(analysis_result, ensure_ascii=False)}",
                    },
                ],
                temperature=0.3,
                max_tokens=300,
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            raise ValueError(f"LLM 洞察生成失败: {e}")


