import json
import re

# -----------------------------
# DOMAIN 수동 매핑
# -----------------------------
DOMAIN_MAPPING = {

    # ===== AI =====
    "Artificial Intelligence": "AI",

    "Machine Learning": "Machine Learning",
    "Deep Learning": "Deep Learning",

    "Data Science": "Data Science",
    "Data Analysis": "Data Analysis",
    "Analytics": "Analytics",
    "Business Analytics": "Analytics",
    "Customs Business Processes Management": "Business Intelligence",
    "Business Technology": "Business Intelligence",
    "Business Intelligence": "Business Intelligence",

    "Computer Vision": "Computer Vision",

    "Natural Language Processing":
        "Natural Language Processing",

    "NLP":
        "Natural Language Processing",

    "Big Data": "Big Data",

    # ===== Software =====
    "Software Development Life Cycle": "Software Development",
    "Software Engineering": "Software Development",
    "Software Development": "Software Development",
    "Java Development":"Software Development",
    "Software": "Software Development",

    # ===== Web =====
    "Web Applications":
        "Web Development",

    "Web Development":
        "Web Development",

    "Frontend Development":
        "Frontend Development",

    "Front-end Development":
        "Frontend Development",

    "Backend Development":
        "Backend Development",

    # ===== Mobile =====
    "Mobile App Development":
        "Mobile Development",

    # ===== Database =====
    "Database Development":
        "Database",

    "Database Engineering":
        "Database",

    "Database Management":
        "Database",

    "Database Administration": "Database Administration",

    "Data Management": "Data Engineering",
    "Data Warehousing":"Data Engineering",
    "data integrity":"Data Engineering",
    "Data Engineering":"Data Engineering",
    "Data Manegement":"Data Engineering",

    # ===== Cloud =====
    "Cloud Migration": "Cloud Computing",

    "Cloud Computing": "Cloud Computing",

    # ===== Infra =====
    "Information Technology":"IT Infrastructure",
    "IT Services":"IT Infrastructure",
    "Networking":"IT Infrastructure",
    "Network Infrastructure":"IT Infrastructure",

    # ===== Security =====
    "Network Security": "Cybersecurity",

    # ===== Enterprise =====
    "Enterprise Systems Engineering": "Enterprise Systems",

    # ===== Other =====
    "Game Development": "Game Development",

    "Blockchain":"Blockchain",

    "IoT": "IoT",

    "Healthcare": "Healthcare",
    "Customer Service": "Marketing",
    "Marketing": "Marketing",
    "Banking": "Finance",
    "Finance": "Finance",
    "Financial and Retailing": "Finance",
    "Wealth Management": "Finance",
    "Medical": "Healthcare",
    "Travel": "Travel",
    "E-commerce": "E-commerce"


}


