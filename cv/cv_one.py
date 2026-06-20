# cv 단일 데이터 대상

import re
import json
import requests
import os
import platform
import shutil
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import pytesseract


# =========================
# Tesseract 경로 설정
# =========================
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    pytesseract.pytesseract.tesseract_cmd = shutil.which("tesseract") or "/usr/bin/tesseract"

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

    "Machine Learning",
    "Deep Learning",
    "NLP",
    "Computer Vision",

    "Statistics",
    "Data Visualization",

    "PyTorch",
    "TensorFlow",
    "Scikit-learn",
    "OpenCV",
    "NumPy",
    "Pandas",
    "Matplotlib",
    "SciPy",

    "Hadoop",
    "Spark",
    "MapReduce",
    "Hive",
    "ETL",
    "Data Warehousing",

    "MySQL",
    "PostgreSQL",
    "MongoDB",
    "SQLite",
    "Oracle",
    "SQL Server",
    "Database Design",
    "Database Administration",
    "Query Optimization",

    "React",
    "React Native",
    "Redux",
    "Angular",
    "HTML",
    "CSS",
    "Bootstrap",
    "Tailwind CSS",

    "Spring",
    "Spring Boot",
    "Django",
    "Flask",
    "Node.js",
    "Express.js",
    "REST API",
    "GraphQL",

    "AWS",
    "Docker",
    "Kubernetes",
    "DevOps",
    "Jenkins",
    "CI/CD",

    "Agile",
    "Scrum",
    "Testing",
    "Performance Testing",

    "Git",
    "Linux",
    "Blockchain",
    "ArcGIS",
    "Unity",
    "Unreal Engine"
]

# =========================
# 2. PDF / 이미지 OCR
# =========================
def clean_ocr_text(text):
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def ocr_image(image_path):
    image = Image.open(image_path)

    text = pytesseract.image_to_string(
        image,
        lang="eng"
    )

    return clean_ocr_text(text)


def ocr_pdf(pdf_path):
    doc = fitz.open(pdf_path)

    all_text = []

    for page_idx in range(len(doc)):
        page = doc[page_idx]

        pix = page.get_pixmap(dpi=300)

        temp_image_path = f"_temp_page_{page_idx + 1}.png"
        pix.save(temp_image_path)

        try:
            page_text = ocr_image(temp_image_path)
            all_text.append(page_text)

        finally:
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)

    doc.close()

    return clean_ocr_text("\n\n".join(all_text))


def extract_text_from_file(file_path):
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {file_path}")

    ext = file_path.suffix.lower()

    if ext == ".pdf":
        print("[OCR] PDF 파일 OCR 처리 중...")
        return ocr_pdf(file_path)

    elif ext in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
        print("[OCR] 이미지 파일 OCR 처리 중...")
        return ocr_image(file_path)

    else:
        raise ValueError(
            "지원하지 않는 파일 형식입니다. PDF, JPG, JPEG, PNG, BMP, WEBP만 가능합니다."
        )



# =========================
# 3. Ollama LLM 호출
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
# 4. LLM으로 CV 구조화
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
# 5. JSON 파싱 보정
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
# 6. 후처리
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

def get_single_cv_file(input_dir):
    supported_exts = [".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".webp"]

    input_dir = Path(input_dir)

    if not input_dir.exists():
        raise FileNotFoundError(f"입력 폴더를 찾을 수 없습니다: {input_dir}")

    cv_files = [
        file for file in input_dir.iterdir()
        if file.is_file() and file.suffix.lower() in supported_exts
    ]

    if len(cv_files) == 0:
        raise FileNotFoundError(
            "cv_dataset 폴더 안에 PDF 또는 이미지 CV 파일이 없습니다."
        )

    if len(cv_files) > 1:
        raise ValueError(
            f"cv_dataset 폴더 안에 CV 파일이 {len(cv_files)}개 있습니다. CV 한 개만 넣어주세요."
        )

    return cv_files[0]


# =========================
# 7. 단일 CV 실행
# =========================
def main():
    BASE_DIR = Path(__file__).resolve().parent.parent

    INPUT_DIR = BASE_DIR / "cv_dataset_one"
    OUTPUT_PATH = BASE_DIR / "json" / "cv_result_one.json"

    os.makedirs(OUTPUT_PATH.parent, exist_ok=True)

    user_id = "user_001"

    try:
        file_path = get_single_cv_file(INPUT_DIR)

        print(f"===== 단일 CV 처리 중: {file_path.name} =====")

        cv_text = extract_text_from_file(file_path)

        if len(cv_text) < 50:
            raise ValueError("OCR로 추출된 CV 텍스트가 너무 짧습니다.")

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

        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(
                final_json,
                f,
                indent=2,
                ensure_ascii=False
            )

        print(f"[DONE] {user_id}")
        print(f"저장 완료: {OUTPUT_PATH}")

    except Exception as e:
        print("[ERROR]")
        print(e)
        raise

if __name__ == "__main__":
    main()