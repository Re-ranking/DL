import json
import os
import re
import requests


INPUT_PATH = "json/cv_result.json"
OUTPUT_PATH = "json/cv_result_normalized.json"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"


ALLOWED_DOMAINS = [
    "AI",
    "Machine Learning",
    "Deep Learning",
    "Data Science",
    "Data Analysis",
    "Computer Vision",
    "Natural Language Processing",
    "Big Data",
    "Software Development",
    "Web Development",
    "Frontend Development",
    "Backend Development",
    "Mobile Development",
    "Database",
    "Database Administration",
    "Data Engineering",
    "Cloud Computing",
    "DevOps",
    "Cybersecurity",
    "Game Development",
    "Blockchain",
    "IoT",
    "Business Intelligence",
    "Analytics",
    "Enterprise Systems",
    "IT Infrastructure"
]


ALLOWED_SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "C", "C++", "C#",
    "Scala", "R", "PHP", "Swift", "SQL",

    "Machine Learning", "Deep Learning", "Predictive Modeling",
    "Data Mining", "Data Visualization", "NLP", "Computer Vision",
    "Statistics", "Analytics",

    "PyTorch", "TensorFlow", "Scikit-learn", "OpenCV",
    "NumPy", "Pandas", "Matplotlib", "SciPy",

    "Hadoop", "Spark", "MapReduce", "Hive", "ETL", "Data Warehousing",

    "MySQL", "PostgreSQL", "MongoDB", "SQLite", "Oracle",
    "SQL Server", "Database Design", "Database Administration",
    "Query Optimization",

    "React", "React Native", "Redux", "Angular",
    "HTML", "CSS", "Bootstrap", "Tailwind CSS",

    "Spring", "Spring Boot", "Django", "Flask", "Node.js",
    "Express.js", "REST API", "GraphQL",

    "AWS", "Docker", "Kubernetes", "DevOps", "Jenkins", "CI/CD",

    "Agile", "Scrum", "Testing", "Performance Testing",

    "Git", "Linux", "Blockchain", "ArcGIS", "Unity", "Unreal Engine"
]


def clean_text(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def run_llm(prompt):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,
            "num_predict": 700
        }
    }

    res = requests.post(OLLAMA_URL, json=payload, timeout=120)
    res.raise_for_status()

    return res.json()["response"]


def extract_json_from_response(response):
    response = response.strip()

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    start = response.find("{")
    end = response.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("LLM 응답에서 JSON을 찾지 못했습니다.")

    return json.loads(response[start:end + 1])


def make_normalize_prompt(user):
    user_id = clean_text(user.get("user_id"))
    name = clean_text(user.get("name"))

    raw_domains = user.get("domains", [])
    raw_skills = user.get("skills", [])
    projects = user.get("projects", [])
    experience = user.get("experience", [])

    prompt = f"""
You are a tag normalization assistant for a personalized contest recommendation system.

Your task:
Normalize the user's raw domains and skills into standardized tags.

Return ONLY valid JSON.
Do NOT include markdown.
Do NOT include explanation.

Use exactly this JSON format:

{{
  "domains": [],
  "skills": []
}}

Rules:
1. You MUST choose domains ONLY from ALLOWED_DOMAINS.
2. You MUST choose skills ONLY from ALLOWED_SKILLS.
3. Do NOT create new domain or skill names.
4. If a raw tag is too specific, map it to the closest allowed tag.
5. If a raw tag is irrelevant, non-technical, or too vague, remove it.
6. Keep only computer science / IT related tags.
7. domains should contain 1 to 5 items.
8. skills should contain 3 to 12 items if possible.
9. Remove duplicates.
10. Use exact capitalization from the allowed lists.

Mapping examples:
- Artificial Intelligence -> AI
- NLP, Natural Language Processing -> Natural Language Processing for domain, NLP for skill
- Data migration and conversion -> ETL
- Data partitioning and sharding strategies -> Database Administration
- Data warehousing concepts and implementation -> Data Warehousing
- Database scripting and automation -> SQL
- Data backup and disaster recovery planning -> Database Administration
- Machine Leaming -> Machine Learning
- Pytorch -> PyTorch
- React.js, React JS -> React
- RESTful, REST APIs -> REST API
- HTML5, HTML/HTML5 -> HTML
- CSS3 -> CSS
- T-SQL, PL/SQL, Oracle SQL -> SQL
- Postgres database -> PostgreSQL
- AWS Lambda -> AWS

ALLOWED_DOMAINS:
{json.dumps(ALLOWED_DOMAINS, ensure_ascii=False)}

ALLOWED_SKILLS:
{json.dumps(ALLOWED_SKILLS, ensure_ascii=False)}

User information:
user_id: {user_id}
name: {name}

Raw domains:
{json.dumps(raw_domains, ensure_ascii=False)}

Raw skills:
{json.dumps(raw_skills, ensure_ascii=False)}

Projects:
{json.dumps(projects, ensure_ascii=False)}

Experience:
{json.dumps(experience, ensure_ascii=False)}
"""
    return prompt


def validate_allowed(items, allowed_list):
    result = []

    allowed_lower_map = {
        allowed.lower(): allowed
        for allowed in allowed_list
    }

    for item in items:
        item = clean_text(item)
        key = item.lower()

        if key in allowed_lower_map:
            normalized = allowed_lower_map[key]

            if normalized not in result:
                result.append(normalized)

    return result


def build_search_text(domains, skills):
    return " ".join(domains + skills)


def normalize_user_with_llm(user):
    prompt = make_normalize_prompt(user)
    response = run_llm(prompt)
    parsed = extract_json_from_response(response)

    domains = validate_allowed(
        parsed.get("domains", []),
        ALLOWED_DOMAINS
    )

    skills = validate_allowed(
        parsed.get("skills", []),
        ALLOWED_SKILLS
    )

    normalized_user = user.copy()
    normalized_user["domains"] = domains
    normalized_user["skills"] = skills
    normalized_user["search_text"] = build_search_text(domains, skills)

    return normalized_user


def main():
    os.makedirs("json", exist_ok=True)

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        cv_data = json.load(f)

    normalized_results = []

    for idx, user in enumerate(cv_data, start=1):
        user_id = user.get("user_id", f"user_{idx:03d}")

        try:
            normalized_user = normalize_user_with_llm(user)
            normalized_results.append(normalized_user)

            print(
                f"[DONE] {user_id} | "
                f"domains={len(normalized_user['domains'])}, "
                f"skills={len(normalized_user['skills'])}"
            )

        except Exception as e:
            print(f"[ERROR] {user_id}")
            print(e)

            # 실패하면 원본 유지하되 search_text만 비워둠
            fallback_user = user.copy()
            fallback_user["domains"] = []
            fallback_user["skills"] = []
            fallback_user["search_text"] = ""

            normalized_results.append(fallback_user)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(normalized_results, f, indent=2, ensure_ascii=False)

    print(f"\n저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()