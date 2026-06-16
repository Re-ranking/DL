# final_recommendation.py
# pip install pandas scikit-learn joblib

import os
import json
import pandas as pd
import joblib

import category_match


# =========================
# 1. 파일 경로 설정
# =========================

# 전체 사용자 성향 데이터
USER_PERSONALITY_PATH = "json/user_personality.json"

# 백엔드에서 받은 설문 JSON 테스트 파일
# 실제 API에서는 이 파일 대신 request body로 받은 dict를 넣으면 됨
BASE_SURVEY_PATH = "json/base_user.json"

# 생성된 모델 입력 feature 저장 경로
RECOMMEND_DATA_PATH = "json/personality_match_user_001.json"

# 학습된 모델
MODEL_PATH = "result/team_recommend_randomforest.pkl"

# 사용자 CV 데이터
CV_PATH = "../json/cv_result.json"

# 공모전 데이터
CONTEST_PATH = "../json/contest_normalize.json"

# 최종 추천 결과 저장 경로
RESULT_PATH = "result/final_team_recommendation.json"

TOP_K = 6

MODEL_WEIGHT = 0.5
CATEGORY_WEIGHT = 0.5

BASE_USER_ID = "user_001"
SELECTED_CONTEST_ID = 95


# =========================
# 2. 설문 JSON → user_personality 형식 변환 설정
# =========================

ANSWER_MAP = {
    "아니다": 0,
    "보통": 1,
    "그렇다": 2
}

PERSONALITY_FIELD_MAP = {
    "startInitiative": "personality_01",
    "completionTendency": "personality_02",
    "adaptability": "personality_03",
    "challengeOrientation": "personality_04",
    "consistency": "personality_05",
    "pressureHandling": "personality_06",
}


# 화면 선택지와 user_personality.json 선택지를 맞추는 정규화
VALUE_MAP = {
    "밤형": "새벽형",
    "주 2~3회": "주 2-3회",

    "기획형": "기획",
    "개발형": "개발",
    "디자인형": "디자인",
    "데이터/AI형": "데이터 / AI",
    "창업/비즈니스형": "창업 / 비즈니스",
    "발표 중심형": "발표 중심",

    "단기 집중형": "단기 집중",
    "중기형": "중기",
    "장기형": "장기",

    "문서로 정리된 피드백": "문서로 정리된 피드백 선호",
}


def normalize_value(value):
    if isinstance(value, list):
        return [normalize_value(v) for v in value]

    if isinstance(value, str):
        return VALUE_MAP.get(value, value)

    return value


def convert_submit_to_user_personality(api_response):
    """
    백엔드 /api/personality-surveys/submit 응답 JSON을
    내부 user_personality.json 형식으로 변환
    """

    data = api_response.get("data", api_response)

    member_id = data.get("memberId")
    user_id = f"user_{int(member_id):03d}" if member_id is not None else BASE_USER_ID

    personality = {}
    for api_key, internal_key in PERSONALITY_FIELD_MAP.items():
        answer = data.get("personality", {}).get(api_key)
        personality[internal_key] = ANSWER_MAP.get(answer, 1)

    user = {
        "user_id": user_id,
        "name": f"member_{member_id}" if member_id is not None else user_id,

        "personality": personality,

        "collaboration_style": {
            "collaboration_role": data.get("collaborationStyle", {}).get("rolePreference", []),
            "collaboration_work_style": data.get("collaborationStyle", {}).get("workStyle", ""),
            "collaboration_decision_style": data.get("collaborationStyle", {}).get("decisionStyle", ""),
            "collaboration_contribution": data.get("collaborationStyle", {}).get("contributionStyle", []),
            "collaboration_conflict_style": data.get("collaborationStyle", {}).get("conflictHandling", ""),
            "collaboration_preference_level": data.get("collaborationStyle", {}).get("cooperationLevel", ""),
        },

        "life_pattern": {
            "life_active_time": data.get("lifePattern", {}).get("activityTime", []),
            "life_available_time": data.get("lifePattern", {}).get("availableTime", []),
            "life_schedule_style": data.get("lifePattern", {}).get("scheduleManagementStyle", ""),
            "life_deadline_style": data.get("lifePattern", {}).get("deadlineHandlingStyle", ""),
            "life_meeting_frequency": data.get("lifePattern", {}).get("meetingFrequency", ""),
            "life_response_speed": data.get("lifePattern", {}).get("responseSpeed", ""),
        },

        "communication": {
            "communication_frequency": data.get("communication", {}).get("communicationFrequency", ""),
            "communication_channel": data.get("communication", {}).get("channelPreference", []),
            "communication_feedback_style": data.get("communication", {}).get("feedbackStyle", ""),
            "communication_expression_style": data.get("communication", {}).get("opinionExpressionStyle", ""),
            "communication_meeting_style": data.get("communication", {}).get("meetingStyle", []),
            "communication_conflict_method": data.get("communication", {}).get("conflictCommunicationStyle", ""),
        },

        "objective": {
            "objective_participation_goal": data.get("objective", {}).get("participationPurpose", []),
            "objective_goal_level": data.get("objective", {}).get("goalLevel", ""),
            "objective_commitment_level": data.get("objective", {}).get("commitmentLevel", ""),
            "objective_contest_type": data.get("objective", {}).get("preferredCompetitionType", []),
            "objective_project_duration": data.get("objective", {}).get("projectDurationPreference", ""),
            "objective_team_atmosphere": data.get("objective", {}).get("desiredTeamMood", ""),
        }
    }

    return user


