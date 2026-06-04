import json
import re
from collections import Counter, defaultdict
from pathlib import Path


WORKSPACE_DIR = Path(r"C:\Users\tduy2\Documents\antigravity\silly-darwin")
WORK_DIR = WORKSPACE_DIR / "mistral_translate_work"
NAME_TITLE_DIR = WORK_DIR / "split_by_prompt" / "json" / "name_title"
REPORT_DIR = WORK_DIR / "reports" / "split_name_title_classification"


GLOSSARY_KEEP = {
    "Echo",
    "Rover",
    "Resonator",
    "Resonance Chain",
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
    "Aero Erosion",
    "Glacio Chafe",
    "Spectro Frazzle",
    "Havoc Bane",
    "Fusion Burst",
    "Electro Flare",
    "Negative Status",
    "Tidal Blight",
    "DMG",
    "DMG Bonus",
    "Crit. Rate",
    "Crit. DMG",
}

PLACEHOLDER_RE = re.compile(r"^(?:\s*(?:<[^>]+>|\{\d+\}|\{[A-Za-z_][A-Za-z0-9_]*\}|\\[nrt]|\{Cus:[^}]+\})\s*)+$")
TOKEN_RE = re.compile(r"(<[^>]+>|\{\d+\}|\{[A-Za-z_][A-Za-z0-9_]*\}|\\[nrt]|\{Cus:[^}]+\})")
LETTER_RE = re.compile(r"[A-Za-z]")
SENTENCE_RE = re.compile(r"[.!?。！？]$")

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
    "customer",
    "receptionist",
    "assistant",
    "director",
    "professor",
    "secretary",
    "administrator",
    "inspector",
    "investigator",
}

UI_WORDS = {
    "read",
    "open",
    "close",
    "start",
    "end",
    "confirm",
    "cancel",
    "back",
    "next",
    "previous",
    "claim",
    "use",
    "equip",
    "unequip",
    "select",
    "reward",
    "rewards",
    "score",
    "rank",
    "gold",
    "silver",
    "bronze",
    "challenge",
    "difficulty",
    "level",
    "phase",
    "stage",
    "chapter",
    "quest",
    "task",
    "mission",
    "shop",
    "menu",
    "settings",
    "material",
    "item",
    "type",
    "category",
    "title",
    "description",
}

KEEP_FILE_HINTS = {
    "lang_area.json",
    "lang_country.json",
    "lang_speaker.json",
    "lang_npc_headinfo.json",
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def strip_tokens(text):
    return TOKEN_RE.sub("", text or "").strip()


def words(text):
    return {part.lower().strip(".,:;!?()[]{}\"'") for part in re.findall(r"[A-Za-z][A-Za-z'.-]*", text or "")}


def has_mixed_punctuation_name(text):
    return any(mark in text for mark in ("???", "？？？", "******", "♪", "&"))


def is_title_case_name(text):
    clean = strip_tokens(text)
    if not clean or len(clean) > 90:
        return False
    if SENTENCE_RE.search(clean):
        return False
    parts = re.findall(r"[A-Za-z][A-Za-z'.-]*", clean)
    if not parts or len(parts) > 5:
        return False
    lower = words(clean)
    if lower & ROLE_WORDS or lower & UI_WORDS:
        return False
    return all(part[:1].isupper() or part.isupper() for part in parts)


def classify(row):
    source = row.get("source_en", "") or ""
    clean = strip_tokens(source)
    lower = words(clean)
    source_file = row.get("source_file", "")
    key = str(row.get("primary_key", ""))

    if not source:
        return "empty_source", "No source text."

    if PLACEHOLDER_RE.match(source):
        return "keep_placeholder_only", "Only placeholders/tags; keep exactly as source."

    if clean in GLOSSARY_KEEP:
        return "keep_glossary_term", "Mandatory English glossary term."

    if "{PlayerName}" in source or "{message}" in source:
        if clean.replace("{PlayerName}", "").replace("{message}", "").strip() == "":
            return "keep_placeholder_only", "Speaker placeholder only; keep exactly as source."
        return "keep_with_placeholder", "Contains speaker/player placeholder; preserve token and likely keep name part."

    if key.startswith("Speaker_") or source_file in KEEP_FILE_HINTS:
        if lower & ROLE_WORDS:
            return "translate_role_or_speaker_title", "Speaker/NPC role title can be translated."
        return "keep_proper_name", "Speaker/place/name file; keep proper name in English."

    if source_file in {"lang_item.json", "lang_weapon.json", "lang_phantom.json"}:
        if lower & UI_WORDS or lower & ROLE_WORDS:
            return "translate_short_ui_title", "Short common UI/item label can be translated."
        return "keep_item_weapon_echo_name", "Item/weapon/Echo name should normally stay English."

    if lower & ROLE_WORDS:
        return "translate_role_or_speaker_title", "Common role/title words detected."

    if lower & UI_WORDS:
        return "translate_short_ui_title", "Common UI/title words detected."

    if ":" in clean and lower & UI_WORDS:
        return "translate_short_ui_title", "Score/rank/title label detected."

    if has_mixed_punctuation_name(clean):
        return "translate_ambiguous_name_title", "Ambiguous punctuation/noise string; translate in name/title pass."

    if is_title_case_name(clean):
        return "keep_proper_name", "Looks like a proper noun/title-case name."

    if len(clean.split()) >= 4:
        return "translate_short_title", "Short phrase/title likely translatable."

    if LETTER_RE.search(clean):
        return "translate_ambiguous_name_title", "Ambiguous short text; translate in name/title pass."

    return "keep_symbol_or_number", "No normal letters; keep exactly."


def main():
    rows = []
    for path in sorted(NAME_TITLE_DIR.rglob("*.json")):
        for row in read_json(path):
            kind, reason = classify(row)
            rows.append(
                {
                    "classification": kind,
                    "reason": reason,
                    "split_id": row.get("split_id", ""),
                    "source_file": row.get("source_file", ""),
                    "original_index": row.get("original_index", ""),
                    "primary_key": row.get("primary_key", ""),
                    "table": row.get("table", ""),
                    "source_en": row.get("source_en", ""),
                    "new_translation_vi": row.get("new_translation_vi", ""),
                }
            )

    counts = Counter(row["classification"] for row in rows)
    by_file = defaultdict(Counter)
    for row in rows:
        by_file[row["source_file"]][row["classification"]] += 1

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(REPORT_DIR / "all_rows.json", {"count": len(rows), "rows": rows})
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["classification"]].append(row)
    for kind, items in sorted(grouped.items()):
        write_json(REPORT_DIR / f"{kind}.json", {"count": len(items), "rows": items})

    summary = {
        "total": len(rows),
        "counts": dict(counts.most_common()),
        "by_file": {file_name: dict(counter.most_common()) for file_name, counter in sorted(by_file.items())},
        "report_dir": str(REPORT_DIR),
    }
    write_json(REPORT_DIR / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
