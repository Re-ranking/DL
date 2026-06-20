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
async def recommend(request: Request):
    """
    CV 파일을 받아 ontology_match.py 실행 후
    공모전 추천 결과 반환

    백엔드 multipart 전송 방식이 FastAPI UploadFile 검증과 안 맞을 수 있어서
    Request에서 form을 직접 파싱한다.
    """

    try:
        form = await request.form()
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "multipart/form-data 파싱 실패",
                "error": str(e),
                "content_type": request.headers.get("content-type")
            }
        )

    print("===== /recommend called =====")
    print("content-type:", request.headers.get("content-type"))
    print("form keys:", list(form.keys()))

    uploaded_file = None
    uploaded_key = None

    # form 안에서 파일 객체를 자동 탐색
    for key, value in form.items():
        print("FORM KEY:", key, "TYPE:", type(value))

        if hasattr(value, "filename") and hasattr(value, "file"):
            uploaded_file = value
            uploaded_key = key
            break

    if uploaded_file is None:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "업로드 파일을 찾지 못했습니다.",
                "received_keys": list(form.keys()),
                "content_type": request.headers.get("content-type")
            }
        )

    print("===== [RECOMMEND] 업로드 파일 수신 =====")
    print("field name:", uploaded_key)
    print("filename:", uploaded_file.filename)
    print("content_type:", uploaded_file.content_type)

    CV_DIR.mkdir(exist_ok=True)

    # 기존 단일 CV 파일 삭제
    for old_file in CV_DIR.iterdir():
        if old_file.is_file():
            old_file.unlink()

    filename = uploaded_file.filename or "uploaded_cv.pdf"
    file_path = CV_DIR / filename

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

@app.post("/personality/recommend")
async def personality_recommend(payload: dict = Body(...)):
    """
    백엔드에서 성향 설문 최종 제출 JSON을 받아
    팀원 추천 결과를 반환하는 API

    실행 흐름:
    1. payload를 personality/json/base_user_submit.json으로 저장
    2. personality/llm_reason.py 실행
       - 내부에서 final_recommendation.py 실행
       - 추천 결과에 reason 추가
    3. personality/result/final_team_recommendation_user_001.json 반환
    """

    PERSONALITY_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PERSONALITY_RESULT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. 백엔드 설문 JSON 저장
    with open(BASE_USER_SUBMIT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print("===== [PERSONALITY RECOMMEND] 설문 JSON 저장 완료 =====")
    print(BASE_USER_SUBMIT_PATH)

    # 2. llm_reason.py 실행
    try:
        subprocess.run(
            [sys.executable, "llm_reason.py"],
            cwd=PERSONALITY_DIR,
            check=True
        )
    except subprocess.CalledProcessError as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "llm_reason.py 실행 중 오류 발생",
                "error": str(e),
                "cwd": str(PERSONALITY_DIR)
            }
        )

    # 3. 추천 결과 파일 확인
    if not PERSONALITY_RECOMMEND_RESULT_PATH.exists():
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "팀원 추천 결과 파일을 찾을 수 없습니다.",
                "expected_path": str(PERSONALITY_RECOMMEND_RESULT_PATH)
            }
        )

    # 4. 추천 결과 반환
    with open(PERSONALITY_RECOMMEND_RESULT_PATH, "r", encoding="utf-8") as f:
        result = json.load(f)

    return {
        "success": True,
        "message": "팀원 추천 성공",
        "data": result
    }