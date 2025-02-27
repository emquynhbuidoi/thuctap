import streamlit as st
import time
from pypdf import PdfWriter
from autogen_agentchat.messages import TextMessage
import asyncio
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
    # print("KAKAKA: ", response)
     # Tạo một placeholder để hiển thị phản hồi từng từ một
    message_placeholder = st.empty()
    response_text = ""
    for word in response.split():
        response_text += word + " "
        message_placeholder.markdown(response_text)
        time.sleep(0.05)  # Hiệu ứng gõ chữ

def chat_processing(prompt):
    with st.chat_message(name="user", avatar="🤬"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message(name="assistant", avatar="🤓"):
        payload = {"prompt": prompt} 
        response = requests.post(url=API_URL, json=payload)
        # print(response.json())
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

if __name__ == "__main__":
    setup_page()
    main()


