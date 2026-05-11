import json

# =============================
# 파일 경로
# =============================
INPUT_PATH = "json/contest_normalized.json"
OUTPUT_PATH = "json/contest_search_text.json"


# =============================
# search_text 생성
# =============================
def make_search_text(contest):

    texts = []

    # domains
    texts.extend(contest.get("domains", []))

    # skills
    texts.extend(contest.get("skills", []))
    
    # 중복 제거
    cleaned = []

    for t in texts:

        if not isinstance(t, str):
            continue

        tag = t.strip()

        if not tag:
            continue

        if tag not in cleaned:
            cleaned.append(tag)

    return " ".join(cleaned)


# =============================
# 메인 실행
# =============================
def main():

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        contests = json.load(f)

    results = []

    for idx, contest in enumerate(contests, start=1):

        item = {
            "contest_id": contest.get("contest_id", ""),
            "search_text": make_search_text(contest)
        }

        results.append(item)

        print(f"[DONE] {idx}/{len(contests)} - {item['contest_id']}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()