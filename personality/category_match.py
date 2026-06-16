import os
import json


# =========================
# 1. 파일 경로 설정
# =========================

CV_PATH = "../json/cv_result.json"
CONTEST_PATH = "../json/contest_normalize.json"
OUTPUT_PATH = "result/category_team_recommendation.json"

TOP_K_TEAMMATES = 6


# =========================
# 2. 소분류 -> 대분류 매핑
# =========================

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
    # Programming Languages
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

    # AI
    "Machine Learning": "AI",
    "Deep Learning": "AI",
    "NLP": "AI",
    "Computer Vision": "AI",

    # Data Analysis
    "Statistics": "Data Analysis",
    "Data Visualization": "Data Analysis",

    # AI Libraries
    "PyTorch": "AI Libraries",
    "TensorFlow": "AI Libraries",
    "Scikit-learn": "AI Libraries",
    "OpenCV": "AI Libraries",
    "NumPy": "AI Libraries",
    "Pandas": "AI Libraries",
    "Matplotlib": "AI Libraries",
    "SciPy": "AI Libraries",

    # Big Data
    "Hadoop": "Big Data",
    "Spark": "Big Data",
    "MapReduce": "Big Data",
    "Hive": "Big Data",
    "ETL": "Big Data",
    "Data Warehousing": "Big Data",

    # Database
    "MySQL": "Database",
    "PostgreSQL": "Database",
    "MongoDB": "Database",
    "SQLite": "Database",
    "Oracle": "Database",
    "SQL Server": "Database",
    "Database Design": "Database",
    "Database Administration": "Database",
    "Query Optimization": "Database",

    # Frontend
    "React": "Frontend",
    "React Native": "Frontend",
    "Redux": "Frontend",
    "Angular": "Frontend",
    "HTML": "Frontend",
    "CSS": "Frontend",
    "Bootstrap": "Frontend",
    "Tailwind CSS": "Frontend",

    # Backend
    "Spring": "Backend",
    "Spring Boot": "Backend",
    "Django": "Backend",
    "Flask": "Backend",
    "Node.js": "Backend",
    "Express.js": "Backend",
    "REST API": "Backend",
    "GraphQL": "Backend",

    # DevOps
    "AWS": "DevOps",
    "Docker": "DevOps",
    "Kubernetes": "DevOps",
    "DevOps": "DevOps",
    "Jenkins": "DevOps",
    "CI/CD": "DevOps",

    # Engineering
    "Agile": "Engineering",
    "Scrum": "Engineering",
    "Testing": "Engineering",
    "Performance Testing": "Engineering",

    # Other
    "Git": "Other",
    "Linux": "Other",
    "Blockchain": "Other",
    "ArcGIS": "Other",
    "Unity": "Other",
    "Unreal Engine": "Other"
}


# =========================
# 3. 기본 함수
# =========================

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def to_parent_set(values, parent_map):
    """
    소분류 리스트를 대분류 set으로 변환
    예:
    ["Python", "Java"] -> {"Programming Languages"}
    ["Machine Learning"] -> {"AI"}
    """
    result = set()

    for value in values:
        parent = parent_map.get(value)

        if parent:
            result.add(parent)

    return result


def make_reason(
    covered_missing_domains,
    covered_new_domains,
    covered_missing_skills,
    covered_new_skills
):
    reasons = []

    if covered_missing_domains:
        reasons.append(
            f"기준 사용자가 부족한 공모전 도메인 영역을 보완합니다: {', '.join(covered_missing_domains)}"
        )

    if covered_missing_skills:
        reasons.append(
            f"기준 사용자가 부족한 공모전 기술 영역을 보완합니다: {', '.join(covered_missing_skills)}"
        )

    if covered_new_domains:
        reasons.append(
            f"같은 공모전 도메인 범위 안에서 기준 사용자에게 없는 세부 도메인을 보유합니다: {', '.join(covered_new_domains)}"
        )

    if covered_new_skills:
        reasons.append(
            f"같은 공모전 기술 범위 안에서 기준 사용자에게 없는 세부 기술을 보유합니다: {', '.join(covered_new_skills)}"
        )

    return " ".join(reasons)


