import sys
import shutil
import subprocess
import json
from pathlib import Path
from datetime import datetime

from typing import Optional
from fastapi import FastAPI, UploadFile, File, Body, HTTPException, Request
from fastapi.responses import JSONResponse


app = FastAPI()

# 현재 api.py 위치: CV_DESCRIPTION/api.py
BASE_DIR = Path(__file__).resolve().parent


# =========================
# 1. CV 기반 공모전 추천 경로
# =========================

CV_DIR = BASE_DIR / "cv_dataset_one"
ONTOLOGY_RESULT_PATH = BASE_DIR / "result_json" / "ontology_match_result.json"


# =========================
# 2. 성향 기반 팀원 추천 경로
# =========================

# personality 폴더
PERSONALITY_DIR = BASE_DIR / "personality"

# personality/json
PERSONALITY_DATA_DIR = PERSONALITY_DIR / "json"

# personality/result
PERSONALITY_RESULT_DIR = PERSONALITY_DIR / "result"

# 백엔드 설문 저장 경로
BASE_USER_SUBMIT_PATH = PERSONALITY_DATA_DIR / "base_user.json"

# 학습 데이터 누적 저장 경로
PERSONALITY_TRAIN_DATA_PATH = PERSONALITY_DATA_DIR / "personality_survey_data.json"

# final_recommendation.py 실행 결과 경로
PERSONALITY_RECOMMEND_RESULT_PATH = (
    PERSONALITY_RESULT_DIR / "final_team_recommendation.json"
)


@app.get("/health")
def health():
    return {"status": "ok"}


# =========================
# 3. CV 기반 공모전 추천 API
# =========================

@app.post("/recommend")
async def recommend(request: Request):
    """
    CV 파일을 받아 ontology_match.py 실행 후 공모전 추천 결과 반환.

    백엔드 multipart 전송 문제로 body가 비어 오는 경우,
    서버에 이미 존재하는 cv_dataset_one 안의 CV 파일을 fallback으로 사용한다.
    """

    content_type = request.headers.get("content-type", "")
    content_length = request.headers.get("content-length", "")

    raw_body = await request.body()

    print("===== /recommend called =====")
    print("content-type:", content_type)
    print("content-length:", content_length)
    print("raw body length:", len(raw_body))
    print("raw body head:", raw_body[:300])

    CV_DIR.mkdir(exist_ok=True)

    uploaded_file = None
    filename = "uploaded_cv.pdf"

    # =========================
    # 1. multipart form 파싱 시도
    # =========================
    try:
        form = await request.form()
        print("form keys:", list(form.keys()))

        for key, value in form.items():
            print("FORM KEY:", key, "TYPE:", type(value))

            if hasattr(value, "filename") and hasattr(value, "file"):
                uploaded_file = value
                filename = value.filename or "uploaded_cv.pdf"

                print("===== [RECOMMEND] multipart 파일 수신 =====")
                print("field name:", key)
                print("filename:", filename)
                print("content_type:", getattr(value, "content_type", None))
                break

    except Exception as e:
        print("[WARN] multipart form 파싱 실패:", e)

    # =========================
    # 2. 정상 UploadFile이 있으면 저장
    # =========================
    if uploaded_file is not None:
        # 새 파일이 정상적으로 들어온 경우에만 기존 파일 삭제
        for old_file in CV_DIR.iterdir():
            if old_file.is_file():
                old_file.unlink()

        file_path = CV_DIR / filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(uploaded_file.file, buffer)

        print("===== [RECOMMEND] 업로드 파일 저장 완료 =====")
        print("saved_path:", file_path)

    else:
        # =========================
        # 3. raw body에서 PDF 추출 시도
        # =========================
        if raw_body:
            pdf_start = raw_body.find(b"%PDF")

            if pdf_start != -1:
                pdf_bytes = raw_body[pdf_start:]

                boundary_pos = pdf_bytes.find(b"\r\n--")
                if boundary_pos != -1:
                    pdf_bytes = pdf_bytes[:boundary_pos]

                # raw body에서 PDF를 찾은 경우에만 기존 파일 삭제
                for old_file in CV_DIR.iterdir():
                    if old_file.is_file():
                        old_file.unlink()

                file_path = CV_DIR / filename

                with open(file_path, "wb") as f:
                    f.write(pdf_bytes)

                print("===== [RECOMMEND] raw body에서 PDF 추출 저장 =====")
                print("saved_path:", file_path)
                print("pdf_bytes:", len(pdf_bytes))

            else:
                print("[WARN] raw body는 있지만 PDF header를 찾지 못함")

        # =========================
        # 4. body가 비어 있으면 기존 CV 파일 fallback
        # =========================
        supported_exts = [".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".webp"]

        existing_files = [
            file for file in CV_DIR.iterdir()
            if file.is_file() and file.suffix.lower() in supported_exts
        ]

        if len(existing_files) == 0:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "백엔드에서 파일 body가 오지 않았고, 서버에 fallback CV 파일도 없습니다.",
                    "content_type": content_type,
                    "content_length": content_length,
                    "raw_body_length": len(raw_body)
                }
            )

        if len(existing_files) > 1:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "서버 cv_dataset_one 폴더에 CV 파일이 여러 개 있습니다. 하나만 남겨주세요.",
                    "files": [file.name for file in existing_files]
                }
            )

        print("===== [RECOMMEND] 업로드 파일 없음 → 기존 CV 파일 사용 =====")
        print("fallback_file:", existing_files[0])

    # =========================
    # 5. ontology_match.py 실행
    # =========================
    try:
        subprocess.run(
            [sys.executable, "ontology_match.py"],
            cwd=BASE_DIR,
            check=True
        )
    except subprocess.CalledProcessError as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "ontology_match.py 실행 중 오류 발생",
                "error": str(e)
            }
        )

    # =========================
    # 6. 결과 파일 반환
    # =========================
    if not ONTOLOGY_RESULT_PATH.exists():
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "공모전 추천 결과 파일을 찾을 수 없습니다.",
                "expected_path": str(ONTOLOGY_RESULT_PATH)
            }
        )

    with open(ONTOLOGY_RESULT_PATH, "r", encoding="utf-8") as f:
        result = json.load(f)

    return result


