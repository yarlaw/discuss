import os
import time
import uuid

import streamlit as st
from langchain_core.prompts import ChatPromptTemplate

from chat_openrouter import ChatOpenRouter
import utils.docloader as docloader
import utils.embedder as embedder

from entities.create_entity import create_entity
from entities.edit_entity import edit_entity
from entities.remove_entity import remove_entity

UPLOAD_FOLDER = "RAG_files"
DEFAULT_CYCLES = 3
DEFAULT_MODEL = "mistralai/mistral-7b-instruct:free"
WELCOME_MESSAGE = """Welcome to the LLM Discussions Bot! 👋

Enter a topic below, and the configured entities will discuss it in multiple cycles. 
Each entity will see and respond to what others have said, including previous discussion cycles. 
Use the 'Discuss circles' slider in the sidebar to control how many rounds of discussion to have. 
Entities are encouraged to be controversial and take strong stances on topics, so expect lively debates!"""

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

model = ChatOpenRouter(model_name=DEFAULT_MODEL)


def get_entity_response(entity, topic, model, entity_materials, previous_responses=None, cycle_num=1, all_previous_cycles=None):
    """
    Generate a response from an entity based on the topic and previous entity responses.
    
    Args:
        entity: The entity dictionary
        topic: The discussion topic
        model: The LLM model to use
        entity_materials: Dictionary of entity materials (for future RAG use)
        previous_responses: List of previous entity responses in this discussion cycle
        cycle_num: Current discussion cycle number
        all_previous_cycles: List of all previous discussion cycles
    """
    entity_uuid = entity["uuid"]
    entity_name = entity["title"]
    
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
    
    # Entity discussion prompt template
    entity_template = """You are {entity_name}.
You are participating in cycle {cycle_num} of a discussion about the topic: "{topic}".

{previous_context}

Please provide your perspective on this topic based on your general understanding.
Be controversial and take a strong stance on the topic. Don't be afraid to disagree with previous speakers.

IMPORTANT INSTRUCTIONS:
1. If this is not the first cycle, refer to what YOU said in previous cycles
2. Reference or challenge what other entities have said (either in this cycle or previous cycles)
3. Evolve your position based on the ongoing discussion
4. Be concise and provocative (2-3 sentences)

Your response as {entity_name} for cycle {cycle_num}:"""
    
    prompt = ChatPromptTemplate.from_template(entity_template)
    chain = prompt | model
    
    try:
        response = chain.invoke({
            "entity_name": entity_name,
            "topic": topic,
            "previous_context": previous_context,
            "cycle_num": cycle_num
        })
        return response.content
    except Exception as e:
        st.error(f"Error in get_entity_response for {entity_name}: {e}", icon="🚨")
        return f"I'm sorry, as {entity_name}, I'm having trouble formulating a response right now."

def load_all_entity_materials():
    """
    Loads and indexes all PDF sources for each entity, marking each source with 'was_loaded'.
    Skips files that have not changed since last load. Updates progress bar.
    """
    entity_materials = st.session_state.setdefault("entity_materials", {})
    processed_files = st.session_state.setdefault("_processed_files", {})
    total_entities = len(st.session_state.entities)
    
    for idx, entity in enumerate(st.session_state.entities):
        pdf_sources = [src for src in entity.get("sources", []) if src["type"] == "pdf"]
        docs_to_index = []
        entity_processed = processed_files.get(entity["uuid"], {})
        
        # Process each PDF source
        for src in pdf_sources:
            file_path = src["filepath"]
            filename = src["filename"]
            mtime = os.path.getmtime(file_path) if os.path.exists(file_path) else None
            
            # Default: not loaded
            src["was_loaded"] = False
            
            # Skip if already processed and unchanged
            if filename in entity_processed and entity_processed[filename] == mtime:
                src["was_loaded"] = True
                continue
                
            try:
                text = docloader.load_pdf(file_path)
                docs_to_index.append({"filename": filename, "text": text})
                if mtime:
                    entity_processed[filename] = mtime
                src["was_loaded"] = True
            except Exception:
                pass
                
        processed_files[entity["uuid"]] = entity_processed
        
        if docs_to_index:
            entity_materials[entity["uuid"]] = embedder.create_index(docs_to_index)
        elif entity["uuid"] not in entity_materials:
            entity_materials[entity["uuid"]] = None
            
        st.session_state.loading_progress = (idx + 1) / total_entities
        
    st.session_state.materials_loaded = True
    st.session_state._entities_changed = False


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


