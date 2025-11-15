from sentence_transformers import SentenceTransformer
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def embed_texts(texts: list[str]) -> list[list[float]]:
    return _model.encode(texts).tolist()
