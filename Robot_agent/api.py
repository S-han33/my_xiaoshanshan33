import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from pydantic import BaseModel
from agent.react_agent import ReactAgent
import traceback
import uvicorn

app = FastAPI(title="云云客服后端", version="1.0")
agent = ReactAgent()


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
def chat(req: ChatRequest):
    full_response = ""
    try:
        for chunk in agent.execute_stream([{"role": "user", "content": req.message}]):
            full_response = chunk
    except Exception as e:
        # 临时调试：把真实错误返回给前端，方便定位
        return {
            "status": 500,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }

    return {"status": 200, "reply": full_response.strip()}


if __name__ == "__main__":
    # 改成 0.0.0.0，允许局域网访问
    uvicorn.run(app, host="0.0.0.0", port=8000)
