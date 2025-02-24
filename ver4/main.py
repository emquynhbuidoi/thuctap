from config import INDEX_NAME_DEFAULT, INDEX_NAME_N_GRAM, INDEX_NAME_EMBEDDING, INDEX_NAME_HYBRID
from utils import get_es_client
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pprint
import calendar
from elasticsearch import Elasticsearch

from sentence_transformers import SentenceTransformer
import torch

app = FastAPI()
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"]
# )

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
#VietNamese embedding: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2?library=sentence-transformers
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2").to(device)

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

async def semantic_search_hybrid(es: Elasticsearch, search_query: str, top_k: int):
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
    return sorted_results
    
@app.get('/api/v1/hybrid_search')
async def hybrid_search(search_query, limit: int = 10):
    es = get_es_client(max_retries=2, sleep_time=1)
    lexical_hits = await lexical_search_hybrid(es, search_query, limit)
    semantic_hits = await semantic_search_hybrid(es, search_query, limit)
    combined_results = reciprocal_rank_fusion(lexical_hits, semantic_hits, k=60)
    return combined_results
   


@app.get('/api/v1/semantic_search')
async def semantic_search(search_query, skip: int = 0, limit: int = 10, year: int | None = None, month: int | None = None, day: int | None = None ):
    es = get_es_client(max_retries=2, sleep_time=1)
    query = {
        "bool": {
            "must": [
                {
                    "knn": {
                        "field": "embedding_field",
                        "query_vector": model.encode(search_query),
                        "k": 10_000
                    }
                }
            ]
        }
    }

    if year:
        query['bool']['filter'] = {                 # https://www.elastic.co/guide/en/elasticsearch/reference/current/query-filter-context.html
            "range": {
                "collection_date": {
                    "gte": f"{year}-01-01",
                    "lte": f"{year}-12-31",
                    "format": "yyyy-MM-dd"
                }
            }
        }
    if month:
        last_day = calendar.monthrange(year, month)[1]
        query['bool']['filter'] = {               
            "range": {
                "collection_date": {
                    "gte": f"{year}-{month:02d}-01",
                    "lte": f"{year}-{month:02d}-{last_day}",
                    "format": "yyyy-MM-dd"
                }
            }
        }
    if day:
        specific_date = f"{year}-{month:02d}-{day:02d}"
        query['bool']['filter'] = {               
            "term": {
                "collection_date": specific_date
            }
        }

    response = es.search(
        index=INDEX_NAME_EMBEDDING,
        body={
            "query": query,
            "_source": {"excludes": ["embedding_field"]},                   # Loại bỏ "embedding_field" khỏi results search
            "from": skip,
            "size": limit
         },
        filter_path=['hits.hits._source, hits.hits._score', 'hits.total']
    )
    total_hits = get_total_hits(response)
    return {
        "len(RESULTS)": total_hits,
        'RESULTS': response['hits'].get("hits", []),
    }

@app.get('/api/v1/regular_search')
async def regular_search(search_query, skip: int = 0, limit: int = 10, year: int | None = None, month: int | None = None, day: int | None = None ):
    es = get_es_client(max_retries=2, sleep_time=1)
    query = {
        "bool": {
            "must": [
                {
                    "multi_match": {
                        "query": search_query,
                        "fields": ['title', 'content']  
                    }
                }
            ]
        }
    }

    if year:
        query['bool']['filter'] = {                 # https://www.elastic.co/guide/en/elasticsearch/reference/current/query-filter-context.html
            "range": {
                "collection_date": {
                    "gte": f"{year}-01-01",
                    "lte": f"{year}-12-31",
                    "format": "yyyy-MM-dd"
                }
            }
        }
    if month:
        last_day = calendar.monthrange(year, month)[1]
        query['bool']['filter'] = {               
            "range": {
                "collection_date": {
                    "gte": f"{year}-{month:02d}-01",
                    "lte": f"{year}-{month:02d}-{last_day}",
                    "format": "yyyy-MM-dd"
                }
            }
        }
    if day:
        specific_date = f"{year}-{month:02d}-{day:02d}"
        query['bool']['filter'] = {               
            "term": {
                "collection_date": specific_date
            }
        }
    response = es.search(
        index=INDEX_NAME_N_GRAM,
        body={
            "query": query,
            "from": skip,
            "size": limit
         },
        filter_path=['hits.hits._source, hits.hits._score', 'hits.total']
    )
    total_hits = get_total_hits(response)
    return {
        "len(RESULTS)": total_hits,
        'RESULTS': response['hits'].get("hits", []),
    }

def get_total_hits(response):
    return response['hits']['total']['value']

@app.get('/api/v1/get_docs_per_year_count/')
async def get_docs_per_year_count(search_query: str):
    es = get_es_client(max_retries=2, sleep_time=1)
    query = {
        "bool": {
            "must": [
                {
                    "multi_match": {
                        "query": search_query,
                        "fields": ['title', 'content']  
                    }
                }
            ]
        }
    }
    response = es.search(
        index=INDEX_NAME_N_GRAM,
        body={
            "query": query,
            "aggs": {
                "gom_doc_theo_tung_nam": {
                    "date_histogram": {                 #https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations-bucket-datehistogram-aggregation.html
                        "field": "collection_date",
                        "calendar_interval": "year", # Group by year
                        "format": "yyyy"
                    }
                }
            }
        },
        filter_path=["aggregations.gom_doc_theo_tung_nam"]
    )
    # return response
    return {"DOCS_PER_YEAR": extrac_docs_per_year(response)}

def extrac_docs_per_year(response):
    aggregations = response.get("aggregations", {})
    docs_per_year = aggregations.get("gom_doc_theo_tung_nam", {})
    buckets = docs_per_year.get("buckets", [])
    return {bucket['key_as_string']: bucket["doc_count"] for bucket in buckets}






















# # import asyncio
# # print(asyncio.run(search('ma', 0, 10)))
if __name__ == "__main__":
    es = get_es_client(max_retries=2, sleep_time=1)
    hybrid_search("Thực tập", limit=4)
#     query = {
#         "bool": {
#             "must": [
#                 {
#                     "multi_match": {
#                         "query": "t",
#                         "fields": ['title', 'content']  
#                     }
#                 }
#             ]
#         }
#     }
#     resp2 = es.indices.refresh(
#         index=INDEX_NAME_HYBRID
#     )
#     print("Refresh: ", resp2)
#     response = es.search(
#         index=INDEX_NAME_HYBRID,
#         body={
#             "query": {
#                 'match_all': {
#                 }
#             },
#             # "query": query,
#             "from": 1,
#             "size": 1
#          },
#         filter_path=['hits.hits._source, hits.hits._score']
#     )
#     print("\nLen of embedding field: ", len(response.body['hits']['hits'][0]['_source']['embedding_field']))
#     print(response.body)
