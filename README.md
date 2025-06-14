# discuss

dicuss is an interactive discussion application powered by Large Language Models (LLMs). It enables you to simulate multi-entity debates on any topic, where each entity can represent a unique persona, expert, or fictional character. Entities draw their knowledge from uploaded PDF documents or Wikipedia articles, and participate in turn-based discussions, responding to each other's arguments in lively, multi-cycle debates.

![image](https://github.com/user-attachments/assets/5f9da4b5-26e6-4ea4-ab20-f884eec13651)

## Features

- **Simulated Multi-Agent Debates:** Entities (LLM-powered) discuss user-provided topics over multiple rounds, each adapting their arguments as the conversation evolves.
- **Persona Mode:** Assign Wikipedia pages to entities, and they will debate topics as if they are that historical figure, expert, or concept—complete with their own knowledge and style.
- **Custom Knowledge Bases:** Upload PDFs or link Wikipedia articles to provide entities with unique sources of information.
- **Interactive Web UI:** Built with Streamlit for a seamless, visual, and real-time debate experience.
- **Dynamic Contextual Arguments:** Each entity references previous statements and loaded documents, making the debate context-aware and engaging.
- **Easy Material Management:** Load and track PDF/Wiki materials for all entities via a sidebar interface.
- **Containerized Deployment:** Includes a Dockerfile for quick setup and reproducibility.

## Getting Started

### Prerequisites

- Python 3.11+
- (Optional) Docker

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yarlaw/discuss
   cd discuss
   ```
2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   pip install streamlit
   ```
3. **Run the application:**

   ```bash
   streamlit run streamlit_app.py
   ```

   The app will be available at `http://localhost:8501`.

### Docker

1. **Build the container:**

   ```bash
   docker build -t stream-chat .
   ```
2. **Run the container:**

   ```bash
   docker run -p 8501:8501 stream-chat
   ```

## Usage

1. **Add Entities:** Each entity can be a generic AI, or be assigned a specific Wikipedia page and/or PDF sources.
2. **Configure Materials:** Upload PDFs or add Wikipedia links for each entity. Materials are loaded and indexed for contextual use.
3. **Set Topic & Cycles:** Choose a discussion topic and how many rounds ("cycles") of debate you'd like.
4. **Start the Debate:** Watch as entities take turns, referencing their sources and each other's arguments.
5. **Persona Mode:** Entities with Wikipedia links will argue as that persona, using knowledge and style from their Wiki article.

## Example Scenarios

- **Historical Debates:** Let Einstein, Tesla, and Marie Curie debate the future of technology.
- **Policy Arguments:** Simulate expert panels with uploaded reports as their knowledge base.
- **Fictional Roundtables:** Have Gandalf, Sherlock Holmes, and Yoda debate the meaning of wisdom.

## Configuration

- **Materials Folder:** Uploaded PDFs are stored in `RAG_files/`.
- **Model Selection:** Default LLM is `mistral-7b` (configurable in code).
- **Discussion Cycles:** Adjustable via the UI sidebar.

## Technologies Used

- [Streamlit](https://streamlit.io/)
- [LangChain](https://python.langchain.com/)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers/)
- [FAISS](https://faiss.ai/) (for document indexing)
- [PyPDF2, PyMuPDF, BeautifulSoup4] (for parsing documents)
