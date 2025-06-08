import streamlit as st

import os

UPLOAD_FOLDER = "RAG_files"

@st.dialog("Remove Entity")
def remove_entity(id):

    st.header("Are you sure you want to remove this entity?")

    if st.button("Submit", type="primary"):
        st.session_state.entities = [x for x in st.session_state.entities if x["uuid"] != id]
        st.rerun()