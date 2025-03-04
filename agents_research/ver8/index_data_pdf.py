from utils import get_es_client
from elasticsearch import Elasticsearch
from config import INDEX_NAME_PDF
from tqdm import tqdm
from pprint import pprint
import json
import torch
from sentence_transformers import SentenceTransformer
from typing import List

def index_data(documents: list[dict], model: SentenceTransformer):
    es = get_es_client(max_retries=5, sleep_time=5)
    _ = _create_index(es=es)
    _ = _insert_documents(es=es, documents=documents, model=model)
    # pprint(f'Indexed {len(documents)} documents into Elasticsearch index "{INDEX_NAME_PDF}"')

    # # es.indices.refresh(index=INDEX_NAME_PDF) 
    # response = es.search(
    #     index=INDEX_NAME_PDF,
    #     body={
    #         "query": {'match_all': {}}
    #     }
    # )
    count_response = es.count(index=INDEX_NAME_PDF)
    print("Số tài liệu trong index:", count_response["count"])


def _create_index(es: Elasticsearch):
    es.indices.delete(index=INDEX_NAME_PDF, ignore_unavailable=True)
    return es.indices.create(
        index=INDEX_NAME_PDF,
        body = {
            "mappings": {
                "properties":{
                    "embedding_field":{
                        "type": "dense_vector"
                    }
                }
            },
            "settings": {
                "analysis": {
                    "analyzer": {
                        "default": {                                # đặt default để esearch áp dụng tokenizer ngram lên tất cả các field.
                            "type": "custom",
                            'tokenizer': "n_gram_tokenizer",
                            "filter": ["lowercase"]                 # Chuyển thành chữ thường khi lưu + khi search chuyển truy vấn thành chữ thường https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-lowercase-tokenfilter.html
                        }
                    },
                    "tokenizer":{
                        "n_gram_tokenizer": {
                            "type": "edge_ngram",
                            "min_gram": 1,
                            "max_gram": 20,
                            "token_chars": ['letter', 'digit']
                        }
                    }
                }
            }
        }
    )

def _insert_documents(es: Elasticsearch, documents: List[dict], model: SentenceTransformer):
    operations = []
    # print("Inserting embedding field and doc...")
    for doc in tqdm(documents, total=(len(documents)), desc='Indexing documents'):
        operations.append({'index': {'_index': INDEX_NAME_PDF}})
        operations.append({
            'title': doc['title'],
            'content': doc['content'],
            'collection_date': doc['collection_date'],
            "embedding_field": model.encode(doc['content'])
        })
    # print("operations: ", operations)
    return es.bulk(operations=operations, refresh=True)

