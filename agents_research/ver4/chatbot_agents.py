import streamlit as st
import time
from pypdf import PdfWriter
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.base import TaskResult
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.azure import AzureAIChatCompletionClient
from azure.core.credentials import AzureKeyCredential
from autogen_core import CancellationToken
from autogen_core.tools import FunctionTool
from autogen_agentchat.messages import TextMessage
import asyncio

from elasticsearch import Elasticsearch
from search_duckduck import get_asearch
from search_elasticsearch import hybrid_search

from sentence_transformers import SentenceTransformer
import torch
torch.classes.__path__ = [] # add this line to manually set it to empty. 

    
def setup_page():
    st.set_page_config(
        page_title="	🐱‍🏍 Supter Chatbot",
        layout="centered"
    )
    st.header("Agentic Chatbot!" )
    st.sidebar.header("Options", divider='rainbow')
    hide_menu_style = """
            <style>
            #MainMenu {visibility: hidden;}
            </style>
            """ 
    st.markdown(hide_menu_style, unsafe_allow_html=True)        # Xoá menu chọn mặc định góc trên bên phải của st

def get_choice():
    choice = st.sidebar.radio("Choose:", ["Normal Chat",
                                          "Chat with a PDF",
                                          "Chat with many PDFs",
                                          "Chat with an image",
                                          "Chat with audio",
                                          "Chat with video"],)
    return choice

def get_clear():
    clear_button=st.sidebar.button("Start new session", key="clear")
    return clear_button

def reload_achat():
    if "messages" not in st.session_state:
            st.session_state.messages = []
    # Hiển thị lại lịch sử chat sau khi app được tải lại
    for message in st.session_state.messages:
        with st.chat_message(message['role'],  avatar="🤓" if message['role'] == "assistant" else "🤬"):
            st.markdown(message['content'])

def effect_chat(response):
    print("KAKAKA: ", response)
     # Tạo một placeholder để hiển thị phản hồi từng từ một
    message_placeholder = st.empty()
    response_text = ""
    for word in response.split():
        response_text += word + " "
        message_placeholder.markdown(response_text)
        time.sleep(0.05)  # Hiệu ứng gõ chữ

async def get_rag_prompt(query: str):
    retrieval_context = await hybrid_search(search_query=query, top_k=3, model=model)
    # Augment the query with the retrieval context.
    augmented_query = f"""Thông tin đã được xác thực:\n{retrieval_context}.\n\n 
    Câu hỏi của tôi là: {query}.\n\n Ưu tiên dựa vào thông tin được xác thực, hãy cung cấp câu trả lời. 
    Nếu trong phạm vi thông tin đã xác thực chưa đủ để trả lời thì mới dùng thông tin bên ngoài khác."""
    return augmented_query

async def get_response(prompt, chat_agent, user_agent):
    print("prompt: ", prompt)
    new_promt = await get_rag_prompt(prompt)
    print("NEW prompt: ", new_promt)
    termination = TextMentionTermination("APPROVE")
    team = RoundRobinGroupChat([chat_agent, user_agent], termination_condition=termination)
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

def chat_processing(prompt, chat_agent, user_agent):
    with st.chat_message(name="user", avatar="🤬"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message(name="assistant", avatar="🤓"):
        response = asyncio.run(get_response(prompt, chat_agent, user_agent))
        effect_chat(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

def main():
    choice = get_choice()
    if choice == "Normal Chat":
        # st.subheader("Normal Chat")
        clear = get_clear()
        if clear:
            if "messages" in st.session_state:
                del st.session_state.messages
        reload_achat()

        chat_agent = AssistantAgent(
                        name="tma_assistant",
                        model_client=client,
                        tools=[get_newinfo2TMA, get_realinfo2TMA],
                        description="Một nhân viên lễ tân chuyên nghiệp của công ty TMA",
                        system_message="""Bạn là một nhân viên lễ tân tại công ty TMA với phong cách trả lời ngắn gọn, chỉ tập trung trả lời những gì được hỏi.
                                        Mục tiêu của bạn là trả lời các thông tin liên quan đến công ty TMA.
                                        Bạn chỉ tập trung làm việc vào mục tiêu của mình.
                                        Đừng tốn thời gian bằng tin nhắn chit chat.
                                        Xem xét các đề xuất khi đưa ra 1 ý tưởng.
                                        Đừng cố tạo câu trả lời sai trọng tâm câu hỏi.
                                        """,
                    )
        user_agent = AssistantAgent(
                        name="assistant",
                        model_client=client,
                        tools=[],
                        description="Một kiểm tra giúp hệ thống đánh giá xem câu trả lời có phù hợp với câu hỏi chưa",
                        system_message="""Bạn có vai trò kiểm tra xem câu trả lời của hệ thống có đúng với câu hỏi của người dùng đặt chưa.
                                        Mục tiêu của bạn chỉ là xem xét câu trả lời của hệ thông có phù hợp với câu hỏi của người dùng hay chưa. 
                                        Nếu thấy câu trả lời của hệ thống quá dài thì hãy nhắc hệ thống có thể tóm tắt câu trả lời tập trung vào nội dung câu hỏi được hay không, mà không cần đưa ra ví dụ cụ thể cho hệ thống biết.
                                        Nếu hệ thống đã trả lời là không biết hay 'Hiện nay, chưa có thông tin chính thức về câu hỏi này' hoặc tương tự thì cũng phản hồi bằng 'APPROVE'.
                                        Nếu câu trả lời của hệ thống và câu hỏi của người dùng đặt chưa phù hợp hoàn toàn thì mới thông báo cho hệ thống trả lời là 'Hiện nay, chưa có thông tin chính thức về câu hỏi này'. Rồi cũng phản hồi bằng 'APPROVE'.
                                        Bạn chỉ tập trung làm việc vào mục tiêu của mình.
                                        Đừng tốn thời gian bằng tin nhắn ngoài lề khác.
                                        Đừng cố tạo câu trả lời sai trọng tâm câu hỏi.
                                        """,
                    )
       
        if prompt := st.chat_input("nhập câu hỏi vào đây..."):
           chat_processing(prompt, chat_agent, user_agent)

# Hàm bọc
async def hybrid_search_tool_func(*, search_query: str):
    return await hybrid_search(search_query=search_query, top_k=4, model=model)

if __name__ == "__main__":
    get_newinfo2TMA = FunctionTool(
        get_asearch, description="Tìm kiếm các thông tin về công ty TMA và các thông tin liên quan khác."
    )
    get_realinfo2TMA = FunctionTool(  
        hybrid_search_tool_func, description="Tìm kiếm các thông tin về công ty TMA."
    )

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    #VietNamese embedding: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2?library=sentence-transformers
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2").to(device)
    
    GITHUB_TOKEN = ""
    client = AzureAIChatCompletionClient(
        # model="gpt-4o-mini",
        # model='gpt-4o',
        # model='Codestral-2501',
        model='Codestral-2501',
        endpoint="https://models.inference.ai.azure.com",
        credential=AzureKeyCredential(GITHUB_TOKEN),
        model_info={
            "json_output": True,
            "function_calling": True,
            "vision": False,
            "family": "unknown",
        },
    )

    setup_page()
    main()




