import uuid
import os

import streamlit as st

from utils.docloader import load_documents_from_folder, load_pdf

UPLOAD_FOLDER = "RAG_files"

@st.dialog("Create New Entity")
def create_entity(new_title):
    title = st.text_input("Title", value=new_title, key="create_entity_title")
    tab1, tab2 = st.tabs(["PDF files", "Wikipedia link"])

    with tab1:
        uploaded_files = st.file_uploader("Choose files", type=["txt", "pdf"], accept_multiple_files=True, key="create_entity_file_uploader")

    with tab2:
        link = st.text_input("Insert link", value="", key="create_entity_link")

    if st.button("Submit", type="primary"):
        entity_uuid = str(uuid.uuid1())
        entity_folder = os.path.join(UPLOAD_FOLDER, entity_uuid)
        os.makedirs(entity_folder, exist_ok=True)
        documents = []
        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_path = os.path.join(entity_folder, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                documents.append({"filename": uploaded_file.name, "path": file_path})
        st.session_state.entities.append({
            "uuid": entity_uuid,
            "title": title,
            "documents": documents,
            "wiki_links": [link] if link else [],
            })
        st.rerun()
