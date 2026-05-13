# pip install sentence-transformers scikit-learn

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


# -----------------------------
# Embedding 모델 로드
# -----------------------------
model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


# -----------------------------
# 비교할 단어들
# -----------------------------
cv_terms = [
    "Python",
    "Machine Learning",
    "Computer Vision",
    "Data Analysis"
]

contest_terms = [
    "Artificial Intelligence",
    "Deep Learning",
    "Image Processing",
    "Big Data"
]


# -----------------------------
# 임베딩 생성
# -----------------------------
cv_embeddings = model.encode(
    cv_terms,
    convert_to_numpy=True,
    normalize_embeddings=True
)

contest_embeddings = model.encode(
    contest_terms,
    convert_to_numpy=True,
    normalize_embeddings=True
)


# -----------------------------
# 유사도 계산
# -----------------------------
similarity_matrix = cosine_similarity(
    cv_embeddings,
    contest_embeddings
)


# -----------------------------
# 결과 출력
# -----------------------------
results = []

for i, cv_term in enumerate(cv_terms):

    for j, contest_term in enumerate(contest_terms):

        score = float(similarity_matrix[i][j])

        results.append({
            "cv_term": cv_term,
            "contest_term": contest_term,
            "similarity": round(score, 4)
        })


# -----------------------------
# 높은 순 정렬
# -----------------------------
results = sorted(
    results,
    key=lambda x: x["similarity"],
    reverse=True
)


# -----------------------------
# 출력
# -----------------------------
print("\n===== TERM SIMILARITY =====\n")

for item in results:

    print(
        f"{item['cv_term']}  <->  "
        f"{item['contest_term']}  "
        f"=> similarity: {item['similarity']}"
    )