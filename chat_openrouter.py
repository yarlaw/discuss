import os
from typing import Optional
import streamlit as st
from langchain_openai import ChatOpenAI
from pydantic import Field, SecretStr


class ChatOpenRouter(ChatOpenAI):
    openai_api_key: Optional[SecretStr] = Field(
        alias="api_key", default=None,
    )
    @property
    @property
    def lc_secrets(self) -> dict[str, str]:
        # Try to get from environment variables first, then fall back to streamlit secrets
        api_key = os.getenv("API_KEY")
        if api_key is None and hasattr(st, 'secrets') and "API_KEY" in st.secrets:
            api_key = st.secrets["API_KEY"]
        return {"openai_api_key": api_key or ""}

    def __init__(self, openai_api_key: Optional[str] = None, **kwargs):
        if openai_api_key is None:
            openai_api_key = os.getenv("API_KEY")
            if openai_api_key is None and hasattr(st, 'secrets') and "API_KEY" in st.secrets:
                openai_api_key = st.secrets["API_KEY"]
        
        # Get base URL from environment or secrets
        base_url = os.getenv("BASE_URL")
        if base_url is None and hasattr(st, 'secrets') and "BASE_URL" in st.secrets:
            base_url = st.secrets["BASE_URL"]
        
        super().__init__(
            base_url=base_url, 
            openai_api_key=openai_api_key, 
            **kwargs
        )