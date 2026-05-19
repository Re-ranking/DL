import json
import os


CV_PATH = "json/cv_result.json"
CONTEST_PATH = "json/contest_normalize.json"
OUTPUT_PATH = "result_json/ontology_match_result.json"

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


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_parent(value, mapping):
    return mapping.get(value, value)


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
    os.makedirs("result_json", exist_ok=True)

    cvs = load_json(CV_PATH)
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