# pip install requests beautifulsoup4 pandas openpyxl

import re
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = "https://www.wevity.com"
CATEGORY_ID = 20  # 웹/모바일/IT

OUTPUT_JSON = "contests_result.json"

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


def is_valid_image_url(image_url):
    """
    실제 사용할 수 있는 이미지 URL인지 검사
    """
    if not image_url:
        return False

    image_url_lower = image_url.lower()

    # 위비티 기본 이미지 제외
    if "noimgs.png" in image_url_lower:
        return False

    # 로고, 아이콘, 버튼, 배너 제외
    exclude_keywords = [
        "icon",
        "logo",
        "btn",
        "button",
        "banner",
        "sns",
        "facebook",
        "twitter",
        "kakao"
    ]

    if any(keyword in image_url_lower for keyword in exclude_keywords):
        return False

    # 이미지 확장자 확인
    image_exts = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    if not any(ext in image_url_lower for ext in image_exts):
        return False

    return True


def extract_image_url(soup):
    """
    상세 페이지에서 대표 이미지 URL 추출
    - noimgs.png 제외
    - lazy loading 속성 확인
    - upload 이미지 우선 선택
    """

    candidates = []

    for img in soup.select("img"):
        src = (
            img.get("src")
            or img.get("data-src")
            or img.get("data-original")
            or img.get("data-lazy")
            or ""
        ).strip()

        if not src:
            continue

        image_url = urljoin(BASE, src)

        if not is_valid_image_url(image_url):
            continue

        candidates.append(image_url)

    # 실제 공모전 포스터는 upload 경로일 가능성이 높음
    for url in candidates:
        if "upload" in url.lower():
            return url

    # upload 이미지가 없으면 후보 중 첫 번째 반환
    if candidates:
        return candidates[0]

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


def crawl_wevity_web_mobile_it(max_pages=7):
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

            contest_id = len(results) + 1

            row = {
                "contest_id": contest_id,
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
            print("이미지 URL:", row["image_url"] if row["image_url"] else "없음")
            print()

            time.sleep(0.3)

    return results


def main():
    contests = crawl_wevity_web_mobile_it(max_pages=7)

    df = pd.DataFrame(contests)

    columns = [
        "contest_id",
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
        OUTPUT_JSON,
        orient="records",
        force_ascii=False,
        indent=2
    )

    print()
    print(f"저장 완료: {len(df)}개")
    print(f"JSON 파일명: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()