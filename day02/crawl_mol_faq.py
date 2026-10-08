"""爬勞動部網站「勞動條件」底下和工資、工時、休假有關的說明頁，存成 data/mol_faq.json。

執行（在專案根目錄）：.\\.venv\\Scripts\\python.exe -m day02.crawl_mol_faq
"""

import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

DATA_DIR = Path(__file__).parent / "data"
SITE = "https://www.mol.gov.tw"
SECTION = "/1607/28162/28166"  # 勞動條件、就業平等
# 只挑和薪資小幫手有關的分類；列表頁（lpsimplelist、nodelist）會展開成底下的每一篇
SEEDS = [
    "/28180/81521/lpsimplelist",    # 工資計算說明（加班費、國定假日、特休未休工資）
    "/28180/28198/nodelist",        # 延時工資（加班費）函釋、加班補休
    "/28180/28194/29050/post",      # 工資認定與給付
    "/28180/28196/29051/post",      # 假日工資
    "/28180/28204/29053/post",      # 特別休假工資
    "/28180/28212/29054/post",      # 平均工資
    "/28180/28216/lpsimplelist",    # 工資懶人包
    "/28218/28226/lpsimplelist",    # 工時相關權益（例假、休息日、國定假日、特休、請假）
    "/28218/28230/lpsimplelist",    # 天然災害勞工出勤權益（颱風假）
    "/28168/28178/lpsimplelist",    # 工作年資相關疑義
]
HEADERS = {"User-Agent": "ai-in-10-days learning project (labor law RAG)"}
DELAY_SECONDS = 1.0
# 每頁都有、和內容無關的欄位與按鈕文字
BOILERPLATE = re.compile(
    r"^(更新日期|發布單位|發布日期|點閱次數)[:：]|^(相關圖片|相關檔案|檔案下載|pdf|odt|docx?|【.*試算系統】)$"
)
# 內文只剩附件標題的頁面（內容都在 PDF 裡）略過
MIN_TEXT_LENGTH = 100


def fetch(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    time.sleep(DELAY_SECONDS)
    return BeautifulSoup(resp.text, "html.parser")


def list_posts(list_url: str) -> list[str]:
    """列表頁 → 底下所有 /post 文章網址。只收同一分類路徑下的連結，避開側邊選單。"""
    prefix = list_url.rsplit("/", 1)[0] + "/"
    soup = fetch(list_url)
    urls = []
    for a in soup.find_all("a", href=True):
        url = urljoin(SITE, a["href"])
        if url.startswith(prefix) and url.endswith("/post") and url not in urls:
            urls.append(url)
    return urls


def parse_post(url: str) -> dict:
    soup = fetch(url)
    title = soup.title.get_text().split("-勞動部全球資訊網")[0].strip()
    content = soup.select_one("section.cp")
    for tag in content.find_all(["style", "script"]):
        tag.decompose()
    lines = [line.strip() for line in content.get_text("\n").splitlines()]
    text = "\n".join(line for line in lines if line and not BOILERPLATE.match(line))
    updated = re.search(r"更新日期[:：]\s*(\d{4}-\d{2}-\d{2})", soup.get_text())
    return {
        "id": "mol-" + url.removesuffix("/post").rsplit("/", 1)[-1],
        "title": title,
        "url": url,
        "updated": updated.group(1) if updated else "",
        "text": text,
    }


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    post_urls: list[str] = []
    for seed in SEEDS:
        url = SITE + SECTION + seed
        found = [url] if url.endswith("/post") else list_posts(url)
        print(f"{seed}：{len(found)} 篇")
        post_urls += [u for u in found if u not in post_urls]

    pages = []
    for url in post_urls:
        try:
            page = parse_post(url)
        except (requests.RequestException, AttributeError) as e:
            print(f"  跳過 {url}：{e}")
            continue
        if len(page["text"]) < MIN_TEXT_LENGTH:
            print(f"  跳過「{page['title']}」：內文只有 {len(page['text'])} 字，內容在附件裡")
            continue
        print(f"  {page['title']}（{len(page['text'])} 字）")
        pages.append(page)

    out = DATA_DIR / "mol_faq.json"
    out.write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"共 {len(pages)} 篇，已寫入 {out}")


if __name__ == "__main__":
    main()