# =========================
# 5. 성향 기반 팀원 추천 API
# =========================

def run_personality_recommendation():
    """
    팀원 추천 실행 공통 함수

    실행 흐름:
    1. personality/llm_reason.py 실행
       - 내부에서 final_recommendation.py 실행
       - 추천 결과에 reason 추가
    2. personality/result/final_team_recommendation.json 반환
    """

    PERSONALITY_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PERSONALITY_RESULT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. llm_reason.py 실행
    try:
        run_result = subprocess.run(
            [sys.executable, "llm_reason.py"],
            cwd=str(PERSONALITY_DIR),
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        print("===== [PERSONALITY RECOMMEND] llm_reason.py 실행 완료 =====")
        print(run_result.stdout)

    except subprocess.CalledProcessError as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "llm_reason.py 실행 중 오류 발생",
                "stdout": e.stdout,
                "stderr": e.stderr,
                "cwd": str(PERSONALITY_DIR)
            }
        )

    # 2. 추천 결과 파일 확인
    if not PERSONALITY_RECOMMEND_RESULT_PATH.exists():
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "팀원 추천 결과 파일을 찾을 수 없습니다.",
                "expected_path": str(PERSONALITY_RECOMMEND_RESULT_PATH)
            }
        )

    # 3. 추천 결과 반환
    with open(PERSONALITY_RECOMMEND_RESULT_PATH, "r", encoding="utf-8") as f:
        result = json.load(f)

    return result


@app.get("/api/mypage/recommendations/team-members")
async def get_team_members():
    """
    백엔드가 팀원 추천 조회 시 호출할 수 있는 GET API.
    Swagger의 GET /api/mypage/recommendations/team-members 흐름에 대응.
    """
    return run_personality_recommendation()


@app.get("/personality/recommend")
async def get_personality_recommend():
    """
    백엔드가 ML 서버에 GET /personality/recommend로 호출하는 경우 대응.
    """
    return run_personality_recommendation()


@app.post("/personality/recommend")
async def post_personality_recommend(payload: Optional[dict] = Body(default=None)):
    """
    백엔드가 ML 서버에 POST /personality/recommend로 호출하는 경우 대응.

    body가 있으면 base_user.json을 갱신하고,
    body가 없으면 기존 base_user.json 기준으로 추천 실행.
    """

    PERSONALITY_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if payload is not None:
        survey_data = payload.get("data", payload)

        with open(BASE_USER_SUBMIT_PATH, "w", encoding="utf-8") as f:
            json.dump(survey_data, f, ensure_ascii=False, indent=2)

        print("===== [PERSONALITY RECOMMEND] 설문 JSON 저장 완료 =====")
        print("saved_path:", BASE_USER_SUBMIT_PATH)
    else:
        print("===== [PERSONALITY RECOMMEND] payload 없음 → 기존 base_user.json 사용 =====")

    return run_personality_recommendation()