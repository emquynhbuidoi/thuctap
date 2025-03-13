from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.base import TaskResult
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.agents import AssistantAgent
from azure.core.credentials import AzureKeyCredential
from autogen_core.tools import FunctionTool
from autogen_ext.models.azure import AzureAIChatCompletionClient
from search_duckduck import get_asearch
from elasticsearch_ne import HybridSearch
from langfuse.decorators import observe, langfuse_context
from config import INDEX_NAME_PDF, INDEX_NAME_HYBRID, MODEL_CHAT_INPUT_COST, MODEL_CHAT_OUTPUT_COST, INDEX_NAME_MEMORY
from typing import Optional
from langfuse_ne import LangfuseHandler 
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType
from index_data_pdf import index_data
from azure.ai.contentsafety import ContentSafetyClient
from azure.core.exceptions import HttpResponseError
from azure.ai.contentsafety.models import AnalyzeTextOptions, TextCategory

langfuse_handler = LangfuseHandler()
hybrid_search_class = HybridSearch()

@observe()
async def get_rag_prompt(query: str, tmp_file_path: Optional[str] = None):
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
        context_from_pdf = await hybrid_search_class.hybrid_search(query, top_k=3, INDEX_NAME=INDEX_NAME_PDF)
        prompt = "Thông tin cung cấp được lấy từ file: " + context_from_pdf + '\n Dựa vào file trả lời câu hỏi: ' + query
        return prompt, context_from_pdf
    
    retrieval_context = await hybrid_search_class.hybrid_search(search_query=query, top_k=3, INDEX_NAME=INDEX_NAME_HYBRID)
    augmented_query = f"""Câu hỏi: {query}.\n Thông tin cần được xác thực:{retrieval_context}."""
    return augmented_query, retrieval_context

async def hybrid_search_tool_func(*, search_query: str):
    return await hybrid_search_class.hybrid_search(search_query=search_query, top_k=3, INDEX_NAME=INDEX_NAME_HYBRID)

