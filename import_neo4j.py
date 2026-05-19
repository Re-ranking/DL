import json
from neo4j import GraphDatabase


URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "anna1219"


CV_PATH = "json/cv_result.json"
CONTEST_PATH = "json/contest_normalize.json"


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


driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)


def clear_database(tx):
    tx.run("MATCH (n) DETACH DELETE n")


def insert_domain_hierarchy(tx):
    for child, parent in DOMAIN_HIERARCHY.items():
        tx.run("""
        MERGE (child:Domain {name: $child})
        MERGE (parent:DomainCategory {name: $parent})
        MERGE (child)-[:SUBDOMAIN_OF]->(parent)
        """, child=child, parent=parent)


def insert_skill_hierarchy(tx):
    for child, parent in SKILL_HIERARCHY.items():
        tx.run("""
        MERGE (child:Skill {name: $child})
        MERGE (parent:SkillCategory {name: $parent})
        MERGE (child)-[:SUBSKILL_OF]->(parent)
        """, child=child, parent=parent)


def insert_user(tx, user):
    tx.run("""
    MERGE (u:User {user_id: $user_id})
    SET u.name = $name
    """,
    user_id=user.get("user_id"),
    name=user.get("name", "")
    )

    for skill in user.get("skills", []):
        tx.run("""
        MERGE (u:User {user_id: $user_id})
        MERGE (s:Skill {name: $skill})
        MERGE (u)-[:HAS_SKILL]->(s)
        """,
        user_id=user.get("user_id"),
        skill=skill
        )

    for domain in user.get("domains", []):
        tx.run("""
        MERGE (u:User {user_id: $user_id})
        MERGE (d:Domain {name: $domain})
        MERGE (u)-[:HAS_DOMAIN]->(d)
        """,
        user_id=user.get("user_id"),
        domain=domain
        )


def insert_contest(tx, contest):
    tx.run("""
    MERGE (c:Contest {contest_id: $contest_id})
    SET c.title = $title
    """,
    contest_id=contest.get("contest_id"),
    title=contest.get("title", "")
    )

    for skill in contest.get("skills", []):
        tx.run("""
        MERGE (c:Contest {contest_id: $contest_id})
        MERGE (s:Skill {name: $skill})
        MERGE (c)-[:REQUIRES_SKILL]->(s)
        """,
        contest_id=contest.get("contest_id"),
        skill=skill
        )

    for domain in contest.get("domains", []):
        tx.run("""
        MERGE (c:Contest {contest_id: $contest_id})
        MERGE (d:Domain {name: $domain})
        MERGE (c)-[:BELONGS_TO_DOMAIN]->(d)
        """,
        contest_id=contest.get("contest_id"),
        domain=domain
        )


def main():
    with open(CV_PATH, "r", encoding="utf-8") as f:
        users = json.load(f)

    with open(CONTEST_PATH, "r", encoding="utf-8") as f:
        contests = json.load(f)

    with driver.session() as session:
        # 기존 데이터 싹 지우고 다시 넣고 싶으면 유지
        session.execute_write(clear_database)
        print("[DONE] Clear Database")

        session.execute_write(insert_domain_hierarchy)
        print("[DONE] Domain Hierarchy")

        session.execute_write(insert_skill_hierarchy)
        print("[DONE] Skill Hierarchy")

        for user in users:
            session.execute_write(insert_user, user)
            print(f"[USER DONE] {user.get('user_id')}")

        for contest in contests:
            session.execute_write(insert_contest, contest)
            print(f"[CONTEST DONE] {contest.get('contest_id')}")

    driver.close()
    print("\nNeo4j 저장 완료")


if __name__ == "__main__":
    main()