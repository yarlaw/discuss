import streamlit as st

import os

UPLOAD_FOLDER = "RAG_files"

@st.dialog("Remove Entity")
def remove_entity(id):
    st.header("Are you sure you want to remove this entity?")

    # Find the entity and list its PDFs
    entity = next((x for x in st.session_state.entities if x["uuid"] == id), None)
    if entity and entity.get("sources"):
        st.markdown("**PDF files to be deleted:**")
        for src in entity["sources"]:
            if src["type"] == "pdf":
                st.write(f"- {src.get('filename', os.path.basename(src['filepath']))}")

    if st.button("Submit", type="primary"):
        # Remove files from disk
        if entity and entity.get("sources"):
            for src in entity["sources"]:
                if src["type"] == "pdf":
                    try:
                        os.remove(src["filepath"])
                    except Exception:
                        pass
        # Remove the entity's folder if empty
        entity_folder = os.path.join(UPLOAD_FOLDER, str(id))
        try:
            if os.path.isdir(entity_folder) and not os.listdir(entity_folder):
                os.rmdir(entity_folder)
        except Exception:
            pass
        # Remove the entity from session state
        st.session_state.entities = [x for x in st.session_state.entities if x["uuid"] != id]
        st.rerun()