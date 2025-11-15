from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(
    host = "localhost",
    port = 6333,
)

COLLECTION_NAME = "product_knowledge"

def init_qdrant_collection():
    if COLLECTION_NAME not in [col.name for col in client.get_collections().collections]:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
        print(f"Collection {COLLECTION_NAME} created successfully")
    else:
        print(f"Collection {COLLECTION_NAME} already exists")

def get_qdrant_client():
    return client