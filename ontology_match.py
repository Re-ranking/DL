import sys
import json
import os
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

CV_ONE_PATH = BASE_DIR / "cv" / "cv_one.py"
CV_DB_PATH = BASE_DIR / "json" / "cv_result.json"

CV_PATH = BASE_DIR / "json" / "cv_result_one.json"
CONTEST_PATH = BASE_DIR / "json" / "contest_normalize.json"
OUTPUT_PATH = BASE_DIR / "result_json" / "ontology_match_result.json"

TOP_K = 5


DOMAIN_PARENT = {
    "AI": "AI",
    "Computer Vision": "AI",
    "Natural Language Processing": "AI",
    "Data Science": "Data",

    "Web Development": "Software",
    "Backend Development": "Software",
    "Mobile Development": "Software",

    "Database": "Infrastructure",
    "Cloud Computing": "Infrastructure",
    "Cybersecurity": "Infrastructure",

    "Blockchain": "Emerging Tech",
    "IoT": "Emerging Tech",

    "Business": "Business",
    "Marketing": "Business",

    "Finance": "Financial",
    "Healthcare": "Healthcare",
    "E-commerce": "Commerce",

    "UX/UI": "Design",

    "Media": "Media",
    "Entertainment": "Media",

    "Environment": "Other",
    "Sports": "Other",
    "Education": "Other"
}


SKILL_PARENT = {
    "Python": "Programming Languages",
    "Java": "Programming Languages",
    "JavaScript": "Programming Languages",
    "TypeScript": "Programming Languages",
    "C": "Programming Languages",
    "C++": "Programming Languages",
    "C#": "Programming Languages",
    "Scala": "Programming Languages",
    "R": "Programming Languages",
    "PHP": "Programming Languages",
    "Swift": "Programming Languages",
    "SQL": "Programming Languages",

    "Machine Learning": "AI Skills",
    "Deep Learning": "AI Skills",
    "NLP": "AI Skills",
    "Computer Vision": "AI Skills",

    "Statistics": "Data Analysis Skills",
    "Data Visualization": "Data Analysis Skills",

    "PyTorch": "AI Libraries",
    "TensorFlow": "AI Libraries",
    "Scikit-learn": "AI Libraries",
    "OpenCV": "AI Libraries",
    "NumPy": "AI Libraries",
    "Pandas": "AI Libraries",
    "Matplotlib": "AI Libraries",
    "SciPy": "AI Libraries",

    "Hadoop": "Big Data Skills",
    "Spark": "Big Data Skills",
    "MapReduce": "Big Data Skills",
    "Hive": "Big Data Skills",
    "ETL": "Big Data Skills",
    "Data Warehousing": "Big Data Skills",

    "MySQL": "Database Skills",
    "PostgreSQL": "Database Skills",
    "MongoDB": "Database Skills",
    "SQLite": "Database Skills",
    "Oracle": "Database Skills",
    "SQL Server": "Database Skills",
    "Database Design": "Database Skills",
    "Database Administration": "Database Skills",
    "Query Optimization": "Database Skills",

    "React": "Frontend Skills",
    "React Native": "Frontend Skills",
    "Redux": "Frontend Skills",
    "Angular": "Frontend Skills",
    "HTML": "Frontend Skills",
    "CSS": "Frontend Skills",
    "Bootstrap": "Frontend Skills",
    "Tailwind CSS": "Frontend Skills",

    "Spring": "Backend Skills",
    "Spring Boot": "Backend Skills",
    "Django": "Backend Skills",
    "Flask": "Backend Skills",
    "Node.js": "Backend Skills",
    "Express.js": "Backend Skills",
    "REST API": "Backend Skills",
    "GraphQL": "Backend Skills",

    "AWS": "DevOps Skills",
    "Docker": "DevOps Skills",
    "Kubernetes": "DevOps Skills",
    "DevOps": "DevOps Skills",
    "Jenkins": "DevOps Skills",
    "CI/CD": "DevOps Skills",

    "Agile": "Engineering Skills",
    "Scrum": "Engineering Skills",
    "Testing": "Engineering Skills",
    "Performance Testing": "Engineering Skills",

    "Git": "Other Skills",
    "Linux": "Other Skills",
    "Blockchain": "Other Skills",
    "ArcGIS": "Other Skills",
    "Unity": "Other Skills",
    "Unreal Engine": "Other Skills"
}

def run_cv_one():
    print("\n===== [STEP 1] CV OCR + LLM 구조화 실행 =====")

    subprocess.run(
        [sys.executable, str(CV_ONE_PATH)],
        check=True,
        cwd=str(BASE_DIR)
    )

    print("===== [STEP 1 DONE] cv_result_one.json 생성 완료 =====\n")


def load_json_safe(path, default):
    if not path.exists():
        return default

    if path.stat().st_size == 0:
        return default

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_parent(value, mapping):
    return mapping.get(value, value)

def normalize_text(value):
    if value is None:
        return ""

    return str(value).strip().lower()


