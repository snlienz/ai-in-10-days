# Day 2 流程圖

方框是程式（函式），斜框是資料，箭頭上標的是傳遞的資料格式。上半部是建索引（只跑一次），下半部是查詢（Day 3 每次提問都會走）。

```mermaid
flowchart TD
    %% ===== 資料來源 =====
    subgraph SRC["資料來源"]
        LAW_WEB[/"全國法規資料庫<br/>LawAll.aspx?pcode=N0030001 / N0030002 / N0030006<br/>格式：HTML"/]
        MOL_WEB[/"勞動部全球資訊網<br/>10 個分類（lpsimplelist / nodelist / post）<br/>格式：HTML"/]
    end

    %% ===== 步驟 1：抓資料 =====
    subgraph S1["步驟 1：下載與解析（fetch_laws.py、crawl_mol_faq.py）"]
        FETCH["fetch_laws.main()<br/>requests.get → parse_law_page()<br/>BeautifulSoup 解析 div.law-reg-content 底下的 div.row"]
        CRAWL["crawl_mol_faq.main()<br/>list_posts() 展開列表頁 → parse_post()<br/>取 section.cp 內文、濾掉 BOILERPLATE、略過少於 100 字的頁面"]
    end

    LAW_WEB -- "HTML 字串（3 部法規）" --> FETCH
    MOL_WEB -- "HTML 字串（31 篇）" --> CRAWL

    LAWS_JSON[/"day02/data/laws.json<br/>list[dict]，181 筆<br/>{id, law, pcode, article_no, chapter,<br/>text, deleted, url, modified}"/]
    FAQ_JSON[/"day02/data/mol_faq.json<br/>list[dict]，26 篇<br/>{id, title, url, updated, text}"/]

    FETCH -- "json.dumps → write_text" --> LAWS_JSON
    CRAWL -- "json.dumps → write_text" --> FAQ_JSON

    %% ===== 步驟 2：切塊 =====
    subgraph S2["步驟 2：切塊（chunking.py）"]
        CHUNK_LAW["chunk_laws_by_article()<br/>一條一塊、略過已刪除條文<br/>前面加上「法規名 第N條（章名）」"]
        CHUNK_FAQ["chunk_faq()<br/>依行累積到約 500 字一塊<br/>相鄰兩塊重疊 1 行"]
    end

    LAWS_JSON -- "list[dict] 條文" --> CHUNK_LAW
    FAQ_JSON -- "list[dict] 說明頁" --> CHUNK_FAQ

    CHUNKS[/"chunks：list[dict]，222 塊<br/>{id: str, text: str, metadata: dict}<br/>法條 174 塊 metadata：source_type=law, law, article_no, chapter, url, modified<br/>說明 48 塊 metadata：source_type=faq, title, url, modified"/]

    CHUNK_LAW -- "174 塊" --> CHUNKS
    CHUNK_FAQ -- "48 塊" --> CHUNKS

    %% ===== 步驟 3：embedding =====
    subgraph S3["步驟 3：產生 embedding（store.py）"]
        EMBED["embed(texts)<br/>SentenceTransformer('BAAI/bge-m3', device='cpu')<br/>normalize_embeddings=True"]
        HF[("Hugging Face 快取<br/>bge-m3 模型權重 約 2.2 GB<br/>第一次執行時下載")]
    end

    CHUNKS -- "list[str]：222 段 text" --> EMBED
    HF -. "載入模型" .-> EMBED

    VECTORS[/"vectors：list[list[float]]<br/>222 × 1024，每個向量長度為 1"/]
    EMBED --> VECTORS

    %% ===== 步驟 4：寫入向量資料庫 =====
    subgraph S4["步驟 4：寫入 Chroma（build_index.py）"]
        ADD["get_client() → 刪掉舊 collection<br/>get_collection()（hnsw:space = cosine）<br/>collection.add(ids, documents, metadatas, embeddings)"]
    end

    CHUNKS -- "ids、documents、metadatas" --> ADD
    VECTORS -- "embeddings" --> ADD

    DB[("day02/chroma_db/<br/>collection「labor_law」222 筆<br/>chroma.sqlite3：id、原文、metadata、向量<br/>&lt;uuid&gt;/：HNSW 索引")]
    ADD --> DB

    %% ===== 查詢流程 =====
    subgraph Q["查詢（search.py，Day 3 用 from day02.search import search）"]
        QUERY[/"使用者問題<br/>str，例如「休息日加班怎麼算」<br/>參數：k=5、source_type=None / law / faq"/]
        Q_EMBED["embed([query])<br/>同一個 bge-m3 模型"]
        Q_SEARCH["collection.query(query_embeddings, n_results=k, where)<br/>用 HNSW 找 cosine 距離最小的 k 塊"]
        RESULTS[/"list[dict]，k 筆，依相似度排序<br/>{id, text, metadata, score}<br/>score = 1 − distance，越接近 1 越相關"/]
    end

    QUERY -- "str" --> Q_EMBED
    HF -. "載入模型" .-> Q_EMBED
    Q_EMBED -- "list[list[float]]：1 × 1024" --> Q_SEARCH
    DB -- "向量索引＋原文＋metadata" --> Q_SEARCH
    Q_SEARCH --> RESULTS
    RESULTS -- "Day 3：條文原文＋條號／網址" --> DAY3(["Day 3 RAG：交給 Claude 生成回答並附出處"])
```

## 對應的執行指令

| 步驟 | 指令 | 產出 |
|---|---|---|
| 1 | `.\.venv\Scripts\python.exe -m day02.fetch_laws` | `data/laws.json` |
| 1 | `.\.venv\Scripts\python.exe -m day02.crawl_mol_faq` | `data/mol_faq.json` |
| 2–4 | `.\.venv\Scripts\python.exe -m day02.build_index` | `chroma_db/` |
| 查詢 | `.\.venv\Scripts\python.exe -m day02.search "問題"` | 印出前 5 名 |
