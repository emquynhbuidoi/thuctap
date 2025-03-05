from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.base import TaskResult
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_core import CancellationToken
from azure.core.credentials import AzureKeyCredential
from autogen_core.tools import FunctionTool
from autogen_ext.models.azure import AzureAIChatCompletionClient
from search_duckduck import get_asearch
from elasticsearch_ne import HybridSearch
from langfuse.decorators import observe
# from langfuse.media import LangfuseMedia

from config import INDEX_NAME_DEFAULT, INDEX_NAME_N_GRAM, INDEX_NAME_EMBEDDING, INDEX_NAME_HYBRID
from typing import Optional
from langfuse_ne import LangfuseHandler 

langfuse_handler = LangfuseHandler()
hybrid_search_class = HybridSearch()

@observe()
async def get_rag_prompt(query: str):
    """
        input: 
            query: str | là câu hỏi đầu vào của người dùng 
                    (p/s nếu là câu hỏi dựa trên file pdf,
                    thì trong prompt tôi đã để thêm thông tin nhận biết là dòng 'Thông tin cung cấp được lấy từ file:'.
                    Do đó không cần phải RAG thêm cho prompt)
        output:
            augmented_query: str | là đầu ra của câu prompt
                - Nếu hỏi dựa trên pdf thì câu prompt ban đầu đã chứa thông tin context nên return luôn.
                - Nếu hỏi bình thường thì thực hiện RAG prompt bằng hybrid_search
    """
    if "Thông tin cung cấp được lấy từ file:" in query:
        return query
    # print("query: ", query)
    retrieval_context = await hybrid_search_class.hybrid_search(search_query=query, top_k=3, INDEX_NAME=INDEX_NAME_HYBRID)
    # print("retrieval_context: ", retrieval_context)
    augmented_query = f"""Câu hỏi: {query}.\n Thông tin đã được xác thực:{retrieval_context}."""
    return augmented_query

@observe(as_type="generation")
async def get_anew_prmopt(query: str, client: AzureAIChatCompletionClient):
    """
        input:
            query: str | là câu query của người dùng sau khi qua hàm get_rag_prompt để RAG thêm thông tin trả lời
            client: AzureAIChatCompletionClient | LLM lấy từ AzureAIChat
        output:
            response.chat_message.content: str | là câu query sau khi được prompt_agent_assistant prompt lại theo định dạng rõ ràng cụ thể hơn.
                Giúp các agents sau có thể dễ dàng trả lời đúng câu hỏi.
                định dạng: Câu hỏi của tôi là: <câu hỏi>.
                            Thông tin đã xác thực là: <thông tin đã xác thực theo dạng từng ý>
                            hoặc
                            Câu hỏi của tôi là: <câu hỏi>.
                            Thông tin đã xác thực là: Thông tin xác thực không có
    """
    prompt_agent = AssistantAgent(
        name="prompt_agent_assistant",
        model_client=client,
        tools=[],
        description="Một prompt engineer",
        system_message="""Bạn Chỉ là một prompt engineer giỏi, với phong cách sửa các prompt dài dòng thành các prompt ngắn gọn, liệt kê theo ý chính.
                        Bạn không thể trả lời câu hỏi, bạn chỉ có thể tóm tắt lại câu hỏi cho hệ thống.
                        Mục tiêu của bạn chỉ là chuyển đổi câu prompt đầu vào khó hiểu thành 1 prompt ngắn gọn theo ý và liệt kê dễ hiểu, logic nhất.
                        Hãy tóm tắt thông tin này và liệt kê theo từng mục theo định dạng: 
                        Câu hỏi của tôi là: <câu hỏi>. 
                        Thông tin đã xác thực là: <thông tin đã xác thực theo dạng từng ý> nếu thông tin xác thực không đúng với câu hỏi thì trả lời 'Thông tin xác thực không có'.
                        Bạn chỉ tập trung làm việc vào mục tiêu của mình.
                        Đừng tốn thời gian bằng tin nhắn chit chat.
                        """,
    )
    response = await prompt_agent.on_messages(
        [TextMessage(content=query, source="user")],
        cancellation_token=CancellationToken(),
    )
    
    langfuse_handler.update_observation_cost(
        model_name="MODEL_CHATGPT_PROMPT",
        input_token=response.chat_message.models_usage.prompt_tokens,
        output_token=response.chat_message.models_usage.completion_tokens,
        cost_input=0.0001,
        cost_output=0.0001
    )
    return response.chat_message.content

async def hybrid_search_tool_func(*, search_query: str):
    return await hybrid_search_class.hybrid_search(search_query=search_query, top_k=3, INDEX_NAME=INDEX_NAME_HYBRID)

