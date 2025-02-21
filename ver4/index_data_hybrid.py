from utils import get_es_client
from elasticsearch import Elasticsearch
from config import INDEX_NAME_HYBRID
from tqdm import tqdm
from pprint import pprint
import json
import torch
from sentence_transformers import SentenceTransformer

def index_data(documents, model: SentenceTransformer):
    es = get_es_client(max_retries=5, sleep_time=5)
    _ = _create_index(es=es)
    _ = _insert_documents(es=es, documents=documents, model=model)
    pprint(f'Indexed {len(documents)} documents into Elasticsearch index "{INDEX_NAME_HYBRID}"')

def _create_index(es: Elasticsearch):
    es.indices.delete(index=INDEX_NAME_HYBRID, ignore_unavailable=True)
    return es.indices.create(
        index=INDEX_NAME_HYBRID,
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

def _insert_documents(es: Elasticsearch, documents, model: SentenceTransformer):
    operations = []
    # print("Inserting embedding field and doc...")
    for doc in tqdm(documents, total=(len(documents)), desc='Indexing documents'):
        operations.append({'index': {'_index': INDEX_NAME_HYBRID}})
        operations.append({
            **doc,
            "embedding_field": model.encode(doc['content'])
        })
    return es.bulk(operations=operations)


if __name__ == "__main__":
    print("hello w")
    with open("./data/tma_data.json", "r", encoding="utf-8") as f:
        documents = json.load(f)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    #VietNamese embedding: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2?library=sentence-transformers
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2").to(device)
    index_data(documents=documents, model=model)