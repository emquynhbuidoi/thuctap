from elasticsearch import Elasticsearch
from config import INDEX_NAME_DEFAULT, INDEX_NAME_N_GRAM, INDEX_NAME_EMBEDDING, INDEX_NAME_HYBRID
from utils import get_es_client
from sentence_transformers import SentenceTransformer
from sentence_transformers import SentenceTransformer
import torch
import asyncio

async def lexical_search_hybrid(es: Elasticsearch,search_query: str, top_k: int):
    query = {
        "multi_match": {
            "query": search_query,
            "fields": ['title', 'content']  
        }
    }
    results = es.search(
        index=INDEX_NAME_HYBRID,
        body={
            "query": query,
            "_source": {"excludes": ["embedding_field"]},                   # Loại bỏ "embedding_field" khỏi results search
            "size": top_k
         }
    )
    hits = results['hits']['hits']
    max_bm25_score = max([hit["_score"] for hit in hits], default=1.0)
    for hit in hits:
        hit['_normalized_score'] = hit['_score'] / max_bm25_score
    return hits

async def semantic_search_hybrid(es: Elasticsearch, search_query: str, top_k: int, model: SentenceTransformer):
    query = {
        "knn": {
            "field": "embedding_field",
            "query_vector": model.encode(search_query),
            "k": 10_000
        }
    }
    results = es.search(
        index=INDEX_NAME_HYBRID,
        body={
            "query": query,
            "_source": {"excludes": ["embedding_field"]},                   # Loại bỏ "embedding_field" khỏi results search
            "size": top_k
         }
    )
    hits = results['hits']['hits']
    max_semantic_score = max([hit["_score"] for hit in hits], default=1.0)      # cosine
    for hit in hits:
        hit['_normalized_score'] = hit['_score'] / max_semantic_score
    return hits

def reciprocal_rank_fusion(lexical_hits, semantic_hits, k=60):
    rrf_score = {}          # Lưu các doc và tổng điểm khi tính rrf trên từng kiểu search
    for rank, hit in enumerate(lexical_hits, start=1):
        doc_id = hit["_id"]
        score = 1 / (k + rank)
        if doc_id in rrf_score:
            rrf_score[doc_id]['rrf_score'] += score
            rrf_score[doc_id]['lexical_score'] += hit['_normalized_score']
        else:
            rrf_score[doc_id] = {
                "title": hit['_source']['title'],
                "content": hit['_source']['content'],
                'lexical_score': hit['_normalized_score'],
                'semantic_score': 0,
                'rrf_score': score
            }

    for rank, hit in enumerate(semantic_hits, start=1):
        doc_id = hit["_id"]
        score = 1 / (k + rank)
        if doc_id in rrf_score:
            rrf_score[doc_id]['rrf_score'] += score
            rrf_score[doc_id]['semantic_score'] += hit['_normalized_score']
        else:
            rrf_score[doc_id] = {
                "title": hit['_source']['title'],
                "content": hit['_source']['content'],
                'lexical_score': 0,
                'semantic_score': hit['_normalized_score'],
                'rrf_score': score
            }
    
    sorted_results = sorted(rrf_score.values(), key=lambda x: x['rrf_score'], reverse=True)
    final_results = [item["content"] for item in sorted_results]
    return final_results

async def hybrid_search(*, search_query: str, top_k: int = 4, model: SentenceTransformer):
    es = get_es_client(max_retries=2, sleep_time=1)
    lexical_hits = await lexical_search_hybrid(es, search_query, top_k=top_k)
    semantic_hits = await semantic_search_hybrid(es, search_query, top_k=top_k, model=model)
    combined_results = reciprocal_rank_fusion(lexical_hits, semantic_hits, k=60)
    return combined_results if combined_results else 'No results found'
   
if __name__ == "__main__":
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    #VietNamese embedding: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2?library=sentence-transformers
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2").to(device)
    asyncio.run(hybrid_search(search_query="Thực tập", top_k=4, model=model))