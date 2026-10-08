# ai-in-10-days

10 天 LLM 學習計畫與作品「勞基法薪資小幫手」，計畫內容見 [10天AI學習計畫.md](10天AI學習計畫.md)。

## 回答語言

- 一律以繁體中文回答，包含說明、程式碼註解與 commit 訊息。
- 程式碼識別字（變數、函式、檔名）與技術專有名詞維持英文。

## 資料夾結構

- 每一天的程式與資料放在對應資料夾：`day01/` ～ `day10/`，各自的 `README.md` 列出當天的完成項目。
- 後面的天數要用前面的成果時（例如 Day 5 呼叫 Day 3 的 RAG），直接從前一天的資料夾 import，不要複製程式碼。
- 所有天數共用根目錄的 `.venv`、`requirements.txt` 與 `.env`。

## Python 環境

- 所有 Python 指令一律使用專案根目錄的 `.venv`，不要用系統 Python。
  - 執行：`.\.venv\Scripts\python.exe <script>`
  - 安裝套件：`.\.venv\Scripts\python.exe -m pip install <套件>`，裝完後更新 `requirements.txt`
- `.venv` 不存在時，用 `python -m venv .venv` 建立，再執行 `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`。
- API 金鑰放在 `.env`（已列入 `.gitignore`），不要寫進程式碼或 commit。
