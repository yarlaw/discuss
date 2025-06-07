import os
import time

from langchain_core.prompts import ChatPromptTemplate
import streamlit as st

from chat_openrouter import ChatOpenRouter
from docloader import load_documents_from_folder, load_pdf
from embedder import create_index

from ui.create_entity import create_entity
 
template = """
Give concrete answers without too many wor1ds.
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

documents = []

if "entities" not in st.session_state:
    st.session_state.entities = [{"title": "Entity 1"}]

with st.sidebar:
    st.header("Configure characters")
    # Dynamically render expanders for each entity
    for idx, entity in enumerate(st.session_state.entities):
        st.button(entity["title"], key=f"entity_button_{idx}")

            

    # Button to add a new entity at the bottom
    if st.button("Add new entity"):
        create_entity("Entity " + str(idx + 1))
    

# if uploaded_files:
#     for uploaded_file in uploaded_files:
#         file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
#         with open(file_path, "wb") as f:
#             f.write(uploaded_file.getbuffer())
#     st.write("Files uploaded successfully!")
#     documents = load_documents_from_folder(UPLOAD_FOLDER)
#     st.session_state.faiss_index = create_index(documents)
#     st.write("Files indexed successfully!")
#     st.session_state.retrieve_files = True

st.title("🗨️ LLM discussions bot")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Let's start chatting! 👇"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])    


question = st.chat_input("What is up?", key = "text")

if question:
    with st.chat_message("user"):
        st.markdown(question)

    answer = answer_question(question, documents, model).content
    print(answer)

    if answer is not None:
        with st.chat_message("assistant"):
            message_placeholder = st.markdown("")
            full_response = ""

            for chunk in answer.split():
                full_response += chunk + " "
                time.sleep(0.05)
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})