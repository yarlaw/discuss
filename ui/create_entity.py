import streamlit as st

import os

UPLOAD_FOLDER = "RAG_files"

@st.dialog("Create New Entity")
def create_entity(new_title):
    title = st.text_input("Title", value=new_title, key="create_entity_title")
    
    tab1, tab2 = st.tabs(["PDF files", "Wikipedia link"])

    with tab1:
        uploaded_file = st.file_uploader("Choose files", type=["txt", "pdf"], accept_multiple_files=True)

    with tab2:
        link = st.text_input("Insert link", value="", key="create_entity_link")

    if st.button("Submit", type="primary"):
        st.session_state.entities.append({"title": title})
        st.rerun()
