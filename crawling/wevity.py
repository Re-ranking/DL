# pip install requests beautifulsoup4 pandas openpyxl

import re
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = "https://www.wevity.com"
CATEGORY_ID = 20  # 웹/모바일/IT

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": BASE,
}

FIELDS = [
    "분야",
    "응모대상",
    "주최/주관",
    "접수기간",
    "총 상금",
    "1등 상금",
    "홈페이지"
]


def get_soup(url):
    res = requests.get(url, headers=HEADERS, timeout=10)
    res.raise_for_status()
    return BeautifulSoup(res.text, "html.parser")


def clean(text):
    return re.sub(r"\s+", " ", str(text)).strip()


def get_list_url(page):
    return (
        f"{BASE}/index_university.php?"
        f"c=find&cidx={CATEGORY_ID}&classonof=off&classonof6=on&gub=1&s=_university&gp={page}"
    )


def crawl_list_page(page):
    url = get_list_url(page)
    soup = get_soup(url)

    contests = []

    for a in soup.select("a[href]"):
        href = a.get("href", "")
        name = clean(a.get_text(" ", strip=True))

        if not name:
            continue

        if "gbn=view" not in href and "gbn=viewok" not in href:
            continue

        source_url = urljoin(BASE, href)

        contests.append({
            "name": name,
            "source_url": source_url
        })

    return contests


def cut_unnecessary_description(description):
    cut_keywords = [
        "시상내역",
        "참가대상",
        "신청기간",
        "참가혜택",
        "심사규정",
        "참가 대상",
        "모집 기간",
        "심사 규정",
        "접수 기간",
        "목록 전체",
        "접수기간",
        "공모기간",
        "작성가이드",
        "문의처",
        "주요 일정",
        "포상",
        "시상금"
    ]

    for keyword in cut_keywords:
        if keyword in description:
            description = description.split(keyword)[0].strip()

    return description


def extract_image_url(soup):
    """
    상세 페이지에서 대표 이미지 URL 추출
    """
    for img in soup.select("img"):
        src = img.get("src", "").strip()

        if not src:
            continue

        src_lower = src.lower()

        # 아이콘, 로고, 버튼류 제외
        if any(x in src_lower for x in ["icon", "logo", "btn", "banner"]):
            continue

        image_url = urljoin(BASE, src)

        # 이미지 확장자가 있는 것 우선
        if any(ext in image_url.lower() for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]):
            return image_url

    return ""


def parse_detail_page(source_url):
    soup = get_soup(source_url)

    full_text = clean(soup.get_text(" ", strip=True))

    data = {
        "분야": "",
        "응모대상": "",
        "주최/주관": "",
        "접수기간": "",
        "총 상금": "",
        "1등 상금": "",
        "홈페이지": "",
        "image_url": "",
        "description": ""
    }

    for li in soup.select("li"):
        text = clean(li.get_text(" ", strip=True))

        for field in FIELDS:
            if text.startswith(field):
                value = text.replace(field, "", 1).strip()
                data[field] = value

    for a in soup.select("a[href]"):
        href = a.get("href", "").strip()
        link_text = clean(a.get_text(" ", strip=True))

        if href.startswith("http") and "wevity.com" not in href:
            if data["홈페이지"] == "" or link_text in data["홈페이지"]:
                data["홈페이지"] = href
                break

    data["image_url"] = extract_image_url(soup)

    marker = "공모전 공모요강"

    if marker in full_text:
        description = full_text.split(marker, 1)[1].strip()
    else:
        description = full_text

    description = cut_unnecessary_description(description)
    description = description[:2000]

    data["description"] = description

    return data


def should_skip_contest(field_text):
    skip_keywords = [
        "광고",
        "마케팅"
    ]

    return any(keyword in str(field_text) for keyword in skip_keywords)


def crawl_wevity_web_mobile_it(max_pages=1):
    results = []
    seen_urls = set()

    for page in range(1, max_pages + 1):
        print(f"[목록] {page}페이지 수집 중")

        try:
            items = crawl_list_page(page)
        except Exception as e:
            print(f"목록 페이지 오류: {e}")
            continue

        print(f"상세 링크 {len(items)}개 발견")

        for item in items:
            if item["source_url"] in seen_urls:
                continue

            seen_urls.add(item["source_url"])

            try:
                detail = parse_detail_page(item["source_url"])
            except Exception as e:
                print(f"상세 페이지 오류: {item['source_url']} / {e}")
                continue

            if should_skip_contest(detail["분야"]):
                print("건너뜀(광고/마케팅):", item["name"])
                continue

            row = {
                "name": item["name"],
                "source_url": item["source_url"],
                "분야": detail["분야"],
                "응모대상": detail["응모대상"],
                "주최/주관": detail["주최/주관"],
                "접수기간": detail["접수기간"],
                "총 상금": detail["총 상금"],
                "1등 상금": detail["1등 상금"],
                "홈페이지": detail["홈페이지"],
                "image_url": detail["image_url"],
                "description": detail["description"]
            }

            results.append(row)
            print("저장:", row["name"])

            time.sleep(0.3)

    return results


def main():
    contests = crawl_wevity_web_mobile_it(max_pages=1)

    df = pd.DataFrame(contests)

    columns = [
        "name",
        "source_url",
        "분야",
        "응모대상",
        "주최/주관",
        "접수기간",
        "총 상금",
        "1등 상금",
        "홈페이지",
        "image_url",
        "description"
    ]

    df = df[columns]

    df.to_json(
        "contests_result.json",
        orient="records",
        force_ascii=False,
        indent=2
    )

    print()
    print(f"저장 완료: {len(df)}개")
    print("파일명: contests_result.json")


if __name__ == "__main__":
    main()