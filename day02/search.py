"""向量檢索。Day 3 的 RAG 會用 `from day02.search import search`。

執行（在專案根目錄）：.\\.venv\\Scripts\\python.exe -m day02.search "休息日加班怎麼算"
"""

import sys

from day02.store import embed, get_collection


def search(query: str, k: int = 5, source_type: str | None = None) -> list[dict]:
    """回傳最相關的 k 塊，每塊含 text、metadata 與 score（cosine 相似度，越高越像）。

    source_type 可限定 "law" 或 "faq"。
    """
    where = {"source_type": source_type} if source_type else None
    result = get_collection().query(query_embeddings=embed([query]), n_results=k, where=where)
    return [
        {"id": id_, "text": doc, "metadata": meta, "score": 1 - dist}
        for id_, doc, meta, dist in zip(result["ids"][0], result["documents"][0],
                                        result["metadatas"][0], result["distances"][0])
    ]


def format_source(meta: dict) -> str:
    if meta["source_type"] == "law":
        return f"{meta['law']} 第{meta['article_no']}條"
    return f"勞動部：{meta['title']}"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    queries = sys.argv[1:] or [
        "休息日加班怎麼算",
        "禮拜六被叫回來上班",
        "國定假日上班要給多少錢",
        "到職三年有幾天特休",
        "颱風天公司要我上班",
        "第 32 條",
    ]
    for q in queries:
        print(f"\n🔍 {q}")
        for r in search(q):
            first_line = r["text"].splitlines()[1][:50] if "\n" in r["text"] else ""
            print(f"  {r['score']:.3f}  {format_source(r['metadata']):<24} {first_line}")
