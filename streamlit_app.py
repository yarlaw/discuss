import os
import time
import uuid

from langchain_core.prompts import ChatPromptTemplate
import streamlit as st

from chat_openrouter import ChatOpenRouter
from docloader import load_documents_from_folder, load_pdf
from embedder import create_index

from entities.create_entity import create_entity
from entities.edit_entity import edit_entity
from entities.remove_entity import remove_entity
 
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
    st.session_state.entities = [{"uuid": uuid.uuid1, "title": "Entity 1"}]

with st.sidebar:
    st.title("Configure entities")

    st.header("Global settings")

    st.slider(
        "Discuss circles",
        min_value=1,
        max_value=5,
        value=3,
        key="discuss_circles",
        help="Number of discuss circles"
    )

    st.header("Entities")
    # Dynamically render expanders for each entity
    for idx, entity in enumerate(st.session_state.entities):
        # st.button(entity["title"], key=f"entity_button_{idx}")

        with st.expander(f"**{entity['title']}**", expanded=False):
            
            # TODO: Display the entity's model
            st.caption("Used model is: mistral")

            # TODO: Display the entity's type of info
            st.text("Type of info: PDF files")

            col1, col2 = st.columns(2)
                
            with col1:
                if st.button(
                    "Edit", 
                        key=f"edit_{idx}",
                        use_container_width=True,
                        type="primary",
                        help=f"Edit {entity['title']}"
                ):
                    edit_entity(entity["uuid"],entity["title"])
                
            with col2:
                if st.button(
                    "Remove", 
                        key=f"remove_{idx}",
                        use_container_width=True,
                        help=f"Remove {entity['title']}"
                ):
                    remove_entity(entity["uuid"])
            

    st.write("")
    # Button to add a new entity at the bottom
    if st.button("Add new entity", type="primary", use_container_width=True):
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