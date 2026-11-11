"""Pre-download ML models at Docker build time.

Runs during `docker build` so the api/worker images contain the models
locally, avoiding runtime downloads from Hugging Face (and the latency and
network dependency they introduce). Models are cached by Hugging Face under
/root/.cache/huggingface, which persists in the image layer.
"""
from sentence_transformers import CrossEncoder, SentenceTransformer

OUT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

if __name__ == "__main__":
    print(f"Pre-downloading embedding model: {OUT_MODEL}")
    SentenceTransformer(OUT_MODEL)
    print(f"Pre-downloading reranker model: {RERANKER_MODEL}")
    CrossEncoder(RERANKER_MODEL)
    print("Model pre-download complete.")
