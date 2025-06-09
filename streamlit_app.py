import os
import time
import uuid

import streamlit as st
from langchain_core.prompts import ChatPromptTemplate

from chat_openrouter import ChatOpenRouter
import utils.docloader as docloader
import utils.embedder as embedder

from entities.create_entity import create_entity
from entities.edit_entity import edit_entity
from entities.remove_entity import remove_entity

UPLOAD_FOLDER = "RAG_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

template = """
Give concrete answers without too many wor1ds.
If you don't know the answer just say that.
Question: {question}
Context: {context}
Answer: 
"""

amount_of_cycles = 3

selected_model = "mistralai/mistral-7b-instruct:free"
model = ChatOpenRouter(model_name=selected_model)

def answer_question(question, documents, model):
    context = "\n\n".join([doc["text"] for doc in documents])
    promt = ChatPromptTemplate.from_template(template)
    chain = promt | model
    return chain.invoke({"question": question, "context": context})

def load_all_entity_materials():
    """
    Loads and indexes all PDF sources for each entity, marking each source with 'was_loaded'.
    Skips files that have not changed since last load. Updates progress bar.
    """
    entity_materials = st.session_state.setdefault("entity_materials", {})
    processed_files = st.session_state.setdefault("_processed_files", {})
    total_entities = len(st.session_state.entities)
    for idx, entity in enumerate(st.session_state.entities):
        pdf_sources = [src for src in entity.get("sources", []) if src["type"] == "pdf"]
        docs_to_index = []
        entity_processed = processed_files.get(entity["uuid"], {})
        for src in pdf_sources:
            file_path = src["filepath"]
            filename = src["filename"]
            mtime = os.path.getmtime(file_path) if os.path.exists(file_path) else None
            # Default: not loaded
            src["was_loaded"] = False
            # Skip if already processed and unchanged
            if filename in entity_processed and entity_processed[filename] == mtime:
                src["was_loaded"] = True
                continue
            try:
                text = docloader.load_pdf(file_path)
                docs_to_index.append({"filename": filename, "text": text})
                if mtime:
                    entity_processed[filename] = mtime
                src["was_loaded"] = True
            except Exception:
                pass
        processed_files[entity["uuid"]] = entity_processed
        if docs_to_index:
            entity_materials[entity["uuid"]] = embedder.create_index(docs_to_index)
        elif entity["uuid"] not in entity_materials:
            entity_materials[entity["uuid"]] = None
        st.session_state.loading_progress = (idx + 1) / total_entities
    st.session_state.materials_loaded = True
    st.session_state._entities_changed = False

# --- Streamlit session state initialization ---
if "query" not in st.session_state:
    st.session_state.query = ""
if "context" not in st.session_state:
    st.session_state.context = ""
if "answer" not in st.session_state:
    st.session_state.answer = ""
if "entities" not in st.session_state:
    st.session_state.entities = [{"uuid": uuid.uuid1, "title": "Entity 1"}]
if "materials_loaded" not in st.session_state:
    st.session_state.materials_loaded = False
if "loading_progress" not in st.session_state:
    st.session_state.loading_progress = 0.0



with st.sidebar:
    st.title("Configure entities")
    st.header("Global settings")
    st.slider(
        "Discuss circles",
        min_value=1,
        max_value=5,
        value=amount_of_cycles,
        key="discuss_circles",
        help="Number of discuss circles"
    )
    st.header("Entities")
    for idx, entity in enumerate(st.session_state.entities):
        with st.expander(f"**{entity['title']}**", expanded=False):
            st.caption("Used model is: mistral")
            pdf_count = len([src for src in entity.get("sources", []) if src["type"] == "pdf"])
            wiki_count = len([src for src in entity.get("sources", []) if src["type"] == "wiki_link"])
            if pdf_count > 0:
                st.badge(f"PDFs: {pdf_count}", color="violet", icon="📄")
            if wiki_count > 0:
                st.badge(f"Wiki: {wiki_count}", color="blue", icon="🌐")
            if len([src for src in entity]) == 0:
                st.markdown(":orange-badge[⚠️No sources attached]")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "Edit",
                    key=f"edit_{idx}",
                    use_container_width=True,
                    type="primary",
                    help=f"Edit {entity['title']}"
                ):
                    edit_entity(entity["uuid"], entity["title"])
            with col2:
                if st.button(
                    "Remove",
                    key=f"remove_{idx}",
                    use_container_width=True,
                    help=f"Remove {entity['title']}"
                ):
                    remove_entity(entity["uuid"])
        if st.session_state.get("_entities_changed", False):
            st.session_state.materials_loaded = False
            st.session_state.loading_progress = 0.0
    if st.button("Add new entity", type="primary", use_container_width=True):
        create_entity("Entity " + str(len(st.session_state.entities) + 1))
        st.session_state._entities_changed = True
    st.write("")
    st.header("Model activation status")

    # Count statistics for all sources
    if not st.session_state.materials_loaded:
        st.progress(st.session_state.loading_progress, text="Loading entity materials...")
        if st.button("Activate & Load All Materials", type="primary", use_container_width=True):
            load_all_entity_materials()
    else:
        st.success("All materials loaded and up to date.")

    total_pdfs = sum(len([src for src in entity.get("sources", []) if src["type"] == "pdf"]) for entity in st.session_state.entities)
    total_links = sum(len([src for src in entity.get("sources", []) if src["type"] == "wiki_link"]) for entity in st.session_state.entities)
    loaded_pdfs = sum(len([src for src in entity.get("sources", []) if src["type"] == "pdf" and src.get("was_loaded")]) for entity in st.session_state.entities)
    st.markdown(f"**PDFs loaded:** {loaded_pdfs} / {total_pdfs}  ")
    st.markdown(f"**Wiki links:** {total_links}")


st.title("🗨️ LLM discussions bot")

if not st.session_state.materials_loaded:
    st.info("Please activate and load all materials before starting the discussion.")
    st.chat_input("Put the theme to discussion", key="text", disabled=True)
else:
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Let's start chatting! 👇"}]
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    question = st.chat_input("Put the theme to discussion", key="text")
    if question:
        with st.chat_message("user"):
            st.markdown(question)
        # You may want to update this to use entity_materials for retrieval
        answer = answer_question(question, [], model).content
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