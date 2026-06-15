import json
import re
import requests


INPUT_PATH = "json/contests_result.json"
OUTPUT_PATH = "json/contest_normalize.json"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"


ALLOWED_DOMAINS = [
    "AI",
    "Data",
    "Software",
    "Infrastructure",
    "Emerging Tech",
    "Business",
    "Financial",
    "Healthcare",
    "Commerce",
    "Design",
    "Media",
    "Other"
]

ALLOWED_SKILLS = [
    "Programming Languages",
    "AI",
    "Data Analysis",
    "AI Libraries",
    "Big Data",
    "Database",
    "Frontend",
    "Backend",
    "DevOps",
    "Engineering",
    "Other"
]


def extract_json(text):
    try:
        return json.loads(text)

    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)

    if not match:
        raise ValueError(f"JSON 형식을 찾지 못했습니다. LLM 응답: {text}")

    return json.loads(match.group())


def clean_list(values, allowed_values):
    if not isinstance(values, list):
        return []

    result = []

    for value in values:
        value = str(value).strip()

        if value in allowed_values and value not in result:
            result.append(value)

    return result


def should_exclude_contest(contest):
    text = " ".join([
        str(contest.get("name", "")),
        str(contest.get("분야", "")),
        str(contest.get("description", ""))
    ])

    skip_keywords = [
        "광고",
        "마케팅"
    ]

    return any(keyword in text for keyword in skip_keywords)


def call_llm(contest):
    title = contest.get("name", "")
    description = contest.get("description", "")

    prompt = f"""
You are preprocessing contest data for a contest recommendation system.

Your task:
1. Extract domains only from ALLOWED_DOMAINS.
2. Extract skills only from ALLOWED_SKILLS.

Important rules:
- domains must be selected only from ALLOWED_DOMAINS.
- skills must be selected only from ALLOWED_SKILLS.
- Do not create new domain names.
- Do not create new skill names.
- If there is no suitable domain or skill, return an empty list.
- Do not include Korean.
- Return JSON only.
- Do not include explanation.

ALLOWED_DOMAINS:
{json.dumps(ALLOWED_DOMAINS, ensure_ascii=False)}

ALLOWED_SKILLS:
{json.dumps(ALLOWED_SKILLS, ensure_ascii=False)}

Contest information:
Title: {title}

Description:
{description}

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

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    raw_text = response.json()["response"]

    parsed = extract_json(raw_text)

    domains = clean_list(
        parsed.get("domains", []),
        ALLOWED_DOMAINS
    )

    skills = clean_list(
        parsed.get("skills", []),
        ALLOWED_SKILLS
    )

    return {
        "domains": domains,
        "skills": skills
    }


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
            normalized = call_llm(contest)

            item = {
                "contest_id": len(result) + 1,

                "title": contest.get("name", ""),

                "domains": normalized["domains"],
                "skills": normalized["skills"],

                "source_url": contest.get("source_url", ""),
                "target": contest.get("응모대상", ""),
                "host": contest.get("주최/주관", ""),
                "period": contest.get("접수기간", ""),
                "total_prize": contest.get("총 상금", ""),
                "first_prize": contest.get("1등 상금", ""),
                "homepage": contest.get("홈페이지", ""),
                "image_url": contest.get("image_url", ""),
                "description": contest.get("description", "")
            }

            result.append(item)

            print(f"[DONE] {idx}/{len(contests)} - {item['title']}")

        except Exception as e:
            error_count += 1

            print(f"[ERROR] {idx}/{len(contests)} - {contest.get('name', '')}")
            print(e)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=2
        )

    print()
    print(f"저장 완료: {OUTPUT_PATH}")
    print(f"원본 개수: {len(contests)}")
    print(f"스킵 개수: {skipped_count}")
    print(f"에러 개수: {error_count}")
    print(f"저장된 개수: {len(result)}")


if __name__ == "__main__":
    main()