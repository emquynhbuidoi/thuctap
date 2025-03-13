# 1. Agents Research
## ngày 14/3 (agents_research/ver12)
### - Hoàn thiện hệ thống chatbot tma info.
### - Tích hợp Memory autogent | Truy vấn các câu hỏi, câu trả lời theo session hiện tại -> Lưu câu hỏi và tách câu trả lời theo từng fact(câu) rồi chuyển về dạng docs -> Lưu vào es -> Dùng HybridSearch để tìm các câu phù hợp với câu hỏi của người dùng hiện tại -> Chuyển thành MemoryContent -> Truyền memory đó vào prompt_agent_assistant và tma_assistant.
* Ảnh Demo Memory autogen:
<div align="center">
  <img src="https://github.com/user-attachments/assets/e6b390c5-cfb1-44e3-aeea-38d78180c2f9" width="80%">
  <img src="https://github.com/user-attachments/assets/da0b5c3f-d14b-4719-b9e6-51d3190289a1)" width="80%">
</div>


## ngày 12/3 
### - Sửa lại code (cấu trúc multi-agents, fastapi).
### - Tích hợp Memory autogent, tích hợp Azure Content-safety để kiểm nội dung hội thoại người dùng.
* Ảnh Demo Memory autogen và Content safety:
<div align="center">
  <img src="https://github.com/user-attachments/assets/78954a9f-faeb-453e-b718-3a41901a4c8e" width="80%">
  <img src="https://github.com/user-attachments/assets/cf903168-e1d0-4d94-b644-72e9c7a925f6" width="80%">
</div>


## ngày 7/3 (agents_research/ver11)
### - Hoàn thiện code phù hợp với pipeline
### - Tích hợp Ragas để đánh giá RAG các phương pháp được chọn: LLMContextPrecisionWithoutReference (đánh giá context truy xuất có tốt hay không) + Faithfulness (đánh giá câu trả lời có liên quan đến context không) + Relevance (để đánh giá câu trả lời có liên quan đến câu hỏi hay không ) => đánh giá câu trả lời có hiệu quả và chính xác với câu hỏi hay không.
* Ảnh Demo hệ thống, và điểm số đánh giá bằng Ragas:
<div align="center">
  <img src="https://github.com/user-attachments/assets/0d5dd600-8d7a-4cac-ba74-693a600be212" width="80%">
  <img src="https://github.com/user-attachments/assets/4efc4ec3-0603-4e71-9040-b64f905c0485" width="80%">
</div>

## ngày 4/3 (agents_research/ver9)
### - Cấu trúc lại file code theo dạng class...
### - Quản lý các file pdf tải lên với langfuse
* Ảnh minh hoạ quản lý file pdf:
<div align="center">
  <img src="https://github.com/user-attachments/assets/382d40d8-56ef-446c-a65b-5e475b1fe6a2" width="80%">
  <img src="https://github.com/user-attachments/assets/8e8f8225-c1e9-403e-bee2-45dd741dc043" width="80%">
</div>



## ngày 4/3 (agents_research/ver8)
### - Quản lý cost api LLM với langfuse (đánh giá cost dựa vào token input và token ouput) sau đó langfuse sẽ trực quan thành biểu đồ
### - Quản lý phiên hội thoại (session) với langfuse: người dùng có thể xem lại các session cũ rồi tiếp tục chat với phiên đó hoặc chat với session
* Ảnh minh hoạ quản lý cost:
<div align="center">
  <img src="https://github.com/user-attachments/assets/72239313-000a-4458-99f1-7ff85048d4ff" width="80%">
</div>
* Ảnh minh hoạ quản lý session
<div align="center">
  <img src="https://github.com/user-attachments/assets/c0916f68-730a-467f-a90b-44c51f9373e9" width="80%">
</div>

## ngày 3/3 (agents_research/ver7)
### - Xây dựng pipeline xử lý PDF file: pdf file -> LlamaParse -> Chunking(SemanticSplitterNodeParser) -> index_data(elsearch) -> hybrid_search -> context  -> agents processing 
* Kết quả demo:
<div align="center">
  <img src="https://github.com/user-attachments/assets/e860ed74-6794-4eff-bee7-99fa9aad9093" width="80%">
  <img src="https://github.com/user-attachments/assets/ebaf45f0-50d0-484d-92b7-561ef3167a12" width="80%">
</div>

## ngày 28/2 (agents_research/ver6)
### - Kết hợp Langfuse để quan sát kết quả trả về của agents theo từng traces và từng section
### - Build pipeline agent-chat: prompt -> get_rag_prompt(elasticsearch) -> get_anew_prmopt(prompt_agent_assistant | tools(duckduckgo, elsearch))-> answer(agent tma_assistant) -> critic (critic_agent)

* Question and Answer:
<div align="center">
  <img src="https://github.com/user-attachments/assets/e1daef4c-b015-4855-8023-f4a70d0892c8" width="80%">
