import os
from langchain_qdrant import QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, SparseVectorParams


class Memory:
    def __init__(self, embeddings, sparse_embeddings):
        client = QdrantClient(path=f"{os.environ['PROJECT_ROOT']}/tmp/langchain_qdrant")
        if not client.collection_exists(collection_name="demo_collection"):
            client.create_collection(
                collection_name="demo_collection",
                vectors_config={"dense": VectorParams(size=1024, distance=Distance.COSINE)},
                sparse_vectors_config={"sparse": SparseVectorParams(index=models.SparseIndexParams(on_disk=False))},
            )
        vector_store = QdrantVectorStore(
            client=client,
            collection_name="demo_collection",
            embedding=embeddings,
            sparse_embedding=sparse_embeddings,
            retrieval_mode=RetrievalMode.HYBRID,
            vector_name="dense",
            sparse_vector_name="sparse",
        )
        self.vector_store = vector_store
        self.retriever = vector_store.as_retriever()
