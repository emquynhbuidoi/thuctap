from utils import get_es_client
from elasticsearch import Elasticsearch
from config import INDEX_NAME_DEFAULT, INDEX_NAME_N_GRAM
from tqdm import tqdm
from pprint import pprint
import json

def index_data(documents, use_n_gram_tokenizer: bool = False):
    index_name = INDEX_NAME_N_GRAM if use_n_gram_tokenizer else INDEX_NAME_DEFAULT
    es = get_es_client(max_retries=5, sleep_time=5)
    _ = _create_index(es=es, use_n_gram_tokenizer=use_n_gram_tokenizer)
    _ = _insert_documents(es=es, documents=documents, use_n_gram_tokenizer=use_n_gram_tokenizer)
    pprint(f'Indexed {len(documents)} documents into Elasticsearch index "{index_name}"')

def _create_index(es: Elasticsearch, use_n_gram_tokenizer=False):
    tokenizer = 'n_gram_tokenizer' if use_n_gram_tokenizer else 'standard'
    index_name = INDEX_NAME_N_GRAM if use_n_gram_tokenizer else INDEX_NAME_DEFAULT

    es.indices.delete(index=index_name, ignore_unavailable=True)
    return es.indices.create(
        index=index_name,
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
    with open("./data/apod.json") as f:
        documents = json.load(f)
    
    index_data(documents=documents, use_n_gram_tokenizer=False)