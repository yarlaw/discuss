import faiss
import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings

class FAISSIndex:
    def __init__(self, faiss_index, metadata):
        self.index = faiss_index
        self.metadata = metadata

    def similarity_search(self, query, k=3):
        D, I = self.index.search(query, k)  # D: distances, I: indices
        results = []
        for idx in I[0]:
            results.append(self.metadata[idx])
        return results

embed_model_id = 'intfloat/e5-small-v2'
model_kwargs = {"device": "cpu", "trust_remote_code": True}

def create_index(documents):
    embeddings = HuggingFaceEmbeddings(model_name=embed_model_id, model_kwargs=model_kwargs)
    texts = [doc["text"] for doc in documents]
    metadata = [{"filename": doc["filename"], "text": doc["text"]} for doc in documents]

    # Generate embeddings
    embeddings_matrix = [embeddings.embed_query(text) for text in texts]
    embeddings_matrix = np.array(embeddings_matrix).astype("float32")

    # Create FAISS index
    index = faiss.IndexFlatL2(embeddings_matrix.shape[1])
    index.add(embeddings_matrix)

    # Return a FAISSIndex object that contains both the index and metadata
    return FAISSIndex(index, metadata)

def retrieve_docs(query, faiss_index, k=3):
    embeddings = HuggingFaceEmbeddings(model_name=embed_model_id, model_kwargs=model_kwargs)
    query_embedding = np.array([embeddings.embed_query(query)]).astype("float32")
    results = faiss_index.similarity_search(query_embedding, k=k)
    return results