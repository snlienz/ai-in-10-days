# Day 2｜資料管線與向量資料庫

收集法條與勞動部常見問答，寫入向量資料庫。這一天全部在本機跑，不需要任何 API key。

## 完成項目

- [x] 從全國法規資料庫下載勞動基準法、施行細則、勞工請假規則（`fetch_laws.py`）
- [x] 爬勞動部網站的常見問答（`crawl_mol_faq.py`）
- [x] 每段資料保留條號或來源網址（`chunking.py` 的 metadata）
- [x] 切塊、產生 embedding，寫入 Chroma（`build_index.py`）

## 執行

在專案根目錄依序執行（用 `-m`，Day 3 之後才能 `from day02.search import search`）：

```powershell
.\.venv\Scripts\python.exe -m day02.fetch_laws      # → day02/data/laws.json
.\.venv\Scripts\python.exe -m day02.crawl_mol_faq   # → day02/data/mol_faq.json
.\.venv\Scripts\python.exe -m day02.build_index     # → day02/chroma_db/（第一次會從 Hugging Face 下載 bge-m3 約 2.2 GB）
.\.venv\Scripts\python.exe -m day02.search "休息日加班怎麼算"
```

## 檔案

| 檔案 | 用途 |
|---|---|
| `fetch_laws.py` | 抓 `LawAll.aspx` 全文頁，逐條解析出條號、章名、條文、修正日期與單條網址 |
| `crawl_mol_faq.py` | 從勞動部「勞動條件」底下挑工資、工時、休假、颱風假、年資相關分類，展開列表頁後逐篇抓內文 |
| `chunking.py` | 切塊策略：法條一條一塊、勞動部說明約 500 字一塊；另有固定字數切法留給 Day 4 比較 |
| `store.py` | Chroma 與 embedding 模型（`BAAI/bge-m3`）的共用設定 |
| `build_index.py` | 切塊 → embedding → 重建 Chroma collection `labor_law` |
| `search.py` | `search(query, k, source_type)`，Day 3 的 RAG 從這裡取資料 |
| `data/` | 下載下來的原始資料（JSON），進 git；`chroma_db/` 可重建，不進 git |

## 安裝注意

- torch 從 PyTorch 官方的 CPU 版來源安裝（`requirements.txt` 第一行的 `--extra-index-url`）。PyPI 的下載速度在這台電腦只有約 50 KB/s，PyTorch 官方來源有 1 MB/s 以上，檔案也比較小。
- chromadb 的相依套件很多，PyPI 慢的時候加上 `--retries 20 --timeout 60`。

## 設計決定

- **法條一條一塊**：法條本身就是完整的語意單位，引用時能直接附條號。每塊前面加上「勞動基準法 第24條（第四章 工作時間、休息、休假）」，讓章名和條號也參與比對。
- **勞動部說明依行累積到約 500 字**：相鄰兩塊重疊一行，避免答案剛好被切在兩塊中間。
- **metadata**：法條保留 `law`、`article_no`、`url`、`modified`；說明頁保留 `title`、`url`、`modified`（更新日期）。回答時用來附出處。
- **embedding 用本機的 bge-m3**：Anthropic 沒有 embedding 模型。bge-m3 是多語言模型，繁體中文效果好、免費，CPU 也跑得動。
- **爬蟲禮貌**：兩個網站的 robots.txt 都允許抓這些頁面（法規資料庫只開放 `LawAll.aspx`，所以抓全文頁而不是單條頁）；每次請求間隔 1 秒。

## 觀察

資料量：勞動基準法 98 條、施行細則 70 條（7 條已刪除）、勞工請假規則 13 條，勞動部說明頁 26 篇（另有 5 篇內容只在 PDF 附件裡，先略過）。切成法條 174 塊、說明 48 塊，在 CPU 上算 embedding 約 5 分鐘。

`search.py` 的 6 個測試查詢：

| 查詢 | 結果 | 觀察 |
|---|---|---|
| 休息日加班怎麼算 | 勞動部「休息日加班費」排第一 | ✅ 口語問題比較接近勞動部的白話說明，前 5 名都是說明頁；但**勞基法第 24 條沒進前 5**，只查法條時前 3 名也沒有它 |
| 禮拜六被叫回來上班 | 第 34 條（輪班）、例假休息日安排 | ⚠️ 「禮拜六」和「休息日」在向量上不夠近，分數都只有 0.55 左右 |
| 國定假日上班要給多少錢 | 勞動部「國定假日工資說明」 | ✅ |
| 到職三年有幾天特休 | 特休說明、勞基法第 38 條 | ✅ |
| 颱風天公司要我上班 | 勞基法第 40 條（天災停止假期） | ✅ 但分數低，後面混進請假規則 |
| 第 32 條 | 施行細則第 32 條、勞基法第 77 條… | ❌ 純向量檢索不認得條號，勞基法第 32 條根本沒出現 |

Day 3、Day 4 要處理的問題：
- 第 24 條這種「計算方式寫在法條裡、但用詞和口語差很多」的條文，需要靠混合檢索（關鍵字＋向量）或把說明頁引用的條號一起帶出來。
- 條號查詢要加關鍵字檢索，或在查詢前先用規則抓出「第 N 條」直接查 metadata。
- 國定假日在 114 年修法後變成 16 天（新增教師節、光復節、行憲紀念日等），Day 1 萃取器的 prompt 已跟著更新。
