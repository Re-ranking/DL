# CV 데이터를 정규화하여 태그로 추출
import json


# -----------------------------
# 공통: 텍스트 정규화
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
# CV → skills, domains만 추출
# -----------------------------
def extract_cv_tags(cv_json):
    return {
        "skills": normalize_list(cv_json.get("skills", [])),
        "domains": normalize_list(cv_json.get("domains", cv_json.get("domain", [])))
    }

# -----------------------------
# 파일 로드
# -----------------------------
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# -----------------------------
# 실행
# -----------------------------
def main():
    cv_data = load_json("cv_result.json")
    contest_data = load_json("contest_result.json")  # 리스트

    # CV 태그
    user_tags = {
        "name": cv_data.get("name"),
        **extract_cv_tags(cv_data)
    }

    print("===== USER TAGS =====")
    print(json.dumps(user_tags, indent=2, ensure_ascii=False))

    print("\n===== CONTEST TAG SAMPLE =====")
    for c in contest_tags_list[:3]:
        print(json.dumps(c, indent=2, ensure_ascii=False))

    # 저장
    with open("user_tags.json", "w", encoding="utf-8") as f:
        json.dump(user_tags, f, indent=2, ensure_ascii=False)

    
    print("\n저장 완료")


if __name__ == "__main__":
    main()