import streamlit as st

import os

UPLOAD_FOLDER = "RAG_files"

@st.dialog("Edit Entity")
def edit_entity(id,old_title):
    title = st.text_input("Title", value=old_title, key="create_entity_title")
    
    tab1, tab2 = st.tabs(["PDF files", "Wikipedia link"])

    with tab1:
        uploaded_file = st.file_uploader("Choose files", type=["txt", "pdf"], accept_multiple_files=True)

    with tab2:
        link = st.text_input("Insert link", value="", key="create_entity_link")

    if st.button("Submit", type="primary"):
        for item in st.session_state.entities:
            if item["uuid"] == id:
                item["title"] = title
                break 
        
        st.rerun()
