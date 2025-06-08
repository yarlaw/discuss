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
        documents = []
        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_path = os.path.join(entity_folder, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                documents.append({"filename": uploaded_file.name, "path": file_path})
        return documents

    def show_and_select_files_to_remove(current_entity):
        files_to_remove = []
        if current_entity and current_entity.get("documents"):
            st.markdown("**Previously files to keep:**")
            for doc in current_entity["documents"]:
                keep = st.checkbox(
                    f"{doc['filename']}", key=f"keep_{id}_{doc['filename']}", value=True
                )
                if not keep:
                    files_to_remove.append(doc)
        return files_to_remove

    with tab1:
        entity_folder = os.path.join(UPLOAD_FOLDER, str(id))
        os.makedirs(entity_folder, exist_ok=True)
        documents = handle_file_uploads(entity_folder)
        current_entity = next((item for item in st.session_state.entities if item["uuid"] == id), None)
        files_to_remove = show_and_select_files_to_remove(current_entity)

    with tab2:
        link = st.text_input("Insert link", value="", key="edit_entity_link")

    if st.button("Submit", type="primary"):
        for item in st.session_state.entities:
            if item["uuid"] == id:
                item["title"] = title
                # Remove selected files from entity and disk
                if files_to_remove:
                    for doc in files_to_remove:
                        if doc in item["documents"]:
                            item["documents"].remove(doc)
                            try:
                                os.remove(doc["path"])
                            except Exception:
                                pass
                # Add new documents to the entity's documents list
                if documents:
                    if "documents" not in item:
                        item["documents"] = []
                    # Only add new files that are not already present
                    for doc in documents:
                        if not any(existing["filename"] == doc["filename"] for existing in item["documents"]):
                            item["documents"].append(doc)
                # Add wiki link if provided
                if link:
                    if "wiki_links" not in item:
                        item["wiki_links"] = []
                    if link not in item["wiki_links"]:
                        item["wiki_links"].append(link)
                break
        st.rerun()
