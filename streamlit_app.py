import streamlit as st
from openai import OpenAI
import pymupdf
import fitz

import time


client = OpenAI(api_key = st.secrets["API_KEY"], base_url = st.secrets["BASE_URL"])

st.title("🗨️ LLM chat bot")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Let's start chatting! 👇"}]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def load_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

with st.sidebar:
    file_path = st.file_uploader("Choose a file", key = "pdf", type="pdf")

    if file_path is not None:
        
        file_text = load_pdf(load_pdf)
        print(file_text)

# Accept user input
if prompt := st.chat_input("What is up?", key = "text"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        assistant_response = client.chat.completions(model = st.secrets["MODEL"], messages = st.session.state.messages)

        # Simulate stream of response with milliseconds delay
        for chunk in assistant_response.split():
            full_response += chunk + " "
            time.sleep(0.05)
            # Add a blinking cursor to simulate typing
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})