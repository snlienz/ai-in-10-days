"""跑 test_cases.json 的 10 段描述，和人工標註的答案比對。

執行：.\\.venv\\Scripts\\python.exe day01\\check_cases.py
"""

import json
import sys
from datetime import date
from pathlib import Path

from extractor import DAY_TYPE_ZH, extract

HERE = Path(__file__).parent
FIELDS = ["monthly_salary", "seniority_years", "overtime_day_type", "overtime_hours"]
# 年資換算到職日時會有幾天的誤差，容許 0.1 年
TOLERANCE = {"seniority_years": 0.1}


def matches(field: str, expected, actual) -> bool:
    if expected is None or actual is None:
        return expected is actual
    if field in TOLERANCE:
        return abs(float(expected) - float(actual)) <= TOLERANCE[field]
    if isinstance(expected, (int, float)):
        return float(expected) == float(actual)
    return expected == actual


def fmt(field: str, value) -> str:
    if value is None:
        return "null"
    if field == "overtime_day_type":
        return DAY_TYPE_ZH[value]
    return str(value)


def main() -> int:
    data = json.loads((HERE / "test_cases.json").read_text(encoding="utf-8"))
    ref = date.fromisoformat(data["reference_date"])
    results = []
    field_correct = 0

    for case in data["cases"]:
        output = extract(case["text"], reference_date=ref).model_dump()
        wrong = [f for f in FIELDS if not matches(f, case["expected"][f], output[f])]
        field_correct += len(FIELDS) - len(wrong)
        results.append({**case, "output": output, "wrong": wrong})

        mark = "✅" if not wrong else "❌"
        print(f"\n{mark} #{case['id']}｜{case['focus']}")
        print(f"   描述：{case['text']}")
        for f in FIELDS:
            exp, act = case["expected"][f], output[f]
            flag = "  " if f not in wrong else "← 錯"
            print(f"   {f:<18} 預期 {fmt(f, exp):<8} 實際 {fmt(f, act):<8} {flag}")
        if output["overtime_date"]:
            print(f"   overtime_date      {output['overtime_date']}")
        for note in output["notes"]:
            print(f"   📝 {note}")

    passed = sum(1 for r in results if not r["wrong"])
    total_fields = len(results) * len(FIELDS)
    print(f"\n整題全對：{passed}/{len(results)}　欄位正確率：{field_correct}/{total_fields}"
          f"（{field_correct / total_fields:.0%}）")

    (HERE / "results.json").write_text(
        json.dumps({"reference_date": data["reference_date"], "results": results},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"完整結果已寫入 {HERE / 'results.json'}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
