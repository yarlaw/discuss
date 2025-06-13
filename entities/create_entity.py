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
        # Initialize a key in session state to track when to clear the link
        if "clear_create_link" not in st.session_state:
            st.session_state["clear_create_link"] = False
            
        # If clear link was pressed in a previous run, use empty string as initial value
        initial_value = "" if st.session_state["clear_create_link"] else ""
        if st.session_state["clear_create_link"]:
            st.session_state["clear_create_link"] = False  # Reset the flag
        
        link = st.text_input("Insert link", value=initial_value, key="create_entity_link_input")
        
        submit_wiki = st.button("Submit Wiki Link", key="submit_wiki_create", use_container_width=True)
        if submit_wiki and link:
            if "wikipedia.org" in link:
                st.success("✅ Wikipedia link submitted successfully!")
            else:
                st.warning("⚠️ Link doesn't appear to be a Wikipedia page.")
        
        persona_mode = st.checkbox("Persona Mode", 
                                   value=False, 
                                   key="create_entity_persona_mode", 
                                   help="When enabled, the entity will assume the persona of the person from the Wikipedia link")
        
        if persona_mode and link and "wikipedia.org" in link:
            st.info("📌 Persona Mode enabled: This entity will speak as the person from the Wikipedia page")
        elif persona_mode and link:
            st.warning("⚠️ Link doesn't appear to be a Wikipedia page about a person. Persona mode may not work correctly.")
        elif persona_mode and not link:
            st.warning("⚠️ Please enter a Wikipedia link to use Persona Mode")

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
            "persona_mode": persona_mode,
            "sources": sources
        })
        
        st.session_state.materials_loaded = False
        st.session_state._entities_changed = True

        st.rerun()
