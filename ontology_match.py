import sys
import json
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

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
    
def extract_json_from_text(text):
    """
    OpenAI 응답에서 JSON만 안전하게 추출.
    혹시 ```json ... ``` 형태로 와도 처리.
    """
    text = text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("OpenAI 응답에서 JSON 객체를 찾을 수 없습니다.")

    return json.loads(text[start:end + 1])


def validate_strength_weakness_items(items):
    """
    strengths/weaknesses가 정확히 4개가 되도록 검증.
    OpenAI가 4개를 못 주면 부족한 만큼 '추가 분석 필요'로 채움.
    score는 0~100 정수로 제한.
    """
    result = []

    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue

            name = str(item.get("name", "")).strip()
            score = item.get("score", 50)

            if not name:
                continue

            try:
                score = int(score)
            except Exception:
                score = 50

            score = max(0, min(100, score))

            result.append({
                "name": name,
                "score": score
            })

    while len(result) < 4:
        result.append({
            "name": "추가 분석 필요",
            "score": 50
        })

    return result[:4]


def generate_strengths_weaknesses_with_openai(cv):
    """
    CV 구조화 결과를 바탕으로 strengths 4개, weaknesses 4개 생성.
    항목명은 고정하지 않고 OpenAI가 CV 내용을 보고 자유롭게 생성한다.
    """

    prompt = f"""
너는 이력서 분석 시스템의 역량 평가 모듈이다.

아래 CV 분석 JSON을 보고 지원자의 장점 strengths 4개와 보완점 weaknesses 4개를 생성해라.

조건:
1. 반드시 JSON만 반환해라.
2. strengths는 정확히 4개 생성해라.
3. weaknesses는 정확히 4개 생성해라.
4. 각 항목은 name, score를 가진다.
5. name은 한국어로 작성한다.
6. score는 0부터 100 사이의 정수다.
7. strengths는 지원자의 강점 역량을 의미한다.
8. weaknesses는 지원자가 상대적으로 보완하면 좋은 역량 영역을 의미한다.
9. strengths와 weaknesses의 항목명은 고정된 목록에서 고르지 말고, CV 내용을 보고 자유롭게 정해라.
10. 항목명은 너무 길지 않게 2~8단어 정도로 작성해라.
11. CV에 없는 내용을 과하게 지어내지 마라.
12. summary, skills, domains, projects, experience 정보를 근거로 판단해라.
13. 서비스 화면에 보여줄 수 있도록 너무 부정적이거나 공격적인 표현은 피하라.
14. weaknesses의 score도 현재 역량 점수로 해석한다. 즉 낮을수록 보완 필요성이 크다.

반환 형식:
{{
  "strengths": [
    {{
      "name": "데이터 분석 역량",
      "score": 92
    }},
    {{
      "name": "AI 모델 활용 능력",
      "score": 88
    }},
    {{
      "name": "백엔드 개발 경험",
      "score": 80
    }},
    {{
      "name": "문제 해결력",
      "score": 85
    }}
  ],
  "weaknesses": [
    {{
      "name": "발표 경험",
      "score": 45
    }},
    {{
      "name": "협업 리딩 경험",
      "score": 50
    }},
    {{
      "name": "서비스 운영 경험",
      "score": 48
    }},
    {{
      "name": "문서화 역량",
      "score": 55
    }}
  ]
}}

CV 분석 JSON:
{json.dumps(cv, ensure_ascii=False, indent=2)}
"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": "너는 CV 분석 결과를 바탕으로 strengths와 weaknesses를 JSON으로만 생성하는 평가 모듈이다."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.2
    )

    content = response.choices[0].message.content
    data = extract_json_from_text(content)

    strengths = validate_strength_weakness_items(data.get("strengths"))
    weaknesses = validate_strength_weakness_items(data.get("weaknesses"))

    return {
        "strengths": strengths,
        "weaknesses": weaknesses
    }

def enrich_cv_with_strengths_weaknesses(cv):
    """
    CV 하나에 strengths, weaknesses 추가.
    OpenAI 실패 시 기본값으로라도 응답이 깨지지 않게 처리.
    """
    try:
        result = generate_strengths_weaknesses_with_openai(cv)

        cv["strengths"] = result["strengths"]
        cv["weaknesses"] = result["weaknesses"]

        print(f"[OPENAI] strengths/weaknesses 생성 완료: {cv.get('name')}")

    except Exception as e:
        print(f"[OPENAI ERROR] strengths/weaknesses 생성 실패: {e}")

        cv["strengths"] = [
            {"name": "기술적 전문성", "score": 80},
            {"name": "문제 해결력", "score": 75},
            {"name": "학습 능력", "score": 70},
            {"name": "프로젝트 수행력", "score": 65}
        ]

        cv["weaknesses"] = [
            {"name": "커뮤니케이션", "score": 50},
            {"name": "협업 및 영향력", "score": 50},
            {"name": "발표", "score": 50},
            {"name": "문서화", "score": 50}
        ]

    return cv
    
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
    
    # 2-1. OpenAI로 strengths / weaknesses 추가
    new_cvs = [
        enrich_cv_with_strengths_weaknesses(cv)
        for cv in new_cvs
    ]

    # 2-2. 보강된 cv_result_one.json 다시 저장
    with open(CV_PATH, "w", encoding="utf-8") as f:
        json.dump(new_cvs, f, ensure_ascii=False, indent=2)

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
            "strengths": cv.get("strengths", []),
            "weaknesses": cv.get("weaknesses", []),
            "recommendations": recommendations
        })

        print(f"[DONE] {cv.get('user_id')}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()