from config import INDEX_NAME_DEFAULT, INDEX_NAME_N_GRAM
from utils import get_es_client
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pprint

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get('/api/v1/regular_search/')
async def search(search_query, skip: int = 0, limit: int = 10):
    es = get_es_client(max_retries=2, sleep_time=1)

    response = es.search(
        index=INDEX_NAME_DEFAULT,
        body={
            "query": {
                'multi_match': {
                    "query": search_query,
                    "fields": ['title', 'explanation']
                }
            },
            "from": skip,
            "size": limit
         },
        filter_path=['hits.hits._source, hits.hits._score', 'hits.total']
    )
    return {'hits': response['hits']['hits']}

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