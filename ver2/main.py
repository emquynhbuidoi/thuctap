from config import INDEX_NAME_DEFAULT, INDEX_NAME_N_GRAM
from utils import get_es_client
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pprint
import calendar

app = FastAPI()
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"]
# )

@app.get('/api/v1/regular_search')
async def search(search_query, skip: int = 0, limit: int = 10, year: int | None = None, month: int | None = None, day: int | None = None ):
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
        index=INDEX_NAME_DEFAULT,
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
        index=INDEX_NAME_DEFAULT,
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






















# import asyncio
# print(asyncio.run(search('ma', 0, 10)))
# if __name__ == "__main__":
#     es = get_es_client(max_retries=2, sleep_time=1)
#     response = es.search(
#         index=INDEX_NAME_DEFAULT,
#         body={
#             "query": {
#                 'match_all': {
#                 }
#             },
#             "from": 1,
#             "size": 2
#          },
#         filter_path=['hits.hits._source, hits.hits._score']
#     )
#     print(response.body['hits']['hits'])