import time

import streamlit as st
from langchain_core.prompts import ChatPromptTemplate

from chat_openrouter import ChatOpenRouter

from utils.setup import initialize_session_state
from sidebar import render_sidebar
from utils.constants import DEFAULT_MODEL_NAME
from utils.models import get_model_id

def get_entity_model(entity):
    model_name = entity.get("model", DEFAULT_MODEL_NAME)
    model_id = get_model_id(model_name)
    return ChatOpenRouter(model_name=model_id)

def get_entity_response(entity, topic, entity_materials, previous_responses=None, cycle_num=1, all_previous_cycles=None):
    entity_uuid = entity["uuid"]
    entity_name = entity["title"]
    
    entity_model = get_entity_model(entity)
    
    pdf_context = ""
    if entity_uuid in entity_materials and entity_materials[entity_uuid]:
        pdf_docs = entity_materials[entity_uuid].get_documents()
        if pdf_docs:
            pdf_context = "CONTEXT FROM YOUR DOCUMENTS:\n"
            for doc in pdf_docs[:3]:  
                pdf_context += f"--- From {doc['filename']} ---\n"
                max_chars = 1500
                text = doc['text'][:max_chars] + ("..." if len(doc['text']) > max_chars else "")
                pdf_context += f"{text}\n\n"
    
    current_cycle_context = ""
    if previous_responses and len(previous_responses) > 0:
        current_cycle_context = f"Current responses in discussion cycle {cycle_num}:\n"
        for prev in previous_responses:
            current_cycle_context += f"- {prev['entity']}: {prev['content']}\n"
    
    previous_cycles_context = ""
    if all_previous_cycles and len(all_previous_cycles) > 0:
        previous_cycles_context = "Previous discussion cycles:\n"
        for cycle_idx, cycle in enumerate(all_previous_cycles):
            previous_cycles_context += f"\nCycle {cycle_idx + 1}:\n"
            for resp in cycle:
                if resp['entity'] == entity_name:
                    previous_cycles_context += f"- YOU said: {resp['content']}\n"
                else:
                    previous_cycles_context += f"- {resp['entity']} said: {resp['content']}\n"
    
    previous_context = current_cycle_context
    if previous_cycles_context:
        previous_context += "\n" + previous_cycles_context
    
    entity_template = """You are {entity_name}.
You are participating in cycle {cycle_num} of a discussion about the topic: "{topic}".

{pdf_context}

{previous_context}

Please provide your perspective on this topic based on your general understanding.
Be controversial and take a strong stance on the topic. Don't be afraid to disagree with previous speakers.

IMPORTANT INSTRUCTIONS:
1. If this is not the first cycle, refer to what YOU said in previous cycles
2. Reference or challenge what other entities have said (either in this cycle or previous cycles)
3. Evolve your position based on the ongoing discussion
4. Be concise and provocative (2-3 sentences)
5. If context from your documents was provided, use it to inform your perspective

Your response as {entity_name} for cycle {cycle_num}:"""
    
    prompt = ChatPromptTemplate.from_template(entity_template)
    chain = prompt | entity_model
    
    try:
        response = chain.invoke({
            "entity_name": entity_name,
            "topic": topic,
            "previous_context": previous_context,
            "cycle_num": cycle_num,
            "pdf_context": pdf_context
        })
        return response.content
    except Exception as e:
        st.error(f"Error in get_entity_response for {entity_name}: {e}", icon="🚨")
        return f"I'm sorry, as {entity_name}, I'm having trouble formulating a response right now."

def conduct_discussion(topic, num_cycles):
    response_container = st.container()
    status_placeholder = st.empty()
    
    all_cycles_responses = []
    
    for cycle in range(1, num_cycles + 1):
        st.session_state.discussion_cycle = cycle
        
        if cycle > 1:
            response_container.divider()
        response_container.subheader(f"Discussion Cycle {cycle}")
        
        entity_responses = []
        
        with status_placeholder.status(f"Entities are discussing (Cycle {cycle}/{num_cycles})...", expanded=True) as status:
            for idx, entity in enumerate(st.session_state.entities):
                status.update(label=f"Cycle {cycle}/{num_cycles} - Entity {idx+1}/{len(st.session_state.entities)}: {entity['title']} is formulating a response...")
                
                previous_responses = [{"entity": resp["entity"], "content": resp["content"]} for resp in entity_responses]
                
                response = get_entity_response(
                    entity, 
                    topic, 
                    st.session_state.get("entity_materials", {}),
                    previous_responses=previous_responses,
                    cycle_num=cycle,
                    all_previous_cycles=all_cycles_responses if all_cycles_responses else None
                )
                
                current_response = {
                    "entity": entity["title"],
                    "entity_uuid": entity["uuid"],
                    "content": response,
                    "role": "assistant",
                    "cycle": cycle
                }
                entity_responses.append(current_response)
                
                with response_container.chat_message("assistant", avatar=f"🤖"):
                    st.markdown(f"**{current_response['entity']}:** {current_response['content']}")
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"**Cycle {cycle} - {current_response['entity']}:** {current_response['content']}"
                })
                
                if idx < len(st.session_state.entities) - 1:
                    time.sleep(0.5)
            
            status.update(label=f"Cycle {cycle}/{num_cycles} complete!", 
                        state="complete" if cycle == num_cycles else None)
        
        all_cycles_responses.append(entity_responses)
        
        if cycle < num_cycles:
            time.sleep(1)

def render_main_interface():
    st.title("🗨️ LLM discussions bot")
    
    if not st.session_state.materials_loaded:
        st.info("Please activate and load all materials before starting the discussion.")
        st.chat_input("Put the theme to discussion", key="text", disabled=True)
        return
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    topic = st.chat_input("Put the theme to discussion", key="text")
    
    if topic:
        st.session_state.messages.append({"role": "user", "content": topic})
        with st.chat_message("user"):
            st.markdown(topic)
        
        st.session_state.current_topic = topic
        st.session_state.discussion_active = True
        
        num_cycles = st.session_state.discuss_circles
        conduct_discussion(topic, num_cycles)
        
        st.session_state.discussion_active = False

def main():
    initialize_session_state()
    
    with st.sidebar:
        render_sidebar()
    render_main_interface()

if __name__ == "__main__":
    main()
