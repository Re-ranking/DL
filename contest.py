import json
import re
import requests


# =============================
# 설정
# =============================
INPUT_PATH = "json/contests_result.json"
OUTPUT_PATH = "json/contest_normalize.json"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"


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


def should_exclude_contest(contest):

    field = str(contest.get("분야", "")).lower()

    skip_keywords = [
        "광고",
        "마케팅"
    ]

    return any(keyword in field for keyword in skip_keywords)


# =============================
# LLM 호출
# =============================
def call_llm(contest):

    title = contest.get("name", "")
    field = contest.get("분야", "")
    description = contest.get("description", "")

    prompt = f"""
You are preprocessing contest data for a contest recommendation system.

Your task:
1. Translate the contest title into concise English.
2. Translate the contest field/category into concise English.
3. Summarize ONLY the important contest content in English.

Remove unnecessary information such as:
- eligibility
- application period
- prize information
- award details
- organizer introduction
- contact information
- submission method
- schedule details
- promotional phrases
- legal notices

Focus only on:
- what participants need to build, design, analyze, or propose
- the main contest topic
- technical themes
- service or product ideas
- AI, data, software, web, mobile, or IT-related goals
- problem-solving direction

Rules:
1. Do not include Korean.
2. Do not include prize, date, target participant, or award information.
3. Keep the description concise.
4. Do not invent details that are not implied.
5. Return JSON only.
6. Do not include explanation.

Contest information:
Title: {title}
Field: {field}

Description:
{description}

Output format:
{{
  "title": "",
  "field": "",
  "description": ""
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

    english_title = str(parsed.get("title", "")).strip()
    english_field = str(parsed.get("field", "")).strip()
    english_description = str(parsed.get("description", "")).strip()

    return (
        english_title,
        english_field,
        english_description
    )


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

            title, field, description = call_llm(contest)

            item = {
                "contest_id": len(result) + 1,

                "title": title,

                "field": field,

                "description": description
            }

            result.append(item)

            print(f"[DONE] {idx}/{len(contests)} - {title}")

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