# =========================
# 3. 기본 함수
# =========================

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[DONE] 저장 완료: {path}")


def load_model(path):
    model = joblib.load(path)

    print(f"[DONE] 모델 로드 완료: {path}")
    print()

    return model


def get_feature_columns_from_model(model):
    if not hasattr(model, "feature_names_in_"):
        raise ValueError(
            "모델 안에 feature_names_in_ 정보가 없습니다. "
            "학습할 때 pandas DataFrame으로 학습해야 합니다."
        )

    feature_cols = model.feature_names_in_.tolist()

    print("===== 모델 Feature Columns 확인 =====")
    print("feature 개수:", len(feature_cols))
    print(feature_cols)
    print()

    return feature_cols


def update_or_append_user(users, new_user):
    """
    같은 user_id가 있으면 교체, 없으면 추가
    """
    new_user_id = new_user["user_id"]

    for i, user in enumerate(users):
        if user.get("user_id") == new_user_id:
            users[i] = new_user
            return users

    users.append(new_user)
    return users


# =========================
# 4. user_personality → 비교 feature 생성
# =========================

def to_list(value):
    if value is None:
        return []

    if isinstance(value, list):
        return value

    if value == "":
        return []

    return [value]


def overlap_count(a, b):
    a_set = set(to_list(a))
    b_set = set(to_list(b))
    return len(a_set & b_set)


def has_overlap(a, b):
    return 1 if overlap_count(a, b) > 0 else 0


def is_same(a, b):
    return 1 if a == b else 0


def is_compatible(a, b):
    """
    현재는 같은 선택지를 compatible로 처리.
    더 정교하게 하고 싶으면 여기에서 궁합 규칙을 추가하면 됨.
    """
    return 1 if a == b else 0


def is_role_complementary(base_roles, candidate_roles):
    """
    후보가 base_user에게 없는 역할을 하나라도 가지고 있으면 보완 가능성 1.
    """
    base_set = set(to_list(base_roles))
    candidate_set = set(to_list(candidate_roles))

    if not candidate_set:
        return 0

    return 1 if len(candidate_set - base_set) > 0 else 0


