from pydantic import BaseModel
from typing import Optional
from fastapi import FastAPI
from chatbot_processing import ChatBot
from pdf_manager import pdf_parser_nodes_index
from utils import get_es_client

app = FastAPI(title="Multi-agent-chatbot")
es = get_es_client(max_retries=2, sleep_time=1)
multi_agent_chatbot = ChatBot(es=es)

class Request(BaseModel):
    prompt: str
    session_id_choiced: Optional[str] = None
    tmp_file_path: Optional[str] = None

@app.post("/chat")
async def chat(request: Request):
    responses = await multi_agent_chatbot.get_response(request.prompt, request.session_id_choiced, request.tmp_file_path)
    return responses

# class Request_pdf(BaseModel):
#     tmp_file_path: str

# @app.post('/parser_index')
# def parser_index(request: Request_pdf):
#     pdf_parser_nodes_index(tmp_file_path=request.tmp_file_path, es=es)
#     return {"message": "Parsing successful"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9999)