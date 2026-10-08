"""Day 1：把勞工的口語描述萃取成結構化資料（LaborCase）。

Day 5 的計算工具會直接 import 這個模組：
    from day01.extractor import extract, LaborCase
"""

from __future__ import annotations

import sys
from datetime import date
from typing import Literal

import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

MODEL = "claude-opus-5-5"

DayType = Literal["weekday", "rest_day", "regular_leave", "national_holiday"]

DAY_TYPE_ZH: dict[str, str] = {
    "weekday": "平日",
    "rest_day": "休息日",
    "regular_leave": "例假",
    "national_holiday": "國定假日",
}


class LaborCase(BaseModel):
    """一段勞工描述中，計算加班費與特休需要的欄位。無法確定的欄位一律為 null。"""

    monthly_salary: int | None = Field(
        description="月薪（新台幣元，整數）。例如「4 萬 2」→ 42000、「35K」→ 35000。只給時薪或沒提到時為 null。"
    )
    seniority_years: float | None = Field(
        description="年資（年，可為小數）。例如「3 年半」→ 3.5；給到職日時以參考日期換算，四捨五入到小數第二位。"
    )
    overtime_day_type: DayType | None = Field(
        description="加班日類型：weekday=平日、rest_day=休息日、regular_leave=例假、national_holiday=國定假日。無法判斷時為 null。"
    )
    overtime_hours: float | None = Field(
        description="這次描述中的加班總時數（小時）。多天加班時加總。"
    )
    overtime_date: str | None = Field(
        description="加班日期（YYYY-MM-DD），只有能從描述與參考日期明確推出時才填，否則為 null。"
    )
    notes: list[str] = Field(
        description="判斷時做的假設或無法確定的地方，用繁體中文，每點一句。沒有就給空陣列。"
    )


SYSTEM_PROMPT = """\
你是台灣勞動基準法的資料萃取器。使用者會用口語描述自己的工作與加班狀況，你要把它轉成結構化欄位，交給後續的加班費計算程式。你只負責萃取，不計算金額。

## 加班日類型的判斷規則
- 台灣多數公司採「一例一休」：週六通常是休息日（rest_day），週日通常是例假（regular_leave）。
  - 描述說「週六／禮拜六／星期六」而沒有其他資訊時，判為 rest_day，並在 notes 註明「假設採週休二日，週六為休息日」。
  - 「週日／禮拜天」同理判為 regular_leave，並在 notes 註明假設。
  - 使用者明確說「休息日」「例假」時，以使用者說的為準。
- 國定假日（national_holiday）指勞基法第 37 條的應放假日：元旦（1/1）、除夕及春節（農曆除夕前一日至正月初三）、和平紀念日（2/28）、兒童節（4/4）、清明節、勞動節（5/1）、端午節、中秋節、教師節（9/28）、國慶日（10/10）、臺灣光復暨金門古寧頭大捷紀念日（10/25）、行憲紀念日（12/25），以及選舉、罷免與公民投票的投票日。
- 「補班日」是正常上班日，判為 weekday。
- 「颱風假」不是法定假日，依當天原本是什麼日子判斷；平常上班日就是 weekday，並在 notes 說明。
- 「連假」裡的每一天可能是國定假日、休息日、例假或彈性放假，不要自行推算是哪一種。描述只說「連假第 N 天」而沒有明確日期時，overtime_day_type 給 null，並在 notes 說明需要查行事曆。
- 平日下班後留下來工作就是 weekday。

## 其他欄位
- 金額、年資、時數都轉成阿拉伯數字。
- 相對時間（「上週六」「去年 3 月到職」）以使用者訊息中的參考日期換算。
- 不要猜測描述中沒有的資訊。沒提到的欄位給 null，不要套用預設值。
- 描述裡有多種解讀時，選最常見的解讀，並把另一種可能寫進 notes。
"""

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def extract(text: str, reference_date: date | None = None) -> LaborCase:
    """把一段口語描述萃取成 LaborCase。reference_date 用來換算「上週六」「去年到職」，預設為今天。"""
    ref = reference_date or date.today()
    weekday_zh = "一二三四五六日"[ref.weekday()]
    response = _get_client().messages.parse(
        model=MODEL,
        max_tokens=16000,
        output_config={"effort": "medium"},
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"參考日期：{ref.isoformat()}（星期{weekday_zh}）\n\n描述：{text}",
        }],
        output_format=LaborCase,
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"模型拒絕回答：{response.stop_details}")
    if response.parsed_output is None:
        raise RuntimeError(f"沒有取得結構化輸出，stop_reason={response.stop_reason}")
    return response.parsed_output


if __name__ == "__main__":
    sample = " ".join(sys.argv[1:]) or "我月薪 4 萬，到職 3 年半，上週六休息日被叫回來加班 6 小時"
    print(sample)
    print(extract(sample).model_dump_json(indent=2))