def make_pair_features(base_user, candidate_user):
    base_personality = base_user.get("personality", {})
    cand_personality = candidate_user.get("personality", {})

    base_collab = base_user.get("collaboration_style", {})
    cand_collab = candidate_user.get("collaboration_style", {})

    base_life = base_user.get("life_pattern", {})
    cand_life = candidate_user.get("life_pattern", {})

    base_comm = base_user.get("communication", {})
    cand_comm = candidate_user.get("communication", {})

    base_obj = base_user.get("objective", {})
    cand_obj = candidate_user.get("objective", {})

    contribution_count = overlap_count(
        base_collab.get("collaboration_contribution", []),
        cand_collab.get("collaboration_contribution", [])
    )

    active_time_count = overlap_count(
        base_life.get("life_active_time", []),
        cand_life.get("life_active_time", [])
    )

    available_time_count = overlap_count(
        base_life.get("life_available_time", []),
        cand_life.get("life_available_time", [])
    )

    communication_channel_count = overlap_count(
        base_comm.get("communication_channel", []),
        cand_comm.get("communication_channel", [])
    )

    meeting_style_count = overlap_count(
        base_comm.get("communication_meeting_style", []),
        cand_comm.get("communication_meeting_style", [])
    )

    participation_goal_count = overlap_count(
        base_obj.get("objective_participation_goal", []),
        cand_obj.get("objective_participation_goal", [])
    )

    contest_type_count = overlap_count(
        base_obj.get("objective_contest_type", []),
        cand_obj.get("objective_contest_type", [])
    )

    features = {
        "base_user_id": base_user["user_id"],
        "candidate_user_id": candidate_user["user_id"],

        "personality_01_same": is_same(
            base_personality.get("personality_01"),
            cand_personality.get("personality_01")
        ),
        "personality_02_same": is_same(
            base_personality.get("personality_02"),
            cand_personality.get("personality_02")
        ),
        "personality_03_same": is_same(
            base_personality.get("personality_03"),
            cand_personality.get("personality_03")
        ),
        "personality_04_same": is_same(
            base_personality.get("personality_04"),
            cand_personality.get("personality_04")
        ),
        "personality_05_same": is_same(
            base_personality.get("personality_05"),
            cand_personality.get("personality_05")
        ),
        "personality_06_same": is_same(
            base_personality.get("personality_06"),
            cand_personality.get("personality_06")
        ),

        "role_complementary": is_role_complementary(
            base_collab.get("collaboration_role", []),
            cand_collab.get("collaboration_role", [])
        ),
        "role_overlap": has_overlap(
            base_collab.get("collaboration_role", []),
            cand_collab.get("collaboration_role", [])
        ),
        "work_style_compatible": is_compatible(
            base_collab.get("collaboration_work_style"),
            cand_collab.get("collaboration_work_style")
        ),
        "decision_style_compatible": is_compatible(
            base_collab.get("collaboration_decision_style"),
            cand_collab.get("collaboration_decision_style")
        ),
        "contribution_overlap": 1 if contribution_count > 0 else 0,
        "contribution_overlap_count": contribution_count,
        "conflict_style_same": is_same(
            base_collab.get("collaboration_conflict_style"),
            cand_collab.get("collaboration_conflict_style")
        ),
        "preference_level_compatible": is_compatible(
            base_collab.get("collaboration_preference_level"),
            cand_collab.get("collaboration_preference_level")
        ),

        "active_time_overlap": 1 if active_time_count > 0 else 0,
        "active_time_overlap_count": active_time_count,
        "available_time_overlap": 1 if available_time_count > 0 else 0,
        "available_time_overlap_count": available_time_count,
        "schedule_style_same": is_same(
            base_life.get("life_schedule_style"),
            cand_life.get("life_schedule_style")
        ),
        "deadline_style_same": is_same(
            base_life.get("life_deadline_style"),
            cand_life.get("life_deadline_style")
        ),
        "meeting_frequency_same": is_same(
            base_life.get("life_meeting_frequency"),
            cand_life.get("life_meeting_frequency")
        ),
        "response_speed_same": is_same(
            base_life.get("life_response_speed"),
            cand_life.get("life_response_speed")
        ),

        "communication_frequency_same": is_same(
            base_comm.get("communication_frequency"),
            cand_comm.get("communication_frequency")
        ),
        "communication_channel_overlap": 1 if communication_channel_count > 0 else 0,
        "communication_channel_overlap_count": communication_channel_count,
        "feedback_style_same": is_same(
            base_comm.get("communication_feedback_style"),
            cand_comm.get("communication_feedback_style")
        ),
        "expression_style_same": is_same(
            base_comm.get("communication_expression_style"),
            cand_comm.get("communication_expression_style")
        ),
        "meeting_style_overlap": 1 if meeting_style_count > 0 else 0,
        "meeting_style_overlap_count": meeting_style_count,
        "communication_conflict_same": is_same(
            base_comm.get("communication_conflict_method"),
            cand_comm.get("communication_conflict_method")
        ),

        "participation_goal_overlap": 1 if participation_goal_count > 0 else 0,
        "participation_goal_overlap_count": participation_goal_count,
        "goal_level_same": is_same(
            base_obj.get("objective_goal_level"),
            cand_obj.get("objective_goal_level")
        ),
        "commitment_level_same": is_same(
            base_obj.get("objective_commitment_level"),
            cand_obj.get("objective_commitment_level")
        ),
        "contest_type_overlap": 1 if contest_type_count > 0 else 0,
        "contest_type_overlap_count": contest_type_count,
        "project_duration_same": is_same(
            base_obj.get("objective_project_duration"),
            cand_obj.get("objective_project_duration")
        ),
        "team_atmosphere_same": is_same(
            base_obj.get("objective_team_atmosphere"),
            cand_obj.get("objective_team_atmosphere")
        ),
    }

    return features


