from agents_ne import get_response
from pydantic import BaseModel
from typing import Optional
from fastapi import FastAPI
from elasticsearch_ne import HybridSearch
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
    return responses[-2]            # lấy response cuối cùng không phải chữ APPROVE

class Request_Search(BaseModel):
    search_query: str
    top_k: int
    index_name: str

@app.post("/hybrid_search")
async def get_hybrid_search(request_search: Request_Search):
    hybrid_search_class = HybridSearch()
    return await hybrid_search_class.hybrid_search(search_query=request_search.search_query, top_k=request_search.top_k, INDEX_NAME=request_search.index_name)
   
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9999)