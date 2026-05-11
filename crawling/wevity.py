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

# 제외할 분야 키워드
SKIP_FIELDS = [
    "광고",
    "마케팅"
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


def extract_image_url(soup):

    skip_keywords = [
        "banner",
        "logo",
        "icon",
        "btn",
        "button",
        "sns",
        "facebook",
        "twitter",
        "kakao",
        "naver"
    ]

    for img in soup.select("img[src]"):

        src = img.get("src", "").strip()

        if not src:
            continue

        image_url = urljoin(BASE, src)
        lower_url = image_url.lower()

        if any(keyword in lower_url for keyword in skip_keywords):
            continue

        return image_url

    return ""


def should_skip_contest(field_text):

    field_text = clean(field_text)

    for keyword in SKIP_FIELDS:
        if keyword in field_text:
            return True

    return False


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

    # 상세 정보 추출
    for li in soup.select("li"):

        text = clean(li.get_text(" ", strip=True))

        for field in FIELDS:

            if text.startswith(field):

                value = text.replace(field, "", 1).strip()
                data[field] = value

    # 홈페이지 URL 추출
    for a in soup.select("a[href]"):

        href = a.get("href", "").strip()
        link_text = clean(a.get_text(" ", strip=True))

        if href.startswith("http") and "wevity.com" not in href:

            if data["홈페이지"] == "" or link_text in data["홈페이지"]:
                data["홈페이지"] = href
                break

    # 이미지 URL
    data["image_url"] = extract_image_url(soup)

    # 상세 내용
    marker = "공모전 공모요강"

    if marker in full_text:
        description = full_text.split(marker, 1)[1].strip()
    else:
        description = full_text

    data["description"] = description

    return data


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

            # 광고/마케팅 분야 제외
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