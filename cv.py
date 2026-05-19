import re
import json
import requests
import os


# =========================
# 1. Allowed Lists
# =========================
ALLOWED_DOMAINS = [
    "AI",
    "Computer Vision",
    "Natural Language Processing",

    "Data Science",

    "Web Development",
    "Backend Development",
    "Mobile Development",

    "Database",
    "Cloud Computing",
    "Cybersecurity",

    "Blockchain",
    "IoT",

    "Business",
    "Marketing",

    "Finance",
    "Healthcare",
    "E-commerce",

    "UX/UI",

    "Media",
    "Entertainment",

    "Environment",
    "Sports",
    "Education"
]


ALLOWED_SKILLS = [
    # Programming Languages
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "C",
    "C++",
    "C#",
    "Scala",
    "R",
    "PHP",
    "Swift",
    "SQL",

    # AI
    "Machine Learning",
    "Deep Learning",
    "NLP",
    "Computer Vision",

    # Data Analysis
    "Statistics",
    "Data Visualization",

    # AI Libraries
    "PyTorch",
    "TensorFlow",
    "Scikit-learn",
    "OpenCV",
    "NumPy",
    "Pandas",
    "Matplotlib",
    "SciPy",

    # Big Data
    "Hadoop",
    "Spark",
    "MapReduce",
    "Hive",
    "ETL",
    "Data Warehousing",

    # Database
    "MySQL",
    "PostgreSQL",
    "MongoDB",
    "SQLite",
    "Oracle",
    "SQL Server",
    "Database Design",
    "Database Administration",
    "Query Optimization",

    # Frontend
    "React",
    "React Native",
    "Redux",
    "Angular",
    "HTML",
    "CSS",
    "Bootstrap",
    "Tailwind CSS",

    # Backend
    "Spring",
    "Spring Boot",
    "Django",
    "Flask",
    "Node.js",
    "Express.js",
    "REST API",
    "GraphQL",

    # DevOps
    "AWS",
    "Docker",
    "Kubernetes",
    "DevOps",
    "Jenkins",
    "CI/CD",

    # Engineering
    "Agile",
    "Scrum",
    "Testing",
    "Performance Testing",

    # Other
    "Git",
    "Linux",
    "Blockchain",
    "ArcGIS",
    "Unity",
    "Unreal Engine"
]


# =========================
# 2. TXT 파일 읽기
# =========================
def load_raw_cv_txt(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return f.read()


# =========================
# 3. CV 단위로 분리
# =========================
def split_raw_cvs(raw_text):
    """
    cv_result_raw.txt 안에 여러 CV가
    ====================================================================================================
    로 구분되어 있다고 가정
    """

    chunks = raw_text.split(
        "===================================================================================================="
    )

    cvs = []

    for chunk in chunks:
        chunk = chunk.strip()

        # 너무 짧은 조각은 제거
        if len(chunk) < 200:
            continue

        cvs.append(chunk)

    return cvs


# =========================
# 4. Ollama LLM 호출
# =========================
def run_llm(prompt):
    url = "http://localhost:11434/api/generate"

    payload = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 700
        }
    }

    res = requests.post(url, json=payload)
    res.raise_for_status()

    return res.json()["response"]


# =========================
# 5. LLM으로 CV 구조화
# =========================
def structure_cv_with_llm(cv_text, user_id):
    prompt = f"""
You are a CV information extraction and normalization system.

Extract structured information from the given CV text.

Return ONLY valid JSON.
Do NOT include explanations.
Do NOT include markdown.
Do NOT extract phone numbers.
Do NOT extract emails.

Allowed domains:
{ALLOWED_DOMAINS}

Allowed skills:
{ALLOWED_SKILLS}

Rules:
1. user_id must be exactly: {user_id}
2. name: extract the person's full name.
3. skills must be selected ONLY from the allowed skills list.
4. domains must be selected ONLY from the allowed domains list.
5. Use exact spelling from the allowed lists.
6. If a skill or domain is not in the allowed list, map it to the closest allowed item if clearly related.
7. If it is not clearly related, remove it.
8. projects should be concise project names or short project keywords.
9. experience should contain job titles or role names only.
10. Do not include phone or email.
11. Do not include empty, meaningless, or duplicate values.
12. Keep projects and experience concise.
13. domains should contain 1 to 5 items.
14. Return this exact JSON format:

{{
  "user_id": "{user_id}",
  "name": "",
  "skills": [],
  "domains": [],
  "projects": [],
  "experience": []
}}

CV_TEXT:
\"\"\"
{cv_text}
\"\"\"
"""

    return run_llm(prompt)


# =========================
# 6. JSON 파싱 보정
# =========================
def extract_json_from_response(response):
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", response)

    if match:
        return json.loads(match.group())

    raise ValueError("LLM 응답에서 JSON을 찾지 못했습니다.")


# =========================
# 7. 후처리
# =========================
def normalize_list(values, allowed_list=None):
    if not isinstance(values, list):
        return []

    result = []

    for value in values:
        if not isinstance(value, str):
            continue

        value = value.strip()

        if not value:
            continue

        # allowed list가 있으면 정확히 포함된 값만 유지
        if allowed_list is not None:
            if value not in allowed_list:
                continue

        if value not in result:
            result.append(value)

    return result


def postprocess_cv(cv_json, user_id):
    return {
        "user_id": user_id,
        "name": str(cv_json.get("name", "")).strip(),
        "skills": normalize_list(
            cv_json.get("skills", []),
            ALLOWED_SKILLS
        ),
        "domains": normalize_list(
            cv_json.get("domains", []),
            ALLOWED_DOMAINS
        ),
        "projects": normalize_list(
            cv_json.get("projects", [])
        ),
        "experience": normalize_list(
            cv_json.get("experience", [])
        )
    }


# =========================
# 8. 전체 실행
# =========================
def main():
    INPUT_PATH = "json/cv_result_raw.txt"
    OUTPUT_PATH = "json/cv_result.json"

    os.makedirs("json", exist_ok=True)

    raw_text = load_raw_cv_txt(INPUT_PATH)
    cv_list = split_raw_cvs(raw_text)

    print(f"총 CV 개수: {len(cv_list)}")

    results = []

    for idx, cv_text in enumerate(cv_list, start=1):
        user_id = f"user_{idx:03d}"

        print(f"\n===== 처리 중: {user_id} =====")

        try:
            llm_response = structure_cv_with_llm(
                cv_text,
                user_id
            )

            structured_json = extract_json_from_response(
                llm_response
            )

            final_json = postprocess_cv(
                structured_json,
                user_id
            )

            results.append(final_json)

            print(f"[DONE] {user_id}")

        except Exception as e:
            print(f"[ERROR] {user_id}")
            print(e)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(
            results,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(f"\n저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()