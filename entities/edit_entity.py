import streamlit as st

import os

UPLOAD_FOLDER = "RAG_files"

@st.dialog("Edit Entity")
def edit_entity(id, old_title):
    title = st.text_input("Title", value=old_title, key="create_entity_title")
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
                    "_uploaded_file": uploaded_file,  # keep reference for writing after submit
                    "was_loaded": False
                })
        return sources

    def show_and_select_sources_to_remove(current_entity):
        sources_to_remove = []
        if current_entity and current_entity.get("sources"):
            st.markdown("**Previously sources to keep:**")
            for idx, src in enumerate(current_entity["sources"]):
                label = src["filename"] if src["type"] == "pdf" else src["filepath"]
                keep = st.checkbox(
                    f"{src['type'].upper()}: {label}", key=f"keep_{id}_{idx}", value=True
                )
                if not keep:
                    sources_to_remove.append(src)
        return sources_to_remove

    with tab1:
        entity_folder = os.path.join(UPLOAD_FOLDER, str(id))
        os.makedirs(entity_folder, exist_ok=True)
        new_sources = handle_file_uploads(entity_folder)
        current_entity = next((item for item in st.session_state.entities if item["uuid"] == id), None)
        sources_to_remove = show_and_select_sources_to_remove(current_entity)

    with tab2:
        link = st.text_input("Insert link", value="", key="edit_entity_link")

    if st.button("Submit", type="primary"):
        for item in st.session_state.entities:
            if item["uuid"] == id:
                item["title"] = title
                # Remove selected sources from entity and disk if PDF
                if sources_to_remove:
                    for src in sources_to_remove:
                        if src in item["sources"]:
                            item["sources"].remove(src)
                            if src["type"] == "pdf":
                                try:
                                    os.remove(src["filepath"])
                                except Exception:
                                    pass
                # Add new sources to the entity's sources list, and write files now
                new_pdf_added = False
                if new_sources:
                    if "sources" not in item:
                        item["sources"] = []
                    for src in new_sources:
                        # Write the file only now
                        if "_uploaded_file" in src:
                            os.makedirs(os.path.dirname(src["filepath"]), exist_ok=True)
                            with open(src["filepath"], "wb") as f:
                                f.write(src["_uploaded_file"].getbuffer())
                            del src["_uploaded_file"]
                        if not any(existing.get("type") == src["type"] and existing.get("filepath") == src["filepath"] for existing in item["sources"]):
                            item["sources"].append(src)
                            if src["type"] == "pdf":
                                new_pdf_added = True
                # Add wiki link if provided
                if link:
                    if "sources" not in item:
                        item["sources"] = []
                    if not any(s["type"] == "wiki_link" and s["filepath"] == link for s in item["sources"]):
                        item["sources"].append({"type": "wiki_link", "filepath": link})
                # If a new PDF was added, mark materials as not loaded
                if new_pdf_added:
                    st.session_state.materials_loaded = False
                break
        st.rerun()
