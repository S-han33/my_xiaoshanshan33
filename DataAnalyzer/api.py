import os
import shutil
import tempfile

import uvicorn
from fastapi import FastAPI, UploadFile
from pydantic import BaseModel

from src.agent.react_agent import ReactAgent
from src.agent import agent_tools
from src.data_loader import Dataloader
app = FastAPI(title="DataAnalyzer", version="1.0")
agent = ReactAgent()


class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat(req: ChatRequest):
    full_response = ""
    for chunk in agent.user_inquiry(req.message):
        full_response += chunk
    return {"status": 200, "reply": full_response.strip()}


@app.post("/upload")
def upload(file: UploadFile):
    """上传数据 → 落成临时文件 → 读进 pandas → 塞给工具状态"""
    suffix = os.path.splitext(file.filename)[1]  # 保留原后缀（.csv / .xlsx），pandas 靠它判断格式
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)  # 把上传的内存内容抄进临时文件
        tmp_path = tmp.name                 # 拿到临时文件在磁盘上的路径

    # 以下照 gradio_app 里 load_file 的样子：读数据 → 塞进 agent_tools.DATA
    meta, df = Dataloader.load_file(tmp_path, file.filename)
    agent_tools.DATA.update(df=df, meta=meta, filename=file.filename, history=[], last_fig=None)
    return {"status": 200, "msg": f"已加载 {file.filename}：{meta['shape'][0]} 行 × {meta['shape'][1]} 列"}


if __name__ == "__main__":
    # 改成 0.0.0.0，允许局域网访问
    uvicorn.run(app, host="0.0.0.0", port=8000)
