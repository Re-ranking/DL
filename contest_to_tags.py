import json
import re
import requests


INPUT_PATH = "json/contests_result_ex.json"
OUTPUT_PATH = "json/contest_tags.json"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"


def clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def extract_contest_id(source_url, idx):
    match = re.search(r"ix=(\d+)", source_url or "")
    if match:
        return match.group(1)
    return str(idx + 1)


def run_llm(prompt):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": 500,
            "temperature": 0.2
        }
    }

    res = requests.post(OLLAMA_URL, json=payload, timeout=120)
    res.raise_for_status()
    return res.json()["response"]


def extract_json_from_response(response):
    response = response.strip()

    start = response.find("{")
    end = response.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("LLM 응답에서 JSON을 찾지 못했습니다.")

    json_text = response[start:end + 1]
    return json.loads(json_text)


def make_prompt(contest):
    title = clean_text(contest.get("name"))
    category = clean_text(contest.get("분야"))
    host = clean_text(contest.get("주최/주관"))
    target = clean_text(contest.get("응모대상"))

    prompt = f"""
You are a contest tag extraction assistant.

Analyze the contest information and generate tags.

Return ONLY valid JSON.
Do NOT include markdown.
Do NOT include explanation.

Use exactly this JSON format:

{{
  "domains": [],
  "skills": []
}}

Rules:
- domains must be English only.
- skills must be English only.
- domains means contest fields, such as AI, Data Analysis, Web Development, App Development, Cybersecurity, Marketing, Design, Game Development, VR/AR.
- skills means useful or required abilities, such as Python, Machine Learning, Data Analysis, UI/UX Design, Web Development, App Development, Video Editing.
- Use 2 to 5 domains.
- Use 3 to 8 skills.
- Infer reasonable tags from title, category, host, and target.
- Do not include Korean.
- Do not include empty strings.

Contest information:
title: {title}
category: {category}
host: {host}
target: {target}
"""
    return prompt


def generate_tags_with_llm(contest):
    prompt = make_prompt(contest)
    response = run_llm(prompt)
    parsed = extract_json_from_response(response)

    return {
        "domains": parsed.get("domains", []),
        "skills": parsed.get("skills", [])
    }


def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        contests = json.load(f)

    results = []
    seen_ids = set()

    for idx, contest in enumerate(contests):
        contest_id = extract_contest_id(contest.get("source_url", ""), idx)

        # 중복 제거
        if contest_id in seen_ids:
            continue
        seen_ids.add(contest_id)

        title = clean_text(contest.get("name"))

        try:
            tags = generate_tags_with_llm(contest)

            result = {
                "contest_id": contest_id,
                "title": title,
                "domains": tags["domains"],
                "skills": tags["skills"]
            }

        except Exception as e:
            print(f"[LLM 실패] {contest_id} / {title}")
            print(e)

            result = {
                "contest_id": contest_id,
                "title": title,
                "domains": [],
                "skills": []
            }

        results.append(result)
        print(f"[DONE] {contest_id} - {title}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()