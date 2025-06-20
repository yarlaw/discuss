import time

import streamlit as st
from langchain_core.prompts import ChatPromptTemplate

from chat_openrouter import ChatOpenRouter

from utils.setup import initialize_session_state
from sidebar import render_sidebar
from utils.constants import DEFAULT_MODEL_NAME, WIKI_LINK
from utils.models import get_model_id
from utils.docloader import extract_persona_name_from_wiki_url

def get_entity_model(entity):
    model_name = entity.get("model", DEFAULT_MODEL_NAME)
    model_id = get_model_id(model_name)
    return ChatOpenRouter(model_name=model_id)

def get_entity_response(entity, topic, entity_materials, previous_responses=None, cycle_num=1, all_previous_cycles=None):
    entity_uuid = entity["uuid"]
    entity_name = entity["title"]

    entity_model = get_entity_model(entity)

    persona_mode, persona_name = get_persona_info(entity)

    context = build_content_context(entity_uuid, entity_materials, persona_mode, persona_name)
    previous_context = build_discussion_context(previous_responses, all_previous_cycles, entity_name, cycle_num)

    entity_template = select_prompt_template(persona_mode, persona_name)

    return generate_model_response(
        entity_model, entity_template, entity_name, topic,
        previous_context, cycle_num, context, persona_mode, persona_name
    )

def get_persona_info(entity):
    persona_mode = entity.get("persona_mode", False)
    persona_name = None

    if persona_mode:
        wiki_url = None
        for src in entity.get("sources", []):
            if src["type"] == "wiki" and WIKI_LINK in src["filepath"]:
                wiki_url = src["filepath"]
                break

        if wiki_url:
            persona_name = extract_persona_name_from_wiki_url(wiki_url)

    return persona_mode, persona_name

def build_content_context(entity_uuid, entity_materials, persona_mode, persona_name):
    context = ""
    if entity_uuid not in entity_materials or not entity_materials[entity_uuid]:
        return context

    docs = entity_materials[entity_uuid].get_documents()
    if not docs:
        return context

    # Categorize documents
    wiki_docs = []
    pdf_docs = []
    for doc in docs:
        if "Wiki_" in doc['filename']:
            wiki_docs.append(doc)
        else:
            pdf_docs.append(doc)

    # Build context based on persona mode
    if persona_mode and persona_name and wiki_docs:
        context = f"ABOUT YOU ({persona_name}):\n"
        for doc in wiki_docs[:1]:
            max_chars = 2000
            text = doc['text'][:max_chars] + ("..." if len(doc['text']) > max_chars else "")
            context += f"{text}\n\n"

        if pdf_docs:
            context += "ADDITIONAL CONTEXT:\n"
            for doc in pdf_docs[:2]:
                context += f"--- From {doc['filename']} ---\n"
                max_chars = 1000
                text = doc['text'][:max_chars] + ("..." if len(doc['text']) > max_chars else "")
                context += f"{text}\n\n"
    else:
        context = "CONTEXT FROM YOUR DOCUMENTS:\n"
        for doc in docs[:3]:
            context += f"--- From {doc['filename']} ---\n"
            max_chars = 1500
            text = doc['text'][:max_chars] + ("..." if len(doc['text']) > max_chars else "")
            context += f"{text}\n\n"

    return context

def build_discussion_context(previous_responses, all_previous_cycles, entity_name, cycle_num):
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

    return previous_context