def make_person_key(cv):
    """
    중복 인물 판단 기준.
    1순위: user_id
    2순위: email
    3순위: name

    cv 구조에 email이 없으면 name 기준으로 중복 확인.
    """

    user_id = normalize_text(cv.get("user_id"))
    email = normalize_text(cv.get("email"))
    name = normalize_text(cv.get("name"))

    if user_id:
        return f"user_id:{user_id}"

    if email:
        return f"email:{email}"

    if name:
        return f"name:{name}"

    return None

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def update_cv_database(new_cvs):
    """
    새로 구조화된 CV 결과를 기존 cv_result.json에 추가.
    단, user_id/email/name 기준으로 이미 있으면 추가하지 않음.
    """

    existing_cvs = load_json_safe(CV_DB_PATH, [])

    if isinstance(existing_cvs, dict):
        existing_cvs = [existing_cvs]

    if isinstance(new_cvs, dict):
        new_cvs = [new_cvs]

    existing_keys = set()

    for cv in existing_cvs:
        key = make_person_key(cv)
        if key:
            existing_keys.add(key)

    added_count = 0
    skipped_count = 0

    for new_cv in new_cvs:
        new_key = make_person_key(new_cv)

        if new_key is None:
            print("[SKIP] user_id/name/email이 없어 중복 판단 불가")
            skipped_count += 1
            continue

        if new_key in existing_keys:
            print(f"[SKIP] 이미 존재하는 인물: {new_key}")
            skipped_count += 1
            continue

        existing_cvs.append(new_cv)
        existing_keys.add(new_key)
        added_count += 1

        print(f"[ADD] 새 인물 추가: {new_key}")

    os.makedirs(CV_DB_PATH.parent, exist_ok=True)

    with open(CV_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(existing_cvs, f, ensure_ascii=False, indent=2)

    print(f"\n===== CV DB 업데이트 완료 =====")
    print(f"추가: {added_count}명")
    print(f"중복/스킵: {skipped_count}명")
    print(f"저장 위치: {CV_DB_PATH}\n")

    return existing_cvs

def match_by_parent(cv_values, contest_values, mapping):
    """
    contest_values는 이미 대분류라고 가정.
    cv_values는 소분류일 수 있으므로 parent로 변환해서 contest 대분류와 비교.
    """

    matched = []

    for contest_value in contest_values:
        for cv_value in cv_values:
            cv_parent = get_parent(cv_value, mapping)

            is_exact_match = cv_value == contest_value
            is_parent_match = cv_parent == contest_value

            if is_exact_match or is_parent_match:
                matched.append({
                    "cv_value": cv_value,
                    "cv_parent": cv_parent,
                    "contest_value": contest_value,
                    "match_type": (
                        "exact"
                        if is_exact_match
                        else "child_of_contest"
                    )
                })

    unique = []
    seen = set()

    for item in matched:
        key = (
            item["cv_value"],
            item["contest_value"],
            item["match_type"]
        )

        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique


def score_match(contest_values, matched_items):
    if not contest_values:
        return 0.0

    matched_contest_values = {
        item["contest_value"]
        for item in matched_items
    }

    return len(matched_contest_values) / len(set(contest_values))


def match_score(cv, contest):
    cv_domains = cv.get("domains", [])
    cv_skills = cv.get("skills", [])

    contest_domains = contest.get("domains", [])
    contest_skills = contest.get("skills", [])

    matched_domains = match_by_parent(
        cv_domains,
        contest_domains,
        DOMAIN_PARENT
    )

    matched_skills = match_by_parent(
        cv_skills,
        contest_skills,
        SKILL_PARENT
    )

    domain_score = score_match(
        contest_domains,
        matched_domains
    )

    skill_score = score_match(
        contest_skills,
        matched_skills
    )

    final_score = domain_score * 0.4 + skill_score * 0.6

    return {
        "domain_score": round(domain_score, 4),
        "skill_score": round(skill_score, 4),
        "final_score": round(final_score, 4),
        "matched_domains": matched_domains,
        "matched_skills": matched_skills,
        "cv_domains": cv_domains,
        "cv_skills": cv_skills,
        "contest_domains": contest_domains,
        "contest_skills": contest_skills
    }


def main():
    os.makedirs(OUTPUT_PATH.parent, exist_ok=True)

    # 1. cv_one.py 먼저 실행
    run_cv_one()

    # 2. cv_one.py가 만든 cv_result_one.json 읽기
    new_cvs = load_json(CV_PATH)

    if isinstance(new_cvs, dict):
        new_cvs = [new_cvs]

    # 3. 기존 cv_result.json에 중복 없으면 추가
    update_cv_database(new_cvs)

    # 4. 추천은 방금 업로드한 CV 기준으로만 실행
    cvs = new_cvs

    contests = load_json(CONTEST_PATH)

    results = []

    for cv in cvs:
        recommendations = []

        for contest in contests:
            score_info = match_score(cv, contest)

            recommendations.append({
                "contest_id": contest.get("contest_id"),
                "title": contest.get("title"),
                **score_info
            })

        recommendations = sorted(
            recommendations,
            key=lambda x: x["final_score"],
            reverse=True
        )[:TOP_K]

        results.append({
            "user_id": cv.get("user_id"),
            "name": cv.get("name"),
            "recommendations": recommendations
        })

        print(f"[DONE] {cv.get('user_id')}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()