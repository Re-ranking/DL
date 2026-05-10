import re
import json
import requests
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import os


# Tesseract 설치 경로
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# =========================
# 1. PDF 읽기 + OCR
# =========================
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    all_text = []

    for page_num, page in enumerate(doc, start=1):
        # 1차: 텍스트 PDF 읽기
        text = page.get_text("text").strip()

        # 2차: 텍스트가 없으면 OCR
        if not text:
            pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = pytesseract.image_to_string(img, lang="eng")

        print(f"\n===== {page_num}페이지 추출 결과 =====")
        print(text)

        all_text.append(text)

    doc.close()
    return "\n".join(all_text)


# =========================
# 2. 기본 전처리
# =========================
def clean_ocr_text(text):
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # OCR에서 자주 깨지는 문자 일부 보정
    text = text.replace(" KPls", " KPIs")
    text = text.replace("KPls", "KPIs")
    text = text.replace(" Al ", " AI ")
    text = text.replace("Healtheare", "Healthcare")
    text = text.replace("Engieering", "Engineering")
    text = text.replace("PRCNCIPAL", "PRINCIPAL")
    text = text.replace("2075", "2015")
    text = text.replace("2074", "2014")
    text = text.replace("2070", "2010")

    return text.strip()


# =========================
# 3. Ollama LLM 호출
# =========================
def run_llm(prompt):
    url = "http://localhost:11434/api/generate"

    payload = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    }

    res = requests.post(url, json=payload)
    res.raise_for_status()

    return res.json()["response"]


# =========================
# 4. LLM으로 CV 구조화
# =========================
def structure_cv_with_llm(text, user_id):
    prompt = f"""
You are a CV parsing assistant.

Extract ONLY the essential information from the following resume text.

Remove all unnecessary details:
- location
- dates
- long descriptions
- education

Return ONLY valid JSON.
Do NOT include explanations.
Do NOT include markdown.

Use exactly this format:

{{
  "user_id": "",
  "name": "",
  "phone": [],
  "email": [],
  "skills": [],
  "projects": [],
  "experience": [],
  "domains": []
}}

Extraction rules:
- user_id: keep exactly as provided
- name: full name
- phone: phone numbers
- email: email addresses
- skills: technical skills
- projects: key project keywords or short phrases
- experience: job titles ONLY
- domains: infer broad professional domains

Important:
- skills, projects, domains must NOT be empty
- keep responses concise
- domains should contain 1 to 5 items

User ID:
{user_id}

CV_TEXT:
{text}
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

    # 혹시 LLM이 앞뒤에 설명 붙였을 때 JSON 부분만 추출
    match = re.search(r"\{[\s\S]*\}", response)
    if match:
        return json.loads(match.group())

    raise ValueError("LLM 응답에서 JSON을 찾지 못했습니다.")


# =========================
# 6. 전체 실행
# =========================
def main():

    import os

    os.makedirs("json", exist_ok=True)

    cv_folder = "cv_dataset"

    pdf_files = [
        f for f in os.listdir(cv_folder)
        if f.endswith(".pdf")
    ]

    results = []

    for idx, pdf_file in enumerate(pdf_files):

        pdf_path = os.path.join(cv_folder, pdf_file)

        print(f"\n===== 처리 중: {pdf_file} =====")

        try:
            raw_text = extract_text_from_pdf(pdf_path)
            cleaned_text = clean_ocr_text(raw_text)

            user_id = f"user_{idx+1:03d}"

            llm_response = structure_cv_with_llm(
                cleaned_text,
                user_id
            )

            structured_json = extract_json_from_response(llm_response)

            results.append(structured_json)

            print(f"[DONE] {pdf_file}")

        except Exception as e:
            print(f"[ERROR] {pdf_file}")
            print(e)

    with open("json/cv_result.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n저장 완료: json/cv_result.json")


if __name__ == "__main__":
    main()