from utils import get_es_client
from elasticsearch import Elasticsearch
from config import INDEX_NAME_DEFAULT, INDEX_NAME_N_GRAM
from tqdm import tqdm
from pprint import pprint
import json

def index_data(documents, use_n_gram_tokenizer: bool = False):
    es = get_es_client(max_retries=5, sleep_time=5)
    _ = _create_index(es=es, use_n_gram_tokenizer=use_n_gram_tokenizer)
    _ = _insert_documents(es=es, documents=documents, use_n_gram_tokenizer=use_n_gram_tokenizer)
    index_name = INDEX_NAME_N_GRAM if use_n_gram_tokenizer else INDEX_NAME_DEFAULT
    pprint(f'Indexed {len(documents)} documents into Elasticsearch index "{index_name}"')

def _create_index(es: Elasticsearch, use_n_gram_tokenizer=False):
    tokenizer = 'n_gram_tokenizer' if use_n_gram_tokenizer else 'standard'
    index_name = INDEX_NAME_N_GRAM if use_n_gram_tokenizer else INDEX_NAME_DEFAULT

    es.indices.delete(index=INDEX_NAME_N_GRAM, ignore_unavailable=True)
    es.indices.delete(index=INDEX_NAME_DEFAULT, ignore_unavailable=True)
    return es.indices.create(
        index=index_name,
        settings = {
            "analysis": {
                "analyzer": {
                    "default": {                                # đặt default để esearch áp dụng tokenizer ngram lên tất cả các field.
                        "type": "custom",
                        'tokenizer': tokenizer,
                        "filter": ["lowercase"]                 # Chuyển thành chữ thường khi lưu + khi search chuyển truy vấn thành chữ thường https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-lowercase-tokenfilter.html
                    }
                },
                "tokenizer":{
                    tokenizer: {
                        "type": "edge_ngram",
                        "min_gram": 1,
                        "max_gram": 20,
                        "token_chars": ['letter', 'digit']
                    }
                }
            }
        }
    )

def _insert_documents(es: Elasticsearch, documents, use_n_gram_tokenizer):
    operations = []
    index_name = INDEX_NAME_N_GRAM if use_n_gram_tokenizer else INDEX_NAME_DEFAULT
    for doc in tqdm(documents, total=(len(documents)), desc='Indexing documents'):
        operations.append({'index': {'_index': index_name}})
        operations.append(doc)
    return es.bulk(operations=operations)


if __name__ == "__main__":
    print("hello w")
    with open("./data/tma_data.json", "r", encoding="utf-8") as f:
        documents = json.load(f)
    
    index_data(documents=documents, use_n_gram_tokenizer=True)