def generate_personality_match_features(users, base_user_id):
    base_user = None

    for user in users:
        if user.get("user_id") == base_user_id:
            base_user = user
            break

    if base_user is None:
        raise ValueError(f"base_user_id를 찾을 수 없습니다: {base_user_id}")

    result = []

    for candidate_user in users:
        if candidate_user.get("user_id") == base_user_id:
            continue

        result.append(make_pair_features(base_user, candidate_user))

    print("===== personality match feature 생성 완료 =====")
    print("base_user_id:", base_user_id)
    print("후보 수:", len(result))
    print()

    return result


# =========================
# 5. 모델 기반 추천 점수 생성
# =========================

def make_model_recommendations(df, model, feature_cols):
    missing_cols = [col for col in feature_cols if col not in df.columns]

    if missing_cols:
        raise ValueError(f"추천 데이터셋에 없는 feature 컬럼: {missing_cols}")

    result = df.copy()

    X_all = result[feature_cols]

    result["recommend_probability"] = model.predict_proba(X_all)[:, 1]
    result["predicted_label"] = model.predict(X_all)

    required_cols = [
        "base_user_id",
        "candidate_user_id",
        "recommend_probability",
        "predicted_label"
    ]

    missing_required_cols = [
        col for col in required_cols
        if col not in result.columns
    ]

    if missing_required_cols:
        raise ValueError(f"모델 추천 결과에 필요한 컬럼이 없습니다: {missing_required_cols}")

    keep_cols = [
        "base_user_id",
        "candidate_user_id",
        "recommend_probability",
        "predicted_label"
    ]

    # 학습용 JSON이 들어온 경우만 유지
    if "recommend_label" in result.columns:
        keep_cols.append("recommend_label")

    model_result = result[keep_cols].copy()

    print("===== 모델 기반 추천 점수 생성 완료 =====")
    print(model_result.head())
    print()

    return model_result


# =========================
# 6. 카테고리 기반 추천 점수 생성
# =========================

def make_category_recommendations(users, contests, base_user_id, contest_id):
    base_user = category_match.find_user_by_id(users, base_user_id)
    contest = category_match.find_contest_by_id(contests, contest_id)

    category_match.TOP_K_TEAMMATES = len(users) - 1

    category_result = category_match.recommend_teammates_for_contest(
        base_user=base_user,
        users=users,
        contest=contest
    )

    category_df = pd.DataFrame(category_result)

    if category_df.empty:
        category_df = pd.DataFrame(
            columns=[
                "candidate_user_id",
                "candidate_name",
                "team_score",
                "score_detail",
                "covered_missing_domains",
                "covered_new_domains",
                "covered_missing_skills",
                "covered_new_skills",
                "candidate_domains",
                "candidate_skills"
            ]
        )

    if "team_score" in category_df.columns:
        category_df = category_df.rename(
            columns={"team_score": "category_team_score"}
        )

    keep_cols = [
        "candidate_user_id",
        "candidate_name",
        "category_team_score",
        "score_detail",
        "covered_missing_domains",
        "covered_new_domains",
        "covered_missing_skills",
        "covered_new_skills",
        "candidate_domains",
        "candidate_skills"
    ]

    keep_cols = [col for col in keep_cols if col in category_df.columns]

    category_df = category_df[keep_cols].copy()

    print("===== 카테고리 기반 추천 점수 생성 완료 =====")
    print(category_df.head())
    print()

    return category_df, base_user, contest


# =========================
# 7. 최종 추천 점수 계산
# =========================