@observe(as_type="generation")
async def get_response(prompt: str, session_id_choiced: Optional[str] = None, tmp_file_path: Optional[str] = None):
    """
        input:
            prompt: str | câu hỏi ban đầu của người dùng
            session_id_choiced: str | là 1 key thể hiện người dung đang chat với session nào
        output:
            response_list: list | là danh sách chứa câu hỏi người dùng và cuộc hội thoại giữa các agents (p/s: cẩu trả lời cuối cùng trong list là APPROVE của Agent critic)
    """
    get_newinfo2TMA = FunctionTool(
        get_asearch, description="Tìm kiếm thông tin khi thông tin xác thực không có."
    )
    get_realinfo2TMA = FunctionTool(  
        hybrid_search_tool_func, description="Tìm kiếm các thông tin về công ty TMA."
    )

    GITHUB_TOKEN = ""
    client = AzureAIChatCompletionClient(
        # model="gpt-4o-mini",
        # model='gpt-4o',
        # model='Meta-Llama-3.1-405B-Instruct',  ###
        # model="DeepSeek-R1",
        # model="Mistral-large",
        model="Mistral-large-2407",
        # model="Meta-Llama-3.1-70B-Instruct",
        # model="Meta-Llama-3-8B-Instruct",       ##
        
        endpoint="https://models.inference.ai.azure.com",
        credential=AzureKeyCredential(GITHUB_TOKEN),
        model_info={
            "json_output": True,
            "function_calling": True,
            "vision": False,
            "family": "unknown",
        }
    )
    chat_agent = AssistantAgent(
                        name="tma_assistant",
                        model_client=client,
                        tools=[get_newinfo2TMA, get_realinfo2TMA],
                        description="Một nhân viên lễ tân chuyên nghiệp của công ty TMA, có thể bổ xung thông tin nếu thông tin xác thực không có.",
                        system_message="""Bạn có nhiệm vụ tiếp nhận câu trả lời bằng tiếng Việt và trả lời 1 cách ngắn gọn, chuyên nghiệp.
                                        Mục tiêu của bạn là trả lời các thông tin liên quan đến công ty TMA ưu tiên sử dụng thông tin đã xác thực trên.
                                        Nếu không thể trả lời từ dữ liệu có sẳn thì bạn có thể bổ xung thông tin khác, bằng cách dùng các search tool của mình.
                                        Bạn chỉ tập trung làm việc vào mục tiêu của mình.
                                        Đừng tốn thời gian bằng tin nhắn chit chat.
                                        Xem xét các đề xuất khi đưa ra 1 ý tưởng.
                                        Đừng cố tạo câu trả lời sai trọng tâm câu hỏi.
                                        """,
                                    
                )
    critic_agent = AssistantAgent(
                    name="critic",
                    model_client=client,
                    tools=[],
                    description="Một nhà phê bình giúp hệ thống đánh giá xem câu trả lời có phù hợp với câu hỏi chưa",
                    system_message="""Bạn là một người kiểm tra thông minh có thể đọc hiểu câu trả lời của hệ thống.
                                    Mục tiêu của bạn chỉ là xem xét câu trả lời của hệ thông có phù hợp với câu hỏi của người dùng hay chưa. 
                                    Nếu hệ thống đã trả lời là không biết hay 'Hiện nay, tôi chưa có thông tin về câu hỏi này, hãy thử tìm kiếm trên website của TMA' hoặc tương tự thì cũng phản hồi bằng 'APPROVE'.
                                    Nếu câu trả lời của hệ thống không chính xác với câu hỏi thì nhắc cho hệ thống trả lời là 'Hiện nay, tôi chưa có thông tin về câu hỏi này, hãy thử tìm kiếm trên website của TMA'.
                                    Nếu thấy câu trả lời của hệ thống quá dài hơn 10 câu thì hãy nhắc cho hệ thống tóm tắt câu trả lời, mà không cần đưa ra ví dụ cụ thể cho hệ thống biết.
                                    Bạn chỉ tập trung làm việc vào mục tiêu của mình.
                                    Đừng tốn thời gian bằng tin nhắn ngoài lề khác.
                                    Đừng cố tạo câu trả lời sai trọng tâm câu hỏi.
                                    """,
                )
    
    # print("prompt: ", prompt)
    rag_promt = await get_rag_prompt(prompt)
    # print("rag_promt prompt: ", rag_promt)
    new_promt = await get_anew_prmopt(rag_promt, client)
    # print("new_promt prompt: ", new_promt)

    text_termination = TextMentionTermination("APPROVE")
    max_msg_termination = MaxMessageTermination(max_messages=10)
    combined_termination = max_msg_termination | text_termination
    team = RoundRobinGroupChat([chat_agent, critic_agent], termination_condition=combined_termination)
    response_list = []
    prompt_tokens = 0
    completion_tokens = 0
    async for message in team.run_stream(task=new_promt):  
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
        cost_input=0.0001,
        cost_output=0.0002
    )
    
    if tmp_file_path is not None:
        langfuse_handler.tmp_file_path = tmp_file_path
    langfuse_handler.update_current_trace(
        name="session_trace",
        session_id=session_id_choiced,
        input=prompt,
        output=response_list[-2]
    )
    
    return response_list