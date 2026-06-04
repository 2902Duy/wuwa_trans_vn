import json
import re
from collections import Counter, defaultdict
from pathlib import Path


WORKSPACE_DIR = Path(r"C:\Users\tduy2\Documents\antigravity\silly-darwin")
WORK_DIR = WORKSPACE_DIR / "mistral_translate_work"
SPLIT_NAME_TITLE_DIR = WORK_DIR / "split_by_prompt" / "json" / "name_title"
REVIEW_DIR = WORK_DIR / "review_translated_only"
REPORT_DIR = WORK_DIR / "reports" / "name_title_analysis"


ROLE_WORDS = {
    "guard",
    "researcher",
    "merchant",
    "student",
    "teacher",
    "doctor",
    "engineer",
    "soldier",
    "captain",
    "leader",
    "worker",
    "staff",
    "owner",
    "clerk",
    "officer",
    "member",
    "council",
    "resident",
    "citizen",
    "girl",
    "boy",
    "man",
    "woman",
    "elder",
    "child",
}

UI_TITLE_WORDS = {
    "chapter",
    "quest",
    "level",
    "phase",
    "stage",
    "reward",
    "challenge",
    "difficulty",
    "shop",
    "menu",
    "settings",
    "confirm",
    "cancel",
    "weapon",
    "material",
    "item",
    "echo",
    "skill",
    "attribute",
    "title",
    "description",
    "type",
    "category",
}

GLOSSARY_NAMES = {
    "Rover",
    "Echo",
    "Resonator",
    "Resonance Skill",
    "Resonance Liberation",
    "Forte Circuit",
    "Basic Attack",
    "Normal Attack",
    "Heavy Attack",
    "Mid-air Attack",
    "Dodge Counter",
    "Intro Skill",
    "Outro Skill",
    "Inherent Skill",
    "DMG",
    "DMG Bonus",
    "Crit. Rate",
    "Crit. DMG",
    "Aero Erosion",
    "Glacio Chafe",
    "Spectro Frazzle",
    "Havoc Bane",
    "Fusion Burst",
    "Electro Flare",
    "Negative Status",
    "Tidal Blight",
}

VIETNAMESE_RE = re.compile(
    r"[ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]",
    re.IGNORECASE,
)
TOKEN_RE = re.compile(r"(<[^>]+>|\{\d+\}|\{[A-Za-z_][A-Za-z0-9_]*\}|\\[nrt]|\{Cus:[^}]+\})")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z'.-]*")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def row_key(row):
    return (
        row.get("database", ""),
        row.get("table", ""),
        row.get("primary_key_column", ""),
        str(row.get("primary_key", "")),
        row.get("column", ""),
    )


def load_review_rows():
    by_file = {}
    for path in sorted(REVIEW_DIR.glob("*.json")):
        if path.name == "summary.json":
            continue
        rows = read_json(path)
        by_file[path.name] = rows
    return by_file


def strip_tokens(text):
    return TOKEN_RE.sub("", text or "").strip()


def lower_words(text):
    return {word.lower().strip(".-'") for word in WORD_RE.findall(text or "")}


def looks_like_person_or_place_name(source):
    clean = strip_tokens(source)
    if not clean or len(clean) > 80:
        return False
    if any(char in clean for char in ".!?"):
        return False
    words = lower_words(clean)
    if not words:
        return False
    if words & ROLE_WORDS:
        return False
    if words & UI_TITLE_WORDS:
        return False
    if clean in GLOSSARY_NAMES:
        return True
    alpha_words = WORD_RE.findall(clean)
    if len(alpha_words) <= 4 and all(word[:1].isupper() or word.isupper() for word in alpha_words):
        return True
    return False


def looks_like_translatable_title(source):
    clean = strip_tokens(source)
    words = lower_words(clean)
    if words & ROLE_WORDS or words & UI_TITLE_WORDS:
        return True
    if len(clean.split()) >= 4 and not clean.endswith((".", "!", "?")):
        return True
    return False


def classify(source, translation):
    source_clean = strip_tokens(source)
    translation_clean = strip_tokens(translation)
    same = source_clean == translation_clean
    source_has_vi = bool(VIETNAMESE_RE.search(source_clean))
    trans_has_vi = bool(VIETNAMESE_RE.search(translation_clean))

    if not translation_clean:
        return "missing_translation"
    if source_clean in GLOSSARY_NAMES and not same:
        return "glossary_name_translated"
    if looks_like_person_or_place_name(source_clean):
        if same:
            return "proper_name_kept"
        return "proper_name_translated_or_changed"
    if looks_like_translatable_title(source_clean):
        if same:
            return "translatable_title_still_english"
        if trans_has_vi or source_has_vi:
            return "translatable_title_translated"
        return "translatable_title_changed_non_vi"
    if same:
        return "short_text_kept"
    if trans_has_vi:
        return "short_text_translated"
    return "short_text_changed_non_vi"


def main():
    review_by_file = load_review_rows()
    rows_out = []
    counts = Counter()
    by_file = defaultdict(Counter)

    for split_path in sorted(SPLIT_NAME_TITLE_DIR.rglob("*.json")):
        split_rows = read_json(split_path)
        for split_row in split_rows:
            source_file = split_row["source_file"]
            original_index = split_row["original_index"]
            review_rows = review_by_file.get(source_file)
            if not review_rows or original_index >= len(review_rows):
                kind = "missing_review_row"
                translation = ""
                review_row = {}
            else:
                review_row = review_rows[original_index]
                translation = review_row.get("translation_vi", "")
                kind = classify(split_row.get("source_en", ""), translation)

            item = {
                "kind": kind,
                "source_file": source_file,
                "original_index": original_index,
                "split_id": split_row.get("split_id", ""),
                "primary_key": split_row.get("primary_key", ""),
                "table": split_row.get("table", ""),
                "source_en": split_row.get("source_en", ""),
                "translation_vi": translation,
                "status": review_row.get("status", ""),
                "issues": review_row.get("issues", ""),
            }
            rows_out.append(item)
            counts[kind] += 1
            by_file[source_file][kind] += 1

    groups = defaultdict(list)
    for item in rows_out:
        groups[item["kind"]].append(item)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(REPORT_DIR / "all_name_title_rows.json", {"count": len(rows_out), "rows": rows_out})
    for kind, items in sorted(groups.items()):
        write_json(REPORT_DIR / f"{kind}.json", {"count": len(items), "rows": items})

    summary = {
        "total": len(rows_out),
        "counts": dict(counts.most_common()),
        "by_file": {file_name: dict(counter.most_common()) for file_name, counter in sorted(by_file.items())},
        "report_dir": str(REPORT_DIR),
    }
    write_json(REPORT_DIR / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
