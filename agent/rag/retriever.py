from .client import get_qdrant_client, COLLECTION_NAME
from .embeddings import embed_texts

client = get_qdrant_client()

def add_documents(docs: list[dict]):
    vectors = embed_texts([d["text"] for d in docs])
    payloads = [{"text": d["text"], **d["metadata"]} for d in docs]
    ids = [d["id"] for d in docs]

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            {"id": ids[i], "vector": vectors[i], "payload": payloads[i]}
            for i in range(len(docs))
        ],
    )

def retrieve(query:str, limit:int=5):
    vector = embed_texts([query])[0]
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=vector,
        limit=limit,
    )
    return[
        {
            "text": hit.payload.get("text"),
            "score": hit.score,
            "metadata": hit.payload,
        }
        for hit in results
    ]