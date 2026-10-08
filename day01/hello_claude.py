"""第一次呼叫 Claude API：看回答內容、token 用量與延遲。

執行：.\\.venv\\Scripts\\python.exe day01\\hello_claude.py
"""

import sys
import time

import anthropic
from dotenv import load_dotenv

load_dotenv()

QUESTION = "用兩句話說明台灣勞基法的「休息日」和「例假」差在哪裡。"


def main() -> None:
    client = anthropic.Anthropic()
    print(f"問題：{QUESTION}\n")
    start = time.perf_counter()
    response = client.messages.create(
        model="claude-opus-5-5",
        max_tokens=16000,
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": QUESTION}],
    )
    print("".join(b.text for b in response.content if b.type == "text").strip())
    print(f"\n⏱ {time.perf_counter() - start:.1f}s｜stop_reason={response.stop_reason}"
          f"｜input {response.usage.input_tokens} / output {response.usage.output_tokens} tokens")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
