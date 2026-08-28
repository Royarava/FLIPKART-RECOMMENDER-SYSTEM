"""Mock embeddings for testing without network access"""
import hashlib
import numpy as np


class MockEmbeddings:
    """Mock embedding model for testing - generates deterministic embeddings"""
    
    def __init__(self, model: str = "mock"):
        self.model = model
    
    def embed_documents(self, texts: list) -> list:
        """Generate mock embeddings for a list of documents"""
        embeddings = []
        for text in texts:
            # Create a deterministic embedding based on text hash
            hash_obj = hashlib.md5(text.encode())
            seed = int(hash_obj.hexdigest(), 16) % (2**32)
            np.random.seed(seed)
            embedding = np.random.randn(768).tolist()  # 768-dim like BAAI/bge-base-en-v1.5
            embeddings.append(embedding)
        return embeddings
    
    def embed_query(self, text: str) -> list:
        """Generate mock embedding for a query"""
        return self.embed_documents([text])[0]