def render_sidebar():
    with st.sidebar:
        st.title("Configure entities")
        
        # Global settings
        st.header("Global settings")
        st.slider(
            "Discuss circles",
            min_value=1,
            max_value=5,
            value=DEFAULT_CYCLES,
            key="discuss_circles",
            help="Number of discuss circles"
        )
        
        st.header("Entities")
        for idx, entity in enumerate(st.session_state.entities):
            with st.expander(f"**{entity['title']}**", expanded=False):
                st.caption("Used model is: mistral")
                
                pdf_count = len([src for src in entity.get("sources", []) if src["type"] == "pdf"])
                wiki_count = len([src for src in entity.get("sources", []) if src["type"] == "wiki_link"])
                
                if pdf_count > 0:
                    st.badge(f"PDFs: {pdf_count}", color="violet", icon="📄")
                if wiki_count > 0:
                    st.badge(f"Wiki: {wiki_count}", color="blue", icon="🌐")
                if not entity.get("sources") or len(entity.get("sources", [])) == 0:
                    st.markdown(":orange-badge[⚠️No sources attached]")
                
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
                        
            if st.session_state.get("_entities_changed", False):
                st.session_state.materials_loaded = False
                st.session_state.loading_progress = 0.0
                
        if st.button("Add new entity", type="primary", use_container_width=True):
            create_entity("Entity " + str(len(st.session_state.entities) + 1))
            st.session_state._entities_changed = True
            
        st.write("")
        
        st.header("Model activation status")
        if not st.session_state.materials_loaded:
            st.progress(st.session_state.loading_progress, text="Loading entity materials...")
            if st.button("Activate & Load All Materials", type="primary", use_container_width=True):
                load_all_entity_materials()
        else:
            st.success("All materials loaded and up to date.")

        total_pdfs = sum(len([src for src in entity.get("sources", []) if src["type"] == "pdf"]) 
        for entity in st.session_state.entities)
        total_links = sum(len([src for src in entity.get("sources", []) if src["type"] == "wiki_link"]) 
        for entity in st.session_state.entities)
        loaded_pdfs = sum(len([src for src in entity.get("sources", []) if src["type"] == "pdf" and src.get("was_loaded")]) 
            for entity in st.session_state.entities)
        
        st.markdown(f"**PDFs loaded:** {loaded_pdfs} / {total_pdfs}")
        st.markdown(f"**Wiki links:** {total_links}")

def conduct_discussion(topic, num_cycles):
    """
    Conduct a multi-cycle discussion on the given topic
    
    Args:
        topic: The discussion topic
        num_cycles: Number of discussion cycles to run
    """
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
                    model, 
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
    """Render the main chat interface"""
    st.title("🗨️ LLM discussions bot")
    
    # Check if materials are loaded
    if not st.session_state.materials_loaded:
        st.info("Please activate and load all materials before starting the discussion.")
        st.chat_input("Put the theme to discussion", key="text", disabled=True)
        return
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    topic = st.chat_input("Put the theme to discussion", key="text")
    if topic:
        # Display user message
        st.session_state.messages.append({"role": "user", "content": topic})
        with st.chat_message("user"):
            st.markdown(topic)
        
        # Start discussion
        st.session_state.current_topic = topic
        st.session_state.discussion_active = True
        
        # Get number of cycles and run discussion
        num_cycles = st.session_state.discuss_circles
        conduct_discussion(topic, num_cycles)
        
        # Mark discussion as complete
        st.session_state.discussion_active = False


def main():
    """Main app function"""
    # Initialize session state
    initialize_session_state()
    
    # Render UI components
    render_sidebar()
    render_main_interface()

if __name__ == "__main__":
    main()