# =========================
# 4. 팀원 추천 핵심 로직
# =========================

def recommend_teammates_for_contest(base_user, users, contest):
    """
    base_user 기준으로 특정 contest에 대해 보완형 팀원 추천
    """

    # 공모전은 이미 대분류로 들어있음
    contest_domains = set(contest["domains"])
    contest_skills = set(contest["skills"])

    # 기준 사용자 소분류
    base_domains = set(base_user["domains"])
    base_skills = set(base_user["skills"])

    # 기준 사용자 소분류 -> 대분류 변환
    base_domain_parents = to_parent_set(base_domains, DOMAIN_PARENT)
    base_skill_parents = to_parent_set(base_skills, SKILL_PARENT)

    # 기준 사용자가 공모전 요구사항 중 아직 못 채운 대분류
    missing_domain_parents = contest_domains - base_domain_parents
    missing_skill_parents = contest_skills - base_skill_parents

    recommendations = []

    for candidate in users:
        if candidate["user_id"] == base_user["user_id"]:
            continue

        candidate_domains = set(candidate["domains"])
        candidate_skills = set(candidate["skills"])

        covered_missing_domains = []
        covered_new_domains = []

        covered_missing_skills = []
        covered_new_skills = []

        # =========================
        # Domain 보완 계산
        # =========================

        for domain in candidate_domains:
            parent = DOMAIN_PARENT.get(domain)

            # 후보자의 도메인이 공모전 요구 대분류 안에 없으면 제외
            if parent not in contest_domains:
                continue

            # 기준 사용자가 이미 가진 소분류면 제외
            if domain in base_domains:
                continue

            # 기준 사용자가 아예 못 채운 대분류를 후보자가 채우는 경우
            if parent in missing_domain_parents:
                covered_missing_domains.append(domain)

            # 기준 사용자가 이미 커버한 대분류 안에서 새로운 소분류를 가진 경우
            else:
                covered_new_domains.append(domain)

        # =========================
        # Skill 보완 계산
        # =========================

        for skill in candidate_skills:
            parent = SKILL_PARENT.get(skill)

            # 후보자의 스킬이 공모전 요구 대분류 안에 없으면 제외
            if parent not in contest_skills:
                continue

            # 기준 사용자가 이미 가진 소분류면 제외
            if skill in base_skills:
                continue

            # 기준 사용자가 아예 못 채운 대분류를 후보자가 채우는 경우
            if parent in missing_skill_parents:
                covered_missing_skills.append(skill)

            # 기준 사용자가 이미 커버한 대분류 안에서 새로운 소분류를 가진 경우
            else:
                covered_new_skills.append(skill)

        # 보완 역량이 하나도 없으면 추천 제외
        if not (
            covered_missing_domains
            or covered_new_domains
            or covered_missing_skills
            or covered_new_skills
        ):
            continue

        # =========================
        # 점수 계산
        # =========================

        # 1. 기준 사용자가 못 채운 대분류를 후보자가 몇 개 채우는지
        covered_missing_domain_parent_count = len({
            DOMAIN_PARENT.get(domain)
            for domain in covered_missing_domains
            if DOMAIN_PARENT.get(domain)
        })

        covered_missing_skill_parent_count = len({
            SKILL_PARENT.get(skill)
            for skill in covered_missing_skills
            if SKILL_PARENT.get(skill)
        })

        covered_missing_parent_count = (
            covered_missing_domain_parent_count
            + covered_missing_skill_parent_count
        )

        missing_parent_total = len(missing_domain_parents) + len(missing_skill_parents)

        if missing_parent_total > 0:
            missing_parent_score = covered_missing_parent_count / missing_parent_total
        else:
            missing_parent_score = 0

        # 2. 공모전 대분류 안에서 기준 사용자에게 없는 소분류를 몇 개 갖고 있는지
        new_child_count = (
            len(covered_missing_domains)
            + len(covered_new_domains)
            + len(covered_missing_skills)
            + len(covered_new_skills)
        )

        contest_parent_total = len(contest_domains) + len(contest_skills)

        if contest_parent_total > 0:
            new_child_score = new_child_count / contest_parent_total
        else:
            new_child_score = 0

        # 점수가 1을 넘지 않게 제한
        new_child_score = min(new_child_score, 1.0)

        # 3. 후보자와 기준 사용자의 역량이 덜 겹칠수록 보완성 높게 평가
        overlap_count = (
            len(base_domains & candidate_domains)
            + len(base_skills & candidate_skills)
        )

        candidate_total_count = len(candidate_domains) + len(candidate_skills)

        if candidate_total_count > 0:
            diversity_score = 1 - (overlap_count / candidate_total_count)
        else:
            diversity_score = 0

        # 최종 점수
        team_score = (
            missing_parent_score * 0.75
            + new_child_score * 0.15
            + diversity_score * 0.10
        )

        team_score = min(team_score, 1.0)

        recommendations.append({
            "candidate_user_id": candidate["user_id"],
            "candidate_name": candidate.get("name", candidate["user_id"]),

            "team_score": round(team_score, 4),

            "score_detail": {
                "missing_parent_score": round(missing_parent_score, 4),
                "new_child_score": round(new_child_score, 4),
                "diversity_score": round(diversity_score, 4)
            },

            "covered_missing_domains": covered_missing_domains,
            "covered_new_domains": covered_new_domains,
            "covered_missing_skills": covered_missing_skills,
            "covered_new_skills": covered_new_skills,

            "candidate_domains": list(candidate_domains),
            "candidate_skills": list(candidate_skills),
        })

    recommendations.sort(key=lambda x: x["team_score"], reverse=True)

    ranked_recommendations = []

    for rank, item in enumerate(recommendations[:TOP_K_TEAMMATES], start=1):
        ranked_item = {
            "rank": rank,
            "candidate_user_id": item["candidate_user_id"],
            "candidate_name": item["candidate_name"],
            "team_score": item["team_score"],
            "score_detail": item["score_detail"],
            "covered_missing_domains": item["covered_missing_domains"],
            "covered_new_domains": item["covered_new_domains"],
            "covered_missing_skills": item["covered_missing_skills"],
            "covered_new_skills": item["covered_new_skills"],
            "candidate_domains": item["candidate_domains"],
            "candidate_skills": item["candidate_skills"]
        }

        ranked_recommendations.append(ranked_item)

    return ranked_recommendations

