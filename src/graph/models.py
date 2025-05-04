from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_qdrant import FastEmbedSparse

# Run Ollama on three ports to avoid cold start for model loads via Ollama API
# Run in a bash shell
# OLLAMA_HOST=localhost:11434 OLLAMA_NUM_PARALLEL=2 OLLAMA_KEEP_ALIVE=-1 OLLAMA_FLASH_ATTENTION=1 ollama serve
# OLLAMA_HOST=localhost:11435 OLLAMA_KEEP_ALIVE=-1 OLLAMA_FLASH_ATTENTION=1 ollama serve
# OLLAMA_HOST=localhost:11436 OLLAMA_KEEP_ALIVE=-1 OLLAMA_FLASH_ATTENTION=1 ollama serve

class Models:
    def __init__(self):
        self.model_llm = ChatOllama(model="llama3.2:3b", temperature=0.5, base_url="http://localhost:11434", cache=None)
        # self.model_llm = ChatOllama(model="llama3.2:1b", temperature=0.5, base_url="http://localhost:11434", cache=None)
        self.model_guard = ChatOllama(model="llama-guard3:8b", temperature=0.5, base_url="http://localhost:11435", cache=None)
        # self.model_guard = ChatOllama(model="llama-guard3:1b", temperature=0.5, base_url="http://localhost:11435", cache=None)
        self.embeddings = OllamaEmbeddings(model="mxbai-embed-large", base_url="http://localhost:11436")
        self.sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")