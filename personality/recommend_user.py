# recommend_user.py
# pip install pandas scikit-learn joblib

import os
import json
import pandas as pd
import joblib


# =========================
# 1. 파일 경로 설정
# =========================

RECOMMEND_DATA_PATH = "json/personality_match_user_001.json"

MODEL_PATH = "result/team_recommend_randomforest.pkl"

RESULT_PATH = "result/team_recommendation_user_001.json"

TOP_K = 6


# =========================
# 2. 데이터 로드
# =========================

def load_dataset(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    print(f"===== 추천 데이터 확인: {path} =====")
    print(df.head())
    print()
    print("전체 후보 수:", len(df))
    print("컬럼 수:", len(df.columns))
    print()

    return df


def load_model(path):
    model = joblib.load(path)

    print(f"[DONE] 모델 로드 완료: {path}")
    print()

    return model


# =========================
# 3. 모델에서 Feature Column 가져오기
# =========================

def get_feature_columns_from_model(model):
    if not hasattr(model, "feature_names_in_"):
        raise ValueError(
            "모델 안에 feature_names_in_ 정보가 없습니다. "
            "학습할 때 반드시 pandas DataFrame으로 학습해야 합니다."
        )

    feature_cols = model.feature_names_in_.tolist()

    print("===== 모델 Feature Columns 확인 =====")
    print("feature 개수:", len(feature_cols))
    print(feature_cols)
    print()

    return feature_cols


# =========================
# 4. 추천 결과 생성
# =========================

def make_recommendations(df, model, feature_cols, top_k=6):
    missing_cols = [col for col in feature_cols if col not in df.columns]

    if missing_cols:
        raise ValueError(f"추천 데이터셋에 없는 feature 컬럼: {missing_cols}")

    X_all = df[feature_cols]

    result = df.copy()

    result["recommend_probability"] = model.predict_proba(X_all)[:, 1]
    result["predicted_label"] = model.predict(X_all)

    result = result.sort_values(
        by="recommend_probability",
        ascending=False
    ).reset_index(drop=True)

    if "rank" in result.columns:
        result = result.drop(columns=["rank"])

    result.insert(0, "rank", range(1, len(result) + 1))

    top_result = result.head(top_k).copy()

    print(f"===== Top-{top_k} 추천 결과 =====")

    display_cols = [
        "rank",
        "base_user_id",
        "candidate_user_id",
        "recommend_probability",
        "predicted_label",
        "recommend_label"
    ]

    display_cols = [col for col in display_cols if col in top_result.columns]

    print(top_result[display_cols])
    print()

    return top_result


# =========================
# 5. 추천 결과 저장
# =========================

def save_recommendation_json(result_df, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    output_cols = [
        "rank",
        "base_user_id",
        "candidate_user_id",
        "recommend_label",
        "recommend_probability",
        "predicted_label"
    ]

    missing_cols = [col for col in output_cols if col not in result_df.columns]

    if missing_cols:
        raise ValueError(f"저장할 결과에 없는 컬럼: {missing_cols}")

    result = result_df[output_cols].to_dict(orient="records")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"[DONE] 추천 결과 JSON 저장 완료: {path}")


# =========================
# 6. 실행
# =========================

def main():
    recommend_df = load_dataset(RECOMMEND_DATA_PATH)

    model = load_model(MODEL_PATH)

    feature_cols = get_feature_columns_from_model(model)

    recommendation_result = make_recommendations(
        df=recommend_df,
        model=model,
        feature_cols=feature_cols,
        top_k=TOP_K
    )

    save_recommendation_json(
        result_df=recommendation_result,
        path=RESULT_PATH
    )

    print()
    print("[DONE] 추천 결과 생성 완료")


if __name__ == "__main__":
    main()