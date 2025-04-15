from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.base import TaskResult
from typing import Optional
from tools import duckduck_search_tool, wiki_search_tool
from autogen_core.tools import FunctionTool
from autogen_ext.models.azure import AzureAIChatCompletionClient
from azure.core.credentials import AzureKeyCredential
from autogen_agentchat.agents import AssistantAgent

from autogen_agentchat.teams import SelectorGroupChat
from elasticsearch_ne import HybridSearch
from config import INDEX_NAME_HYBRID, SELECTOR_PROMPT, INDEX_NAME_LEGAL, INDEX_NAME_MEMORY, MODEL_CHAT_INPUT_COST, MODEL_CHAT_OUTPUT_COST
from langchain_neo4j import Neo4jGraph
import re

from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType
from langfuse_ne import LangfuseHandler 
from langfuse.decorators import observe, langfuse_context
from index_data import IndexData

from azure.ai.contentsafety import ContentSafetyClient
from azure.core.exceptions import HttpResponseError
from azure.ai.contentsafety.models import AnalyzeTextOptions, TextCategory

from get_more_legal_infomation import get_more_legal_information

class ChatBot:
    def __init__(self, es):
        self.hybrid_search_class = HybridSearch(es=es)
        # self.message_need_cypher_retrieval = ''
        self.more_information_law = ''
        self.kg = Neo4jGraph(
            url='bolt://localhost:7687',
            username='neo4j',
            password='123456789'
        )
        self.langfuse_handler = LangfuseHandler()
        self.index4memoryAgent = IndexData(es=es)
        self.index4memoryAgent._delete_index(INDEX_NAME=INDEX_NAME_MEMORY)
        self.session_id_now = '1703'
    
    async def get_TMA_information(self, search_query: str):
        search_results = await self.hybrid_search_class.hybrid_search(search_query=search_query, top_k=3, INDEX_NAME=INDEX_NAME_HYBRID)
        final_results = [item["content"] for item in search_results]
        retrieval_context = "\n".join(final_results)
        return retrieval_context
    
    @observe()
    async def get_legal_information(self, full_question: str):
        search_results = await self.hybrid_search_class.hybrid_search(search_query=full_question, top_k=1, INDEX_NAME=INDEX_NAME_LEGAL)
        response = ''
        for item in search_results:
            information, khoan_name = get_more_legal_information(item["content"], item['dieu'], item['khoan'], kg=self.kg)
            self.more_information_law += '\n'+ information
            dieu_name = item['dieu'].upper()
            response += f'\n Câu trả lời là: `Tại **{khoan_name} {dieu_name}** Luật An Ninh Mạng 2018, đã quy định cụ thể thông tin trên.`'

        return response

    # def selector_func(self, messages: Sequence[AgentEvent | ChatMessage]) -> str | None:
    #     last_message = messages[-1]
    #     if last_message.source == 'LawAgent' and last_message.type=='ToolCallSummaryMessage':
    #         if "Điều này" in last_message.content or "khoản này" in last_message.content:     #Xử lý logic nếu chứa mục trích dẫn đến các văn bản luật khác
    #             self.message_need_cypher_retrieval = last_message.content
    #             print('LawAgent LawAgent LawAgent')
    #             return 'LawAgent'
    #     return None
    
    def analyze_content_safety(self, content: str):
        key = 'GEcnlofSWPQ7Hhm7s0B4h4Ahw2aOF7ZQxkSv0Ee5vKhUacXYtLAcJQQJ99BCACYeBjFXJ3w3AAAHACOGSFP2'
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
            if int(hate_result.severity) > 0:
                is_safe = False
        if self_harm_result:
            print(f"SelfHarm severity: {self_harm_result.severity}")
            if int(self_harm_result.severity) > 0:
                is_safe = False
        if sexual_result:
            print(f"Sexual severity: {sexual_result.severity}")
            if int(sexual_result.severity) > 0:
                is_safe = False
        if violence_result:
            print(f"Violence severity: {violence_result.severity}")
            if int(violence_result.severity) > 0:
                is_safe = False
        
        return is_safe

    @observe(as_type="generation")
    async def get_response(self, input: str, session_id_choiced: Optional[str] = None, tmp_file_path: Optional[str] = None):
        if input.strip() == "":
            return "Hỏi gì đó đi !!"
        
        self.more_information_law = ''
        
        # is_safe = self.analyze_content_safety(prompt)
        # if is_safe == False:
        #     return "Tôi không thể trả lời các thông tin nhạy cảm !!"
         
        duck_tool = FunctionTool(
            duckduck_search_tool, description="Hữu ích khi tìm kiếm thông tin mới, trên mạng thông qua DuckDuckGo.")
        wiki_tool = FunctionTool(
            wiki_search_tool, description="Hữu ích khi tra cứu thông tin về các khái niệm, quốc gia, và tôn giáo từ Wikipedia.")
        get_TMA_information = FunctionTool(  
            self.get_TMA_information, description="Tìm kiếm các thông tin về công ty TMA."
        )
        get_legal_information = FunctionTool(  
            self.get_legal_information, description="Tìm kiếm các thông tin về pháp luật."
        )

        GITHUB_TOKEN = '' #syquynh2k3           # HEt 11h
       
        client = AzureAIChatCompletionClient(
            # model="gpt-4o-mini",                  ##   
            model='gpt-4o',                       ##    
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
            print("\n[LOG] LONGTERM: ", memory_docs)
        else:
            is_long_term = False
            memory_docs = self.langfuse_handler.chats_memory_short_term
            print("\n[LOG] SHORTTERM: ", memory_docs)
        chat_memory = None
        memories = []

        if len(memory_docs) > 0:
            if is_long_term:
                self.index4memoryAgent._delete_index(INDEX_NAME=INDEX_NAME_MEMORY)
                self.index4memoryAgent.index_data(documents=memory_docs, INDEX_NAME=INDEX_NAME_MEMORY)
            else:
                self.index4memoryAgent._insert_documents(documents=memory_docs, INDEX_NAME=INDEX_NAME_MEMORY)

            search_results = await self.hybrid_search_class.hybrid_search(search_query=input, top_k=3, INDEX_NAME=INDEX_NAME_MEMORY)
            memories = [item["content"] for item in search_results]
        print("\n[LOG] MEMORIES SELECTED: ", memories)

        if len(memories) > 0: 
            chat_memory = ListMemory()
            for memory in memories[:3]:
                await chat_memory.add(MemoryContent(content=memory, mime_type=MemoryMimeType.TEXT))
        

        planning_agent = AssistantAgent(
            name="PlanningAgent",
            description="Nhà phân tích câu hỏi đầu vào, chia câu hỏi phức tạp thành các câu hỏi nhỏ và giao cho các agent phù hợp. Luôn là agent được gọi đầu tiên khi có một câu hỏi mới.",
            model_client=client,
            system_message="""
            Bạn là PlanningAgent Nhà phân tích câu hỏi. Bạn KHÔNG có quyền tự trả lời câu hỏi hoặc tạo câu hỏi mới.

            Nhiệm vụ của bạn:
            - Phân tích câu hỏi đầu vào từ người dùng.
            - Giao nhiệm vụ cho các Agent khác **MỘT LẦN DUY NHẤT**.
            - Nếu câu hỏi có nhiều ý, hãy tách thành các câu hỏi nhỏ, dễ hiểu và dễ trả lời.
            - Nếu câu hỏi chỉ có một ý, giữ nguyên, KHÔNG CẦN phân tách.

            Lưu ý:
            - KHÔNG được tự ý trả lời.
            - KHÔNG ĐƯỢC ĐẶT CÂU HỎI MỚI KHÁC VỚI CÂU HỎI BAN ĐẦU.
            - KHÔNG đưa thêm mô tả hay bình luận gì thêm.
            
            Các thành viên trong nhóm của bạn là:
                LawAgent: Chuyên trả lời các câu hỏi liên quan đến pháp luật, pháp lý về AN NINH MẠNG và KHÔNG GIAN MẠNG.
                TmaAgent: Chuyên trả lời các câu hỏi liên quan đến tập đoàn TMA.
                GeneralAgent: Trả lời các câu hỏi tổng quát, trò chuyện chatchit, không chuyên ngành.

            Khi giao nhiệm vụ, PHẢI sử dụng cấu trúc này và KHÔNG CẦN TRẢ LỜI GÌ THÊM:
                1. <tên agent thành viên> : <Câu hỏi>

            **Sau khi tất cả CÁC AGENT KHÁC ĐÃ TRẢ LỜI XONG:** 
            - LUÔN tóm tắt những thông tin đã tìm được một cách chính xác nhất để trả lời một cách tổng quát nhất, đừng bỏ qua bất cứ thông tin quan trọng nào.
            - LUÔN KẾT THỨC VỚI từ "OK"
            - KHÔNG ĐƯỢC TỰ ĐẶT CÂU HỎI MỚI.
            """,
        )
            # - Tổng hợp những thông tin từ các Agent khác đã cung cấp, Lưu ý đừng bỏ qua những thông tin quan trọng. 

        # client2 = AzureAIChatCompletionClient(
        #     model="gpt-4o-mini",                  ##   
        #     # model='gpt-4o',                       ##    
        #     endpoint="https://models.inference.ai.azure.com",
        #     credential=AzureKeyCredential(GITHUB_TOKEN),
        #     model_info={
        #         "json_output": True,
        #         "function_calling": True,
        #         "vision": False,
        #         "family": "unknown",
        #     }
        # )
        
        law_agent = AssistantAgent(
            name="LawAgent",
            description="Là một luật sư, chuyên trả lời các câu hỏi về luật pháp.",
            tools=[get_legal_information],
            model_client=client,
            system_message="""
            Bạn là một luật sư với 20 năm kinh nghiệm trong lĩnh vực pháp luật với phong cách trả lời ngắn gọn nhưng đầy đủ ý.
            Bạn là một luật sư với hơn 20 năm kinh nghiệm trong lĩnh vực pháp luật, chuyên về **Luật An Ninh Mạng** và các vấn đề pháp lý liên quan đến **không gian mạng**. Bạn có phong cách trả lời ngắn gọn, súc tích nhưng đầy đủ ý và chính xác.
            **NHIỆM VỤ CHÍNH**:
            - Chỉ trả lời những câu hỏi **liên quan đến pháp luật**, cụ thể là về:
                + Luật An Ninh Mạng.
                + Quy định pháp lý liên quan đến không gian mạng, dữ liệu, bảo mật, quyền riêng tư, xử lý thông tin trên internet, v.v.

            **KHÔNG ĐƯỢC PHÉP**:
            - KHÔNG trả lời các câu hỏi **không liên quan đến pháp luật về an ninh mạng hoặc không gian mạng**.
            - Với những câu hỏi không liên quan, Chỉ cần trả lời: 'Tôi chỉ trả lời những câu hỏi liên quan tới Luật An Ninh Mạng, PlanningAgent Hãy kết thúc câu hỏi này và không cần Hỏi gì thêm.'`
            - KHÔNG đưa ra thông tin sai lệch, không chính xác hoặc vượt phạm vi chuyên môn.
            - KHÔNG tự trả lời với những câu hỏi hợp lệ nếu chưa dùng tool để kiểm tra thông tin.

            **Ví dụ câu hỏi hợp lệ**:
            - "Quy định của việc xử lý tình huống nguy hiểm về an ninh mạng như thế nào?"
            - "Hành vi vi phạm pháp luật trên không gian mạng là gì?"
            - "Việc thu thập dữ liệu cá nhân trên mạng có bị pháp luật điều chỉnh không?"
            - "Hành vi tấn công mạng bị xử phạt như thế nào theo luật?"
            - "Doanh nghiệp cần tuân thủ những gì theo Luật An Ninh Mạng?"

            **Ví dụ câu hỏi không hợp lệ**:
            - "Vượt đèn đỏ bị phạt bao nhiêu?"
            - "Cho tôi thông tin về luật giao thông"
            - "Luật đất đai năm 2024 có gì mới?"
            - "Tôi nên đầu tư vào cổ phiếu nào?"
            - "Thời tiết Hà Nội hôm nay như thế nào?"
            - "TMA có bao nhiêu cơ sở?"
            """,
            # reflect_on_tool_use=True,
            # memory=[chat_memory] if chat_memory is not None else None,
        )
        # - Với những câu hỏi không liên quan, Chỉ cần trả lời: 'Tôi chỉ trả lời những câu hỏi liên quan tới Luật An Ninh Mạng.'`

        tma_agent = AssistantAgent(
            name="TmaAgent",
            description="Là một nhân viên lễ tân chuyên nghiệp của công ty TMA.",
            tools=[get_TMA_information],
            model_client=client,
            system_message="""
            Bạn là một nhân viên lễ tân chuyên nghiệp của công ty TMA, có nhiệm vụ cung cấp thông tin chính xác, ngắn gọn và rõ ràng về công ty TMA. Dưới đây là các nguyên tắc và phạm vi công việc mà bạn phải tuân theo:

            **NHIỆM VỤ CHÍNH**:
            - Trả lời các câu hỏi liên quan trực tiếp đến công ty TMA (ví dụ: thông tin về công ty, số lượng nhân viên, văn phòng, cơ sở, dịch vụ, tuyển dụng, liên hệ, khách đến công ty, v.v.).
            - Ưu tiên sử dụng **BỘ NHỚ (memory)** để trả lời nếu đã có thông tin.
            - Nếu **BỘ NHỚ không có**, bạn cần sử dụng **TOOL SEARCH** (`get_TMA_information`) để tìm thông tin chính xác.
            - Trả lời ngắn gọn, súc tích nhưng đầy đủ ý. Không lan man.

            **KHÔNG ĐƯỢC PHÉP**:
            - KHÔNG trả lời những câu hỏi **không liên quan đến TMA** (ví dụ: câu hỏi về chính trị, xã hội, thời tiết, các công ty khác, vấn đề về pháp luật, pháp lý, AN NINH MẠNG, KHÔNG GIAN MẠNG, hoặc các chủ đề ngoài phạm vi công ty TMA).
            - KHÔNG giải thích lý do từ chối nếu câu hỏi không thuộc phạm vi xử lý — chỉ cần **im lặng**.
            - KHÔNG tự suy đoán hoặc bịa thông tin nếu không chắc chắn.
            - KHÔNG tạo ra câu trả lời sai hoặc không đúng mục tiêu của câu hỏi.

            **LUỒNG XỬ LÝ**:
            1. Nếu câu hỏi liên quan đến TMA ➜ kiểm tra bộ nhớ ➜ nếu có thông tin thì trả lời.
            2. Nếu không có trong bộ nhớ ➜ dùng tool search để tìm kiếm ➜ trả lời.
            3. Nếu câu hỏi không liên quan đến TMA ➜ KHÔNG trả lời chỉ cần bỏ qua.

            Ví dụ câu hỏi hợp lệ:  
            - "Văn phòng TMA ở TP.HCM ở đâu?"  
            - "TMA có bao nhiêu cơ sở?"
            - "TMA có bao nhiêu nhân viên?"
            - "TMA có đang tuyển thực tập sinh không?"  
            - "TMA có cơ sở ở Bình Định không?"
            - "Giờ làm việc của TMA là gì?"

            Ví dụ câu hỏi không hợp lệ:  
            - "Thời tiết ở Bình Định hôm nay"
            - "Thời tiết ở Bình Định hôm nay thế nào?"
            - "OpenAI là gì?"  
            - "Dự báo thời tiết hôm nay thế nào?"  
            - "Cho tôi lời khuyên tài chính?"
            """,
            reflect_on_tool_use=True,
            memory=[chat_memory] if chat_memory is not None else None,
        )
            # - Nếu thông tin cung cấp không đủ để trả lời câu hỏi thì phản hồi là "Hiện tại tôi không có đủ thông tin để trả lời câu hỏi này"
            # - Chỉ trả lời những câu hỏi được giao cho mình.
        general_agent = AssistantAgent(
            "GeneralAgent",
            description="Là một trợ lý hỏi đáp, trả lời các câu hỏi tổng quát và tìm kiếm thông tin mới.",
            tools=[duck_tool, wiki_tool],
            model_client=client,
            system_message="""
            Bạn là một trợ lý chuyên trả lời các câu hỏi thường ngày và cung cấp thông tin mới nhất với phong cách trả lời ngắn gọn nhưng đầy đủ ý. 
            Nguyên tắc làm việc:
            - Chỉ trả lời những câu hỏi được gán cho bạn là GeneralAgent.
            - Lưu ý không trả lời những câu hỏi đã được gán cho các Agent khác.
            - ƯU TIÊN sử dụng thông tin BỘ NHỚ để trả lời câu hỏi.
            - Nếu THÔNG TIN BỘ NHỚ KHÔNG ĐỦ ĐỂ TRẢ LỜI, HÃY LUÔN sử dụng những tools của mình (DuckDuckGo, Wikipedia) để có thể trả lời bất kì câu hỏi nào.
            
            - Không cố tạo ra câu trả lời sai hoặc không liên quan đến câu hỏi.
            """,
            # reflect_on_tool_use=True,
            memory=[chat_memory] if chat_memory is not None else None,
        )
            # - LƯU Ý KHÔNG CẦN trả lời những câu hỏi liên quan tới công ty TMA và Pháp Luật. Nếu nhận được câu hỏi về vấn đề này thì hãy bỏ qua mà KHÔNG CẦN phản hồi gì thêm.

        text_mention_termination = TextMentionTermination("OK")
        max_messages_termination = MaxMessageTermination(max_messages=10)
        termination = text_mention_termination | max_messages_termination

        team = SelectorGroupChat(
            [planning_agent, law_agent, tma_agent, general_agent],
            model_client=client,
            termination_condition=termination,
            selector_prompt=SELECTOR_PROMPT,
            # allow_repeated_speaker=True,  
            # selector_func=self.selector_func,
        )
    
        response_list = []
        prompt_tokens = 0
        completion_tokens = 0
        async for message in team.run_stream(task=input):  
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
        
        print("self.more_information_law: ", self.more_information_law)
        final_response = response_list[-1] + '\n' +self.more_information_law
        final_response = final_response.replace("OK", '')

        self.langfuse_handler.tmp_file_path = tmp_file_path          # Cập nhật kể cả có truyền tmp_file_path qua hay không để hệ thông khỏi bị lỗi os.remove
        self.langfuse_handler.update_current_trace(
            name="session_trace",
            session_id=session_id_choiced,
            input=input,
            output=final_response
        )

        self.langfuse_handler.trace_id = langfuse_context.get_current_trace_id()
        # # Xử lý chấm điểm cho RAG
        # if self.more_information_law.strip():
        #     contexts = self.more_information_law.strip()
        #     print("\n\ncontexts: ", contexts)
        #     score_ragas = await self.langfuse_handler.score_with_ragas(query=input, context=contexts, answer=final_response)
        #     print("score_ragas: ", score_ragas)

        
        return final_response

        
        

         
