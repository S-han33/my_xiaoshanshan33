FROM python:3.13-slim
WORKDIR /app

# 先单独装依赖（利用 Docker 层缓存：改代码不会重新下载依赖）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860
EXPOSE 8000
ENTRYPOINT ["python", "app.py"]

# 使用方法：
# docker run -p 7860:7860 your-image              # 默认启动app（Gradio）
# docker run -p 8000:8000 your-image python api.py # 启动API服务
