# llm_reason.py

import sys
import json
import subprocess
import requests
from pathlib import Path


# =========================
# 1. 경로 설정
# =========================

# 현재 파일 위치: CV_DESCRIPTION/personality/llm_reason.py
BASE_DIR = Path(__file__).resolve().parent

JSON_DIR = BASE_DIR / "json"
RESULT_DIR = BASE_DIR / "result"

# 백엔드에서 저장한 기준 사용자 설문 JSON
BASE_USER_SUBMIT_PATH = JSON_DIR / "base_user.json"

# final_recommendation.py 실행 결과
FINAL_RECOMMENDATION_PATH = RESULT_DIR / "final_team_recommendation.json"

# 실행할 추천 코드
FINAL_RECOMMENDATION_SCRIPT = BASE_DIR / "final_recommendation.py"


# =========================
# 2. LLM 설정
# =========================

OLLAMA_URL = "http://localhost:11434/api/generate"
LLM_MODEL_NAME = "llama3"


# =========================
# 3. JSON 유틸
# =========================

def load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# =========================
# 4. final_recommendation.py 실행
# =========================

def run_final_recommendation():
    """
    점수 기반 팀원 추천 코드 실행
    """

    if not FINAL_RECOMMENDATION_SCRIPT.exists():
        raise FileNotFoundError(
            f"final_recommendation.py를 찾을 수 없습니다: {FINAL_RECOMMENDATION_SCRIPT}"
        )

    print("===== [STEP 1] final_recommendation.py 실행 시작 =====")

    subprocess.run(
        [sys.executable, str(FINAL_RECOMMENDATION_SCRIPT)],
        cwd=BASE_DIR,
        check=True
    )

    print("===== [STEP 1 DONE] final_recommendation.py 실행 완료 =====")


# =========================
# 5. LLM 추천 이유 생성
# =========================

def clean_llm_reason(reason: str) -> str:
    """
    LLM이 붙이는 불필요한 도입 문구 제거
    """

    remove_prefixes = [
        "Based on the provided user information and candidate information,",
        "Based on the provided information,",
        "Based on the given information,",
        "Here's a possible explanation for why",
        "Here's a possible explanation:",
        "Here is a possible explanation:",
        "Possible explanation:",
        "추천 이유는 다음과 같습니다.",
        "추천 이유는 다음과 같아요.",
        "추천 이유는 다음과 같습니다:",
        "추천 이유:",
        "다음은 추천 이유입니다.",
        "다음은 추천 이유입니다:",
        "가능한 설명은 다음과 같습니다.",
        "가능한 설명은 다음과 같습니다:",
        "출력:"
    ]

    cleaned = reason.strip()

    # 여러 개의 도입 문구가 연속으로 붙는 경우 반복 제거
    changed = True
    while changed:
        changed = False

        for prefix in remove_prefixes:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
                cleaned = cleaned.lstrip(":：-–— \n\t\"'")
                changed = True

    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]

    bad_starts = (
        "based on",
        "here's",
        "here is",
        "possible explanation",
        "this candidate is suitable because",
        "추천 이유",
        "다음은",
        "가능한 설명"
    )

    while lines and lines[0].lower().startswith(bad_starts):
        lines.pop(0)

    cleaned = " ".join(lines).strip()
    cleaned = cleaned.lstrip(":：-–— \n\t\"'")

    return cleaned

