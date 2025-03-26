from pydantic import BaseModel
from config import PROMPT_EXTRACT_4_RUN, PROMPT_EXTRACT_4_BUILD
from openai import OpenAI
from langchain_neo4j import Neo4jGraph

class Extract_Entity(BaseModel):
    name: str
    type: str

class Extract_entities(BaseModel):
    entities: list[Extract_Entity]

# class Relationship(BaseModel):
#     entity1: Extract_Entity
#     entity2: Extract_Entity
#     relationship: str

# class Extract_Entity_Relationship(BaseModel):
#     entities: list[Extract_Entity]
#     relationships: list[Relationship]

def extract_entities(client: OpenAI, doc):
    en_extracted = []
    response = client.beta.chat.completions.parse(
        model=model_name,
        messages=[
            {"role": "system", "content": PROMPT_EXTRACT_4_RUN},
            {"role": "user", "content": "INPUT: \n" + doc}
        ],
        response_format=Extract_entities
    )
    entities = response.choices[0].message.parsed.entities
    # relationships = response.choices[0].message.parsed.relationships
    print("\n\nEntity Defined")
    for entity in entities:
        if entity.name != 'tma' and f"(:{entity.type})" not in en_extracted:
            en_extracted.append(f"(:{entity.type})")
        print(f'ENTITY: (:{entity.type})')
        print(f'MERGE ({entity.name}:{entity.type} {{name: "{entity.name}"}})')

    # print("\n\nRelationship Defined")
    # for relationship in relationships:
    #     print(f'MERGE ({relationship.entity1.name})-[:{relationship.relationship}]->({relationship.entity2.name})')


    return en_extracted

if __name__ == '__main__':
    # question = "Chủ tịch của TMA là ai?"
    # docs1 = 'Chủ tịch tập đoàn TMA là chú Nguyễn Hữu Lệ'
    # docs2 = 'Chi phí phát triển phần mềm tại TMA phụ thuộc vào mô hình định giá (theo giờ, theo dự án, mô hình khác); liên hệ qua website tmasolutions để biết thêm chi tiết.'
    # docs3 = 'Yêu cầu đầu vào thực tập sinh tại TMA: sinh viên năm 3 trở lên, thực tập fulltime tối thiểu 3 tháng; hồ sơ gồm CV Tiếng Anh, Bảng điểm/Bằng cấp (nếu có) và Giấy giới thiệu thực tập.'
    # docs4 = "Hiện tại, ông Nguyễn Hữu Lệ đang giữ chức vụ chủ tịch của TMA"

    # question = "TMA có bao nhiêu cơ sở?"
    # docs1 = 'Hãy đăng ký ngay để có cơ hội là nhân viên chính thức của TMA.'
    # docs2 = 'TMA hiện tại có 12 văn phòng trong đó 6 văn phòng trong nước và 6 văn phòng ở nước ngoài'
    # docs3 = 'Giải bóng đá tại TMA vừa mới diễn ra vào ngày 25/03.'
    # docs4 = '12 cơ sở của TMA hiện đang hoạt động và ngày càng phát triển.'
    
    question = "TMA có bao nhiêu nhân viên?"
    docs1 = 'Chủ tịch tập đoàn TMA là chú Nguyễn Hữu Lệ'
    docs2 = 'Chi phí phát triển phần mềm tại TMA phụ thuộc vào mô hình định giá (theo giờ, theo dự án, mô hình khác); liên hệ qua website tmasolutions để biết thêm chi tiết.'
    docs3 = 'TMA hiện tại có 6 cơ sở trên cả nước bao gồm 4,000 kỹ sư tài năng.'
    docs4 = "Số nhân sự hiện tại của TMA là 4.000"

    token = '' 
    endpoint = "https://models.inference.ai.azure.com"
    model_name = "gpt-4o-mini"

    client = OpenAI(api_key=token, base_url=endpoint)
    uri = 'bolt://localhost:7687'
    username = 'neo4j'
    password = '123456789'
    kg = Neo4jGraph(url=uri,username=username,password=password)
    
    en_extracted_in_question = extract_entities(client=client, doc=question)
    docs_selected = []
    if len(en_extracted_in_question) > 0:
        for doc in [docs1, docs2, docs3, docs4]:
            en_extracted_in_docs = extract_entities(client=client, doc=doc)
            
            is_match = False
            for en_ques in en_extracted_in_question:
                for en_doc in en_extracted_in_docs:
                    cypher_query_code = "RETURN EXISTS {" + f"{en_ques}" + f"-[r]-" + f"{en_doc}" + "}"
                    result = list(kg.query(cypher_query_code)[0].values())[0]
                    print("\n\cypher_query_code: ", cypher_query_code, ' -> ', result)
                    is_match = result
                    if is_match == True:            # Nếu 2 entity có quan hệ
                        docs_selected.append(doc)
                        break
                    elif en_ques == en_doc :        # Nếu 2 entity giống nhau
                        docs_selected.append(doc)
                        is_match = True
                        break
                if is_match == True:
                    break
        
        print("DOCS sau khi loc la: ", docs_selected)
    else:
        print("Không có thực thể nào đc trích xuất ở question...")
