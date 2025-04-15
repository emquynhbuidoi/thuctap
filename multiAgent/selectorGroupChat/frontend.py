import streamlit as st
import requests
from typing import Optional
import tempfile
from langfuse_ne import LangfuseHandler

def setup_page():
    """
        hàm tạo layout cho streamlit
    """
    if 'page_configured' not in st.session_state:
        print("[LOG]: page_configured")
        st.set_page_config(page_title="🐱‍🏍 Supter Chatbot", layout="centered")
        st.session_state.page_configured = True

    st.header("Multi Agent Chatbot" )
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
                                                "Chat with a PDF"])
    return choice

def get_session():
    """
        hàm trả về danh sách id của selected_session user chọn ở sidebar
    """
    sessions =  st.session_state.langfuse.fetch_sesions()
    if not sessions:
        st.sidebar.warning("Không có session nào được lưu hôm nay.")
        return None
    session_list_id = [session.id for session in sessions]
    session_options = [(None, "Cuộc Hội Thoại Mới")]  
    for session_id in session_list_id:
        traces = st.session_state.langfuse.fetch_traces(session_id)
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

        traces = st.session_state.langfuse.fetch_traces(session_id=session_id_selected)
        for trace in traces:
            st.session_state.messages.append({"role": "user", "content": trace.input})
            st.session_state.messages.append({"role": "assistant", "content": trace.output})
        for message in st.session_state.messages:
            with st.chat_message(message['role'],  avatar="🤓" if message['role'] == "assistant" else "🤬"):
                st.markdown(message['content'])
    elif session_id_selected == st.session_state.session_id:                                       # Đây là trường hợp đang chat trong session mới
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        for message in st.session_state.messages:
            with st.chat_message(message['role'],  avatar="🤓" if message['role'] == "assistant" else "🤬"):
                st.markdown(message['content'])
    elif session_id_selected != st.session_state.session_id:    
        st.session_state.session_id = session_id_selected                                           # Đây là trường hợp đang chat với session cũ muốn qua session mới thì reset lại ui
        st.session_state.messages = []

        
def chat_processing(prompt: str, session_id_choiced: str = None, tmp_file_path: str=None):
    """
        input:
            prompt: str |   Câu hỏi đầu vào của người dùng.
            session_id_choiced: str | key session_id_choiced đang thực hiện đối thoại.
            tmp_file_path: str| đường dẫn tạm thời tới file pdf đã được upload

    """
    with st.chat_message(name="user", avatar="🤬"):
        if 'Thông tin:' in prompt:
            prompt_media = prompt
            prompt_media = prompt_media.split("Thông tin:")[0]
            prompt_media = prompt_media.replace('Câu hỏi:', " ").strip()
            st.markdown(prompt_media)
        else:
            st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message(name="assistant", avatar="🤓"):
        API_URL="http://127.0.0.1:9999/chat"
        payload = {
            "prompt": prompt,
            "session_id_choiced": session_id_choiced,
            "tmp_file_path": tmp_file_path
        } 
        response = requests.post(url=API_URL, json=payload)
        # print('\n\nresponse.json(): ', response.json())
        if response.status_code == 200:
            st.markdown(response.json())
        else:
            st.markdown("Unknown Messages")
    st.session_state.messages.append({"role": "assistant", "content": response.json()})

def main():
    choice = get_choice()
    session_id_choiced = get_session()
    
    if choice == "Normal Chat":
        clear = get_clear()
        if clear:
            if "messages" in st.session_state:
                del st.session_state.messages
        reload_achat(session_id_choiced)

        prompt = st.chat_input("Nhập câu hỏi vào đây...")
        if prompt and prompt.strip():
           chat_processing(prompt, session_id_choiced=session_id_choiced, tmp_file_path=None)
            
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
            prompt = st.chat_input("Nhập câu hỏi vào đây...")
            if prompt and prompt.strip():
                if 'file' not in st.session_state or st.session_state.file != uploaded_files.name:      # Chỉ parser file khi là lần đâu hoặc là file mới
                    st.session_state.file = uploaded_files.name
                    API_URL="http://127.0.0.1:9999/parser_index"
                    payload={
                        'tmp_file_path': tmp_file_path
                    }
                    response = requests.post(url=API_URL, json=payload)
                    if response.status_code != 200:
                        print("Lõi trong quá trình PARSER INDEX")
                chat_processing(prompt=prompt, session_id_choiced=session_id_choiced, tmp_file_path=tmp_file_path)

if __name__ == "__main__":
    print("[LOG]: CHAY LAI STREAMLIT")
    if 'langfuse' not in st.session_state:
        print("[LOG]: langfuse session_state")
        st.session_state.langfuse = LangfuseHandler()
    
    setup_page()
    main()