# -----------------------------
# SKILL 수동 매핑
# -----------------------------
SKILL_MAPPING = {

    # ===== Programming Languages =====
    "Programming": "Python",
    "Python": "Python",
    "PYTHON": "Python",
    "Python 3": "Python",
    "R": "R",
    "R Studio": "R",
    "R Programming": "R",
    "Java": "Java",
    "CORE JAVA": "Java",
    "JavaScript": "JavaScript",
    "Javascript": "JavaScript",
    "TypeScript": "TypeScript",
    "C": "C",
    "c": "C",
    "C++": "C++",
    "C/C++": "C++",
    "C#": "C#",
    "Scala": "Scala",
    "PHP": "PHP",
    "Swift": "Swift",

    # ===== SQL / Database Query =====
    "SQL": "SQL",
    "SOL": "SQL",
    "Dynamic SOL": "SQL",
    "SQL Scripting": "SQL",
    "SQL DDL": "SQL",
    "T-SQL": "SQL",
    "T-SOL Development": "SQL",
    "PL/SQL": "SQL",
    "PL/SOL": "SQL",
    "SQL/PLSQL": "SQL",
    "Oracle SQL": "SQL",
    "Microsoft SQL": "SQL",
    "Microsoft SQL Server": "SQL Server",
    "Microsoft SQL Server Management Studio (SSMS)": "SQL Server",
    "SQL Server": "SQL Server",
    "MS SQL Server": "SQL Server",
    "Azure SQL": "SQL Server",

    # ===== AI / ML =====
    "Artificial Intelligence": "Machine Learning",
    "Machine Learning": "Machine Learning",
    "machine learning": "Machine Learning",
    "Machine Leaming": "Machine Learning",
    "ML Algorithms": "Machine Learning",
    "Machine Learning Algorithms": "Machine Learning",
    "machine learning algorithms": "Machine Learning",
    "Machine learning and AI": "Machine Learning",
    "Deep Learning": "Deep Learning",
    "deep reinforcement learning": "Deep Learning",

    "Predictive Analytics": "Predictive Modeling",
    "predictive analytics": "Predictive Modeling",
    "Predictive Modeling": "Predictive Modeling",
    "predictive modeling": "Predictive Modeling",
    "predictive models": "Predictive Modeling",
    "Predictive models": "Predictive Modeling",
    "Building predictive models": "Predictive Modeling",

    "Data Mining": "Data Mining",
    "data mining": "Data Mining",
    "Data Mining and Visualization Tools": "Data Mining",

    "Data Visualization": "Data Visualization",
    "data visualization": "Data Visualization",
    "Scientific Data Visualization": "Data Visualization",
    "Data Visualization: Excel, Google Sheets": "Data Visualization",

    "Natural Language Processing": "NLP",
    "natural language processing": "NLP",
    "NLP": "NLP",
    "natural language": "NLP",

    "Computer Vision": "Computer Vision",
    "image recognition model development": "Computer Vision",
    "Object Detection project": "Computer Vision",

    "Statistics": "Statistics",
    "STATISTICS": "Statistics",
    "statistical modeling": "Statistics",
    "Statistical Analysis Tools": "Statistics",
    "statistical analysis": "Statistics",

    "Logical, analytical thinker with great influencing skill": "Analytics",
    "Analyzing Skills": "Analytics",
    "Analytics": "Analytics",
    "advance analytics": "Analytics",
    "Decizion Analytics": "Analytics",

    # ===== AI Libraries =====
    "Pytorch": "PyTorch",
    "PyTorch": "PyTorch",
    "Tensorflow": "TensorFlow",
    "TensorFlow": "TensorFlow",
    "Scikit Learn": "Scikit-learn",
    "Scikit learn": "Scikit-learn",
    "scikit-learn": "Scikit-learn",
    "Scikit-learn": "Scikit-learn",
    "OpenCV": "OpenCV",
    "NumPy": "NumPy",
    "numpy": "NumPy",
    "Pandas": "Pandas",
    "Matplotlib": "Matplotlib",
    "MatPlotlib": "Matplotlib",
    "matplotlib": "Matplotlib",
    "SciPy": "SciPy",

    # ===== Big Data =====
    "Hadoop": "Hadoop",
    "HADOOP": "Hadoop",
    "Spark": "Spark",
    "Spark-MLlib": "Spark",
    "Map Reduce": "MapReduce",
    "MapReduce": "MapReduce",
    "Hive": "Hive",
    "HIVE": "Hive",
    "ETL": "ETL",
    "ETL processes": "ETL",
    "ETL process streamlining": "ETL",
    "Talend ETL": "ETL",

    "Data Warehousing": "Data Warehousing",
    "Data warehousing": "Data Warehousing",
    "Data warehousing concepts and implementation": "Data Warehousing",
    "Snowflake Data Warehouse": "Data Warehousing",
    "Comprehensive data warehouse solution": "Data Warehousing",

    # ===== Database =====
    "MySQL": "MySQL",
    "PostgreSQL": "PostgreSQL",
    "Postgres": "PostgreSQL",
    "Postgres database": "PostgreSQL",
    "PostgreSQL administration": "PostgreSQL",
    "MongoDB": "MongoDB",
    "MonboDB": "MongoDB",
    "SQLite": "SQLite",
    "Oracle": "Oracle",
    "Oracle Database": "Oracle",
    "Oracle 11g": "Oracle",
    "Oracle 9i/10g": "Oracle",

    "Database Design": "Database Design",
    "Database design": "Database Design",
    "Database architecture": "Database Design",
    "Database Architecture": "Database Design",
    "Data Modeling": "Database Design",
    "Data modeling": "Database Design",
    "Table design": "Database Design",
    "Designing database structures": "Database Design",
    "Database normalization": "Database Design",
    "Data partitioning models": "Database Design",
    "Data partitioning and sharding strategies": "Database Design",

    "Database Administration": "Database Administration",
    "DB administration": "Database Administration",
    "Database Troubleshooting": "Database Administration",
    "Data backup and disaster recovery planning": "Database Administration",
    "Database scripting and automation": "Database Administration",
    "Database scripting": "Database Administration",
    "Database automation": "Database Administration",
    "Database triggers": "Database Administration",
    "Database Triggers": "Database Administration",
    "backup and recovery": "Database Administration",

    "Query Optimization": "Query Optimization",
    "Query optimization": "Query Optimization",
    "SQL query tuning techniques": "Query Optimization",
    "Database Optimization": "Query Optimization",
    "SQL Server performance tuning": "Query Optimization",
    "Performance tuning": "Query Optimization",

    "Data Migration": "ETL",
    "data migration": "ETL",
    "Data migration": "ETL",
    "Data migration and conversion": "ETL",
    "Migration to SQL Server": "ETL",
    "legacy databases migration": "ETL",
    "legacy system migration to Oracle database": "ETL",

    # ===== Web / Frontend =====
    "React": "React",
    "React.js": "React",
    "React JS": "React",
    "ReactJS": "React",
    "React Native": "React Native",
    "Redux": "Redux",
    "Redux Toolkit": "Redux",
    "Angular": "Angular",
    "Angular.js": "Angular",

    "HTML": "HTML",
    "HTML5": "HTML",
    "HTML/HTML5": "HTML",
    "HTML/CSS": "HTML",

    "CSS": "CSS",
    "css": "CSS",
    "CSS3": "CSS",
    "CS8/CSS3": "CSS",

    "Bootstrap": "Bootstrap",
    "Tailwind": "Tailwind CSS",
    "Tailwind CSS": "Tailwind CSS",

    # ===== Backend =====
    "Spring": "Spring",
    "Struts / Spring": "Spring",
    "Spring Boot": "Spring Boot",
    "Django": "Django",
    "Flask": "Flask",
    "NodeJS": "Node.js",
    "Node.js": "Node.js",
    "Express": "Express.js",
    "Express.js": "Express.js",

    "REST API": "REST API",
    "REST APIs": "REST API",
    "RESTful": "REST API",
    "WebAPI": "REST API",
    "Server-side API": "REST API",
    "APIs, Server, Network Infrastructure": "REST API",
    "Network Security": "REST API",
    "GraphQL": "GraphQL",

    # ===== Cloud / DevOps =====
    "AWS": "AWS",
    "AWS Lambda": "AWS",
    "AWS (Redshift)": "AWS",
    "Docker": "Docker",
    "Kubernetes": "Kubernetes",
    "DevOps": "DevOps",
    "DevOps services": "DevOps",
    "Test Automation & DevOps": "DevOps",
    "Jenkins": "Jenkins",
    "Continuous Integration environment (Jenkins)": "Jenkins",
    "CI/CD": "CI/CD",
    "CI/CD support": "CI/CD",

    # ===== Engineering =====
    "Agile": "Agile",
    "Agile Development": "Agile",
    "Agile methodologies": "Agile",
    "Agile/Lean methodologies": "Agile",
    "Agile tools": "Agile",
    "Agile Programming": "Agile",
    "Business Process Mapping experience": "Agile",
    "Scrum": "Scrum",
    "Scrum master": "Scrum",
    "Scrum & Agile Methodologies": "Scrum",

    "Testing": "Testing",
    "testing": "Testing",
    "Manual Testing": "Testing",
    "Functional testing": "Testing",
    "Unit testing": "Testing",
    "Unit Test code": "Testing",
    "Test automation": "Testing",
    "Automated testing framework": "Testing",
    "Robot test framework": "Testing",

    "Performance Testing": "Performance Testing",
    "Performance testing": "Performance Testing",
    "Load testing": "Performance Testing",
    "Performance Improvement": "Performance Testing",

    # ===== Other Tools =====
    "Git": "Git",
    "GIT": "Git",
    "Git/GitHub": "Git",
    "Source Control": "Git",

    "Linux": "Linux",
    "UNIX/Linux Operating system": "Linux",

    "Blockchain": "Blockchain",
    "ArcGIS": "ArcGIS",
    "Unity": "Unity",
    "Unreal Engine": "Unreal Engine",
}


