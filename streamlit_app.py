import streamlit as st
from openai import OpenAI

import random
import time


client = OpenAI(api_key = st.secrets["API_KEY"], base_url = st.secrets["BASE_URL"])

st.title("🗨️ LLM chat bot")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Let's start chatting! 👇"}]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        assistant_response = client.chat.completions.create(
            model=st.secrets["MODEL"],
            messages=st.session_state.messages
        )

        assistant_message = assistant_response.choices[0].message.content

        # Simulate stream of response with milliseconds delay
        for chunk in assistant_message.split():
            full_response += chunk + " "
            message_placeholder.markdown(full_response + "▌")  # Simulate typing
            time.sleep(0.05)  # Small delay for effect
        
        message_placeholder.markdown(full_response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})

