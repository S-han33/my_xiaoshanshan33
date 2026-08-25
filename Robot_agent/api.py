from fastapi import FastAPI
from pydantic import BaseModel
from agent.react_agent import ReactAgent
import uvicorn

app = FastAPI(title="云云客服后端", version="1.0")
agent = ReactAgent()


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
async def chat(req: ChatRequest):
    full_response = ""
    for chunk in agent.execute_stream([{"role": "user", "content": req.message}]):
        full_response = chunk

    return {"status": 200, "reply": full_response.strip()}


if __name__ == "__main__":
    # 改成 0.0.0.0，允许局域网访问
    uvicorn.run(app, host="0.0.0.0", port=8000)
