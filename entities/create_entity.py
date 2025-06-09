import uuid
import os

import streamlit as st

UPLOAD_FOLDER = "RAG_files"

@st.dialog("Create New Entity")
def create_entity(new_title):
    title = st.text_input("Title", value=new_title, key="create_entity_title")
    tab1, tab2 = st.tabs(["PDF files", "Wikipedia link"])

    with tab1:
        uploaded_files = st.file_uploader("Choose files", type=["txt", "pdf"], accept_multiple_files=True, key="create_entity_file_uploader")

    with tab2:
        link = st.text_input("Insert link", value="", key="create_entity_link_input")

    if st.button("Submit", type="primary"):
        entity_uuid = str(uuid.uuid1())
        entity_folder = os.path.join(UPLOAD_FOLDER, entity_uuid)
        os.makedirs(entity_folder, exist_ok=True)
        sources = []
        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_path = os.path.join(entity_folder, uploaded_file.name)
                # Mark as not loaded yet
                sources.append({
                    "type": "pdf",
                    "filepath": file_path,
                    "filename": uploaded_file.name,
                    "was_loaded": False
                })
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
        if link:
            sources.append({"type": "wiki_link", "link": link})
        st.session_state.entities.append({
            "uuid": entity_uuid,
            "title": title,
            "sources": sources
        })
        st.rerun()
