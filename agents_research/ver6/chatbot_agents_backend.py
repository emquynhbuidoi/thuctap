from agents_ne import get_response
from pydantic import BaseModel
from fastapi import FastAPI
app=FastAPI(title="AI Agent ChatBot")

class Request(BaseModel):
    prompt: str

@app.post("/chat")
async def chat_endpoint(request: Request):
    if not request:
        return {"error": "request IS NULL"}
    
    responses = await get_response(request.prompt)
    return responses[-2]            # lấy response cuối cùng không phải chữ APPROVE

#Step3: Run app & Explore Swagger UI Docs
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9999)