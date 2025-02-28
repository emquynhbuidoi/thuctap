import streamlit as st
import time
from pypdf import PdfWriter
from google import genai
from google.genai import types
from autogen_agentchat.messages import TextMessage
import requests
API_URL="http://127.0.0.1:9999/chat"

# from langfuse import Langfuse


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

def chat_processing(prompt: str, txt_in_file: str = None):
    with st.chat_message(name="user", avatar="🤬"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message(name="assistant", avatar="🤓"):
        if txt_in_file:
            prompt = "Thông tin cung cấp được lấy từ file: " + txt_in_file.text + '\n Câu hỏi: ' + prompt
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
            file_upload = client_gemini.files.upload(file='./odata/'+uploaded_files.name)
            chat2 = client_gemini.chats.create(model=MODEL_ID,
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
            text_in_spdf = chat2.send_message("Mô tả lại toàn bộ nội dung trong file")
            if prompt := st.chat_input("nhập câu hỏi vào đây..."):
                chat_processing(prompt, text_in_spdf)
        
    elif choice == "Chat with many PDFs":
        st.subheader("Chat with your PDF file")
        clear = get_clear()
        if clear:
            if "messages" in st.session_state:
                del st.session_state.messages
        reload_achat()
        
        uploaded_files2 = st.file_uploader("Choose 1 or more files",  type=['pdf'], accept_multiple_files=True)
        print("uploaded_files2: ", uploaded_files2)
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
    client_gemini = genai.Client(api_key='AIzaSyA2DAuvWV3wphi6r0o-74NLUaRXFDjPHc8')
    MODEL_ID = "gemini-2.0-flash"
    setup_page()
    main()


