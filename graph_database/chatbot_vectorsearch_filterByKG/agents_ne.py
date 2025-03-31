from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.base import TaskResult
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.agents import AssistantAgent
from azure.core.credentials import AzureKeyCredential
from autogen_core.tools import FunctionTool
from autogen_ext.models.azure import AzureAIChatCompletionClient
from tools import duckduck_search_tool, wiki_search_tool
from elasticsearch_ne import HybridSearch
from langfuse.decorators import observe, langfuse_context
from config import INDEX_NAME_PDF, INDEX_NAME_HYBRID, MODEL_CHAT_INPUT_COST, MODEL_CHAT_OUTPUT_COST, INDEX_NAME_MEMORY
from typing import Optional
from langfuse_ne import LangfuseHandler 
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType
from index_data_ne import IndexData
from azure.ai.contentsafety import ContentSafetyClient
from azure.core.exceptions import HttpResponseError
from azure.ai.contentsafety.models import AnalyzeTextOptions, TextCategory

from elasticsearch import Elasticsearch
from filter_by_KG import Filter_By_KG

class ResponseClass:
    def __init__(self, es: Elasticsearch):
        es = es
        self.langfuse_handler = LangfuseHandler()
        self.hybrid_search_class = HybridSearch(es=es)
        self.index4memoryAgent = IndexData(es=es)
        self.session_id_now = '1703'
        self.index4memoryAgent._delete_index(INDEX_NAME=INDEX_NAME_MEMORY)
        self.filter_by_kg = Filter_By_KG()
        
    @observe()
    async def get_rag_prompt(self, query: str, tmp_file_path: Optional[str] = None, entities_in_ques: str=''):
        """
            input: 
                query: str | là câu hỏi đầu vào của người dùng 
                tmp_file_path: Optional[str] | đường dẫn tới file pdf tạm thời để xử lý cần trích xuất pdf context không.
            output:
                augmented_query: str | là đầu ra của câu prompt
                    - Nếu hỏi dựa trên pdf thì câu prompt ban đầu đã chứa thông tin context nên return luôn.
                    - Nếu hỏi bình thường thì thực hiện RAG prompt bằng hybrid_search
        """
        # if "Thông tin cung cấp được lấy từ file:" in query:
        if tmp_file_path is not None:
            search_results = await self.hybrid_search_class.hybrid_search(query, top_k=3, INDEX_NAME=INDEX_NAME_PDF)
            final_results = [item["content"] for item in search_results]
            context_from_pdf = "\n".join(final_results)
            augmented_query = "Thông tin cần xác thực được lấy từ file: " + context_from_pdf + '\n Dựa vào file trả lời câu hỏi: ' + query
            return augmented_query, context_from_pdf
        
        search_results = await self.hybrid_search_class.hybrid_search(search_query=query, top_k=3, INDEX_NAME=INDEX_NAME_HYBRID)
        print("\n\nSearch_results: ", search_results)
        search_results_after_filter = []
        entities_in_docs = [item["entities_extracted"] for item in search_results]
        for idx, doc in enumerate(entities_in_docs):
            check = self.filter_by_kg.cypher_query_check(entities_in_ques, doc)
            if check == True:
                print("\nTRUE: ", search_results[idx])
                search_results_after_filter.append(search_results[idx])

        print("\n\nSearch_results_after_filter::: ", search_results_after_filter)
        final_results = [item["content"] for item in search_results_after_filter]
        retrieval_context = "\n".join(final_results)
        augmented_query = f"""Câu hỏi: {query}.\n Thông tin cần xác thực: {retrieval_context}"""
        return augmented_query, retrieval_context

    async def hybrid_search_tool_func(self, search_query: str):
        search_results = await self.hybrid_search_class.hybrid_search(search_query=search_query, top_k=3, INDEX_NAME=INDEX_NAME_HYBRID)
        final_results = [item["content"] for item in search_results]
        retrieval_context = "\n".join(final_results)
        return retrieval_context


    def analyze_content_safety(self, content: str):
        key = ''
        endpoint = "https://content-safety-sq2.cognitiveservices.azure.com/"
        client = ContentSafetyClient(endpoint, AzureKeyCredential(key))
        request = AnalyzeTextOptions(text=content)

        try:
            response = client.analyze_text(request)
        except HttpResponseError as e:
            print("Analyze text failed.")
            if e.error:
                print(f"Error code: {e.error.code}")
                print(f"Error message: {e.error.message}")
                raise
            print(e)
            raise

        hate_result = next(item for item in response.categories_analysis if item.category == TextCategory.HATE)
        self_harm_result = next(item for item in response.categories_analysis if item.category == TextCategory.SELF_HARM)
        sexual_result = next(item for item in response.categories_analysis if item.category == TextCategory.SEXUAL)
        violence_result = next(item for item in response.categories_analysis if item.category == TextCategory.VIOLENCE)
        
        is_safe = True
        if hate_result:
            print(f"Hate severity: {hate_result.severity}")
            is_safe = False
        if self_harm_result:
            print(f"SelfHarm severity: {self_harm_result.severity}")
            is_safe = False
        if sexual_result:
            print(f"Sexual severity: {sexual_result.severity}")
            is_safe = False
        if violence_result:
            print(f"Violence severity: {violence_result.severity}")
            is_safe = False
        
        return is_safe

    @observe(as_type="generation")
    async def get_response(self, prompt: str, session_id_choiced: Optional[str] = None, tmp_file_path: Optional[str] = None):
        """
            input:
                prompt: str | câu hỏi ban đầu của người dùng.
                session_id_choiced: Optional(str) | là 1 key thể hiện người dung đang chat với session nào.
                tmp_file_path: Optional(str) | đường dẫn tới file pdf tạm thời.
            output:
                response_list: list | là danh sách chứa câu hỏi người dùng và cuộc hội thoại giữa các agents (p/s: cẩu trả lời cuối cùng trong list là Phù hợp của Agent critic).
        """
        if prompt.strip() == "":
            return "Hỏi gì đó đi !!"

        # is_safe = analyze_content_safety(prompt)
        # if is_safe == False:
        #     return "Tôi không thể trả lời các thông tin nhạy cảm !!"
        duck_tool = FunctionTool(
            duckduck_search_tool, description="Hữu ích khi tìm kiếm thông tin từ DuckDuckGo, đặc biệt trong trường hợp không có thông tin xác thực."
        )
        # get_realinfo2TMA = FunctionTool(  
        #     hybrid_search_tool_func, description="Tìm kiếm các thông tin về công ty TMA."
        # )
        wiki_tool = FunctionTool(
            wiki_search_tool, description="Hữu ích khi tra cứu thông tin về các khái niệm, quốc gia, và tôn giáo từ Wikipedia."
        )
        
        ## LLM azure github
        GITHUB_TOKEN = ""
        client = AzureAIChatCompletionClient(
            # model="gpt-4o-mini",                  ##   
            model='gpt-4o',                       ##    
            # model='Meta-Llama-3.1-405B-Instruct', ## 
            # model="DeepSeek-R1",      
            # model="Mistral-large",                  ##            
            # model="Mistral-large-2407",                 ###
            # model="Meta-Llama-3.1-70B-Instruct",            ###
            # model="Meta-Llama-3-8B-Instruct",       ##
            # model='Meta-Llama-3.1-8B-Instruct',       ## 
            # model='Llama-3.3-70B-Instruct',               ## 
            endpoint="https://models.inference.ai.azure.com",
            credential=AzureKeyCredential(GITHUB_TOKEN),
            model_info={
                "json_output": True,
                "function_calling": True,
                "vision": False,
                "family": "unknown",
            }
        )


        is_long_term = True
        if session_id_choiced != self.session_id_now:
            self.session_id_now = session_id_choiced
            memory_docs = self.langfuse_handler.get_chats_memory_longterm(session_id=session_id_choiced)
            print("\n\nLONGTERM: ", memory_docs)
        else:
            is_long_term = False
            memory_docs = self.langfuse_handler.chats_memory_short_term
            print("\n\nShort TERM: ", memory_docs)
        chat_memory = None
        memories = []

        if len(memory_docs) > 0:
            if is_long_term:
                self.index4memoryAgent._delete_index(INDEX_NAME=INDEX_NAME_MEMORY)
                self.index4memoryAgent.index_data(documents=memory_docs, INDEX_NAME=INDEX_NAME_MEMORY)
            else:
                self.index4memoryAgent._insert_documents(documents=memory_docs, INDEX_NAME=INDEX_NAME_MEMORY)

            search_results = await self.hybrid_search_class.hybrid_search(search_query=prompt, top_k=3, INDEX_NAME=INDEX_NAME_MEMORY)
            memories = [item["content"] for item in search_results]
        print("\n\nmemories sẽ được chọn: ", memories)

        if len(memories) > 0: 
            chat_memory = ListMemory()
            for memory in memories[:3]:
                await chat_memory.add(MemoryContent(content=memory, mime_type=MemoryMimeType.TEXT))
        
        prompt_agent = AssistantAgent(
            name="prompt_agent_assistant",
            model_client=client,
            tools=[duck_tool, wiki_tool],
            description="Một prompt engineer",
            system_message="""Bạn chỉ là một người chọn ra thông tin xác thực từ 'thông tin cần xác thực và bộ nhớ' sao cho đúng với câu hỏi đã cho theo tiêu chí ngắn gọn, dễ hiểu.
                            - Nếu thông tin cần xác thực và thông tin trong bộ nhớ không đúng với câu hỏi, phải tìm kiếm trên website để cập nhật thông tin.
                            - Bạn không thể đặt câu hỏi mới và đưa ra câu trả lời.
                            - Hãy phản hồi theo định dạng sau:
                                    Câu hỏi: <Hãy nêu lại câu hỏi ban đầu của người dùng>. 
                                    Thông tin đã xác thực là: <chỉ chọn ra thông tin có thể dùng để trả lời câu hỏi và liệt kê theo từng ý>. 
                                hoặc
                                    Nếu câu hỏi theo kiểu cung cấp thông tin hoặc 1 hướng dẫn như: 'Hãy nhớ', 'Hãy trả lời theo' thì phải phản hồi 'Xin cảm ơn, Tôi đã ghi nhớ'.
                            """,
            memory=[chat_memory] if chat_memory is not None else None
        )
        chat_agent = AssistantAgent(
                            name="tma_assistant",
                            model_client=client,
                            description="Một nhân viên lễ tân chuyên nghiệp của công ty TMA.",
                            system_message="""Bạn là một nhân viên lễ tân chuyên nghiệp của công ty TMA, có nhiệm vụ đưa ra câu trả lời bằng tiếng Việt một cách ngắn gọn, chuyên nghiệp.
                                            **Mục tiêu:**
                                            - Có thể dùng thông tin có trong bộ nhớ và thông tin đã xác thực để trả lời câu hỏi.
                                            - Nếu không chắc chắn về câu trả lời thì phản hồi là: 'Hiện nay, tôi chưa có thông tin về câu hỏi này, hãy thử tìm kiếm trên website để cập nhật thông tin mới'.
                                            - Nêu nhận được phản hồi với nội dung như: 'Xin cảm ơn, Tôi đã ghi nhớ' thì trả lời lại là 'Phù hợp'.
                                            **Nguyên tắc làm việc:**
                                            - Đưa ra các câu trả lời có độ dài từ 3-4 câu rõ ràng, đúng trọng tâm câu hỏi.  
                                            - Tập trung vào nhiệm vụ, tránh lan man.
                                            - Xem xét các đề xuất trước khi đưa ra câu trả lời.  
                                            - Không tạo ra câu trả lời sai hoặc không liên quan đến câu hỏi.  
                                            """,
                            memory=[chat_memory] if chat_memory is not None else None
                    )
                                        # + Nếu câu trả lời không chính xác hoặc không liên quan. Hãy nhắc lại câu hỏi của người dùng kèm câu trả lời: "Hiện nay, tôi chưa có thông tin về câu hỏi này, hãy thử tìm kiếm trên website để cập nhật thông tin mới.".
        critic_agent = AssistantAgent(
                        name="critic",
                        model_client=client,
                        tools=[],
                        description="Một nhà phê bình giúp hệ thống đánh giá xem câu trả lời có phù hợp với câu hỏi chưa",
                        system_message="""Bạn là một nhà phê bình thông minh, có khả năng đánh giá xem câu trả lời có phù hợp với câu hỏi chưa.
                                    **Mục tiêu:**
                                    - Đánh giá xem câu trả lời có phù hợp với câu hỏi hay không.  
                                        + Nếu câu trả lời là không chính xác với câu hỏi hoặc "Hiện nay, tôi chưa có thông tin về câu hỏi này, hãy thử tìm kiếm trên website để cập nhật thông tin mới." hoặc nội dung tương tự Phản hồi 'Phù hợp'.  
                                    **Nguyên tắc làm việc:**
                                    - Bạn không thể đặt câu hỏi hay trả lời bất cứ câu hỏi nào.
                                    - Chỉ tập trung vào nhiệm vụ của bạn, không phản hồi các tin nhắn ngoài lề.  
                                    - Giữ phản hồi ngắn gọn, chính xác và đúng trọng tâm.  
                                    """,
                        # memory=[chat_memory] if chat_memory is not None else None
                    )
        entities_in_ques = self.filter_by_kg.extract_entities(prompt)
        rag_promt, contexts = await self.get_rag_prompt(query=prompt, tmp_file_path=tmp_file_path, entities_in_ques=entities_in_ques)

        text_termination = TextMentionTermination("Phù hợp")
        max_msg_termination = MaxMessageTermination(max_messages=17)
        combined_termination = max_msg_termination | text_termination
        team = RoundRobinGroupChat([prompt_agent, chat_agent, critic_agent], termination_condition=combined_termination)
        response_list = []
        prompt_tokens = 0
        completion_tokens = 0
        # async for message in team.run_stream(task=new_promt): 
        async for message in team.run_stream(task=rag_promt):  
            if isinstance(message, TaskResult):
                if message.stop_reason is None:
                    response_list.append("NONE")
            else:
                print(message)
                if getattr(message, 'type', None) == 'TextMessage':
                    response_list.append(message.content)
                prompt_tokens += message.models_usage.prompt_tokens if message.models_usage is not None else 0
                completion_tokens += message.models_usage.completion_tokens if message.models_usage is not None else 0
        
        self.langfuse_handler.update_observation_cost(
            model_name='MODEL_CHATGPT',
            input_token=prompt_tokens,
            output_token=completion_tokens,
            cost_input=MODEL_CHAT_INPUT_COST,
            cost_output=MODEL_CHAT_OUTPUT_COST
        )
        
        self.langfuse_handler.tmp_file_path = tmp_file_path          # Cập nhật kể cả có truyền tmp_file_path qua hay không để hệ thông khỏi bị lỗi os.remove
        self.langfuse_handler.update_current_trace(
            name="session_trace",
            session_id=session_id_choiced,
            input=prompt,
            output=response_list[-2]
        )
        self.langfuse_handler.trace_id = langfuse_context.get_current_trace_id()
        # Xử lý chấm điểm cho RAG
        # print("\n\ncontexts: ", contexts)
        # score_ragas = await langfuse_handler.score_with_ragas(query=prompt, context=contexts, answer=response_list[-2])
        # print("score_ragas: ", score_ragas)
        return response_list







