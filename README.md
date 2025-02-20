# Elasticsearch Research
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


