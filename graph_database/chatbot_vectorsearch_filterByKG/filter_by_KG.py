from pydantic import BaseModel
from config import PROMPT_EXTRACT_4_RUN,PROMPT_EXTRACT_4_BUILD
from openai import OpenAI
from langchain_neo4j import Neo4jGraph

class Extract_Entity(BaseModel):
    name: str
    type: str

class Extract_entities(BaseModel):
    entities: list[Extract_Entity]

class Filter_By_KG:
    def __init__(self):
        token = '' 
        endpoint = "https://models.inference.ai.azure.com"
        # model_name = "gpt-4o-mini"
        self.model_name = "gpt-4o"
        self.client = OpenAI(api_key=token, base_url=endpoint)
        uri = 'bolt://localhost:7687'
        username = 'neo4j'
        password = '123456789'
        self.kg = Neo4jGraph(url=uri,username=username,password=password)

    def extract_entities(self, doc:str):
        en_extracted = []
        response = self.client.beta.chat.completions.parse(
            model=self.model_name,
            messages=[
                {"role": "system", "content": PROMPT_EXTRACT_4_RUN},
                {"role": "user", "content": "INPUT: \n" + doc}
            ],
            response_format=Extract_entities
        )
        entities = response.choices[0].message.parsed.entities
        print("\n\nEntity Defined")
        for entity in entities:
            # if entity.name != 'tma' and f"(:{entity.type})" not in en_extracted:
            if f"(:{entity.type})" not in en_extracted:
                en_extracted.append(f"(:{entity.type})")
                # en_extracted.append(f'(:{entity.type} {{name: "{entity.name}"}})')
            print(f'ENTITY: (:{entity.type})')
            print(f'MERGE ({entity.name}:{entity.type} {{name: "{entity.name}"}})')
        return en_extracted

    def cypher_query_check(self, ens_que:str, ens_doc:str):
        for en_que in ens_que:
            for en_doc in ens_doc:
                cypher_query_code = "RETURN EXISTS {" + f"{en_que}" + f"-[r]-" + f"{en_doc}" + "}"
                result = list(self.kg.query(cypher_query_code)[0].values())[0]
                print("\ncypher_query_code: ", cypher_query_code, ' -> ', result)
                if result == True:
                    return result
                elif en_que == en_doc:
                    return True
        
        return False   
