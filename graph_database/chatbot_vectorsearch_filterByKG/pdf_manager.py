import os
from dotenv import load_dotenv
load_dotenv()
from llama_cloud_services import LlamaParse
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
embed_model  = HuggingFaceEmbedding(model_name = "paraphrase-multilingual-MiniLM-L12-v2")

import re  
# from utils import get_es_client
from elasticsearch import Elasticsearch
from index_data_ne import IndexData
from datetime import datetime
from config import INDEX_NAME_PDF

def pdf_parser_nodes_index(tmp_file_path, es: Elasticsearch):
    """
        input: 
            source_file: streamlit.UploadedFile | là file pdf của người dùng tải lên được quản lý bởi streamlit
        main:
            Hàm xử lý file chuyển pdf sang text bằng LlamaParse. 
            Thực hiện semantic chunking bằng  SemanticSplitterNodeParser của LlamaIndex.
            Sau đó, gọi hàm index_data để chuyển các node vào elasticSearch
    """
    # if source_file == None:
    #     return None
    
    parser = LlamaParse(result_type='text')
    # with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
    #     tmp_file.write(source_file.read())
    file_path = tmp_file_path

    documents = parser.load_data(file_path)

    splitter = SemanticSplitterNodeParser(
        buffer_size=1, breakpoint_percentile_threshold=40, embed_model=embed_model)
    nodes = splitter.get_nodes_from_documents(documents)
    documents_node = []
    for i, node in enumerate(nodes):
        content = node.get_content()
        # 1. Loại bỏ khoảng trắng đầu/cuối
        content = content.strip()
        # 2. Thay nhiều khoảng trắng thành 1 khoảng trắng
        content = re.sub(r"\s+", " ", content)
        # 3. Chuẩn hóa xuống dòng: thay nhiều dòng trống bằng 1 dòng
        content = re.sub(r"\n\s*\n+", "\n", content)
        print(f"\n\nNode {i+1}: ", content) 
        documents_node.append(
            {
                'title': "Doc From Pdf File",
                'content': content,
                'collection_date': str(datetime.today().strftime("%Y-%m-%d"))
            }
        )
    # es = get_es_client(max_retries=2, sleep_time=1)
    index = IndexData(es=es)
    index.index_data(documents_node, INDEX_NAME=INDEX_NAME_PDF)

    
    

