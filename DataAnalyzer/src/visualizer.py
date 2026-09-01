"""
可视化图表生成模块
根据分析方案自动生成 Plotly 交互式图表
"""

import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any


class Visualizer:
    """智能可视化器：根据分析意图和数据自动选择并生成最佳图表"""

    @staticmethod
    def create_chart(
        df: pd.DataFrame,
        chart_type: str,
        x_column: Optional[str] = None,
        y_column: Optional[str] = None,
        group_column: Optional[str] = None,
        title: str = "数据分析图表",
        **kwargs,
    ) -> Optional[go.Figure]:
        """
        根据参数自动生成对应类型的图表
        """
        chart_methods = {
            "line": Visualizer._create_line_chart,
            "bar": Visualizer._create_bar_chart,
            "scatter": Visualizer._create_scatter_chart,
            "pie": Visualizer._create_pie_chart,
            "heatmap": Visualizer._create_heatmap,
            "histogram": Visualizer._create_histogram,
            "box": Visualizer._create_box_chart,
        }

        method = chart_methods.get(chart_type)
        if method:
            return method(df, x_column, y_column, group_column, title, **kwargs)
        return None

    @staticmethod
    def _create_line_chart(df, x, y, group, title, **kwargs):
        """折线图 — 适合趋势分析"""
        if group and group in df.columns:
            fig = px.line(df, x=x, y=y, color=group, title=title, markers=True)
        else:
            fig = px.line(df, x=x, y=y, title=title, markers=True)
        fig.update_layout(template="plotly_white", hovermode="x unified")
        return fig

    @staticmethod
    def _create_bar_chart(df, x, y, group, title, **kwargs):
        """柱状图 — 适合对比分析"""
        if group and group in df.columns:
            fig = px.bar(df, x=x, y=y, color=group, title=title, barmode="group")
        else:
            fig = px.bar(df, x=x, y=y, title=title)
        fig.update_layout(template="plotly_white")
        return fig

    @staticmethod
    def _create_scatter_chart(df, x, y, group, title, **kwargs):
        """散点图 — 适合相关性可视化"""
        if group and group in df.columns:
            fig = px.scatter(df, x=x, y=y, color=group, title=title, trendline="ols")
        else:
            fig = px.scatter(df, x=x, y=y, title=title, trendline="ols")
        fig.update_layout(template="plotly_white")
        return fig

    @staticmethod
    def _create_pie_chart(df, x, y, group, title, **kwargs):
        """饼图 — 适合占比展示"""
        if y is None:
            # 如果没有 Y，对 X 列计数
            value_counts = df[x].value_counts().reset_index()
            value_counts.columns = [x, "count"]
            fig = px.pie(value_counts, names=x, values="count", title=title)
        else:
            # 按 X 分组求 Y 的和
            agg_data = df.groupby(x)[y].sum().reset_index()
            fig = px.pie(agg_data, names=x, values=y, title=title)
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(template="plotly_white")
        return fig

    @staticmethod
    def _create_heatmap(df, x, y, group, title, **kwargs):
        """热力图 — 适合相关性矩阵"""
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.shape[1] < 2:
            fig = go.Figure()
            fig.add_annotation(
                text="需要至少 2 个数值列才能生成热力图",
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            )
            fig.update_layout(title=title, template="plotly_white")
            return fig

        corr_matrix = numeric_df.corr()
        fig = px.imshow(
            corr_matrix,
            text_auto=".2f",
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            title=title,
            aspect="auto",
        )
        fig.update_layout(template="plotly_white")
        return fig

    @staticmethod
    def _create_histogram(df, x, y, group, title, **kwargs):
        """直方图 — 适合分布分析"""
        col = x if x and x in df.select_dtypes(include=[np.number]).columns else y
        if col is None:
            col = df.select_dtypes(include=[np.number]).columns[0]

        if group and group in df.columns:
            fig = px.histogram(df, x=col, color=group, title=title, marginal="box", opacity=0.7)
        else:
            fig = px.histogram(df, x=col, title=title, marginal="box")
        fig.update_layout(template="plotly_white")
        return fig

    @staticmethod
    def _create_box_chart(df, x, y, group, title, **kwargs):
        """箱线图 — 适合异常值检测"""
        if group and group in df.columns:
            fig = px.box(df, x=group, y=y, title=title, points="outliers")
        elif x and x in df.columns:
            fig = px.box(df, x=x, y=y, title=title, points="outliers")
        else:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            fig = px.box(df, y=numeric_cols[:6], title=title, points="outliers")
        fig.update_layout(template="plotly_white")
        return fig

    @staticmethod
    def create_auto_eda_charts(df: pd.DataFrame) -> list:
        """
        自动生成探索性数据分析(EDA)图表套件
        返回多个图表的列表
        """
        charts = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

        # 1. 缺失值热力图
        if df.isnull().sum().sum() > 0:
            missing_pct = (df.isnull().sum() / len(df) * 100).reset_index()
            missing_pct.columns = ["列名", "缺失比例(%)"]
            missing_pct = missing_pct[missing_pct["缺失比例(%)"] > 0]
            fig_missing = px.bar(
                missing_pct,
                x="列名",
                y="缺失比例(%)",
                title="📊 缺失值分析",
                color="缺失比例(%)",
                color_continuous_scale="Reds",
            )
            fig_missing.update_layout(template="plotly_white")
            charts.append(("缺失值分析", fig_missing))

        # 2. 相关性热力图
        if len(numeric_cols) >= 2:
            corr = df[numeric_cols].corr()
            fig_corr = px.imshow(
                corr,
                text_auto=".2f",
                color_continuous_scale="RdBu_r",
                zmin=-1,
                zmax=1,
                title="🔗 相关性热力图",
                aspect="auto",
            )
            fig_corr.update_layout(template="plotly_white")
            charts.append(("相关性热力图", fig_corr))

        # 3. 数值列分布
        for col in numeric_cols[:4]:  # 最多展示前4个数值列
            fig_dist = px.histogram(
                df, x=col, title=f"📉 {col} 分布", marginal="box", nbins=30
            )
            fig_dist.update_layout(template="plotly_white")
            charts.append((f"{col} 分布", fig_dist))

        # 4. 类别列柱状图
        for col in categorical_cols[:2]:  # 最多展示前2个类别列
            if df[col].nunique() <= 20:
                vc = df[col].value_counts().nlargest(10).reset_index()
                vc.columns = [col, "count"]
                fig_bar = px.bar(vc, x=col, y="count", title=f"📊 {col} 频次统计 (Top 10)")
                fig_bar.update_layout(template="plotly_white")
                charts.append((f"{col} 频次", fig_bar))

        return charts