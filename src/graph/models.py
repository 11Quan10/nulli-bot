from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_qdrant import FastEmbedSparse

class Models:
    def __init__(self):
        self.model_llm = ChatOllama(model="llama3.2:3b-instruct-q4_K_M", temperature=0.5, base_url="http://localhost:11434", cache=None)
        # self.model_llm = ChatOllama(model="llama3.2:1b-instruct-q4_K_M", temperature=0.5, base_url="http://localhost:11434", cache=None)
        # self.model_llm = ChatOllama(model="llama3.1:8b-instruct-q4_K_S", temperature=0.5, base_url="http://localhost:11434", cache=None)
        # self.model_guard = ChatOllama(model="llama-guard3:8b", temperature=0.5, base_url="http://localhost:11435", cache=None)
        self.model_guard = ChatOllama(model="llama-guard3:1b", temperature=0.5, base_url="http://localhost:11435", cache=None)
        # self.embeddings = OllamaEmbeddings(model="mxbai-embed-large", base_url="http://localhost:11436")
        # self.sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")