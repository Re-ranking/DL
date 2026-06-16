# train_randomforest.py
# pip install pandas scikit-learn joblib

import os
import json
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)


# =========================
# 1. 파일 경로 설정
# =========================

TRAIN_DATA_PATH = "json/personality_match.json"

MODEL_PATH = "result/team_recommend_randomforest.pkl"
FEATURE_IMPORTANCE_PATH = "result/feature_importance.json"


# =========================
# 2. JSON 데이터 로드
# =========================

def load_dataset(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    print(f"===== 학습 데이터 확인: {path} =====")
    print(df.head())
    print()
    print("전체 데이터 수:", len(df))
    print("컬럼 수:", len(df.columns))
    print()

    if "recommend_label" not in df.columns:
        raise ValueError("'recommend_label' 컬럼이 없습니다.")

    print("label 분포:")
    print(df["recommend_label"].value_counts())
    print()

    return df


# =========================
# 3. 학습 Feature 구성
# =========================

def prepare_features(df):
    target_col = "recommend_label"

    drop_cols = [
        "base_user_id",
        "candidate_user_id",
        "recommend_label",
        "rank"
    ]

    feature_cols = [
        col for col in df.columns
        if col not in drop_cols
        and pd.api.types.is_numeric_dtype(df[col])
    ]

    if len(feature_cols) == 0:
        raise ValueError("학습에 사용할 feature 컬럼이 없습니다.")

    X = df[feature_cols]
    y = df[target_col].astype(int)

    print("===== 학습 Feature 확인 =====")
    print("feature 개수:", len(feature_cols))
    print(feature_cols)
    print()

    return X, y, feature_cols


# =========================
# 4. 모델 학습
# =========================

def train_model(X, y):
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        random_state=42,
        class_weight="balanced"
    )

    model.fit(X_train, y_train)

    return model, X_train, X_test, y_train, y_test


# =========================
# 5. 모델 평가
# =========================

def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)

    print("===== 모델 평가 =====")
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print()

    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print()

    print("Classification Report:")
    print(classification_report(y_test, y_pred))


# =========================
# 6. Feature Importance 생성
# =========================

def get_feature_importance(model, feature_cols):
    importance_df = pd.DataFrame({
        "feature": feature_cols,
        "importance": model.feature_importances_
    }).sort_values(by="importance", ascending=False)

    print("===== Feature Importance Top-15 =====")
    print(importance_df.head(15))
    print()

    return importance_df


# =========================
# 7. 저장 함수
# =========================

def save_model(model, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    joblib.dump(model, path)

    print(f"[DONE] 모델 저장 완료: {path}")



def save_feature_importance(importance_df, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    result = importance_df.to_dict(orient="records")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"[DONE] Feature Importance 저장 완료: {path}")


# =========================
# 8. 실행
# =========================

def main():
    train_df = load_dataset(TRAIN_DATA_PATH)

    X, y, feature_cols = prepare_features(train_df)

    model, X_train, X_test, y_train, y_test = train_model(X, y)

    evaluate_model(model, X_test, y_test)

    importance_df = get_feature_importance(model, feature_cols)

    save_model(model, MODEL_PATH)

    save_feature_importance(importance_df, FEATURE_IMPORTANCE_PATH)

    print()
    print("[DONE] 학습 완료")


if __name__ == "__main__":
    main()