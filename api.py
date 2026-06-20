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
BASE_USER_SUBMIT_PATH = PERSONALITY_DATA_DIR / "base_user_submit.json"

# 학습 데이터 누적 저장 경로
PERSONALITY_TRAIN_DATA_PATH = PERSONALITY_DATA_DIR / "personality_survey_data.json"

# final_recommendation.py 실행 결과 경로
PERSONALITY_RECOMMEND_RESULT_PATH = (
    PERSONALITY_RESULT_DIR / "final_team_recommendation_user_001.json"
)


@app.get("/health")
def health():
    return {"status": "ok"}


# =========================
# 3. CV 기반 공모전 추천 API
# =========================

@app.post("/recommend")
async def recommend(file: UploadFile = File(...)):
    """
    CV 파일을 받아 ontology_match.py 실행 후
    공모전 추천 결과 반환
    """

    CV_DIR.mkdir(exist_ok=True)

    # 기존 단일 CV 파일 삭제
    for old_file in CV_DIR.iterdir():
        if old_file.is_file():
            old_file.unlink()

    file_path = CV_DIR / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

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

    return {
        "success": True,
        "message": "공모전 추천 성공",
        "data": result
    }


# =========================
# 4. 성향 설문 데이터 저장 API
# =========================

@app.post("/personality/train")
async def personality_train(payload: dict = Body(...)):
    """
    백엔드에서 성향 설문 데이터를 받아
    나중에 재학습용 데이터로 누적 저장하는 API

    저장 위치:
    CV_DESCRIPTION/personality/json/personality_survey_data.json
    """

    PERSONALITY_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 백엔드 응답 구조가 { success, message, data } 형태이면 data만 사용
    survey_data = payload.get("data", payload)

    saved_item = {
        "survey_id": survey_data.get("surveyId"),
        "member_id": survey_data.get("memberId"),
        "status": survey_data.get("status"),
        "dl_sync_status": survey_data.get("dlSyncStatus"),
        "current_step": survey_data.get("currentStep"),

        "personality": survey_data.get("personality", {}),
        "collaboration_style": survey_data.get("collaborationStyle", {}),
        "life_pattern": survey_data.get("lifePattern", {}),
        "communication": survey_data.get("communication", {}),
        "objective": survey_data.get("objective", {}),

        "submitted_at": survey_data.get("submittedAt"),
        "received_at": datetime.now().isoformat(timespec="seconds")
    }

    if PERSONALITY_TRAIN_DATA_PATH.exists():
        with open(PERSONALITY_TRAIN_DATA_PATH, "r", encoding="utf-8") as f:
            train_data = json.load(f)
    else:
        train_data = []

    train_data.append(saved_item)

    with open(PERSONALITY_TRAIN_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(train_data, f, ensure_ascii=False, indent=2)

    return {
        "success": True,
        "message": "personality survey data received",
        "saved_path": str(PERSONALITY_TRAIN_DATA_PATH),
        "data": saved_item
    }


# =========================
# 5. 성향 기반 팀원 추천 API
# =========================

@app.post("/recommend")
async def recommend(
    request: Request,
    file: Optional[UploadFile] = File(None),
    cv: Optional[UploadFile] = File(None),
    cvFile: Optional[UploadFile] = File(None),
    uploadFile: Optional[UploadFile] = File(None),
    multipartFile: Optional[UploadFile] = File(None),
    resume: Optional[UploadFile] = File(None),
):
    """
    CV 파일을 받아 ontology_match.py 실행 후
    공모전 추천 결과 반환

    백엔드 multipart field name이 file이 아닐 수도 있어서
    여러 이름을 허용한다.
    """

    # 1. 백엔드가 어떤 multipart key로 보내는지 로그 확인
    try:
        form = await request.form()
        print("===== /recommend form keys =====")
        print(list(form.keys()))
    except Exception as e:
        print("[WARN] form key 확인 실패:", e)

    # 2. 가능한 파일 필드명 중 하나 선택
    uploaded_file = file or cv or cvFile or uploadFile or multipartFile or resume

    if uploaded_file is None:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "CV 파일을 찾지 못했습니다.",
                "hint": "multipart field name이 file, cv, cvFile, uploadFile, multipartFile, resume 중 하나여야 합니다."
            }
        )

    print("===== [RECOMMEND] 업로드 파일 수신 =====")
    print("filename:", uploaded_file.filename)
    print("content_type:", uploaded_file.content_type)

    CV_DIR.mkdir(exist_ok=True)

    # 기존 단일 CV 파일 삭제
    for old_file in CV_DIR.iterdir():
        if old_file.is_file():
            old_file.unlink()

    # 파일명 없을 경우 대비
    original_filename = uploaded_file.filename or "uploaded_cv.pdf"
    file_path = CV_DIR / original_filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(uploaded_file.file, buffer)

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

    return {
        "success": True,
        "message": "공모전 추천 성공",
        "data": result
    }