</div>
* Output RAG Prompt:
<div align="center">
  <img src="https://github.com/user-attachments/assets/841fc376-0df0-4dd7-bf23-9826bcf6c7f4" width="80%">
</div>
* Output get_anew_prmopt from prompt_agent_assistant:
<div align="center">
  <img src="https://github.com/user-attachments/assets/20a04c65-7724-41a7-8c5d-1d751615abbc" width="80%">
</div>

## ngày 27/2 (agents_research/ver5)
### - Thực hiện chia code chatbot agent thành front_end, back_end, giao tiếp với nhau bằng fastapi.

## ngày 26/2 (agents_research/ver4)
### - Build Chatbot agent với TMA info
### - Sử dụng 2 tool (get_asearch duckduckgo và hybrid_search_tool_func elasticsearh) để tìm kiếm thông tin. Bên cạnh đó kết hợp với get_rag_prompt để chỉnh sửa promts nhắc cho chatbot ưu tiên trả lời theo thông tin đã lưu trước ở elasticSeach.
* Kết quả chạy thử
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
* Kết quả sử dụng Function Tool
<div align="center">
  <img src="https://github.com/user-attachments/assets/9799986f-f509-4abb-87a3-38c8451a1feb" width="80%">
  <img src="https://github.com/user-attachments/assets/4ec93f65-8e2f-48f7-86e8-ccfcc78195e3" width="80%">
</div>
* Kết quả sử dụng Agentic RAG 1 chiều
<div align="center">
  <img src="https://github.com/user-attachments/assets/8f3bf3b6-6565-4b07-bae9-4a8d9a078d90" width="80%">
  <img src="https://github.com/user-attachments/assets/3bf17173-5549-49da-9ebe-6ad018a62eda" width="80%">
</div>






# 2. Elasticsearch Research
## ngày 21/2 (ver4)
### - Thực hiện Hybrid Searching với data TMA information. 
### - Sử dụng thuật toán Reciprocal Rank Fusion (RRF) để kết hợp 2 cách seach là lexical_search và semantic_search.   
* kết quả chạy khi tìm kiếm "các sự kiện ở TMA":  
 + Với kết quả trả về đầu tiên thiên về lexical_score sẽ cho ra kết quả tìm kiếm theo từ khoá sự kiện.
 + Với kết quả thứ trả về thứ 2, ta thấy không có bất kỳ từ khoá tìm kiếm nào ở kết quả, nhưng hệ thống vẫn cho ra được sự kiện là "cuộc thi ảnh". Nhờ vào semantic_search tìm kiếm theo ngữ nghĩa.
<div align="center">
  <img src="https://github.com/user-attachments/assets/2a04f4e1-62d4-4d09-863f-6945ebb30547" width="80%">
  <img src="https://github.com/user-attachments/assets/e6f38cbf-4405-4afa-aa91-4da489b0b50e" width="80%">
</div>


## ngày 20/2 (ver3)
### - Thực hiện search matching ngram tokenization với data TMA information. 
### - Thực hiện senmatic seach with dense_vector với data TMA information.  
* kết quả chạy với search matching ngram tokenization
<div align="center">
  <img src="https://github.com/user-attachments/assets/876ac175-306e-4283-b537-792e5e161d7d" width="80%">
  <img src="https://github.com/user-attachments/assets/18b914aa-b085-484c-946d-8ad4bdc145d5" width="80%">
</div>
* kết quả chạy với senmatic seach with dense_vector
<div align="center">
  <img src="https://github.com/user-attachments/assets/75386108-f121-4dc7-b037-379aa343e64f" width="80%">
  <img src="https://github.com/user-attachments/assets/b0d8a10d-7949-44b6-b576-b6446740259a" width="80%">
</div>


## ngày 19/2 (ver2)
### - Thu thập dữ liệu TMA infomation (tiếng việ) bằng scraping (793 docs). 
### - Chạy elasticsearch (dùng multi_match | filter (range)), tìm kiếm theo từ khoá, tìm kiếm theo ngày tháng năm.  
* kết quả chạy
<div align="center">
  <img src="https://github.com/user-attachments/assets/8c05321a-03ee-4860-b29a-29691ce3592d" width="80%">
  <img src="https://github.com/user-attachments/assets/b1091594-4b3b-4fab-b864-593bc5cfc0aa" width="80%">
</div>

## ngày 18/2 (ver1)
### - Chạy elasticsearch (dùng multi_match | search matching) kết hợp fastapi trên data có sẳn 
* kết quả chạy
<div align="center">
  <img src="https://github.com/user-attachments/assets/26855439-2ec3-4c87-b73d-117a64051f09" width="80%">
  <img src="https://github.com/user-attachments/assets/753919fe-5256-4978-ab63-1329c938725c" width="80%">
</div>

## ngày 17/2 (elasticsearch.ipynb)
### - Demo KNN search trên tập data tiếng việt ở mục 10, file elacsticseach.ipynb:
mode VietNamese embedding trên hugging face: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2?library=sentence-transformers
(demo chạy CPU)


