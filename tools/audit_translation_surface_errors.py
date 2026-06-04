import json
import re
import sqlite3
from collections import Counter
from pathlib import Path


DB_ROOT = Path("work_db_vi_mistral")
JSON_ROOT = Path("mistral_translate_work/split_by_prompt/json")
REPORT_DIR = Path("mistral_translate_work/reports/translation_surface_audit")


VI_RE = re.compile(
    r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ"
    r"ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]"
)

BROKEN_TERMS = [
    "Resonatorss",
    "Resonatorsss",
    "Resonatorssss",
    "Echoeses",
    "Echoess",
    "Tranform",
    "Transfrom",
    "Transform thành",
    "Biến Đổi thành",
]

EXACT_BAD = {
    "Cancel",
    "Confirm",
    "Select",
    "Tap",
    "Claim",
    "Remove",
    "Place",
    "Previous",
    "Ongoing",
    "Requirement",
    "Equipped",
    "Unlocked",
    "Revive",
    "Controls",
    "Skills",
    "Wave",
    "Leave",
    "Rating",
    "Tactics",
    "Details",
    "Locked",
    "Unavailable",
    "Defeated",
    "Track",
    "Back",
    "Close",
    "Start",
    "Continue",
    "Skip",
    "Retry",
    "Next",
    "View",
    "Obtained",
    "Unlock",
    "Friends",
    "Gallery",
    "Map",
    "Backpack",
    "Utilities",
    "Feedback",
    "Tutorials",
    "Guidebook",
    "Events",
    "Store",
    "Trophies",
    "Team",
    "Convene",
    "Missions",
    "Achievements",
    "Database",
    "Forces",
    "Settings",
    "Overview",
}

BAD_WORDS = [
    "You",
    "She",
    "He",
    "They",
    "But",
    "Wait",
    "Then",
    "After",
    "Today",
    "Reporter",
    "Items",
    "Description",
    "Voice",
    "Alert",
    "Module",
    "Requirement",
    "Reset",
    "Support",
    "Transform",
    "Select",
    "Tap",
    "Claim",
    "Confirm",
    "Cancel",
    "Continue",
    "Backpack",
    "Guidebook",
    "Utilities",
    "Feedback",
    "Tutorials",
    "Gallery",
    "Friends",
    "Store",
    "Trophies",
    "Team",
    "Convene",
]

ALLOWED_WORDS = {
    "Echo",
    "Echoes",
    "Resonator",
    "Resonators",
    "Rover",
    "DMG",
    "HP",
    "ATK",
    "DEF",
    "Crit",
    "CRIT",
    "Aero",
    "Glacio",
    "Fusion",
    "Electro",
    "Spectro",
    "Havoc",
    "Tacet",
    "Discord",
    "Sonata",
    "Terminal",
    "Data",
    "Bank",
    "Normal",
    "Heavy",
    "Attack",
    "Resonance",
    "Skill",
    "Liberation",
    "Intro",
    "Outro",
    "Forte",
    "Circuit",
    "Concerto",
    "Energy",
    "Weapon",
    "Weapons",
    "Utility",
    "Domain",
    "Novelty",
    "Shop",
    "Token",
    "UID",
    "COST",
    "STR",
    "CON",
    "STA",
    "Lv",
    "Lv.",
    "EXP",
    "WavesLine",
    "KURO",
}

ASSET_RE = re.compile(r"<texture=[^>]+>|/Game/[^\s>]+")
TAG_RE = re.compile(r"<[^>]+>")
WORD_RE = re.compile(r"\b[A-Za-z][A-Za-z.'-]*\b")


def clean_for_scan(text: str) -> str:
    text = ASSET_RE.sub("", text)
    text = TAG_RE.sub("", text)
    return text


def classify(text: str, source: str = "") -> list[str]:
    kinds = []
    raw = text
    text = clean_for_scan(text).strip()
    if not text:
        return kinds
    if text == "%%":
        kinds.append("exact_double_percent")
    if "%%" in text and "%" not in (source or ""):
        kinds.append("unexpected_double_percent")
    for term in BROKEN_TERMS:
        if term in text:
            kinds.append(f"broken_term:{term}")
    if text in EXACT_BAD:
        kinds.append("exact_untranslated_ui")
    if VI_RE.search(text):
        for word in BAD_WORDS:
            if re.search(rf"\b{re.escape(word)}\b", text):
                kinds.append(f"mixed_bad_word:{word}")
        m = re.match(r"^[A-Za-z][A-Za-z.'-]*\b", text)
        if m and m.group(0) not in ALLOWED_WORDS:
            kinds.append("leading_english_word")
    else:
        words = [w for w in WORD_RE.findall(text) if w not in ALLOWED_WORDS]
        if words and len(text) <= 40 and not raw.startswith("<") and not re.fullmatch(r"[A-Z0-9_./:{} -]+", text):
            kinds.append("short_english_no_vietnamese")
    return sorted(set(kinds))


def scan_db() -> list[dict]:
    hits = []
    for db_path in DB_ROOT.glob("*.db"):
        con = sqlite3.connect(db_path)
        try:
            for table, in con.execute("SELECT name FROM sqlite_master WHERE type='table'"):
                cols = [row[1] for row in con.execute(f"PRAGMA table_info({table})")]
                if "Content" not in cols:
                    continue
                id_col = "Id" if "Id" in cols else cols[0]
                for row_id, content in con.execute(f"SELECT {id_col}, Content FROM {table}"):
                    if not isinstance(content, str):
                        continue
                    for kind in classify(content):
                        hits.append(
                            {
                                "source_type": "db",
                                "kind": kind,
                                "db": db_path.name,
                                "table": table,
                                "id": row_id,
                                "text": content,
                            }
                        )
        finally:
            con.close()
    return hits


def scan_json() -> list[dict]:
    hits = []
    for path in JSON_ROOT.rglob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            continue
        rel = path.relative_to(JSON_ROOT).as_posix()
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                continue
            text = item.get("new_translation_vi")
            if not isinstance(text, str):
                continue
            source = item.get("source_en") or ""
            for kind in classify(text, source):
                hits.append(
                    {
                        "source_type": "json",
                        "kind": kind,
                        "file": rel,
                        "index": index,
                        "split_id": item.get("split_id"),
                        "primary_key": item.get("primary_key"),
                        "source_en": source,
                        "text": text,
                    }
                )
    return hits


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    hits = scan_db() + scan_json()
    summary = {
        "total_hits": len(hits),
        "by_source_type": dict(Counter(h["source_type"] for h in hits).most_common()),
        "by_kind": dict(Counter(h["kind"] for h in hits).most_common()),
        "top_db": dict(Counter(h.get("db", "") for h in hits if h["source_type"] == "db").most_common(50)),
        "top_json_files": dict(
            Counter(h.get("file", "") for h in hits if h["source_type"] == "json").most_common(50)
        ),
    }
    (REPORT_DIR / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (REPORT_DIR / "hits.json").write_text(json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
