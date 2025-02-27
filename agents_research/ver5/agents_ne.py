from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.base import TaskResult
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_core import CancellationToken
from azure.core.credentials import AzureKeyCredential
from autogen_core.tools import FunctionTool
from autogen_ext.models.azure import AzureAIChatCompletionClient
from search_duckduck import get_asearch
from search_elasticsearch import hybrid_search
from sentence_transformers import SentenceTransformer
import torch
torch.classes.__path__ = []

from langfuse.decorators import observe, langfuse_context
from langfuse import Langfuse

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
#VietNamese embedding: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2?library=sentence-transformers
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2").to(device)

# langfuse_client = Langfuse(
#     secret_key="sk-lf-b4dc18fb-3038-4fad-a7c5-d4942f579c4b",
#     public_key="pk-lf-c1601387-27ef-43fa-8253-c4e1b05b64fd",
#     host="https://cloud.langfuse.com"
# )

# # Tạo root trace (trace chính)
# root_trace = langfuse_client.trace(
#     name="tma_chatbot_conversation",
#     # input={"prompt": new_promt}
# )

@observe()
async def get_rag_prompt(query: str):
    retrieval_context = await hybrid_search(search_query=query, top_k=3, model=model)
    # Augment the query with the retrieval context.
    augmented_query = f"""Thông tin đã được xác thực:\n{retrieval_context}.\n
    Câu hỏi của tôi là: {query}.\n Ưu tiên dựa vào thông tin được xác thực, hãy cung cấp câu trả lời. 
    Nếu thấy thông tin trên không đúng phù hợp với câu hỏi thì hãy dùng thông tin bên ngoài."""
    return augmented_query

async def hybrid_search_tool_func(*, search_query: str):
    return await hybrid_search(search_query=search_query, top_k=4, model=model)

@observe(as_type="generation")
async def get_response(prompt: str):
    
    get_newinfo2TMA = FunctionTool(
        get_asearch, description="Dùng để tìm kiếm tất cả thông tin."
    )
    get_realinfo2TMA = FunctionTool(  
        hybrid_search_tool_func, description="Chỉ tìm kiếm các thông tin về công ty TMA."
    )

    GITHUB_TOKEN = ""
    client = AzureAIChatCompletionClient(
        model="gpt-4o-mini",
        # model='gpt-4o',
        # model='Codestral-2501',
        # model="Mistral-Large-2411",
        endpoint="https://models.inference.ai.azure.com",
        credential=AzureKeyCredential(GITHUB_TOKEN),
        model_info={
            "json_output": True,
            "function_calling": True,
            "vision": False,
            "family": "unknown",
        },
    )

    chat_agent = AssistantAgent(
                        name="tma_assistant",
                        model_client=client,
                        tools=[get_newinfo2TMA, get_realinfo2TMA],
                        description="Một nhân viên lễ tân chuyên nghiệp của công ty TMA",
                        system_message="""Bạn là một nhân viên lễ tân tại công ty TMA với phong cách trả lời ngắn gọn, chỉ trả lời những thông tin liên quan đến công ty TMA.
                                        Mục tiêu của bạn là trả lời các thông tin liên quan đến công ty TMA.
                                        Bạn chỉ tập trung làm việc vào mục tiêu của mình.
                                        Đừng tốn thời gian bằng tin nhắn chit chat.
                                        Xem xét các đề xuất khi đưa ra 1 ý tưởng.
                                        Đừng cố tạo câu trả lời sai trọng tâm câu hỏi.
                                        """,
                )
    test_agent = AssistantAgent(
                    name="assistant",
                    model_client=client,
                    tools=[],
                    description="Một kiểm tra giúp hệ thống đánh giá xem câu trả lời có phù hợp với câu hỏi chưa",
                    system_message="""Bạn chỉ có vai trò kiểm tra xem câu trả lời của hệ thống có đúng với câu hỏi của người dùng đặt chưa, không có quyền đưa ra câu trả lời.
                                    Mục tiêu của bạn chỉ là xem xét câu trả lời của hệ thông có phù hợp với câu hỏi của người dùng hay chưa. 
                                    Nếu thấy câu trả lời của hệ thống quá dài thì hãy nhắc hệ thống có thể tóm tắt câu trả lời tập trung vào nội dung câu hỏi được hay không, mà không cần đưa ra ví dụ cụ thể cho hệ thống biết.
                                    Nếu hệ thống đã trả lời là không biết hay 'Hiện nay, chưa có thông tin chính thức về câu hỏi này' hoặc tương tự thì cũng phản hồi bằng 'APPROVE'.
                                    Nếu câu trả lời của hệ thống và câu hỏi của người dùng đặt chưa phù hợp hoàn toàn thì mới thông báo cho hệ thống trả lời là 'Hiện nay, chưa có thông tin chính thức về câu hỏi này'. Rồi cũng phản hồi bằng 'APPROVE'.
                                    Bạn chỉ tập trung làm việc vào mục tiêu của mình.
                                    Đừng tốn thời gian bằng tin nhắn ngoài lề khác.
                                    Đừng cố tạo câu trả lời sai trọng tâm câu hỏi.
                                    """,
                )
    
    print("prompt: ", prompt)
    new_promt = await get_rag_prompt(prompt)
    print("NEW prompt: ", new_promt)
    termination = TextMentionTermination("APPROVE")
    team = RoundRobinGroupChat([chat_agent, test_agent], termination_condition=termination)
    prev_response = None 
    last_response = None 
    async for message in team.run_stream(task=new_promt):  # Dùng new_promt thay vì prompt
        if isinstance(message, TaskResult):
            print("Stop Reason:", message.stop_reason)
            break
        else:
            print(message)
            prev_response = last_response  
            last_response = message.content  
    
    
    return prev_response if prev_response is not None else "No prior response"



# langfuse_client.shutdown()