"""向量資料庫與 embedding 模型的共用設定。Day 3 之後都從這裡拿 collection。"""

from functools import lru_cache
from pathlib import Path

import chromadb

DB_DIR = Path(__file__).parent / "chroma_db"
COLLECTION = "labor_law"
# 多語言模型，中文（含繁體）效果好；第一次執行會下載約 2.2 GB，之後從快取讀
EMBED_MODEL = "BAAI/bge-m3"


@lru_cache(maxsize=1)
def get_model():
    from sentence_transformers import SentenceTransformer  # 載入要幾秒，用到才 import

    return SentenceTransformer(EMBED_MODEL, device="cpu")


def embed(texts: list[str]) -> list[list[float]]:
    # normalize 後內積就等於 cosine similarity
    vectors = get_model().encode(texts, normalize_embeddings=True, batch_size=8,
                                 show_progress_bar=len(texts) > 20)
    return vectors.tolist()


def get_client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(path=str(DB_DIR))


def get_collection(name: str = COLLECTION) -> chromadb.Collection:
    return get_client().get_or_create_collection(name, metadata={"hnsw:space": "cosine"})
