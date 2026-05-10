import json
from difflib import SequenceMatcher


# -----------------------------
# 공통 정규화
# -----------------------------
def normalize(text):
    return str(text).lower().strip()


def normalize_list(value):
    if not value:
        return []

    if isinstance(value, list):
        return [normalize(v) for v in value if str(v).strip()]

    return [normalize(value)]


# -----------------------------
# 문자열 유사도
# -----------------------------
def text_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


# -----------------------------
# 태그 리스트 매칭 점수
# -----------------------------
def tag_match_score(user_tags, contest_tags, threshold=0.75):
    user_tags = normalize_list(user_tags)
    contest_tags = normalize_list(contest_tags)

    if not user_tags or not contest_tags:
        return 0.0

    matched = 0

    for c_tag in contest_tags:
        for u_tag in user_tags:
            if c_tag == u_tag or text_similarity(c_tag, u_tag) >= threshold:
                matched += 1
                break

    return matched / len(contest_tags)


# -----------------------------
# 1차 후보 필터링용 태그 점수
# -----------------------------
def preliminary_tag_score(user, contest):
    user_all_tags = (
        normalize_list(user.get("skills", [])) +
        normalize_list(user.get("domains", []))
    )

    contest_all_tags = (
        normalize_list(contest.get("all_skills", contest.get("skills", []))) +
        normalize_list(contest.get("domains", contest.get("domain", []))) +
        normalize_list(contest.get("target_major", []))
    )

    if not user_all_tags or not contest_all_tags:
        return 0.0

    matched = 0

    for c_tag in contest_all_tags:
        for u_tag in user_all_tags:
            if c_tag == u_tag or text_similarity(c_tag, u_tag) >= 0.75:
                matched += 1
                break

    return matched / len(contest_all_tags)


# -----------------------------
# 공모전 하나에 대한 최종 점수 계산
# -----------------------------
def calculate_score(user, contest):
    user_skills = user.get("skills", [])
    user_domains = user.get("domains", [])

    contest_skills = contest.get("all_skills", contest.get("skills", []))
    contest_domains = contest.get("domains", contest.get("domain", []))
    target_major = contest.get("target_major", [])

    skill_score = tag_match_score(user_skills, contest_skills)
    domain_score = tag_match_score(user_domains, contest_domains)
    major_score = tag_match_score(user_domains, target_major)

    final_score = (
        skill_score * 0.45 +
        domain_score * 0.35 +
        major_score * 0.20
    )

    return {
        "skill_score": round(skill_score, 4),
        "domain_score": round(domain_score, 4),
        "major_score": round(major_score, 4),
        "final_score": round(final_score, 4)
    }


# -----------------------------
# 전체 reranking
# -----------------------------
def rerank_contests(user_tags_path, contest_tags_path, output_path):
    with open(user_tags_path, "r", encoding="utf-8") as f:
        user_data = json.load(f)

    with open(contest_tags_path, "r", encoding="utf-8") as f:
        contest_data = json.load(f)

    if isinstance(user_data, list):
        user = user_data[0]
    else:
        user = user_data

    # -----------------------------
    # 1차: 태그 기반 후보 30개 추출
    # -----------------------------
    first_candidates = []

    for contest in contest_data:
        pre_score = preliminary_tag_score(user, contest)

        if pre_score > 0:
            first_candidates.append({
                **contest,
                "preliminary_score": round(pre_score, 4)
            })

    first_candidates.sort(
        key=lambda x: x["preliminary_score"],
        reverse=True
    )

    top_30_candidates = first_candidates[:30]

    # -----------------------------
    # 2차: 후보 30개 정밀 점수 계산
    # -----------------------------
    scored_results = []

    for contest in top_30_candidates:
        scores = calculate_score(user, contest)

        result = {
            **contest,
            **scores
        }

        scored_results.append(result)

    scored_results.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    # -----------------------------
    # 최종 5개만 저장
    # -----------------------------
    final_top_5 = scored_results[:5]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_top_5, f, ensure_ascii=False, indent=2)

    return final_top_5


# -----------------------------
# 실행
# -----------------------------
if __name__ == "__main__":
    results = rerank_contests(
        "user_tags.json",
        "contest_tags.json",
        "reranked_result.json"
    )

    print("=== 최종 추천 결과 TOP 5 ===")
    for i, item in enumerate(results, start=1):
        print(f"{i}. {item.get('title', '제목 없음')} / score: {item['final_score']}")