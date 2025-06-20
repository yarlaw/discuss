import streamlit as st

from entities.create_entity import create_entity
from entities.remove_entity import remove_entity
from entities.edit_entity import edit_entity

from utils.material_loader import load_all_entity_materials
from utils.constants import DEFAULT_CYCLES
from utils.models import get_model_family
from utils.docloader import extract_persona_name_from_wiki_url

@st.fragment
def render_sidebar():
    st.title("Configure entities")

    render_global_settings()
    render_entities_section()
    st.write("")
    render_model_activation_status()

def render_global_settings():
    st.header("Global settings")
    st.slider(
        "Discuss circles",
        min_value=1,
        max_value=5,
        value=DEFAULT_CYCLES,
        key="discuss_circles",
        help="Number of discuss circles"
    )

def render_entities_section():
    st.header("Entities")

    for idx, entity in enumerate(st.session_state.entities):
        with st.expander(f"**{entity['title']}**", expanded=False):
            _render_entity_details(entity, idx)

        if st.session_state.get("_entities_changed", False):
            st.session_state.materials_loaded = False
            st.session_state.loading_progress = 0.0

    if st.button("Add new entity", type="primary", use_container_width=True):
        create_entity("Entity " + str(len(st.session_state.entities) + 1))
        st.session_state._entities_changed = True

def _render_entity_details(entity, idx):
    model_name = entity.get("model", "mistral-7b")
    model_family = get_model_family(model_name)
    st.caption(f"Model: {model_name} ({model_family})")

    render_persona_info(entity)
    render_source_badges(entity)
    render_entity_actions(entity, idx)

def render_persona_info(entity):
    if not entity.get("persona_mode", False):
        return

    wiki_url = None
    for src in entity.get("sources", []):
        if src["type"] == "wiki" and "wikipedia.org" in src["filepath"]:
            wiki_url = src["filepath"]
            break

    if wiki_url:
        persona_name = extract_persona_name_from_wiki_url(wiki_url)
        if persona_name:
            st.caption(f"🎭 Persona Mode: {persona_name}")
        else:
            st.caption("🎭 Persona Mode enabled")
    else:
        st.caption("🎭 Persona Mode enabled (needs Wikipedia link)")

def render_source_badges(entity):
    sources = entity.get("sources", [])
    pdf_count = len([src for src in sources if src["type"] == "pdf"])
    wiki_count = len([src for src in sources if src["type"] == "wiki"])

    badges = []
    if pdf_count > 0:
        badges.append(f":violet-badge[📄 PDFs: {pdf_count}]")
    if wiki_count > 0:
        badges.append(f":blue-badge[🌐 Wiki: {wiki_count}]")

    if badges:
        st.markdown(" ".join(badges))
    elif not sources or len(sources) == 0:
        st.markdown(":orange-badge[⚠️No sources attached]")

def render_entity_actions(entity, idx):
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

def render_model_activation_status():
    st.header("Model activation status")

    if not st.session_state.materials_loaded:
        if st.button("Activate & Load All Materials", type="primary", use_container_width=True):
            load_all_entity_materials()
    else:
        st.success("All materials loaded and up to date.")

    render_source_loading_stats()

def render_source_loading_stats():
    entities = st.session_state.entities

    total_pdfs = sum(len([src for src in entity.get("sources", []) if src["type"] == "pdf"])
                     for entity in entities)
    loaded_pdfs = sum(len([src for src in entity.get("sources", []) if src["type"] == "pdf" and src.get("was_loaded")])
                      for entity in entities)
    st.markdown(f"**PDFs loaded:** {loaded_pdfs} / {total_pdfs}")

    total_links = sum(len([src for src in entity.get("sources", []) if src["type"] == "wiki"])
                      for entity in entities)
    loaded_links = sum(len([src for src in entity.get("sources", []) if src["type"] == "wiki" and src.get("was_loaded")])
                       for entity in entities)
    st.markdown(f"**Wiki links:** {loaded_links} / {total_links}")
