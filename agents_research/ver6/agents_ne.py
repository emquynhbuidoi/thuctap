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
from search_elasticsearch import hybrid_search
from sentence_transformers import SentenceTransformer
import torch
torch.classes.__path__ = []

from langfuse.decorators import observe, langfuse_context
from langfuse import Langfuse

import os
# get keys for your project from https://cloud.langfuse.com
os.environ["LANGFUSE_PUBLIC_KEY"] = ""
os.environ["LANGFUSE_SECRET_KEY"] = ""

langfuse = Langfuse(
  secret_key="",
  public_key="",
  host="https://cloud.langfuse.com"
)

import uuid
session_id = str(uuid.uuid4())

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
#VietNamese embedding: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2?library=sentence-transformers
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2").to(device)

@observe()
async def get_rag_prompt(query: str):
    if "Thông tin cung cấp được lấy từ file:" in query:
        return query
     
    retrieval_context = await hybrid_search(search_query=query, top_k=3, model=model)
    # Augment the query with the retrieval context.
    augmented_query = f"""Câu hỏi: {query}.\n Thông tin đã được xác thực:\n{retrieval_context}.\n"""
    return augmented_query

@observe()
async def get_anew_prmopt(query: str, client: AzureAIChatCompletionClient):
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
    # print("response.chat_message.content: ", response.chat_message.content)
    
    return response.chat_message.content

async def hybrid_search_tool_func(*, search_query: str):
    return await hybrid_search(search_query=search_query, top_k=3, model=model)

@observe(as_type="generation")
async def get_response(prompt: str):
    get_newinfo2TMA = FunctionTool(
        get_asearch, description="Tìm kiếm thông tin khi thông tin xác thực không có."
    )
    get_realinfo2TMA = FunctionTool(  
        hybrid_search_tool_func, description="Tìm kiếm các thông tin về công ty TMA."
    )

    GITHUB_TOKEN = ""
    client = AzureAIChatCompletionClient(
        model="gpt-4o-mini",
        # model='gpt-4o',
        # model='Meta-Llama-3.1-405B-Instruct',
        # model="DeepSeek-R1",
        # model="Mistral-large",
        # model="Mistral-large-2407",
        # model="Mistral-Large-2411",
        # model="Meta-Llama-3-8B-Instruct",
        
        
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
                                        Nếu đang xử lý, hãy báo vui lòng chờ trong giây lát..
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
                                    Nếu hệ thống đã trả lời là không biết hay 'Hiện nay, chưa có thông tin chính thức về câu hỏi này' hoặc tương tự thì cũng phản hồi bằng 'APPROVE'.
                                    Nếu câu trả lời của hệ thống và câu hỏi của người dùng đặt chưa phù hợp thì phải nhắc cho hệ thống trả lời là 'Hiện nay, chưa có thông tin chính thức về câu hỏi này'.
                                    Nếu thấy câu trả lời của hệ thống quá dài hơn 4 câu thì hãy nhắc cho hệ thống tóm tắt câu trả lời, mà không cần đưa ra ví dụ cụ thể cho hệ thống biết.
                                    Nếu đang xử lý, hãy báo vui lòng chờ trong giây lát..
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
    async for message in team.run_stream(task=new_promt):  
        if isinstance(message, TaskResult):
            # print("Stop Reason:", message.stop_reason)
            if message.stop_reason is None:
                # print("NONE NONE NONE NONE NONE NONE")
                response_list.append("NONE")
            break
        else:
            # print(message)
            response_list.append(message.content)
            

    langfuse_context.update_current_trace(
        name="session_trace",
        session_id=session_id,
        input=prompt,
        output=response_list[-2]
    )
    return response_list

