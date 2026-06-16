import sys
from fastapi import FastAPI, UploadFile, File, Body
import shutil
import subprocess
import json
from pathlib import Path
from datetime import datetime

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent

# =========================
# CV 추천 관련 경로
# =========================

CV_DIR = BASE_DIR / "cv_dataset_one"
RESULT_PATH = BASE_DIR / "result_json" / "ontology_match_result.json"


# =========================
# 성향 추천 관련 경로
# =========================

PERSONALITY_DATA_DIR = BASE_DIR / "json"

# 학습 데이터 저장용
PERSONALITY_TRAIN_DATA_PATH = PERSONALITY_DATA_DIR / "personality_survey_data.json"

# final_recommendation.py가 읽을 백엔드 설문 JSON
BASE_USER_SUBMIT_PATH = PERSONALITY_DATA_DIR / "base_user_submit.json"

# final_recommendation.py 실행 후 결과
PERSONALITY_RECOMMEND_RESULT_PATH = (
    BASE_DIR / "result" / "final_team_recommendation_user_001.json"
)


@app.get("/health")
def health():
    return {"status": "ok"}


# =========================
# 1. CV 기반 공모전 추천
# =========================

@app.post("/recommend")
async def recommend(file: UploadFile = File(...)):
    CV_DIR.mkdir(exist_ok=True)

    for old_file in CV_DIR.iterdir():
        if old_file.is_file():
            old_file.unlink()

    file_path = CV_DIR / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    subprocess.run(
        [sys.executable, "ontology_match.py"],
        cwd=BASE_DIR,
        check=True
    )

    with open(RESULT_PATH, "r", encoding="utf-8") as f:
        result = json.load(f)

    return result


# =========================
# 2. 성향 설문 데이터 저장용
# =========================

@app.post("/personality/train")
async def personality_train(payload: dict = Body(...)):
    """
    백엔드에서 성향 설문 데이터를 받아
    나중에 모델 재학습용 데이터로 누적 저장하는 API
    """

    PERSONALITY_DATA_DIR.mkdir(exist_ok=True)

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
# 3. 성향 기반 팀원 추천
# =========================

@app.post("/personality/recommend")
async def personality_recommend(payload: dict = Body(...)):
    """
    백엔드에서 성향 설문 최종 제출 JSON을 받아
    팀원 추천 결과를 반환하는 API

    실행 흐름:
    1. payload를 json/base_user_submit.json으로 저장
    2. final_recommendation.py 실행
    3. result/final_team_recommendation_user_001.json 반환
    """

    PERSONALITY_DATA_DIR.mkdir(exist_ok=True)

    # 1. 백엔드에서 받은 설문 JSON 저장
    with open(BASE_USER_SUBMIT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print("===== [PERSONALITY RECOMMEND] 설문 JSON 저장 완료 =====")
    print(BASE_USER_SUBMIT_PATH)

    # 2. final_recommendation.py 실행
    subprocess.run(
        [sys.executable, "final_recommendation.py"],
        cwd=BASE_DIR,
        check=True
    )

    # 3. 추천 결과 파일 확인
    if not PERSONALITY_RECOMMEND_RESULT_PATH.exists():
        return {
            "success": False,
            "message": "팀원 추천 결과 파일을 찾을 수 없습니다.",
            "expected_path": str(PERSONALITY_RECOMMEND_RESULT_PATH)
        }

    with open(PERSONALITY_RECOMMEND_RESULT_PATH, "r", encoding="utf-8") as f:
        result = json.load(f)

    return {
        "success": True,
        "message": "팀원 추천 성공",
        "data": result
    }