# 1. Agents Research
## ngày 27/2 (agents_research/ver5)
### - Thực hiện chia code chatbot agent thành front_end, back_end, giao tiếp với nhau bằng fastapi. Kết hợp Langfuse để quan sát kết quả trả về của agents


## ngày 26/2 (agents_research/ver4)
### - Build Chatbot agent với TMA info
### - Sử dụng 2 tool (get_asearch duckduckgo và hybrid_search_tool_func elasticsearh) để tìm kiếm thông tin. Bên cạnh đó kết hợp với get_rag_prompt để chỉnh sửa promts nhắc cho chatbot ưu tiên trả lời theo thông tin đã lưu trước ở elasticSeach.
Kết quả chạy thử
<div align="center">
  <img src="https://github.com/user-attachments/assets/fc22c65e-81bc-448f-a86f-07180d7aa80d" width="80%">
  <img src="https://github.com/user-attachments/assets/c3e4fd2f-6e9b-40ad-ae4f-d36378cd027f" width="80%">
  <img src="https://github.com/user-attachments/assets/49ef0ccf-d447-486d-85fd-19ecb3d3e957" width="80%">
</div>



## ngày 25/2 (agents_research/ver3)
### - Tìm hiểu và xây dựng các hệ thông Human-in-the-loop, Meta Prompting System, Multi agent Group Chat, Metacognition AI Agents




## ngày 24/2 (agents_research/ver2)
### - Thực hiện sử dụng Function Tool (tự tạo truy vẫn dữ liệu mẫu, api duckduckgo search)
### - Xây dựng Agentic RAG kết hợp ElasticSearch (hybrid search) trên dữ liệu TMA infomation. Nhưng chỉ truy xuất 1 chiều (vì chưa thực thiện đánh giá độ hài lòng kết quả RAG, rồi cho quay lại phân tích với LLM) 
Kết quả sử dụng Function Tool
<div align="center">
  <img src="https://github.com/user-attachments/assets/9799986f-f509-4abb-87a3-38c8451a1feb" width="80%">
  <img src="https://github.com/user-attachments/assets/4ec93f65-8e2f-48f7-86e8-ccfcc78195e3" width="80%">
</div>


Kết quả sử dụng Agentic RAG 1 chiều
<div align="center">
  <img src="https://github.com/user-attachments/assets/8f3bf3b6-6565-4b07-bae9-4a8d9a078d90" width="80%">
  <img src="https://github.com/user-attachments/assets/3bf17173-5549-49da-9ebe-6ad018a62eda" width="80%">
</div>

# 2. Elasticsearch Research
## ngày 21/2 (ver4)
### - Thực hiện Hybrid Searching với data TMA information. 
### - Sử dụng thuật toán Reciprocal Rank Fusion (RRF) để kết hợp 2 cách seach là lexical_search và semantic_search.   
kết quả chạy khi tìm kiếm "các sự kiện ở TMA":  
 + Với kết quả trả về đầu tiên thiên về lexical_score sẽ cho ra kết quả tìm kiếm theo từ khoá sự kiện.
 + Với kết quả thứ trả về thứ 2, ta thấy không có bất kỳ từ khoá tìm kiếm nào ở kết quả, nhưng hệ thống vẫn cho ra được sự kiện là "cuộc thi ảnh". Nhờ vào semantic_search tìm kiếm theo ngữ nghĩa.
<div align="center">
  <img src="https://github.com/user-attachments/assets/2a04f4e1-62d4-4d09-863f-6945ebb30547" width="80%">
  <img src="https://github.com/user-attachments/assets/e6f38cbf-4405-4afa-aa91-4da489b0b50e" width="80%">
</div>


## ngày 20/2 (ver3)
### - Thực hiện search matching ngram tokenization với data TMA information. 
### - Thực hiện senmatic seach with dense_vector với data TMA information.  
kết quả chạy với search matching ngram tokenization
<div align="center">
  <img src="https://github.com/user-attachments/assets/876ac175-306e-4283-b537-792e5e161d7d" width="80%">
  <img src="https://github.com/user-attachments/assets/18b914aa-b085-484c-946d-8ad4bdc145d5" width="80%">
</div>

kết quả chạy với senmatic seach with dense_vector
<div align="center">
  <img src="https://github.com/user-attachments/assets/75386108-f121-4dc7-b037-379aa343e64f" width="80%">
  <img src="https://github.com/user-attachments/assets/b0d8a10d-7949-44b6-b576-b6446740259a" width="80%">
</div>


## ngày 19/2 (ver2)
### - Thu thập dữ liệu TMA infomation (tiếng việ) bằng scraping (793 docs). 
### - Chạy elasticsearch (dùng multi_match | filter (range)), tìm kiếm theo từ khoá, tìm kiếm theo ngày tháng năm.  
kết quả chạy

<div align="center">
  <img src="https://github.com/user-attachments/assets/8c05321a-03ee-4860-b29a-29691ce3592d" width="80%">
  <img src="https://github.com/user-attachments/assets/b1091594-4b3b-4fab-b864-593bc5cfc0aa" width="80%">
</div>

## ngày 18/2 (ver1)
### - Chạy elasticsearch (dùng multi_match | search matching) kết hợp fastapi trên data có sẳn 
kết quả chạy

<div align="center">
  <img src="https://github.com/user-attachments/assets/26855439-2ec3-4c87-b73d-117a64051f09" width="80%">
  <img src="https://github.com/user-attachments/assets/753919fe-5256-4978-ab63-1329c938725c" width="80%">
</div>

## ngày 17/2 (elasticsearch.ipynb)
### - Demo KNN search trên tập data tiếng việt ở mục 10, file elacsticseach.ipynb:
mode VietNamese embedding trên hugging face: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2?library=sentence-transformers
(demo chạy CPU)


