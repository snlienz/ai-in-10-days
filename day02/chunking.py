"""切塊策略。Day 4 會拿「依條切」和「依固定字數切」來比較，所以兩種都放在這裡。

每個 chunk 是 dict：id、text（拿去做 embedding 的文字）、metadata（Chroma 只接受 str/int/float/bool）。
"""

FAQ_CHUNK_SIZE = 500
FAQ_OVERLAP_LINES = 1


def law_header(article: dict) -> str:
    """每塊前面加上法規名稱、條號與章名，讓「第 24 條」「工作時間」這類查詢也對得上。"""
    chapter = f"（{article['chapter']}）" if article["chapter"] else ""
    return f"{article['law']} 第{article['article_no']}條{chapter}"


def law_metadata(article: dict) -> dict:
    return {
        "source_type": "law",
        "law": article["law"],
        "article_no": article["article_no"],
        "chapter": article["chapter"],
        "url": article["url"],
        "modified": article["modified"],
    }


def chunk_laws_by_article(articles: list[dict]) -> list[dict]:
    """一條一塊。法條本身就是語意完整的單位，引用時也能直接附條號。"""
    return [
        {
            "id": article["id"],
            "text": f"{law_header(article)}\n{article['text']}",
            "metadata": law_metadata(article),
        }
        for article in articles
        if not article["deleted"]
    ]


def split_fixed(text: str, size: int, overlap: int) -> list[str]:
    """不管語意，每 size 個字切一刀，前後重疊 overlap 個字。"""
    step = size - overlap
    return [text[i:i + size] for i in range(0, max(len(text) - overlap, 1), step)]


def chunk_laws_fixed(articles: list[dict], size: int = 300, overlap: int = 50) -> list[dict]:
    """把同一部法規的條文接成一長串再固定字數切。一塊可能跨好幾條，也可能把一條切成兩半。

    metadata 的 article_no 記錄這塊涵蓋到的所有條號（以逗號分隔），Day 4 算命中率用。
    """
    chunks = []
    for law in dict.fromkeys(a["law"] for a in articles):
        parts, spans, pos = [], [], 0
        for a in articles:
            if a["law"] != law or a["deleted"]:
                continue
            part = f"第{a['article_no']}條\n{a['text']}\n"
            spans.append((pos, pos + len(part), a["article_no"]))
            parts.append(part)
            pos += len(part)
        full = "".join(parts)
        step = size - overlap
        for n, piece in enumerate(split_fixed(full, size, overlap)):
            start, end = n * step, n * step + len(piece)
            covered = [no for s, e, no in spans if s < end and e > start]
            chunks.append({
                "id": f"{law}-fixed-{n}",
                "text": f"{law}\n{piece}",
                "metadata": {"source_type": "law", "law": law,
                             "article_no": ",".join(covered), "chunking": f"fixed{size}"},
            })
    return chunks


def chunk_faq(pages: list[dict], size: int = FAQ_CHUNK_SIZE) -> list[dict]:
    """勞動部說明頁依行累積到約 size 字一塊，相鄰兩塊重疊最後一行，避免答案剛好被切開。"""
    chunks = []
    for page in pages:
        lines = page["text"].splitlines()
        pieces, current = [], []
        for line in lines:
            if current and sum(len(x) for x in current) + len(line) > size:
                pieces.append(current)
                current = current[-FAQ_OVERLAP_LINES:]
            current.append(line)
        if current:
            pieces.append(current)
        for n, piece in enumerate(pieces):
            chunks.append({
                "id": f"{page['id']}-{n}",
                "text": f"勞動部說明：{page['title']}\n" + "\n".join(piece),
                "metadata": {
                    "source_type": "faq",
                    "title": page["title"],
                    "url": page["url"],
                    "modified": page["updated"],
                },
            })
    return chunks
