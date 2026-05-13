# pip install sentence-transformers scikit-learn

import json
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


CV_PATH = "json/cv_result.json"
CONTEST_PATH = "json/contest_normalize.json"
OUTPUT_PATH = "result_json/embedding_result.json"

TOP_K = 5
TERM_TOP_N = 10


def clean_text(text):
    text = str(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def json_to_text(obj):
    return clean_text(json.dumps(obj, ensure_ascii=False))


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_user_id(cv, idx):
    return (
        cv.get("user_id")
        or cv.get("id")
        or cv.get("name")
        or f"user_{idx}"
    )


def get_contest_id(contest, idx):
    return (
        contest.get("contest_id")
        or contest.get("id")
        or f"contest_{idx}"
    )


def get_list_value(data, keys):
    result = []

    for key in keys:
        value = data.get(key)

        if isinstance(value, list):
            result.extend(value)

        elif isinstance(value, str) and value.strip():
            result.append(value)

    return result


def unique_terms(terms):
    result = []

    for term in terms:
        term = str(term).strip()

        if term and term not in result:
            result.append(term)

    return result


def analyze_term_similarity(model, cv, contest, top_n=10):
    cv_terms = []
    contest_terms = []

    cv_terms += get_list_value(cv, ["domains"])
    cv_terms += get_list_value(cv, ["skills"])
    cv_terms += get_list_value(cv, ["experience"])
    cv_terms += get_list_value(cv, ["projects"])

    contest_terms += get_list_value(contest, ["title"])
    contest_terms += get_list_value(contest, ["field"])
    contest_terms += get_list_value(contest, ["description"])
    

    cv_terms = unique_terms(cv_terms)
    contest_terms = unique_terms(contest_terms)

    if not cv_terms or not contest_terms:
        return []

    cv_term_embeddings = model.encode(
        cv_terms,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    contest_term_embeddings = model.encode(
        contest_terms,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    similarity_matrix = cosine_similarity(
        cv_term_embeddings,
        contest_term_embeddings
    )

    pairs = []

    for i, cv_term in enumerate(cv_terms):
        for j, contest_term in enumerate(contest_terms):
            pairs.append({
                "cv_term": cv_term,
                "contest_term": contest_term,
                "term_similarity": round(
                    float(similarity_matrix[i][j]),
                    4
                )
            })

    pairs = sorted(
        pairs,
        key=lambda x: x["term_similarity"],
        reverse=True
    )

    return pairs[:top_n]


def main():
    cv_data = load_json(CV_PATH)
    contest_data = load_json(CONTEST_PATH)

    if isinstance(cv_data, dict):
        cv_data = [cv_data]

    if isinstance(contest_data, dict):
        contest_data = [contest_data]

    cv_texts = [json_to_text(cv) for cv in cv_data]
    contest_texts = [json_to_text(contest) for contest in contest_data]

    model = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )

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

    similarity_matrix = cosine_similarity(
        cv_embeddings,
        contest_embeddings
    )

    results = []

    for user_idx, scores in enumerate(similarity_matrix):
        cv = cv_data[user_idx]
        user_id = get_user_id(cv, user_idx)

        top_indices = scores.argsort()[::-1][:TOP_K]

        top_contests = []

        for rank, contest_idx in enumerate(top_indices, start=1):
            contest = contest_data[contest_idx]

            top_contests.append({
                "rank": rank,
                "contest_id": get_contest_id(contest, contest_idx),
                "contest_name": contest.get("title", contest.get("name", "")),
                "similarity_score": round(float(scores[contest_idx]), 4),

                "term_similarity_analysis": analyze_term_similarity(
                    model,
                    cv,
                    contest,
                    top_n=TERM_TOP_N
                )
            })

        results.append({
            "user_id": user_id,
            "top_5_contests": top_contests
        })

        print(f"[DONE] {user_id}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()