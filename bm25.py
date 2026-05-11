import json
import re
from rank_bm25 import BM25Okapi


# =============================
# 파일 경로
# =============================
CV_PATH = "json/cv_search_text.json"
CONTEST_PATH = "json/contest_search_text.json"
OUTPUT_PATH = "result_json/bm25_result.json"


# =============================
# 간단 토크나이저
# =============================
def tokenize(text):
    text = str(text).lower()
    tokens = re.findall(r"[a-zA-Z0-9가-힣+#.]+", text)
    return tokens


# =============================
# 메인 실행
# =============================
def main():
    with open(CV_PATH, "r", encoding="utf-8") as f:
        users = json.load(f)

    with open(CONTEST_PATH, "r", encoding="utf-8") as f:
        contests = json.load(f)

    contest_texts = [contest["search_text"] for contest in contests]
    tokenized_contests = [tokenize(text) for text in contest_texts]

    bm25 = BM25Okapi(tokenized_contests)

    results = []

    for user in users:
        user_id = user["user_id"]
        query = user["search_text"]
        tokenized_query = tokenize(query)

        scores = bm25.get_scores(tokenized_query)

        ranked = sorted(
            zip(contests, scores),
            key=lambda x: x[1],
            reverse=True
        )

        top_results = []

        for rank, (contest, score) in enumerate(ranked[:10], start=1):
            top_results.append({
                "rank": rank,
                "contest_id": contest["contest_id"],
                "bm25_score": float(score),
                "contest_search_text": contest["search_text"]
            })

        results.append({
            "user_id": user_id,
            "user_search_text": query,
            "recommendations": top_results
        })

        print(f"[DONE] {user_id}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()