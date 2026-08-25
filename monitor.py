"""
P-Bandai(台灣) 재고/신상품 모니터링 스크립트
- 특정 상품 페이지의 재고 상태 변화 감지
- 시리즈 목록 페이지의 신상품 등록 감지
- 변화 발생 시 Discord 웹훅으로 알림 전송

실행 환경: Python 3.10+, Playwright(Chromium)
상태 저장: state.json (GitHub Actions에서는 커밋으로 영속화)
"""

import json
import os
import re
import sys
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

# ============ 설정 (필요에 따라 수정하세요) ============

# 재고 확인할 상품 페이지들 (여러 개 등록 가능)
ITEM_URLS = [
    "https://p-bandai.com/tw/item/A2866729001",
]

# 신상품 확인할 시리즈/목록 페이지들 (여러 개 등록 가능)
SERIES_URLS = [
    "https://p-bandai.com/tw/series/onepiece-series?_f_series=03-002&offset=0&limit=20&sortType=NewArrival&_f_productStatuses=Waiting,On",
]

# 재고 없음을 나타내는 키워드 (대소문자 구분 없이 매칭됨)
OUT_OF_STOCK_KEYWORDS = [
    "OUT OF STOCK",
    "售完", "已售完", "缺貨", "販売を終了", "SOLD OUT", "sold out",
]

# 상품 링크 패턴 (시리즈 페이지에서 개별 상품 코드 추출용)
ITEM_LINK_PATTERN = re.compile(r"/tw/item/([A-Za-z0-9]+)")

STATE_FILE = Path(__file__).parent / "state.json"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

# =======================================================


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"items": {}, "series": {}}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def send_discord(message: str) -> None:
    if not DISCORD_WEBHOOK_URL:
        print("[WARN] DISCORD_WEBHOOK_URL이 설정되지 않아 알림을 보내지 않습니다.")
        print(message)
        return
    resp = requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, timeout=15)
    if resp.status_code >= 300:
        print(f"[ERROR] Discord 전송 실패: {resp.status_code} {resp.text}")


def fetch_page_text(page, url: str) -> str:
    page.goto(url, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(1500)  # 추가 렌더링 대기
    return page.content()


def check_item_stock(page, url: str, state: dict) -> None:
    html = fetch_page_text(page, url)
    text = re.sub(r"<[^>]+>", " ", html)  # 태그 제거 후 텍스트만 확인

    text_lower = text.lower()
    is_out_of_stock = any(kw.lower() in text_lower for kw in OUT_OF_STOCK_KEYWORDS)
    current_status = "out_of_stock" if is_out_of_stock else "in_stock"

    prev_status = state["items"].get(url)
    state["items"][url] = current_status

    if prev_status is None:
        print(f"[INFO] 최초 확인: {url} -> {current_status}")
        return

    if prev_status == "out_of_stock" and current_status == "in_stock":
        send_discord(f"🎉 **재입고 감지!**\n{url}")
    elif prev_status != current_status:
        print(f"[INFO] 상태 변경: {url} : {prev_status} -> {current_status}")


def check_series_new_items(page, url: str, state: dict) -> None:
    html = fetch_page_text(page, url)
    codes = sorted(set(ITEM_LINK_PATTERN.findall(html)))

    prev_codes = set(state["series"].get(url, []))
    state["series"][url] = codes

    if not prev_codes:
        print(f"[INFO] 최초 확인: {url} -> {len(codes)}개 상품")
        return

    new_codes = set(codes) - prev_codes
    for code in new_codes:
        item_url = f"https://p-bandai.com/tw/item/{code}"
        send_discord(f"🆕 **신상품 등록!**\n{item_url}")


def main() -> None:
    state = load_state()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(locale="zh-TW")

        for url in ITEM_URLS:
            try:
                check_item_stock(page, url, state)
            except Exception as e:
                print(f"[ERROR] 상품 체크 실패 ({url}): {e}", file=sys.stderr)

        for url in SERIES_URLS:
            try:
                check_series_new_items(page, url, state)
            except Exception as e:
                print(f"[ERROR] 시리즈 체크 실패 ({url}): {e}", file=sys.stderr)

        browser.close()

    save_state(state)


if __name__ == "__main__":
    main()
