# pip install rank_bm25

import json
import re
from rank_bm25 import BM25Okapi


CV_PATH = "json/cv_result.json"
CONTEST_PATH = "json/contest_normalize.json"
OUTPUT_PATH = "result_json/bm25_result.json"

TOP_K = 5


def clean_text(text):
    text = str(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def remove_id_fields(obj):
    """
    JSON 내부의 id 관련 필드 제거
    """

    if isinstance(obj, dict):

        filtered = {}

        for k, v in obj.items():

            if k.lower() == "id":
                continue

            if k.lower().endswith("_id"):
                continue

            filtered[k] = remove_id_fields(v)

        return filtered

    elif isinstance(obj, list):

        return [
            remove_id_fields(item)
            for item in obj
        ]

    return obj


def json_to_text(obj):
    """
    JSON 전체를 문자열로 변환
    id 계열 필드는 제외
    """

    cleaned_obj = remove_id_fields(obj)

    return clean_text(
        json.dumps(cleaned_obj, ensure_ascii=False)
    )


def tokenize(text):
    """
    영어/숫자/한글 단어 기준 토큰화
    """

    return re.findall(r"[a-zA-Z0-9가-힣]+", text.lower())


def load_json(path):

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():

    cv_data = load_json(CV_PATH)
    contest_data = load_json(CONTEST_PATH)

    if isinstance(cv_data, dict):
        cv_data = [cv_data]

    if isinstance(contest_data, dict):
        contest_data = [contest_data]

    contest_texts = [
        json_to_text(contest)
        for contest in contest_data
    ]

    tokenized_contests = [
        tokenize(text)
        for text in contest_texts
    ]

    bm25 = BM25Okapi(tokenized_contests)

    all_results = []

    for user_idx, user in enumerate(cv_data):

        user_text = json_to_text(user)
        user_tokens = tokenize(user_text)

        scores = bm25.get_scores(user_tokens)

        ranked = sorted(
            zip(contest_data, scores),
            key=lambda x: x[1],
            reverse=True
        )[:TOP_K]

        user_result = {
            "user_index": user_idx,
            "user_name": user.get("name", f"user_{user_idx}"),
            "recommendations": []
        }

        for rank, (contest, score) in enumerate(ranked, start=1):

            contest_tokens = tokenize(
                json_to_text(contest)
            )

            matched_tokens = list(
                set(user_tokens) & set(contest_tokens)
            )

            user_result["recommendations"].append({
                "rank": rank,
                "contest_id": contest.get("contest_id"),
                "title": contest.get("title"),
                "bm25_score": round(float(score), 4),
                "matched_tokens": matched_tokens
            })

        all_results.append(user_result)

        print(f"[DONE] user {user_idx} TOP {TOP_K} BM25 ranking complete")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:

        json.dump(
            all_results,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(f"\nSaved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()