def select_prompt_template(persona_mode, persona_name):
    if persona_mode and persona_name:
        return """You are {persona_name}. You'll be participating in a discussion as if you were the real {persona_name}, based on the Wikipedia information provided.
You are participating in cycle {cycle_num} of a discussion about the topic: "{topic}".

{pdf_context}

{previous_context}

Please provide your perspective on this topic based on the knowledge, beliefs, personality, and writing style of {persona_name}.
Speak in first person as if you are actually {persona_name}.

IMPORTANT INSTRUCTIONS:
1. Stay in character as {persona_name} at all times - use your background knowledge to authentically represent this person
2. If this is not the first cycle, maintain consistency with what YOU said in previous cycles
3. React to what other participants have said in a way that's authentic to {persona_name}'s personality and views
4. Be concise but substantive (2-3 sentences)
5. Base your response on the persona information from the Wikipedia article and your knowledge about {persona_name}
6. Your response should reflect {persona_name}'s known opinions, expertise, time period, and speaking style

Your response as {persona_name} for cycle {cycle_num}:"""
    else:
        return """You are {entity_name}.
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

def generate_model_response(entity_model, entity_template, entity_name, topic, previous_context, cycle_num, context, persona_mode, persona_name):
    prompt = ChatPromptTemplate.from_template(entity_template)
    chain = prompt | entity_model

    try:
        invoke_params = {
            "entity_name": entity_name,
            "topic": topic,
            "previous_context": previous_context,
            "cycle_num": cycle_num,
            "pdf_context": context
        }

        if persona_mode and persona_name:
            invoke_params["persona_name"] = persona_name

        response = chain.invoke(invoke_params)
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

        setup_cycle_display(response_container, cycle)

        entity_responses = process_entity_responses(
            topic,
            cycle,
            num_cycles,
            response_container,
            status_placeholder,
            all_cycles_responses
        )
        all_cycles_responses.append(entity_responses)

        if cycle < num_cycles:
            time.sleep(1)

def setup_cycle_display(container, cycle):
    if cycle > 1:
        container.divider()
    container.subheader(f"Discussion Cycle {cycle}")

def process_entity_responses(topic, cycle, num_cycles, response_container, status_placeholder, all_cycles_responses):
    entity_responses = []

    with status_placeholder.status(f"Entities are discussing (Cycle {cycle}/{num_cycles})...", expanded=True) as status:
        for idx, entity in enumerate(st.session_state.entities):
            update_entity_status(status, cycle, num_cycles, idx, entity)

            previous_responses = [{"entity": resp["entity"], "content": resp["content"]} for resp in entity_responses]

            response = get_entity_response(
                entity,
                topic,
                st.session_state.get("entity_materials", {}),
                previous_responses=previous_responses,
                cycle_num=cycle,
                all_previous_cycles=all_cycles_responses if all_cycles_responses else None
            )

            current_response = create_response_object(entity, response, cycle)
            entity_responses.append(current_response)

            display_entity_response(response_container, entity, current_response, cycle)

            if idx < len(st.session_state.entities) - 1:
                time.sleep(0.5)

        update_cycle_status(status, cycle, num_cycles)

    return entity_responses

def update_entity_status(status, cycle, num_cycles, idx, entity):
    status.update(
        label=f"Cycle {cycle}/{num_cycles} - Entity {idx+1}/{len(st.session_state.entities)}: "
              f"{entity['title']} is formulating a response..."
    )

def create_response_object(entity, response, cycle):
    return {
        "entity": entity["title"],
        "entity_uuid": entity["uuid"],
        "content": response,
        "role": "assistant",
        "cycle": cycle
    }

def display_entity_response(container, entity, current_response, cycle):
    persona_mode = entity.get("persona_mode", False)
    persona_name = None

    if persona_mode:
        wiki_url = None
        for src in entity.get("sources", []):
            if src["type"] == "wiki" and WIKI_LINK in src["filepath"]:
                wiki_url = src["filepath"]
                break

        if wiki_url:
            persona_name = extract_persona_name_from_wiki_url(wiki_url)

    with container.chat_message("assistant", avatar="🤖"):
        if persona_mode and persona_name:
            st.markdown(f"**{current_response['entity']}** (as *{persona_name}*): {current_response['content']}")
        else:
            st.markdown(f"**{current_response['entity']}:** {current_response['content']}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": f"**Cycle {cycle} - {current_response['entity']}" +
                   (f" (as {persona_name})" if persona_mode and persona_name else "") +
                   f":** {current_response['content']}"
    })

def update_cycle_status(status, cycle, num_cycles):
    status.update(
        label=f"Cycle {cycle}/{num_cycles} complete!",
        state="complete" if cycle == num_cycles else None
    )

def render_main_interface():
    st.title("🗨️ LLM discussions bot")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if not st.session_state.materials_loaded:
        st.info("Please activate and load all materials before starting the discussion.")
        st.chat_input("Firstly activate all materials", key="text", disabled=True)
        return


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
