from agents_ne import get_response
from pydantic import BaseModel
from fastapi import FastAPI, Depends
from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch
from utils import get_es_client
import torch
torch.classes.__path__ = []
from search_elasticsearch import lexical_search_hybrid, semantic_search_hybrid,reciprocal_rank_fusion
app=FastAPI(title="AI Agent ChatBot")

class Request(BaseModel):
    prompt: str

@app.post("/chat")
async def chat_endpoint(request: Request):
    if not request:
        return {"error": "request IS NULL"}
    
    responses = await get_response(request.prompt)
    return responses[-2]            # lấy response cuối cùng không phải chữ APPROVE


class Request_Search(BaseModel):
    # es: Elasticsearch
    search_query: str
    top_k: int
    index_name: str

def get_model():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    return SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2").to(device)

@app.post("/hybrid_search")
async def get_hybrid_search(request_search: Request_Search, model: SentenceTransformer = Depends(get_model)):
    es = get_es_client(max_retries=2, sleep_time=1)
    lexical_hits = await lexical_search_hybrid(es, request_search.search_query, top_k=request_search.top_k, INDEX_NAME=request_search.index_name)
    semantic_hits = await semantic_search_hybrid(es, request_search.search_query, top_k=request_search.top_k, model=model, INDEX_NAME=request_search.index_name)
    combined_results = reciprocal_rank_fusion(lexical_hits=lexical_hits, semantic_hits=semantic_hits, k=60, top_k=request_search.top_k)
    return combined_results if combined_results else 'No results found'

#Step3: Run app & Explore Swagger UI Docs
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9999)