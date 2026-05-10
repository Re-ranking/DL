import re
import json
import requests
import fitz  # PyMuPDF
from PIL import Image
import pytesseract


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
def structure_cv_with_llm(text):
    prompt = """
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

{
  "name": "",
  "phone": [],
  "email": [],
  "skills": [],
  "projects": [],
  "experience": [],
  "domains": []
}

Extraction rules:
- name: full name
- phone: phone numbers
- email: email addresses
- skills: technical skills (e.g., Python, Machine Learning, Spark)
- projects: key project keywords or short phrases
- experience: job titles ONLY (no company, no dates)
- domains: infer the user's main professional/academic domains from skills, projects, and experience

Domain inference examples:
- Python, ML, PyTorch, TensorFlow, data analysis → AI, Machine Learning, Data Science
- SQL, database, ETL, dashboard, analytics → Data Analysis, Database
- React, Spring Boot, API, frontend, backend → Web Development, Backend, Frontend
- healthcare, medical, patient, diagnosis → Healthcare AI
- finance, stock, trading, risk → FinTech
- image, CNN, object detection, OCR → Computer Vision
- NLP, chatbot, text classification, LLM → Natural Language Processing

Important:
- skills, projects, and domains must NOT be empty
- if missing, infer from context
- keep responses concise
- domains should be broad categories, not sentences
- domains should contain 1 to 5 items

Output rules:
- Return ONLY valid JSON
- Do NOT include any explanation or text outside JSON
- Do NOT include markdown
- The JSON must be complete and syntactically correct
- The response must end with a closing curly brace }

CV_TEXT:
""" + text

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
    pdf_path = "0.pdf"

    raw_text = extract_text_from_pdf(pdf_path)
    cleaned_text = clean_ocr_text(raw_text)

    print("\n\n===== 전처리된 텍스트 =====")
    print(cleaned_text)

    llm_response = structure_cv_with_llm(cleaned_text)

    print("\n\n===== LLM 원본 응답 =====")
    print(llm_response)

    structured_json = extract_json_from_response(llm_response)

    print("\n\n===== 최종 구조화 JSON =====")
    print(json.dumps(structured_json, indent=2, ensure_ascii=False))

    with open("cv_result.json", "w", encoding="utf-8") as f:
        json.dump(structured_json, f, indent=2, ensure_ascii=False)

    print("\n저장 완료: cv_result.json")


if __name__ == "__main__":
    main()