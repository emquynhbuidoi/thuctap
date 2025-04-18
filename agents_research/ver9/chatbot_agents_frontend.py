# https://github.com/pavanbelagatti/Chat-PDF-LlamaIndex/blob/main/streamlit_app.py
import streamlit as st
import time
from pypdf import PdfWriter
from google import genai
from google.genai import types
import requests
from pdf_manager import pdf_parser_nodes_index
from config import INDEX_NAME_PDF
from typing import Optional
from langfuse_ne import LangfuseHandler
import torch
torch.classes.__path__ = []
import tempfile

def setup_page():
    """
        hàm tạo layout cho streamlit
    """
    st.set_page_config(
        page_title="	🐱‍🏍 Supter Chatbot",
        layout="centered"
    )
    st.header("Agentic Chatbot!" )
    st.sidebar.header("Tuỳ chọn", divider='rainbow')
    hide_menu_style = """
            <style>
            #MainMenu {visibility: hidden;}
            </style>
            """ 
    st.markdown(hide_menu_style, unsafe_allow_html=True)        # Xoá menu chọn mặc định góc trên bên phải của st

def get_choice():
    """
        hàm tạo sidebar radio để chọn kiểu đối thoại
    """
    choice = st.sidebar.radio("Kiểu đối thoại:", ["Normal Chat",
                                                "Chat with a PDF",
                                                "Chat with an image",
                                                "Chat with audio",
                                                "Chat with video"])
    
    return choice

def get_session():
    """
        hàm trả về danh sách id của selected_session user chọn ở sidebar
    """
    sessions =  langfuse_class.fetch_sesions()
    if not sessions:
        st.sidebar.warning("Không có session nào được lưu hôm nay.")
        return None
    session_list_id = [session.id for session in sessions]
    session_options = [(None, "Cuộc Hội Thoại Mới")]  
    for session_id in session_list_id:
        traces = langfuse_class.fetch_traces(session_id)
        if len(traces) != 0:
            session_options.append((session_id, traces[0].input))

    selected_session = st.sidebar.selectbox(
        label="Lịch sử hỏi đáp",
        options=session_options,
        format_func=lambda x: x[1]
    )
    return selected_session[0]

def get_clear():
    """
        Hàm xoá màn hình ui
    """
    clear_button=st.sidebar.button("Xoá màn hình", key="clear")
    return clear_button

def reload_achat(session_id_selected: Optional[str]=None):
    """
        Hàm xử lý màn hình lịch sử chat đối với mỗi session
    """
    if "session_id" not in st.session_state:
        st.session_state.session_id = None  # Đảm bảo biến tồn tại

    if session_id_selected is not None and session_id_selected != st.session_state.session_id:      # Đây là trường hợp đang chat với session cũ
        st.session_state.session_id = session_id_selected  
        st.session_state.messages = []
        if session_id_selected is not None:
            traces = langfuse_class.fetch_traces(session_id=session_id_selected)
            for trace in traces:
                st.session_state.messages.append({"role": "user", "content": trace.input})
                st.session_state.messages.append({"role": "assistant", "content": trace.output})
            # Hiển thị lại lịch sử chat sau khi app được tải lại
            for message in st.session_state.messages:
                with st.chat_message(message['role'],  avatar="🤓" if message['role'] == "assistant" else "🤬"):
                    st.markdown(message['content'])
    elif session_id_selected == st.session_state.session_id:                                       # Đây là trường hợp đang chat trong session mới
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        # Hiển thị lại lịch sử chat sau khi app được tải lại
        for message in st.session_state.messages:
            with st.chat_message(message['role'],  avatar="🤓" if message['role'] == "assistant" else "🤬"):
                st.markdown(message['content'])
    elif session_id_selected != st.session_state.session_id:    
        st.session_state.session_id = session_id_selected                                           # Đây là trường hợp đang chat với session cũ muốn qua session mới thì reset lại ui
        st.session_state.messages = []
        

def effect_chat(response):
    """
        Hàm tạo hiệu ứng phản hồi của hệ thống như đang gõ từng chữ
    """
     # Tạo một placeholder để hiển thị phản hồi từng từ một
    message_placeholder = st.empty()
    response_text = ""
    for word in response.split():
        response_text += word + " "
        message_placeholder.markdown(response_text)
        time.sleep(0.05)  # Hiệu ứng gõ chữ

