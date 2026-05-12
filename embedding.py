# pip install sentence-transformers scikit-learn

import json
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


CV_PATH = "json/cv_result.json"
CONTEST_PATH = "json/contest_normalize.json"
OUTPUT_PATH = "result_json/embedding_result.json"

TOP_K = 5


# -----------------------------
# 텍스트 정리
# -----------------------------
def clean_text(text):
    text = str(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


# -----------------------------
# JSON → 문자열 변환
# -----------------------------
def json_to_text(obj):

    return clean_text(
        json.dumps(obj, ensure_ascii=False)
    )


# -----------------------------
# JSON 로드
# -----------------------------
def load_json(path):

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# -----------------------------
# user_id 가져오기
# -----------------------------
def get_user_id(cv, idx):

    return (
        cv.get("user_id")
        or cv.get("id")
        or cv.get("name")
        or f"user_{idx}"
    )


# -----------------------------
# contest_id 가져오기
# -----------------------------
def get_contest_id(contest, idx):

    return (
        contest.get("contest_id")
        or contest.get("id")
        or contest.get("name")
        or f"contest_{idx}"
    )


# -----------------------------
# 메인
# -----------------------------
def main():

    cv_data = load_json(CV_PATH)
    contest_data = load_json(CONTEST_PATH)

    # dict 하나면 list로 변경
    if isinstance(cv_data, dict):
        cv_data = [cv_data]

    if isinstance(contest_data, dict):
        contest_data = [contest_data]

    # -----------------------------
    # 텍스트 생성
    # -----------------------------
    cv_texts = [
        json_to_text(cv)
        for cv in cv_data
    ]

    contest_texts = [
        json_to_text(contest)
        for contest in contest_data
    ]

    # -----------------------------
    # 임베딩 모델 로드
    # -----------------------------
    model = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    # -----------------------------
    # 임베딩 생성
    # -----------------------------
    cv_embeddings = model.encode(
        cv_texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    contest_embeddings = model.encode(
        contest_texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    # -----------------------------
    # 코사인 유사도 계산
    # -----------------------------
    similarity_matrix = cosine_similarity(
        cv_embeddings,
        contest_embeddings
    )

    results = []

    # -----------------------------
    # 사용자별 추천
    # -----------------------------
    for user_idx, scores in enumerate(similarity_matrix):

        cv = cv_data[user_idx]

        user_id = get_user_id(cv, user_idx)

        # 높은 점수 순 정렬
        top_indices = scores.argsort()[::-1][:TOP_K]

        top_contests = []

        for rank, contest_idx in enumerate(top_indices, start=1):

            contest = contest_data[contest_idx]

            top_contests.append({
                "rank": rank,
                "contest_id": get_contest_id(contest, contest_idx),
                "contest_name": contest.get("name", ""),
                "similarity_score": round(
                    float(scores[contest_idx]),
                    4
                ),
                "source_url": contest.get("source_url", "")
            })

        results.append({
            "user_id": user_id,
            "top_5_contests": top_contests
        })

        print(f"[DONE] {user_id}")

    # -----------------------------
    # 저장
    # -----------------------------
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:

        json.dump(
            results,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(f"\n저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()