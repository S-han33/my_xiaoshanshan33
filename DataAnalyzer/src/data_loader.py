"""
数据加载与预处理模块
支持 CSV、Excel、JSON 格式的数据导入
"""

import pandas as pd
from typing import Tuple,Optional


class Dataloader:
    Data_formats = ["csv","xlsx","xls","json"]

    @staticmethod
    def detect_format(filename:str) ->str:
        ext = filename.rsplit(".",1)[-1].lower()
        if ext not in Dataloader.Data_formats:
            raise ValueError (f"不支持的文件格式: .{ext}，支持: {Dataloader.Data_formats}")
        return ext
    @staticmethod
    def load_file(file_obj, filename: str) :
        file = Dataloader.detect_format(filename)
        if file == "csv":
           df = pd.read_csv(file_obj)
        elif file in ("xlsx", "xls"):
            df = pd.read_excel(file_obj)
        elif file == "json":
            df = pd.read_json(file_obj)
        else:
            raise ValueError(f"不支持的文件格式: {file}")
        meta = Dataloader.get_info(df)
        return meta,df

    @staticmethod
    def get_info(df: pd.DataFrame):   #概况
        return {
            "shape": df.shape,
            "columns" : df.columns.tolist(),
            "dtypes" : df.dtypes.astype(str).to_dict(),
            "missing_count" :df.isnull().sum().to_dict(),
            "missing_pct": (df.isnull().sum()/len(df)*100).round(2).to_dict(),
            "numeric_columns": df.select_dtypes(include=["number"]).columns.tolist(),
            "categorical_columns" :df.select_dtypes(include=["object","category"]).columns.tolist(),
            "datetime_columns": df.select_dtypes(include=["datetime"]).columns.tolist(),
            "memory_usage": f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB",
        }

    @staticmethod
    def preview(df: pd.DataFrame):
        return df.head()

    @staticmethod
    def describe(df: pd.DataFrame):  #统计
        numeric = df.select_dtypes(include=["number"])
        if numeric.empty:
            return pd.DataFrame({"提示": ["数据集中没有数值列"]})
        return numeric.describe()

    @staticmethod
    def derive_column(df: pd.DataFrame, derived):  #新列
        if not isinstance(derived, dict) or not derived.get("expression"):
            return df
        df = df.copy()  # 复制一份算，不动原数据
        df[derived["name"]] = df.eval(derived["expression"])
        return df

    @staticmethod
    def clean_data(
        df: pd.DataFrame,
        drop_na: bool = False,
        fill_na_strategy: Optional[str] = None,
        fill_value: Optional[float] = None,
    ):
        df = df.copy()
        if drop_na:
            df = df.dropna()
            return df
        if fill_na_strategy:
            numeric_cols = df.select_dtypes(include=["number"]).columns
            for col in numeric_cols:
                if df[col].isnull().sum() > 0:
                    if fill_na_strategy == "mean":
                        df[col].fillna(df[col].mean(), inplace=True)
                    elif fill_na_strategy == "median":
                        df[col].fillna(df[col].median(), inplace=True)
                    elif fill_na_strategy == "mode":
                            df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else 0, inplace=True)
                    elif fill_na_strategy == "value" and fill_value is not None:
                        df[col].fillna(fill_value, inplace=True)
        return  df





