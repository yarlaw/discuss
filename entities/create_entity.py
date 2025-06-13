import uuid
import os

import streamlit as st
from utils.models import list_available_models, get_model_family
from utils.constants import DEFAULT_MODEL_NAME, UPLOAD_FOLDER

@st.dialog("Create New Entity")
def create_entity(new_title):
    title = st.text_input("Title", value=new_title, key="create_entity_title")
    
    available_models = list_available_models()
    model_labels = [f"{model} ({get_model_family(model)})" for model in available_models]
    model_index = available_models.index(DEFAULT_MODEL_NAME) if DEFAULT_MODEL_NAME in available_models else 0
    
    selected_model_label = st.selectbox(
        "LLM Model",
        options=model_labels,
        index=model_index,
        key="create_entity_model",
        help="Select the LLM model for this entity"
    )
    
    selected_model = selected_model_label.split(" (")[0]
    
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
                sources.append({
                    "type": "pdf",
                    "filepath": file_path,
                    "filename": uploaded_file.name,
                    "was_loaded": False
                })
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
        if link:
            sources.append({
                "type": "wiki", 
                "filepath": link,
                "was_loaded": False
            })
        st.session_state.entities.append({
            "uuid": entity_uuid,
            "title": title,
            "model": selected_model, 
            "sources": sources
        })
        
        st.session_state.materials_loaded = False
        st.session_state._entities_changed = True

        st.rerun()
