import json
import re
import requests


# =============================
# 설정
# =============================
INPUT_PATH = "json/contests_result_ex.json"
OUTPUT_PATH = "json/contest_normalized.json"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"

EXCLUDE_KEYWORDS = [
    "숏폼",
    "광고/마케팅"
]


# =============================
# 유틸 함수
# =============================
def extract_json(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError(f"JSON 형식을 찾지 못했습니다. LLM 응답: {text}")

    return json.loads(match.group())


def clean_tag_list(values):
    if not isinstance(values, list):
        return []

    result = []

    for v in values:
        if not isinstance(v, str):
            continue

        tag = v.strip()

        if not tag:
            continue

        if tag not in result:
            result.append(tag)

    return result


def should_exclude_contest(contest):
    text = " ".join([
        str(contest.get("name", "")),
        str(contest.get("분야", "")),
        str(contest.get("응모대상", "")),
        str(contest.get("주최/주관", "")),
        str(contest.get("description", "")),
        str(contest.get("상세내용", "")),
    ]).lower()

    for keyword in EXCLUDE_KEYWORDS:
        if keyword.lower() in text:
            return True

    return False


def make_search_text(item):
    parts = [
        item.get("title", ""),
        " ".join(item.get("domains", [])),
        " ".join(item.get("skills", [])),
        item.get("original_field", ""),
        item.get("organizer", ""),
    ]

    return " ".join(str(p) for p in parts if p).strip()


def call_llm(contest):
    title = contest.get("name", "")
    field = contest.get("분야", "")
    target = contest.get("응모대상", "")
    organizer = contest.get("주최/주관", "")
    description = contest.get("description", contest.get("상세내용", ""))

    prompt = f"""
You are extracting structured tags for a contest recommendation system.

Extract domains and skills from the contest information.

Contest information:
Title: {title}
Category: {field}
Target: {target}
Organizer: {organizer}
Description: {description}

Definitions:
- domains: broad contest areas or fields. Examples: AI, Data Science, Cybersecurity, FinTech, Media, Game Development, Web Development, Mobile Development, Healthcare, Education, Public Data, Smart City.
- skills: detailed technologies, tools, methods, or competencies that may be useful for participating. Examples: Python, Machine Learning, Data Analysis, LLM, Prompt Engineering, Web Development, App Development, UI/UX, Data Visualization.

Rules:
1. Extract tags naturally from the contest title, category, organizer, and description.
2. domains should be broad and concise.
3. skills should be more specific than domains.
4. Do not force Web Development just because the category contains 웹/모바일/IT.
5. If there is not enough information, return fewer tags.
6. Do not invent overly specific technologies that are not implied.
7. Return JSON only.
8. Do not include explanation.
9. skills and domains must be in english.

Output format:
{{
  "domains": [],
  "skills": []
}}
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0
        }
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    response.raise_for_status()

    raw_text = response.json()["response"]
    parsed = extract_json(raw_text)

    domains = clean_tag_list(parsed.get("domains", []))
    skills = clean_tag_list(parsed.get("skills", []))

    return domains, skills


# =============================
# 메인 실행
# =============================
def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        contests = json.load(f)

    result = []
    skipped_count = 0
    error_count = 0

    for idx, contest in enumerate(contests, start=1):

        if should_exclude_contest(contest):
            skipped_count += 1
            print(f"[SKIP] {idx}/{len(contests)} - {contest.get('name', '')}")
            continue

        try:
            domains, skills = call_llm(contest)

            item = {
                "contest_id": len(result) + 1,
                "title": contest.get("name", ""),
                "domains": domains,
                "skills": skills,
                "source_url": contest.get("source_url", ""),
                "original_field": contest.get("분야", ""),
                "target": contest.get("응모대상", ""),
                "organizer": contest.get("주최/주관", ""),
                "period": contest.get("접수기간", ""),
                "total_prize": contest.get("총 상금", ""),
                "first_prize": contest.get("1등 상금", "")
            }

            item["search_text"] = make_search_text(item)

            result.append(item)

            print(f"[DONE] {idx}/{len(contests)} - {item['title']}")
            print(f"       domains: {domains}")
            print(f"       skills : {skills}")

        except Exception as e:
            error_count += 1
            print(f"[ERROR] {idx}/{len(contests)} - {contest.get('name', '')}")
            print(e)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n저장 완료: {OUTPUT_PATH}")
    print(f"원본 개수: {len(contests)}")
    print(f"제거된 개수: {skipped_count}")
    print(f"에러 개수: {error_count}")
    print(f"저장된 개수: {len(result)}")


if __name__ == "__main__":
    main()