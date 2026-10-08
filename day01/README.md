# Day 1｜LLM API 與結構化輸出

把勞工的口語描述萃取成 JSON，作為 Day 5 計算工具的輸入。

## 完成項目

- [ ] 呼叫 Claude API（`hello_claude.py`）
- [x] 用 Pydantic 定義輸出格式：月薪、年資、加班日類型（平日／休息日／國定假日／例假）、加班時數（`extractor.py` 的 `LaborCase`）
- [ ] 準備 10 段口語描述，手動檢查萃取結果（`test_cases.json`、`check_cases.py`）
- [ ] 特別檢查「禮拜六」「連假」這類模糊說法有沒有判斷錯

## 檔案

| 檔案 | 用途 |
|---|---|
| `hello_claude.py` | 第一次呼叫 Claude API，印出回答、token 用量與延遲 |
| `extractor.py` | `extract(text) -> LaborCase`，用 `messages.parse()` 搭配 Pydantic 取得結構化輸出。Day 5 用 `from day01.extractor import extract` 引用 |
| `test_cases.json` | 10 段口語描述與人工標註的答案，參考日期固定為 2026-10-07 |
| `check_cases.py` | 逐題比對萃取結果，印出錯誤欄位與模型的 notes，並寫出 `results.json` |

## 執行

先把根目錄的 `.env.example` 複製成 `.env`，填入 `ANTHROPIC_API_KEY`。

```powershell
.\.venv\Scripts\python.exe day01\hello_claude.py
.\.venv\Scripts\python.exe day01\extractor.py "我月薪 4 萬，到職 3 年半，上週六休息日被叫回來加班 6 小時"
.\.venv\Scripts\python.exe day01\check_cases.py
```

## 輸出格式（LaborCase）

```json
{
  "monthly_salary": 40000,
  "seniority_years": 3.5,
  "overtime_day_type": "rest_day",
  "overtime_hours": 6,
  "overtime_date": "2026-10-03",
  "notes": []
}
```

- `overtime_day_type`：`weekday` 平日、`rest_day` 休息日、`regular_leave` 例假、`national_holiday` 國定假日；無法判斷時為 `null`。
- 沒提到的欄位一律給 `null`，不套用預設值，Day 5 的 Agent 才知道要反問。
- `notes` 記錄模型做的假設，例如「假設採週休二日，週六為休息日」。

## 模糊說法的判斷規則（寫在 system prompt）

| 說法 | 判斷 | 理由 |
|---|---|---|
| 禮拜六／週六 | 休息日，並在 notes 註明假設 | 一例一休下多數公司週六是休息日，但公司可以另外約定 |
| 禮拜天／週日 | 例假 | 同上 |
| 週六剛好是國慶日 | 國定假日 | 具體日期優先於星期幾 |
| 連假第 N 天 | `null` | 連假裡可能混著國定假日、休息日、例假，交給 Day 5 的「查日期類型」工具 |
| 補班日 | 平日 | 補班日是正常上班日 |
| 颱風假 | 依當天原本的日子判斷 | 颱風假不是法定假日 |

## 學到的東西

- **token**：中文大約 1 個字 1 個多 token，`hello_claude.py` 會印出實際的 input / output token 數。
- **temperature**：Claude Opus 5.5 已不接受 `temperature`，改用 `output_config.effort`（low／medium／high…）控制思考深度與花費；萃取任務用 `medium`。
- **結構化輸出**：`messages.parse(output_format=LaborCase)` 會把 Pydantic model 轉成 JSON schema 限制輸出，回傳的 `parsed_output` 已經是驗證過的 `LaborCase`，不用自己 `json.loads`。
- **欄位描述就是 prompt**：`Field(description=...)` 會進到 schema 裡，模型看得到，例如「4 萬 2 → 42000」的換算規則就寫在這裡。