def analyze_content_safety(content: str):
    key = ''
    endpoint = ""
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
async def get_response(prompt: str, session_id_choiced: Optional[str] = None, tmp_file_path: Optional[str] = None):
    """
        input:
            prompt: str | câu hỏi ban đầu của người dùng.
            session_id_choiced: Optional(str) | là 1 key thể hiện người dung đang chat với session nào.
            tmp_file_path: Optional(str) | đường dẫn tới file pdf tạm thời.
        output:
            response_list: list | là danh sách chứa câu hỏi người dùng và cuộc hội thoại giữa các agents (p/s: cẩu trả lời cuối cùng trong list là APPROVE của Agent critic).
    """
    # is_safe = analyze_content_safety(prompt)
    # if is_safe == False:
    #     return "Tôi không thể trả lời các thông tin nhạy cảm !!"
    print("session_id_choiced hiện tại là: ", session_id_choiced)
    get_newinfo2TMA = FunctionTool(
        get_asearch, description="Tìm kiếm thông tin khi thông tin xác thực không có."
    )
    get_realinfo2TMA = FunctionTool(  
        hybrid_search_tool_func, description="Tìm kiếm các thông tin về công ty TMA."
    )

    GITHUB_TOKEN = ""
    client = AzureAIChatCompletionClient(
        # model="gpt-4o-mini",
        model='gpt-4o',                       ## 
        # model='Meta-Llama-3.1-405B-Instruct', ## 
        # model="DeepSeek-R1",
        # model="Mistral-large",                 ### 
        # model="Mistral-large-2407",                 ###
        # model="Meta-Llama-3.1-70B-Instruct",            ###
        # model="Meta-Llama-3-8B-Instruct",       ##
        # model='Meta-Llama-3.1-8B-Instruct',       ## 
        # model='Llama-3.3-70B-Instruct', 

        
        endpoint="https://models.inference.ai.azure.com",
        credential=AzureKeyCredential(GITHUB_TOKEN),
        model_info={
            "json_output": True,
            "function_calling": True,
            "vision": False,
            "family": "unknown",
        }
    )
    
    # Xử lý memory agen autogen ở đây........
    chat_memory = None
    lst_memory = []
    memory_doc = langfuse_handler.get_chat_memory_doc(session_id=session_id_choiced)
    if len(memory_doc) > 0:
        index_data(documents=memory_doc, INDEX_NAME=INDEX_NAME_MEMORY)
        memorys = await hybrid_search_class.hybrid_search(search_query=prompt, top_k=3, INDEX_NAME=INDEX_NAME_MEMORY)
        lst_memory = memorys.strip().split('\n')
    if len(lst_memory) > 0: 
        chat_memory = ListMemory()
        for memory in lst_memory[:3]:
            await chat_memory.add(MemoryContent(content=memory, mime_type=MemoryMimeType.TEXT))

    prompt_agent = AssistantAgent(
        name="prompt_agent_assistant",
        model_client=client,
        tools=[],
        description="Một prompt engineer",
        system_message="""Bạn chỉ là một người chọn ra thông tin xác thực đúng với câu hỏi đã cho.
                        - Bạn không thể đặt câu hỏi mới.
                        - Bạn không thể trả lời câu hỏi.
                        - Mục tiêu là chọn ra thông tin xác thực đúng với câu hỏi theo tiêu chí ngắn gọn, dễ hiểu theo ý chính, dạng liệt kê.
                        - Nếu câu hỏi theo kiểu cung cấp thông tin hoặc 1 hướng dẫn thì hãy phản hồi 'Câu hỏi theo dạng cung cấp thông tin'.
                        - Hãy phản hồi theo định dạng sau:
                            Câu hỏi: (hãy ghi lại câu hỏi đã cho). 
                            Thông tin đã xác thực là: (hãy chọn ra thông tin đã xác thực và liệt kê theo từng ý). 
                        - Nếu thông tin xác thực không đúng với câu hỏi, trả lời "hãy tìm kiếm trên website để cập nhật thông tin mới và sử dụng bộ nhớ để trả lời".
                        """,
        memory=[chat_memory] if chat_memory is not None else None
    )
    chat_agent = AssistantAgent(
                        name="tma_assistant",
                        model_client=client,
                        tools=[get_newinfo2TMA, get_realinfo2TMA],
                        description="Một nhân viên lễ tân chuyên nghiệp của công ty TMA, có thể bổ xung thông tin nếu thông tin xác thực không có.",
                        system_message="""Bạn là một nhân viên lễ tân chuyên nghiệp của công ty TMA, có nhiệm vụ tiếp nhận và trả lời câu hỏi bằng tiếng Việt một cách ngắn gọn, chuyên nghiệp.
                                        **Mục tiêu:**
                                        - Có thể dùng thông tin có trong bộ nhớ và thông tin đã xác thực để trả lời câu hỏi.
                                        - Nếu không thể trả lời từ dữ liệu có sẵn, bạn có thể tìm kiếm trên website để cập nhật thông tin mới. 
                                        **Nguyên tắc làm việc:**
                                        - Tập trung vào nhiệm vụ, tránh lan man.
                                        - Đưa ra các câu trả lời rõ ràng, đúng trọng tâm câu hỏi.  
                                        - Xem xét các đề xuất trước khi đưa ra câu trả lời.  
                                        - Tránh tạo ra câu trả lời sai hoặc không liên quan đến câu hỏi.  
                                        """,
                        memory=[chat_memory] if chat_memory is not None else None
                )
    critic_agent = AssistantAgent(
                    name="critic",
                    model_client=client,
                    tools=[],
                    description="Một nhà phê bình giúp hệ thống đánh giá xem câu trả lời có phù hợp với câu hỏi chưa",
                    system_message="""Bạn là một nhà phê bình thông minh, có khả năng đánh giá xem câu trả lời có phù hợp với câu hỏi chưa.
                                **Mục tiêu:**
                                - Nếu câu hỏi theo dạng cung cấp thông tin hoặc 1 hướng dẫn thì hãy trả lời là 'APPROVE'.
                                - Nếu câu trả lời dài hơn 7 câu, yêu cầu hệ thống tóm tắt lại. 
                                - Đánh giá xem câu trả lời có phù hợp với câu hỏi hay không.  
                                    + Nếu câu trả lời là "Không biết" hoặc "Hiện nay, tôi chưa có thông tin về câu hỏi này, hãy thử tìm kiếm trên website để cập nhật thông tin mới." hoặc nội dung tương tự Phản hồi 'APPROVE'.  
                                    + Nếu câu trả lời không chính xác hoặc không liên quan. Trả lời là: "Hiện nay, tôi chưa có thông tin về câu hỏi này, hãy thử tìm kiếm trên website để cập nhật thông tin mới." và Phản hồi 'APPROVE'
                                **Nguyên tắc làm việc:**
                                - Chỉ tập trung vào nhiệm vụ của bạn, không phản hồi các tin nhắn ngoài lề.  
                                - Tránh đưa ra ví dụ hoặc gợi ý chi tiết cho hệ thống.  
                                - Giữ phản hồi ngắn gọn, chính xác và đúng trọng tâm.  
                                """,
                    # memory=[chat_memory] if chat_memory is not None else None
                )
    
    rag_promt, contexts = await get_rag_prompt(prompt, tmp_file_path)

    text_termination = TextMentionTermination("APPROVE")
    max_msg_termination = MaxMessageTermination(max_messages=20)
    combined_termination = max_msg_termination | text_termination
    team = RoundRobinGroupChat([prompt_agent, chat_agent, critic_agent], termination_condition=combined_termination)
    response_list = []
    prompt_tokens = 0
    completion_tokens = 0
    async for message in team.run_stream(task=rag_promt):  
        if isinstance(message, TaskResult):
            if message.stop_reason is None:
                response_list.append("NONE")
            break
        else:
            print(message)
            prompt_tokens += message.models_usage.prompt_tokens if message.models_usage is not None else 0
            completion_tokens += message.models_usage.completion_tokens if message.models_usage is not None else 0
            response_list.append(message.content)

    langfuse_handler.update_observation_cost(
        model_name='MODEL_CHATGPT',
        input_token=prompt_tokens,
        output_token=completion_tokens,
        cost_input=MODEL_CHAT_INPUT_COST,
        cost_output=MODEL_CHAT_OUTPUT_COST
    )
    
    langfuse_handler.tmp_file_path = tmp_file_path          # Cập nhật kể cả có truyền tmp_file_path qua hay không để hệ thông khỏi bị lỗi os.remove
    langfuse_handler.update_current_trace(
        name="session_trace",
        session_id=session_id_choiced,
        input=prompt,
        output=response_list[-2]
    )
    langfuse_handler.trace_id = langfuse_context.get_current_trace_id()
    # Xử lý chấm điểm cho RAG
    # print("\n\ncontexts: ", contexts)
    # score_ragas = await langfuse_handler.score_with_ragas(query=prompt, context=contexts, answer=response_list[-2])
    # print("score_ragas: ", score_ragas)
    return response_list