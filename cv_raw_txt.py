# pip install pymupdf pytesseract pillow

import os
import re
import fitz  # PyMuPDF
import pytesseract
from PIL import Image

# 윈도우 로컬이면 필요
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

INPUT_DIR = "cv_dataset"
OUTPUT_PATH = "json/cv_result_raw.txt"

os.makedirs("json", exist_ok=True)


def split_sentences(text):
    """
    문장 단위 줄바꿈
    """

    text = text.replace("\r", " ")

    # 문장 끝마다 줄바꿈
    text = re.sub(r'([.!?])\s+', r'\1\n', text)

    # 여러 줄 정리
    text = re.sub(r'\n{2,}', '\n', text)

    return text.strip()


def extract_text_from_pdf(pdf_path):
    """
    1차: PDF 내장 텍스트 추출
    2차: 텍스트 거의 없으면 OCR
    """

    doc = fitz.open(pdf_path)

    full_text = ""

    for page_num, page in enumerate(doc, start=1):

        page_text = page.get_text().strip()

        # 텍스트 거의 없으면 OCR 수행
        if len(page_text) < 30:

            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

            img = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples
            )

            page_text = pytesseract.image_to_string(
                img,
                lang="eng",
                config="--psm 6"
            )

        page_text = split_sentences(page_text)

        full_text += f"\n\n===== PAGE {page_num} =====\n\n"
        full_text += page_text

    doc.close()

    return full_text.strip()


def main():

    results = []

    files = [
        f for f in os.listdir(INPUT_DIR)
        if f.lower().endswith(".pdf")
    ]

    print(f"총 {len(files)}개 PDF 처리 시작")

    for idx, filename in enumerate(files, start=1):

        pdf_path = os.path.join(INPUT_DIR, filename)

        try:

            extracted_text = extract_text_from_pdf(pdf_path)

            results.append({
                "file_name": filename,
                "text": extracted_text
            })

            print(f"[OK] {idx}/{len(files)} - {filename}")

        except Exception as e:

            print(f"[ERROR] {idx}/{len(files)} - {filename}")
            print(e)

    # TXT 저장
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:

        for item in results:

            f.write(f"FILE: {item['file_name']}\n\n")

            f.write(item["text"])

            f.write("\n\n")
            f.write("=" * 100)
            f.write("\n\n")

    print(f"\n저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()