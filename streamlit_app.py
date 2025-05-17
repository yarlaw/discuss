import os
import time

from langchain_core.prompts import ChatPromptTemplate
import streamlit as st

from chat_openrouter import ChatOpenRouter
from docloader import load_documents_from_folder, load_pdf
from embedder import create_index
 
template = """
Give concreate answers without too many wor1ds.
If you don't know the answer just say that.
Question: {question}
Context: {context}
Answer: 
"""

selected_model = "mistralai/mistral-7b-instruct:free"
model = ChatOpenRouter(model_name = selected_model)

def answer_question(question, documents, model):
    context = "\n\n".join([doc["text"] for doc in documents])
    promt = ChatPromptTemplate.from_template(template)
    chain = promt | model
    return chain.invoke({"question": question, "context": context})

if "query" not in st.session_state:
    st.session_state.query = ""
if "context" not in st.session_state:
    st.session_state.context = ""
if "answer" not in st.session_state:
    st.session_state.answer = ""

UPLOAD_FOLDER = "RAG_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

with st.sidebar:
    st.header("Upload files")
    uploaded_files = st.file_uploader("Choose files", type=["txt", "pdf"], accept_multiple_files=True)
    if st.button("Clear all files"):
        for file in os.listdir(UPLOAD_FOLDER):
            os.remove(os.path.join(UPLOAD_FOLDER, file))
        st.write("All files cleared!")

    if st.button("Load PDF"):
        pdf_file = st.file_uploader("Choose a PDF file", type="pdf")
        if pdf_file:
            load_pdf(pdf_file, UPLOAD_FOLDER)
            st.write("PDF loaded successfully!")

if uploaded_files:
    for uploaded_file in uploaded_files:
        file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
    st.write("Files uploaded successfully!")
    documents = load_documents_from_folder(UPLOAD_FOLDER)
    st.session_state.faiss_index = create_index(documents)
    st.write("Files indexed successfully!")
    st.session_state.retrieve_files = True


st.title("🗨️ LLM chat bot")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Let's start chatting! 👇"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])    


question = st.chat_input("What is up?", key = "text")
answer = answer_question(question, documents, model)

with st.chat_message("user"):
    st.markdown(question)

with st.chat_message("assistant"):
    message_placeholder = st.empty()
    full_response = ""

    for chunk in answer.split():
        full_response += chunk + " "
        time.sleep(0.05)
        message_placeholder.markdown(full_response + "▌")
    message_placeholder.markdown(full_response)
st.session_state.messages.append({"role": "assistant", "content": full_response})