def chat_processing(prompt: str, context_from_pdf: str = None, session_id_choiced: str = None, tmp_file_path: str=None):
    """
        input:
            prompt: str |   Câu hỏi đầu vào của người dùng.
            context_from_pdf: str   | ngữ cảnh đuọc truy xuất từ pdf file bằng hybridSearch. Nếu khác None, thì được nối với prompt theo cấu trúc.
            session_id_choiced: str | key session_id_choiced đang thực hiện đối thoại.

    """
    with st.chat_message(name="user", avatar="🤬"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message(name="assistant", avatar="🤓"):
        if context_from_pdf:
            prompt = "Thông tin cung cấp được lấy từ file: " + context_from_pdf + '\n Dựa vào file trả lời câu hỏi: ' + prompt          
        API_URL="http://127.0.0.1:9999/chat"
        payload = {
            "prompt": prompt,
            "session_id_choiced": session_id_choiced,
            "tmp_file_path": tmp_file_path
        } 
        print("ccccccccc: ", tmp_file_path)
        response = requests.post(url=API_URL, json=payload)
        if response.status_code == 200:
            effect_chat(response.json())
        else:
            effect_chat("Unknown Messages")
    st.session_state.messages.append({"role": "assistant", "content": response.json()})

def main():
    choice = get_choice()
    session_id_choiced = get_session()
    print("session_id_choiced: ", session_id_choiced)

    if choice == "Normal Chat":
        clear = get_clear()
        if clear:
            if "messages" in st.session_state:
                del st.session_state.messages
        reload_achat(session_id_choiced)

        if prompt := st.chat_input("nhập câu hỏi vào đây..."):
           chat_processing(prompt, session_id_choiced=session_id_choiced)

    elif choice == "Chat with a PDF":
        st.subheader("Chat with a PDF")
        uploaded_files = st.file_uploader("Chọn file pdf để bắt đầu hội thoại", type=['pdf'], accept_multiple_files=False)
        clear = get_clear()
        if clear:
            if "messages" in st.session_state:
                del st.session_state.messages
        reload_achat(session_id_choiced)
        if uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_files.read())
                tmp_file_path = tmp_file.name  # Lưu lại đường dẫn để sử dụng sau
            if prompt := st.chat_input("nhập câu hỏi vào đây..."):
                if 'file' not in st.session_state:
                    st.session_state.file = uploaded_files.name
                    pdf_parser_nodes_index(tmp_file_path)
                elif 'file' in st.session_state and st.session_state.file != uploaded_files.name:
                    pdf_parser_nodes_index(tmp_file_path)
                
                API_URL="http://127.0.0.1:9999/hybrid_search"
                payload = {
                    "search_query": prompt,
                    'top_k': 3,
                    'index_name': INDEX_NAME_PDF
                } 
                response = requests.post(url=API_URL, json=payload)
                if response.status_code == 200:
                    context_from_pdf = response.json()
                else:
                    context_from_pdf = "Unknown Messages"
               
                print("context_from_pdf: ", context_from_pdf)
                print("tmp_file_path: ", tmp_file_path)
                chat_processing(prompt=prompt, context_from_pdf=context_from_pdf, session_id_choiced=session_id_choiced, tmp_file_path=tmp_file_path)

    elif choice == "Chat with an image":
        st.subheader("Chat with an image")
        uploaded_files2 = st.file_uploader("Choose your PNG or JPEG file",  type=['png','jpg'], accept_multiple_files=False)
        clear = get_clear()
        if clear:
            if "messages" in st.session_state:
                del st.session_state.messages
        reload_achat()
        if uploaded_files2:
            file_upload = client_gemini.files.upload(file='./odata/'+uploaded_files2.name)
            chat3 = client_gemini.chats.create(model=MODEL_ID,
                    history=[
                        types.Content(
                            role="user",
                            parts=[
    
                                    types.Part.from_uri(
                                        file_uri=file_upload.uri,
                                        mime_type=file_upload.mime_type),
                                    ]
                            ),
                        ]
                    )
            text_in_spdf = chat3.send_message("Mô tả lại toàn bộ nội dung trong bức ảnh")
            if prompt := st.chat_input("nhập câu hỏi vào đây..."):
                chat_processing(prompt, text_in_spdf)
    
    elif choice == "Chat with audio":
        st.subheader("Chat with your audio file")
        uploaded_files3 = st.file_uploader("Choose your mp3 or wav file",  type=['mp3','wav'], accept_multiple_files=False)
        clear = get_clear()
        if clear:
            if "messages" in st.session_state:
                del st.session_state.messages
        reload_achat()
        if uploaded_files3:
            file_upload = client_gemini.files.upload(file='./odata/'+uploaded_files3.name)
            chat4 = client_gemini.chats.create(model=MODEL_ID,
                    history=[
                        types.Content(
                            role="user",
                            parts=[
    
                                    types.Part.from_uri(
                                        file_uri=file_upload.uri,
                                        mime_type=file_upload.mime_type),
                                    ]
                            ),
                        ]
                    )
            text_in_spdf = chat4.send_message("Mô tả lại toàn bộ nội dung trong file audio.")
            if prompt := st.chat_input("nhập câu hỏi vào đây..."):
                chat_processing(prompt, text_in_spdf)

    elif choice == "Chat with video":
        st.subheader("Chat with your video file")
        uploaded_files4 = st.file_uploader("Choose your mp4 or mov file",  type=['mp4','mov'], accept_multiple_files=False)
        clear = get_clear()
        if clear:
            if "messages" in st.session_state:
                del st.session_state.messages
        reload_achat()
        if uploaded_files4:
            file_upload = client_gemini.files.upload(file='./odata/'+uploaded_files4.name)
            chat4 = client_gemini.chats.create(model=MODEL_ID,
                    history=[
                        types.Content(
                            role="user",
                            parts=[
    
                                    types.Part.from_uri(
                                        file_uri=file_upload.uri,
                                        mime_type=file_upload.mime_type),
                                    ]
                            ),
                        ]
                    )
            text_in_spdf = chat4.send_message("Mô tả lại toàn bộ nội dung video.")
            if prompt := st.chat_input("nhập câu hỏi vào đây..."):
                chat_processing(prompt, text_in_spdf)

if __name__ == "__main__":
    client_gemini = genai.Client(api_key='')
    MODEL_ID = "gemini-2.0-flash"
    langfuse_class = LangfuseHandler()
    setup_page()
    main()