def generate_recommend_reason(base_user: dict, candidate: dict) -> str:
    """
    기준 사용자와 추천 후보 정보를 바탕으로
    LLM이 추천 이유를 생성한다.
    """

    prompt = f"""
너는 팀 프로젝트 팀원 추천 시스템의 설명 생성기야.

아래 기준 사용자 정보와 추천 후보 정보를 바탕으로,
추천 후보가 왜 이 사용자에게 적합한 팀원인지 한국어로 2문장만 작성해.

반드시 지켜야 할 조건:
- 첫 문장부터 바로 추천 이유를 작성할 것
- "Based on", "Here's", "possible explanation", "추천 이유는", "다음은", "가능한 설명은" 같은 도입 문구를 절대 쓰지 말 것
- 후보 이름을 과하게 반복하지 말 것
- 점수 계산식, final_score, probability, predicted_label 같은 숫자나 필드명을 직접 언급하지 말 것
- 너무 과장하지 말 것
- 협업 성향, 역할 선호, 작업 방식, 생활 패턴, 목표, 보완 관계를 중심으로 설명할 것
- JSON 형식이 아니라 순수 문장만 출력할 것
- 출력은 반드시 한국어 문장 2개만 작성할 것

좋은 출력 예시:
협업 방식과 역할 선호가 기준 사용자와 잘 맞아 팀 프로젝트에서 자연스럽게 역할을 나누기 좋습니다. 작업 스타일과 목표 방향도 비슷해 일정 조율과 의사소통 과정에서 안정적인 협업이 기대됩니다.

나쁜 출력 예시:
Here's a possible explanation for why this candidate is suitable.
Based on the provided user information, this candidate is suitable.
추천 이유는 다음과 같습니다.

[기준 사용자 정보]
{json.dumps(base_user, ensure_ascii=False, indent=2)}

[추천 후보 정보]
{json.dumps(candidate, ensure_ascii=False, indent=2)}

출력:
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": LLM_MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3
                }
            },
            timeout=60
        )

        response.raise_for_status()
        result = response.json()

        reason = result.get("response", "").strip()

        if not reason:
            return make_fallback_reason(candidate)

        reason = clean_llm_reason(reason)

        return reason

    except Exception as e:
        print("[LLM REASON ERROR]", e)
        return make_fallback_reason(candidate)

def make_fallback_reason(candidate: dict) -> str:
    """
    LLM 호출 실패 시 기본 추천 이유 반환
    """

    candidate_user_id = candidate.get("candidate_user_id", "해당 후보")

    return (
        f"{candidate_user_id}는 기준 사용자와 성향 및 협업 방식이 비교적 잘 맞아 "
        "팀 프로젝트에서 함께하기 적합한 후보입니다. 역할 분담과 소통 방식 측면에서도 "
        "무난하게 협업할 가능성이 높습니다."
    )


# =========================
# 6. 추천 결과에 reason 추가
# =========================

def attach_reasons_to_candidates(base_user: dict, recommendation_result):
    """
    final_recommendation.py 결과에 reason 필드를 추가한다.
    result 구조가 list 또는 dict여도 동작하도록 처리한다.
    """

    # case 1: 결과 자체가 리스트인 경우
    if isinstance(recommendation_result, list):
        for candidate in recommendation_result:
            if isinstance(candidate, dict):
                candidate["reason"] = generate_recommend_reason(base_user, candidate)

        return recommendation_result

    # case 2: 결과가 dict인 경우
    if isinstance(recommendation_result, dict):

        possible_keys = [
            "recommendations",
            "data",
            "result",
            "final_recommendations",
            "team_recommendations",
            "recommended_teammates"
        ]

        for key in possible_keys:
            if key in recommendation_result and isinstance(recommendation_result[key], list):
                for candidate in recommendation_result[key]:
                    if isinstance(candidate, dict):
                        candidate["reason"] = generate_recommend_reason(base_user, candidate)

                return recommendation_result

        # 위 키들이 없을 때 dict 내부에서 첫 번째 list를 자동 탐색
        for key, value in recommendation_result.items():
            if isinstance(value, list):
                for candidate in value:
                    if isinstance(candidate, dict):
                        candidate["reason"] = generate_recommend_reason(base_user, candidate)

                return recommendation_result

    return recommendation_result


# =========================
# 7. main
# =========================

def main():
    print("===== [LLM REASON] 팀원 추천 + 추천 이유 생성 시작 =====")

    # 1. 기준 사용자 설문 JSON 읽기
    payload = load_json(BASE_USER_SUBMIT_PATH)

    # 백엔드 응답 구조가 { success, message, data } 형태이면 data만 사용
    base_user = payload.get("data", payload)

    # 2. final_recommendation.py 실행
    run_final_recommendation()

    # 3. 추천 결과 읽기
    recommendation_result = load_json(FINAL_RECOMMENDATION_PATH)

    # 4. LLM reason 추가
    result_with_reasons = attach_reasons_to_candidates(
        base_user=base_user,
        recommendation_result=recommendation_result
    )

    # 5. reason이 붙은 결과 다시 저장
    save_json(FINAL_RECOMMENDATION_PATH, result_with_reasons)

    print("===== [LLM REASON DONE] 추천 이유 추가 완료 =====")
    print(f"저장 경로: {FINAL_RECOMMENDATION_PATH}")


if __name__ == "__main__":
    main()