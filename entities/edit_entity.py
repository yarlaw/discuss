import streamlit as st
import os

from utils.models import list_available_models, get_model_family
from utils.constants import DEFAULT_MODEL_NAME, UPLOAD_FOLDER

@st.dialog("Edit Entity")
def edit_entity(id, old_title):
    title = st.text_input("Title", value=old_title, key="edit_entity_title")
    
    current_entity = next((item for item in st.session_state.entities if item["uuid"] == id), None)
    
    available_models = list_available_models()
    model_labels = [f"{model} ({get_model_family(model)})" for model in available_models]
    
    current_model = current_entity.get("model", DEFAULT_MODEL_NAME) if current_entity else DEFAULT_MODEL_NAME
    model_index = available_models.index(current_model) if current_model in available_models else 0
    
    selected_model_label = st.selectbox(
        "LLM Model",
        options=model_labels,
        index=model_index,
        key=f"edit_entity_model_{id}",
        help="Select the LLM model for this entity"
    )
    
    selected_model = selected_model_label.split(" (")[0]

    def show_and_select_sources_to_remove(current_entity):
        sources_to_remove = []
        if current_entity and current_entity.get("sources"):
            st.markdown("**Previously sources to keep:**")
            for idx, src in enumerate(current_entity["sources"]):
                label = src["filename"] if src["type"] == "pdf" else src["filepath"]
                keep = st.checkbox(
                    f"{src['type'].capitalize()}: {label}", key=f"keep_{id}_{idx}", value=True
                )
                if not keep:
                    sources_to_remove.append(src)
        return sources_to_remove
    
    sources_to_remove = show_and_select_sources_to_remove(current_entity)
    
    tab1, tab2 = st.tabs(["PDF files", "Wikipedia link"])

    def handle_file_uploads(entity_folder):
        uploaded_files = st.file_uploader(
            "Choose files", type=["txt", "pdf"], accept_multiple_files=True, key=f"edit_entity_file_uploader_{id}"
        )
        sources = []
        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_path = os.path.join(entity_folder, uploaded_file.name)
                sources.append({
                    "type": "pdf",
                    "filepath": file_path,
                    "filename": uploaded_file.name,
                    "_uploaded_file": uploaded_file,
                    "was_loaded": False
                })
        return sources

    


    with tab1:
        entity_folder = os.path.join(UPLOAD_FOLDER, str(id))
        os.makedirs(entity_folder, exist_ok=True)
        new_sources = handle_file_uploads(entity_folder)
        current_entity = next((item for item in st.session_state.entities if item["uuid"] == id), None)

    with tab2:
        current_wiki = ""
        if current_entity and current_entity.get("sources"):
            for src in current_entity["sources"]:
                if src["type"] == "wiki":
                    current_wiki = src["filepath"]
                    break
        
        link = st.text_input("Insert link", value=current_wiki, key=f"edit_entity_link_{id}")
        
        submit_wiki = st.button("Submit|Replace Wiki Link", key=f"submit_wiki_{id}", use_container_width=True)
        if submit_wiki and link:
            if "wikipedia.org" in link:
                st.success("✅ Wikipedia link submitted|replaced successfully!")
            else:
                st.warning("⚠️ Link doesn't appear to be a Wikipedia page.")
        
        persona_mode = st.checkbox("Persona Mode", 
                                value=current_entity.get("persona_mode", False) if current_entity else False, 
                                key=f"edit_entity_persona_mode_{id}", 
                                help="When enabled, the entity will assume the persona of the person from the Wikipedia link")
        
        if persona_mode and link and "wikipedia.org" in link:
            st.info("📌 Persona Mode enabled: This entity will speak as the person from the Wikipedia page")
        elif persona_mode and link:
            st.warning("⚠️ Link doesn't appear to be a Wikipedia page about a person. Persona mode may not work correctly.")
        elif persona_mode and not link:
            st.warning("⚠️ Please enter a Wikipedia link to use Persona Mode")

    if st.button("Submit", type="primary"):
        for item in st.session_state.entities:
            if item["uuid"] == id:
                item["title"] = title
                item["model"] = selected_model
                if sources_to_remove:
                    for src in sources_to_remove:
                        if src in item["sources"]:
                            item["sources"].remove(src)
                            if src["type"] == "pdf":
                                try:
                                    os.remove(src["filepath"])
                                except Exception:
                                    pass
                new_pdf_added = False
                wiki_changed = False
                
                if new_sources:
                    if "sources" not in item:
                        item["sources"] = []
                    for src in new_sources:
                        if "_uploaded_file" in src:
                            os.makedirs(os.path.dirname(src["filepath"]), exist_ok=True)
                            with open(src["filepath"], "wb") as f:
                                f.write(src["_uploaded_file"].getbuffer())
                            del src["_uploaded_file"]
                        if not any(existing.get("type") == src["type"] and existing.get("filepath") == src["filepath"] for existing in item["sources"]):
                            item["sources"].append(src)
                            if src["type"] == "pdf":
                                new_pdf_added = True
                if link:
                    if "sources" not in item:
                        item["sources"] = []
                    
                    existing_wiki = next((s for s in item["sources"] if s["type"] == "wiki"), None)
                    
                    if existing_wiki:
                        if existing_wiki["filepath"] != link:
                            existing_wiki["filepath"] = link
                            existing_wiki["was_loaded"] = False
                            wiki_changed = True
                    else:
                        item["sources"].append({
                            "type": "wiki", 
                            "filepath": link,
                            "was_loaded": False
                        })
                        wiki_changed = True
                else:
                    existing_wiki = next((s for s in item["sources"] if s["type"] == "wiki"), None)
                    if existing_wiki:
                        item["sources"].remove(existing_wiki)
                        wiki_changed = True
                
                item["persona_mode"] = persona_mode
                
                if new_pdf_added or wiki_changed:
                    st.session_state.materials_loaded = False
                    st.session_state._entities_changed = True
                
                break
        st.rerun()
