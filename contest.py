import json
import re
import requests

# =============================
# 설정
# =============================
INPUT_PATH = "json/contests_result_ex.json"
OUTPUT_PATH = "json/contest_result_cleaned.json"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"

EXCLUDE_KEYWORDS = [
    "숏폼",
    "광고/마케팅"
]

ALLOWED_DOMAINS = [
    "AI",
    "Machine Learning",
    "Data Science",
    "Data Analysis",

    "Software Development",
    "Web Development",
    "Mobile Development",

    "Cloud Computing",
    "Cybersecurity",

    "Game Development",
    "Blockchain",
    "IoT",

    "Business Intelligence",
    "Analytics",

    "Enterprise Systems",

    "Healthcare",
    "Marketing",
    "Travel",
    "Finance",
    "E-commerce",
    "Startup",
    "Investment",
    "Business",
    "Entrepreneurship",
    "Service Planning",
    "Product Management",
    "Design",
    "Media",
    "Content Creation",
    "Education",
    "Environment",
    "Social Impact",
    "Research",
    "Logistics",
    "Entertainment"
]

ALLOWED_SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "C", "C++", "C#", "Scala", "R",
    "PHP", "Swift", "SQL",

    "Machine Learning", "Deep Learning", "Predictive Modeling", "Data Mining",
    "Data Visualization", "NLP", "Computer Vision", "Statistics", "Analytics",

    "PyTorch", "TensorFlow", "Scikit-learn", "OpenCV", "NumPy", "Pandas",
    "Matplotlib", "SciPy",

    "Hadoop", "Spark", "MapReduce", "Hive", "ETL", "Data Warehousing",

    "MySQL", "PostgreSQL", "MongoDB", "SQLite", "Oracle", "SQL Server",
    "Database Design", "Database Administration", "Query Optimization",

    "React", "React Native", "Redux", "Angular", "HTML", "CSS", "Bootstrap",
    "Tailwind CSS",

    "Spring", "Spring Boot", "Django", "Flask", "Node.js", "Express.js",
    "REST API", "GraphQL",

    "AWS", "Docker", "Kubernetes", "DevOps", "Jenkins", "CI/CD",

    "Agile", "Scrum", "Testing", "Performance Testing",

    "Git", "Linux", "Blockchain", "ArcGIS", "Unity", "Unreal Engine"
]


# =============================
# 유틸 함수
# =============================
def extract_json(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("JSON 형식을 찾지 못했습니다.")
    return json.loads(match.group())


def filter_allowed(values, allowed_list):
    if not isinstance(values, list):
        return []

    result = []
    for v in values:
        if v in allowed_list and v not in result:
            result.append(v)

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


def call_llm(contest):
    title = contest.get("name", "")
    field = contest.get("분야", "")
    target = contest.get("응모대상", "")
    organizer = contest.get("주최/주관", "")

    prompt = f"""
You are extracting structured tags for a contest recommendation system.

You must select domains and skills ONLY from the allowed lists.

Allowed domains:
{ALLOWED_DOMAINS}

Allowed skills:
{ALLOWED_SKILLS}

Contest information:
Title: {title}
Category: {field}
Target: {target}
Organizer: {organizer}

Rules:
1. domains must contain only values from Allowed domains.
2. skills must contain only values from Allowed skills.
3. Do not infer technical skills unless they are explicitly mentioned or strongly required.
4. If no clear skill is required, return an empty skills list.
5. Do not force Web Development just because the contest is from an IT category.
6. Domains must reflect the actual contest content, not only the source website category.
7. Do not invent new labels.
8. Return JSON only.
9. Do not include explanation.

Output format:
{{
  "domains": [],
  "skills": []
}}
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    response.raise_for_status()

    raw_text = response.json()["response"]
    parsed = extract_json(raw_text)

    domains = filter_allowed(parsed.get("domains", []), ALLOWED_DOMAINS)
    skills = filter_allowed(parsed.get("skills", []), ALLOWED_SKILLS)

    return domains, skills


# =============================
# 메인 실행
# =============================
def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        contests = json.load(f)

    result = []
    skipped_count = 0

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

            result.append(item)

            print(f"[DONE] {idx}/{len(contests)} - {item['title']}")
            print(f"       domains: {domains}")
            print(f"       skills : {skills}")

        except Exception as e:
            print(f"[ERROR] {idx}/{len(contests)} - {contest.get('name', '')}")
            print(e)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n저장 완료: {OUTPUT_PATH}")
    print(f"원본 개수: {len(contests)}")
    print(f"제거된 개수: {skipped_count}")
    print(f"저장된 개수: {len(result)}")


if __name__ == "__main__":
    main()