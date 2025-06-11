import streamlit as st
from entities.create_entity import create_entity
from entities.remove_entity import remove_entity
from entities.edit_entity import edit_entity

from utils.material_loader import load_all_entity_materials
from utils.constants import DEFAULT_CYCLES
from utils.models import get_model_family

@st.fragment
def render_sidebar():
    st.title("Configure entities")
        
    st.header("Global settings")
    st.slider(
        "Discuss circles",
        min_value=1,
        max_value=5,
        value=DEFAULT_CYCLES,
        key="discuss_circles",
        help="Number of discuss circles"
    )


    st.header("Entities")
    for idx, entity in enumerate(st.session_state.entities):
        with st.expander(f"**{entity['title']}**", expanded=False):
            model_name = entity.get("model", "mistral-7b")
            model_family = get_model_family(model_name)
            st.caption(f"Model: {model_name} ({model_family})")
                
            pdf_count = len([src for src in entity.get("sources", []) if src["type"] == "pdf"])
            wiki_count = len([src for src in entity.get("sources", []) if src["type"] == "wiki_link"])
                
            if pdf_count > 0:
                st.badge(f"PDFs: {pdf_count}", color="violet", icon="📄")
            if wiki_count > 0:
                st.badge(f"Wiki: {wiki_count}", color="blue", icon="🌐")
            if not entity.get("sources") or len(entity.get("sources", [])) == 0:
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
    if not st.session_state.materials_loaded:
        st.progress(st.session_state.loading_progress, text="Loading entity materials...")
        if st.button("Activate & Load All Materials", type="primary", use_container_width=True):
            load_all_entity_materials()
    else:
        st.success("All materials loaded and up to date.")

    total_pdfs = sum(len([src for src in entity.get("sources", []) if src["type"] == "pdf"]) 
    for entity in st.session_state.entities)
    loaded_pdfs = sum(len([src for src in entity.get("sources", []) if src["type"] == "pdf" and src.get("was_loaded")]) 
        for entity in st.session_state.entities)
        
    st.markdown(f"**PDFs loaded:** {loaded_pdfs} / {total_pdfs}")

    total_links = sum(len([src for src in entity.get("sources", []) if src["type"] == "wiki_link"]) 
    for entity in st.session_state.entities)

    st.markdown(f"**Wiki links:** {total_links}")
