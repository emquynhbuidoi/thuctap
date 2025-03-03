# https://github.com/pavanbelagatti/Chat-PDF-LlamaIndex/blob/main/streamlit_app.py

import streamlit as st
import time
from pypdf import PdfWriter
from google import genai
from google.genai import types
from autogen_agentchat.messages import TextMessage
import requests


# from langfuse import Langfuse
from pdf_manager import pdf_parser_nodes_index
from sentence_transformers import SentenceTransformer
import torch

torch.classes.__path__ = []
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
#VietNamese embedding: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2?library=sentence-transformers
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2").to(device)

from config import INDEX_NAME_PDF
from search_elasticsearch import hybrid_search
import asyncio

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
     # Tạo một placeholder để hiển thị phản hồi từng từ một
    message_placeholder = st.empty()
    response_text = ""
    for word in response.split():
        response_text += word + " "
        message_placeholder.markdown(response_text)
        time.sleep(0.05)  # Hiệu ứng gõ chữ

def chat_processing(prompt: str, context_from_pdf: str = None):
    with st.chat_message(name="user", avatar="🤬"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message(name="assistant", avatar="🤓"):
        if context_from_pdf:
            prompt = "Thông tin cung cấp được lấy từ file: " + context_from_pdf + '\n Dựa vào file trả lời câu hỏi: ' + prompt
        
        API_URL="http://127.0.0.1:9999/chat"
        payload = {"prompt": prompt} 
        response = requests.post(url=API_URL, json=payload)
        if response.status_code == 200:
            effect_chat(response.json())
        else:
            effect_chat("Unknown Messages")
    st.session_state.messages.append({"role": "assistant", "content": response.json()})

def main():
    choice = get_choice()
    if choice == "Normal Chat":
        # st.subheader("Normal Chat")
        clear = get_clear()
        if clear:
            if "messages" in st.session_state:
                del st.session_state.messages
        reload_achat()

        if prompt := st.chat_input("nhập câu hỏi vào đây..."):
           chat_processing(prompt)

    elif choice == "Chat with a PDF":
        st.subheader("Chat with a PDF")
        uploaded_files = st.file_uploader("Choose your pdf file", type=['pdf'], accept_multiple_files=False)
        clear = get_clear()
        if clear:
            if "messages" in st.session_state:
                del st.session_state.messages
        reload_achat()
        if uploaded_files:
            # file_upload = client_gemini.files.upload(file='./odata/'+uploaded_files.name)
            # chat2 = client_gemini.chats.create(model=MODEL_ID,
            #         history=[
            #             types.Content(
            #                 role="user",
            #                 parts=[
    
            #                         types.Part.from_uri(
            #                             file_uri=file_upload.uri,
            #                             mime_type=file_upload.mime_type),
            #                         ]
            #                 ),
            #             ]
            #         )
            # text_in_spdf = chat2.send_message("Mô tả lại toàn bộ nội dung trong file")

            if prompt := st.chat_input("nhập câu hỏi vào đây..."):
                pdf_parser_nodes_index(uploaded_files, model=model)
                API_URL="http://127.0.0.1:9999/hybrid_search"
                payload = {
                    "search_query": prompt,
                    'top_k': 3,
                    'index_name': INDEX_NAME_PDF,
                } 
                response = requests.post(url=API_URL, json=payload)
                if response.status_code == 200:
                    context_from_pdf = response.json()
                else:
                    context_from_pdf = "Unknown Messages"

                # print("response.status_code: ", response.status_code)
                print("context_from_pdf: ", context_from_pdf)
                chat_processing(prompt, context_from_pdf)



        
    elif choice == "Chat with many PDFs":
        st.subheader("Chat with your PDF file")
        uploaded_files2 = st.file_uploader("Choose 1 or more files",  type=['pdf'], accept_multiple_files=True)
        clear = get_clear()
        if clear:
            if "messages" in st.session_state:
                del st.session_state.messages
        reload_achat()
        if uploaded_files2:
            merger = PdfWriter()
            for file in uploaded_files2:
                    merger.append(file)

            fullfile = "./odata/merged_all_files.pdf"
            merger.write(fullfile)
            merger.close()

            file_upload = client_gemini.files.upload(file= fullfile) 
            chat2b = client_gemini.chats.create(model=MODEL_ID,
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
            text_in_spdf = chat2b.send_message("Mô tả lại toàn bộ nội dung trong file")
            if prompt := st.chat_input("nhập câu hỏi vào đây..."):
                chat_processing(prompt, text_in_spdf)

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
    setup_page()
    main()


