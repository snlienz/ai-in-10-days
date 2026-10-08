"""把 data/laws.json 與 data/mol_faq.json 切塊、算 embedding，寫入 Chroma。

執行（在專案根目錄）：.\\.venv\\Scripts\\python.exe -m day02.build_index
每次都會重建 collection，資料更新後重跑即可。
"""

import json
import time
from pathlib import Path

from day02.chunking import chunk_faq, chunk_laws_by_article
from day02.store import COLLECTION, get_client, get_collection, embed

DATA_DIR = Path(__file__).parent / "data"


def main() -> None:
    articles = json.loads((DATA_DIR / "laws.json").read_text(encoding="utf-8"))
    pages = json.loads((DATA_DIR / "mol_faq.json").read_text(encoding="utf-8"))
    chunks = chunk_laws_by_article(articles) + chunk_faq(pages)
    n_law = sum(c["metadata"]["source_type"] == "law" for c in chunks)
    print(f"切塊：法條 {n_law} 塊、勞動部說明 {len(chunks) - n_law} 塊")
    longest = max(chunks, key=lambda c: len(c["text"]))
    print(f"最長的一塊 {len(longest['text'])} 字：{longest['id']}")

    start = time.perf_counter()
    vectors = embed([c["text"] for c in chunks])
    print(f"embedding 完成：{len(vectors)} 個 {len(vectors[0])} 維向量，花 {time.perf_counter() - start:.0f} 秒")

    client = get_client()
    if COLLECTION in [c.name for c in client.list_collections()]:
        client.delete_collection(COLLECTION)
    collection = get_collection()
    collection.add(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
        embeddings=vectors,
    )
    print(f"已寫入 Chroma collection「{COLLECTION}」，共 {collection.count()} 筆")


if __name__ == "__main__":
    main()
