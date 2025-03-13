from agents_ne import get_response
from pydantic import BaseModel
from typing import Optional
from fastapi import FastAPI
from elasticsearch_ne import HybridSearch
from pdf_manager import pdf_parser_nodes_index

app=FastAPI(title="AI Agent ChatBot")

class Request(BaseModel):
    prompt: str
    session_id_choiced: Optional[str] = None
    tmp_file_path: Optional[str] = None

@app.post("/chat")
async def chat_endpoint(request: Request):
    if not request:
        return {"error": "request IS NULL"}
    responses = await get_response(request.prompt, request.session_id_choiced, request.tmp_file_path)
    if isinstance(responses, str):
        return responses
    return str(responses[-2])            # lấy response cuối cùng không phải chữ APPROVE


##############################################
class Request_pdf(BaseModel):
    tmp_file_path: str

@app.post('/parser_index')
def parser_index(request: Request_pdf):
    pdf_parser_nodes_index(tmp_file_path=request.tmp_file_path)
    return {"message": "Parsing successful"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9999)