def find_user_by_id(users, user_id):
    for user in users:
        if user["user_id"] == user_id:
            return user

    raise ValueError(f"해당 user_id를 찾을 수 없습니다: {user_id}")


def find_contest_by_id(contests, contest_id):
    for contest in contests:
        if int(contest["contest_id"]) == int(contest_id):
            return contest

    raise ValueError(f"해당 contest_id를 찾을 수 없습니다: {contest_id}")

# =========================
# 5. 전체 실행
# =========================

def main():
    users = load_json(CV_PATH)
    contests = load_json(CONTEST_PATH)

    # 테스트용으로 기준 사용자와 클릭한 공모전 지정
    BASE_USER_ID = "user_001"
    SELECTED_CONTEST_ID = 95

    base_user = find_user_by_id(users, BASE_USER_ID)
    contest = find_contest_by_id(contests, SELECTED_CONTEST_ID)

    recommended_teammates = recommend_teammates_for_contest(
        base_user=base_user,
        users=users,
        contest=contest
    )

    result = {
        "base_user_id": base_user["user_id"],
        "base_user_name": base_user.get("name", base_user["user_id"]),
        "base_user_domains": base_user["domains"],
        "base_user_skills": base_user["skills"],

        "contest_id": contest["contest_id"],
        "contest_title": contest["title"],
        "contest_domains": contest["domains"],
        "contest_skills": contest["skills"],

        "recommended_teammates": recommended_teammates
    }

    save_json(result, OUTPUT_PATH)

    print(f"[DONE] 선택 사용자/공모전 기준 팀원 추천 완료: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()