import json
import os


CV_INPUT_PATH = "json/cv_result.json"
CONTEST_INPUT_PATH = "json/contest_normalize.json"

CV_OUTPUT_PATH = "bm25/cv_search_text.json"
CONTEST_OUTPUT_PATH = "bm25/contest_search_text.json"


DOMAIN_HIERARCHY = {
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

    "Marketing": "Business",
    "Finance": "Financial",
    "Healthcare": "Healthcare",
    "E-commerce": "Commerce",
    "UX/UI": "Design",
    "Entertainment": "Media",

    "Environment": "Other",
    "Sports": "Other",
    "Education": "Other"
}


SKILL_HIERARCHY = {
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


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_unique(result, value):
    if value and value not in result:
        result.append(value)


def expand_domains(domains):
    result = []

    for domain in domains:
        add_unique(result, domain)

        parent = DOMAIN_HIERARCHY.get(domain)
        if parent:
            add_unique(result, parent)

    return result


def expand_skills(skills):
    result = []

    for skill in skills:
        add_unique(result, skill)

        parent = SKILL_HIERARCHY.get(skill)
        if parent:
            add_unique(result, parent)

    return result


def build_search_text(item):

    values = set()

    domains = item.get("domains", [])
    skills = item.get("skills", [])
    projects = item.get("projects", [])
    experience = item.get("experience", [])

    expanded_domains = expand_domains(domains)
    expanded_skills = expand_skills(skills)

    for value in expanded_domains:
        values.add(value)

    for value in expanded_skills:
        values.add(value)

    for value in projects:
        values.add(value)

    for value in experience:
        values.add(value)

    return " ".join(sorted(values))


def make_cv_search_text(cv_data):
    result = []

    for user in cv_data:
        item = {
            "user_id": user.get("user_id"),
            "name": user.get("name", ""),
            "domains": user.get("domains", []),
            "skills": user.get("skills", []),
            "projects": user.get("projects", []),
            "experience": user.get("experience", []),
            "search_text": build_search_text(user)
        }

        result.append(item)

    return result


def make_contest_search_text(contest_data):
    result = []

    for contest in contest_data:
        item = {
            "contest_id": contest.get("contest_id"),
            "title": contest.get("title", ""),
            "domains": contest.get("domains", []),
            "skills": contest.get("skills", []),
            "search_text": build_search_text(contest)
        }

        result.append(item)

    return result


def main():
    cv_data = load_json(CV_INPUT_PATH)
    contest_data = load_json(CONTEST_INPUT_PATH)

    cv_result = make_cv_search_text(cv_data)
    contest_result = make_contest_search_text(contest_data)

    save_json(CV_OUTPUT_PATH, cv_result)
    save_json(CONTEST_OUTPUT_PATH, contest_result)

    print(f"CV 저장 완료: {CV_OUTPUT_PATH}")
    print(f"Contest 저장 완료: {CONTEST_OUTPUT_PATH}")


if __name__ == "__main__":
    main()