def normalize(text):
    return str(text).strip().lower()



def clean_domains(domain_list):

    result = []

    normalized_mapping = {
        normalize(k): v
        for k, v in DOMAIN_MAPPING.items()
    }

    for item in domain_list:

        key = normalize(item)

        if key in normalized_mapping:

            mapped = normalized_mapping[key]

            if mapped not in result:
                result.append(mapped)

    return result

def clean_skills(skill_list):

    result = []

    normalized_mapping = {
        normalize(k): v
        for k, v in SKILL_MAPPING.items()
    }

    for item in skill_list:

        key = normalize(item)

        if key in normalized_mapping:

            mapped = normalized_mapping[key]

            if mapped not in result:
                result.append(mapped)

    return result


# -----------------------------
# 파일 로드
# -----------------------------
INPUT_PATH = "json/cv_result.json"
OUTPUT_PATH = "json/cv_result_cleaned.json"

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)


# -----------------------------
# 전체 처리
# -----------------------------
for user in data:

    user["domains"] = clean_domains(
        user.get("domains", [])
    )

    user["skills"] = clean_skills(
        user.get("skills", [])
    )

    user["tags"] = ", ".join(
    user.get("domains", []) +
    user.get("skills", [])
)

    print(f"[DONE] {user.get('user_id')}")


# -----------------------------
# 저장
# -----------------------------
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("\n=== CLEANING FINISHED ===")
print(f"saved -> {OUTPUT_PATH}")