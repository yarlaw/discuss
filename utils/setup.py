import os
import uuid

import streamlit as st
from utils.constants import WELCOME_MESSAGE,UPLOAD_FOLDER

def initialize_session_state():
    """Initialize all session state variables needed for the app"""
    if "query" not in st.session_state:
        st.session_state.query = ""
    if "context" not in st.session_state:
        st.session_state.context = ""
    if "answer" not in st.session_state:
        st.session_state.answer = ""
    if "entities" not in st.session_state:
        st.session_state.entities = [{"uuid": uuid.uuid1(), "title": "Entity 1"}]
    if "materials_loaded" not in st.session_state:
        st.session_state.materials_loaded = False
    if "loading_progress" not in st.session_state:
        st.session_state.loading_progress = 0.0
    if "discussion_active" not in st.session_state:
        st.session_state.discussion_active = False
    if "current_topic" not in st.session_state:
        st.session_state.current_topic = ""
    if "discussion_cycle" not in st.session_state:
        st.session_state.discussion_cycle = 0
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
