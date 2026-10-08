"""從全國法規資料庫下載法條全文，逐條存成 data/laws.json。

執行（在專案根目錄）：.\\.venv\\Scripts\\python.exe -m day02.fetch_laws
"""

import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DATA_DIR = Path(__file__).parent / "data"
BASE_URL = "https://law.moj.gov.tw/LawClass/"
# robots.txt 只開放 LawAll.aspx，所以抓全文頁，每條的連結另外組成 LawSingle 網址給人點
LAWS = {
    "N0030001": "勞動基準法",
    "N0030002": "勞動基準法施行細則",
    "N0030006": "勞工請假規則",
}
HEADERS = {"User-Agent": "ai-in-10-days learning project (labor law RAG)"}


def normalize_article_no(raw: str) -> str:
    """「第 9-1 條」→「9-1」"""
    return re.sub(r"[第條\s]", "", raw)


def parse_law_page(html: str, pcode: str, law_name: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    modified = ""
    th = soup.find("th", string=re.compile("修正日期"))
    if th and th.find_next("td"):
        modified = " ".join(th.find_next("td").get_text().split())

    articles = []
    chapter = ""
    container = soup.select_one("div.law-reg-content")
    for node in container.find_all("div", recursive=False):
        classes = node.get("class", [])
        if "h3" in classes:
            # 章、節標題，例如「第 四 章 工作時間、休息、休假」
            chapter = " ".join(node.get_text().split())
            continue
        if "row" not in classes:
            continue
        article_no = normalize_article_no(node.select_one("div.col-no").get_text())
        # 每個 div 是一項或一款，換行分開，保留條文的段落結構
        lines = [d.get_text(strip=True) for d in node.select("div.law-article > div")]
        text = "\n".join(line for line in lines if line)
        articles.append({
            "id": f"{pcode}-{article_no}",
            "law": law_name,
            "pcode": pcode,
            "article_no": article_no,
            "chapter": chapter,
            "text": text,
            "deleted": bool(re.fullmatch(r"[（(]刪除[）)]", text)),
            "url": f"{BASE_URL}LawSingle.aspx?pcode={pcode}&flno={article_no}",
            "modified": modified,
        })
    return articles


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    all_articles = []
    for pcode, law_name in LAWS.items():
        resp = requests.get(f"{BASE_URL}LawAll.aspx", params={"pcode": pcode},
                            headers=HEADERS, timeout=30)
        resp.raise_for_status()
        articles = parse_law_page(resp.text, pcode, law_name)
        deleted = sum(a["deleted"] for a in articles)
        print(f"{law_name}：{len(articles)} 條（已刪除 {deleted} 條），修正日期 {articles[0]['modified']}")
        all_articles.extend(articles)
        time.sleep(1)

    out = DATA_DIR / "laws.json"
    out.write_text(json.dumps(all_articles, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"共 {len(all_articles)} 條，已寫入 {out}")


if __name__ == "__main__":
    main()