def make_final_recommendations(
    model_df,
    category_df,
    base_user,
    contest,
    top_k=6
):
    merged = model_df.merge(
        category_df,
        on="candidate_user_id",
        how="left"
    )

    merged["category_team_score"] = merged["category_team_score"].fillna(0.0)
    merged["recommend_probability"] = merged["recommend_probability"].fillna(0.0)

    merged["final_score"] = (
        merged["recommend_probability"] * MODEL_WEIGHT
        + merged["category_team_score"] * CATEGORY_WEIGHT
    )

    merged = merged.sort_values(
        by="final_score",
        ascending=False
    ).reset_index(drop=True)

    if "rank" in merged.columns:
        merged = merged.drop(columns=["rank"])

    merged.insert(0, "rank", range(1, len(merged) + 1))

    top_result = merged.head(top_k).copy()

    final_recommendations = []

    for _, row in top_result.iterrows():
        item = {
            "rank": int(row["rank"]),
            "base_user_id": row["base_user_id"],
            "candidate_user_id": row["candidate_user_id"],

            "final_score": round(float(row["final_score"]), 4),
            "recommend_probability": round(float(row["recommend_probability"]), 4),
            "category_team_score": round(float(row["category_team_score"]), 4),

            "predicted_label": int(row["predicted_label"])
        }

        if "recommend_label" in row and pd.notna(row["recommend_label"]):
            item["recommend_label"] = int(row["recommend_label"])

        if "candidate_name" in row and pd.notna(row["candidate_name"]):
            item["candidate_name"] = row["candidate_name"]

        optional_cols = [
            "score_detail",
            "covered_missing_domains",
            "covered_new_domains",
            "covered_missing_skills",
            "covered_new_skills",
            "candidate_domains",
            "candidate_skills"
        ]

        for col in optional_cols:
            if col in row and row[col] is not None:
                value = row[col]

                if isinstance(value, float) and pd.isna(value):
                    continue

                item[col] = value

        final_recommendations.append(item)

    result = {
        "base_user_id": base_user["user_id"],
        "base_user_name": base_user.get("name", base_user["user_id"]),
        "base_user_domains": base_user.get("domains", []),
        "base_user_skills": base_user.get("skills", []),

        "contest_id": contest["contest_id"],
        "contest_title": contest["title"],
        "contest_domains": contest.get("domains", []),
        "contest_skills": contest.get("skills", []),

        "weight": {
            "model_weight": MODEL_WEIGHT,
            "category_weight": CATEGORY_WEIGHT
        },

        "recommended_teammates": final_recommendations
    }

    print(f"===== 최종 Top-{top_k} 추천 결과 =====")
    print(
        top_result[
            [
                "rank",
                "base_user_id",
                "candidate_user_id",
                "recommend_probability",
                "category_team_score",
                "final_score",
                "predicted_label"
            ]
        ]
    )
    print()

    return result


# =========================
# 8. 실행
# =========================

def main():
    # 1. 전체 성향 데이터 로드
    personality_users = load_json(USER_PERSONALITY_PATH)

    # 2. 백엔드 설문 JSON 로드 후 user_personality 형식으로 변환
    # 실제 API 연동 시에는 BASE_SURVEY_PATH 대신 request body dict를 넣으면 됨
    if os.path.exists(BASE_SURVEY_PATH):
        survey_json = load_json(BASE_SURVEY_PATH)
        base_user = convert_submit_to_user_personality(survey_json)

        global BASE_USER_ID
        BASE_USER_ID = base_user["user_id"]

        personality_users = update_or_append_user(personality_users, base_user)

        print("[DONE] 백엔드 설문 JSON → user_personality 형식 변환 완료")
        print("base_user_id:", BASE_USER_ID)
        print()

    else:
        print("[INFO] BASE_SURVEY_PATH가 없어 기존 user_personality.json 기준으로 실행합니다.")
        print("base_user_id:", BASE_USER_ID)
        print()

    # 3. base_user와 전체 후보 비교 feature 생성
    recommend_features = generate_personality_match_features(
        users=personality_users,
        base_user_id=BASE_USER_ID
    )

    # 확인용 저장
    save_json(recommend_features, RECOMMEND_DATA_PATH)

    recommend_df = pd.DataFrame(recommend_features)

    print(f"===== 모델 추천 입력 데이터 확인: {RECOMMEND_DATA_PATH} =====")
    print(recommend_df.head())
    print("전체 후보 수:", len(recommend_df))
    print()

    # 4. 모델 추천 점수
    model = load_model(MODEL_PATH)
    feature_cols = get_feature_columns_from_model(model)

    model_result_df = make_model_recommendations(
        df=recommend_df,
        model=model,
        feature_cols=feature_cols
    )

    # 5. 카테고리 추천 점수
    cv_users = load_json(CV_PATH)
    contests = load_json(CONTEST_PATH)

    category_result_df, base_cv_user, contest = make_category_recommendations(
        users=cv_users,
        contests=contests,
        base_user_id=BASE_USER_ID,
        contest_id=SELECTED_CONTEST_ID
    )

    # 6. 최종 추천 점수
    final_result = make_final_recommendations(
        model_df=model_result_df,
        category_df=category_result_df,
        base_user=base_cv_user,
        contest=contest,
        top_k=TOP_K
    )

    # 7. 저장
    save_json(final_result, RESULT_PATH)

    print("[DONE] 최종 팀원 추천 완료")


if __name__ == "__main__":
    main()