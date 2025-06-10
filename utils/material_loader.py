import os

import streamlit as st

import utils.docloader as docloader
import utils.embedder as embedder
from utils.constants import UPLOAD_FOLDER

def load_entity_materials(entity, entity_materials, processed_files):
    entity_uuid = entity["uuid"]
    docs_to_index = []
    entity_processed = processed_files.get(entity_uuid, {})
    
    for src in entity.get("sources", []):
        src["was_loaded"] = False
        
        if src["type"] == "pdf":
            doc_info, was_loaded, processed_entry = load_pdf_source(src, entity_processed)
            src["was_loaded"] = was_loaded
            
            if doc_info and was_loaded and processed_entry:
                docs_to_index.append(doc_info)
                entity_processed[src["filename"]] = processed_entry
                
        elif src["type"] == "wiki_link":
            doc_info, was_loaded, processed_entry = load_wiki_source(src, entity_processed)
            src["was_loaded"] = was_loaded
            
    
    processed_files[entity_uuid] = entity_processed
    
    if docs_to_index:
        entity_materials[entity_uuid] = embedder.create_index(docs_to_index)
    elif entity_uuid not in entity_materials:
        entity_materials[entity_uuid] = None
    
    return entity_materials, processed_files

def load_all_entity_materials():
    entity_materials = st.session_state.setdefault("entity_materials", {})
    processed_files = st.session_state.setdefault("_processed_files", {})
    total_entities = len(st.session_state.entities)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        for idx, entity in enumerate(st.session_state.entities):
            status_text.text(f"Processing entity: {entity['title']} ({idx+1}/{total_entities})")
            
            entity_materials, processed_files = load_entity_materials(
                entity, entity_materials, processed_files
            )
            
            progress = (idx + 1) / total_entities
            progress_bar.progress(progress)
            st.session_state.loading_progress = progress
            
        st.session_state.materials_loaded = True
        st.session_state._entities_changed = False
        
        status_text.empty()
        
        st.rerun()
    except Exception as e:
        st.error(f"Error loading materials: {str(e)}", icon="🚨")
        st.session_state.materials_loaded = False


def load_pdf_source(src, entity_processed):
    file_path = src["filepath"]
    filename = src["filename"]
    mtime = os.path.getmtime(file_path) if os.path.exists(file_path) else None
    
    was_loaded = False
    
    if filename in entity_processed and entity_processed[filename] == mtime:
        return None, True, entity_processed[filename]
    
    try:
        text = docloader.load_pdf(file_path)
        doc_info = {"filename": filename, "text": text}
        
        updated_processed_entry = mtime
        was_loaded = True
        return doc_info, was_loaded, updated_processed_entry
    except Exception as e:
        st.error(f"Error loading PDF {filename}: {str(e)}", icon="🚨")
        return None, False, None

def load_wiki_source(src, entity_processed):
    return None, True, None