import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


JSON_ROOT = Path("mistral_translate_work/split_by_prompt/json")
TARGET_DIRS = [JSON_ROOT / "ui", JSON_ROOT / "system_text"]
REPORT_DIR = Path("mistral_translate_work/reports/ui_system_full_audit")


VI_RE = re.compile(
    r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡ"
    r"ùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄ"
    r"ÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]"
)
ASCII_WORD_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9'./&+-]*\b")
TAG_RE = re.compile(r"<[^>]+>")
PLACEHOLDER_RE = re.compile(r"\{[^{}]*\}")
TEXTURE_RE = re.compile(r"<texture=[^>]+>|/Game/[^\s>]+")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


ALLOWED_EN_WORDS = {
    "Echo", "Echoes", "Resonator", "Resonators", "Rover", "DMG", "HP", "ATK", "DEF",
    "CRIT", "Crit", "Aero", "Glacio", "Fusion", "Electro", "Spectro", "Havoc",
    "Tacet", "Discord", "Sonata", "Terminal", "Data", "Bank", "Normal", "Heavy",
    "Attack", "Basic", "Mid-air", "Resonance", "Skill", "Liberation", "Intro",
    "Outro", "Forte", "Circuit", "Concerto", "Energy", "Weapon", "Weapons",
    "Utility", "Domain", "Novelty", "Shop", "Token", "UID", "COST", "STA",
    "Lv", "EXP", "WavesLine", "KURO", "Co-op", "NPC", "PC", "Gamepad", "Touch",
    "Dodge", "Cooldown", "Buff", "Debuff", "Shield", "Dreamland", "Coupon",
}

SUSPICIOUS_EN_WORDS = {
    "Cancel", "Confirm", "Select", "Tap", "Claim", "Remove", "Place", "Previous",
    "Ongoing", "Requirement", "Equipped", "Unlocked", "Revive", "Controls", "Skills",
    "Wave", "Leave", "Rating", "Tactics", "Details", "Locked", "Unavailable",
    "Defeated", "Track", "Back", "Close", "Start", "Continue", "Skip", "Retry",
    "Next", "View", "Obtained", "Unlock", "Friends", "Gallery", "Map", "Backpack",
    "Utilities", "Feedback", "Tutorials", "Guidebook", "Events", "Store", "Trophies",
    "Team", "Convene", "Missions", "Achievements", "Database", "Forces", "Settings",
    "Overview", "You", "She", "He", "They", "But", "Wait", "Then", "After", "Today",
    "Reporter", "Items", "Description", "Voice", "Alert", "Module", "Reset", "Support",
    "Transform", "Use", "Hold", "Release", "Jump", "Gather", "Deploy", "Photo",
    "Research", "Instructions", "Notice", "Time", "Note", "Amount", "Male", "Female",
    "None", "Malee", "Supplies", "Exchange", "Play", "Save", "Normal", "No",
}

BROKEN_TERMS = {
    "Resonatorss", "Resonatorsss", "Echoeses", "Echoess", "Tranform", "Transfrom",
    "Transform thành", "Biến Đổi thành", "Thường Attack", "Bạn'tan", "Bạn Tan",
    "Malee:", "None ", "Play Triển", "Save Đày", "Nghiên cứu Institute",
}

COARSE_OR_BAD_VI = {
    "cút đi", "Cút đi", "cút ngay", "Cút ngay", "cút ", "Cút ",
}

MOJIBAKE_MARKERS = (
    "Ã¡", "Ã ", "Ã¢", "Ã£", "Ã©", "Ã¨", "Ãª", "Ã­", "Ã¬", "Ã³", "Ã²", "Ã´",
    "Ãº", "Ã¹", "Ã½", "áº", "á»", "Ä‘", "Ä", "Æ°", "Æ¡", "Å©",
)


def clean_text(text: str) -> str:
    text = TEXTURE_RE.sub("", text)
    text = TAG_RE.sub("", text)
    return text


def token_set(pattern: re.Pattern, text: str) -> Counter:
    return Counter(pattern.findall(text or ""))


def tag_names(text: str) -> Counter:
    names = []
    for tag in TAG_RE.findall(text or ""):
        if tag.startswith("</"):
            names.append(tag)
        else:
            names.append(re.sub(r"\s.*?>", ">", tag))
    return Counter(names)


def classify(source: str, target: str) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    src = source or ""
    tgt = target or ""
    src_clean = clean_text(src).strip()
    tgt_clean = clean_text(tgt).strip()

    if not tgt.strip():
        issues.append(("high", "empty_translation"))
        return issues

    if src_clean and tgt_clean == src_clean:
        issues.append(("high", "same_as_source"))

    if CONTROL_RE.search(tgt):
        issues.append(("high", "control_character_in_translation"))

    if any(marker in tgt for marker in MOJIBAKE_MARKERS):
        issues.append(("high", "possible_mojibake"))

    for term in BROKEN_TERMS:
        if term in tgt:
            issues.append(("high", f"broken_term:{term}"))

    for term in COARSE_OR_BAD_VI:
        if term in tgt:
            issues.append(("high", f"coarse_or_bad_vi:{term.strip()}"))

    src_placeholders = token_set(PLACEHOLDER_RE, src)
    tgt_placeholders = token_set(PLACEHOLDER_RE, tgt)
    if src_placeholders != tgt_placeholders:
        issues.append(("high", "placeholder_mismatch"))

    src_tags = tag_names(src)
    tgt_tags = tag_names(tgt)
    if src_tags != tgt_tags:
        issues.append(("medium", "tag_mismatch"))

    if "%%" in tgt and "%%" not in src:
        issues.append(("medium", "unexpected_double_percent"))
    if tgt.strip() == "%%" and src.strip() != "%%":
        issues.append(("high", "exact_double_percent_wrong"))

    if tgt.count("\n") > src.count("\n") + 4 or src.count("\n") > tgt.count("\n") + 4:
        issues.append(("medium", "large_linebreak_count_delta"))

    if re.search(r"\s{4,}", tgt) and not re.search(r"\s{4,}", src):
        issues.append(("low", "unexpected_long_spaces"))

    has_vi = bool(VI_RE.search(tgt_clean))
    words = ASCII_WORD_RE.findall(tgt_clean)
    meaningful_words = [w for w in words if w not in ALLOWED_EN_WORDS and not re.fullmatch(r"[A-Z]{2,}", w)]
    suspicious_words = [w for w in words if w in SUSPICIOUS_EN_WORDS]

    if not has_vi and words and len(tgt_clean) <= 80:
        issues.append(("medium", "english_or_untranslated_short_text"))

    if has_vi and suspicious_words:
        issues.append(("medium", "mixed_language_suspicious_words:" + ",".join(sorted(set(suspicious_words))[:8])))

    if has_vi and meaningful_words:
        # Lower severity than exact suspicious words: many UI strings keep proper nouns or game terms.
        issues.append(("low", "mixed_language_other_words:" + ",".join(sorted(set(meaningful_words))[:8])))

    if re.search(r"\b(None|No)\s+[a-zà-ỹđ]", tgt):
        issues.append(("high", "literal_none_or_no_in_vietnamese_sentence"))

    if re.search(r"\b(Malee|Femalee|Confere|Home hát|Night đêm|Night khuya|Bóng Night)\b", tgt):
        issues.append(("high", "known_machine_translation_artifact"))

    if re.search(r"\{Cus:Ipt,[^}]*[À-ỹĐđ]", tgt):
        issues.append(("high", "translated_input_tag"))

    if re.search(r"</?[A-Za-z][A-Za-z0-9#=_\"' -]*$", tgt):
        issues.append(("high", "possibly_broken_angle_tag"))

    return issues


def severity_rank(severity: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(severity, 9)


def main() -> None:
    suspects = []
    total_rows = 0
    translated_rows = 0
    untranslated_rows = 0
    files_scanned = 0
    domain_counts = Counter()
    issue_counts = Counter()
    severity_counts = Counter()

    for root in TARGET_DIRS:
        if not root.exists():
            continue
        domain = root.name
        for path in sorted(root.rglob("*.json")):
            files_scanned += 1
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                continue
            rel = path.relative_to(JSON_ROOT).as_posix()
            for index, row in enumerate(data):
                if not isinstance(row, dict):
                    continue
                total_rows += 1
                domain_counts[domain] += 1
                source = row.get("source_en", "")
                target = row.get("new_translation_vi", "")
                if isinstance(target, str) and target.strip():
                    translated_rows += 1
                else:
                    untranslated_rows += 1
                issues = classify(str(source or ""), str(target or ""))
                if not issues:
                    continue
                highest = sorted({sev for sev, _ in issues}, key=severity_rank)[0]
                issue_labels = [label for _, label in issues]
                for sev, label in issues:
                    issue_counts[label] += 1
                    severity_counts[sev] += 1
                suspects.append(
                    {
                        "severity": highest,
                        "domain": domain,
                        "json_file": rel,
                        "json_index": index,
                        "split_id": row.get("split_id", ""),
                        "database": row.get("database", ""),
                        "table": row.get("table", ""),
                        "primary_key_column": row.get("primary_key_column", ""),
                        "primary_key": row.get("primary_key", ""),
                        "column": row.get("column", ""),
                        "prompt_domain": row.get("prompt_domain", ""),
                        "issues": issue_labels,
                        "source_en": source,
                        "new_translation_vi": target,
                    }
                )

    suspects.sort(key=lambda r: (severity_rank(r["severity"]), r["domain"], r["json_file"], str(r["primary_key"])))

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    suspects_path = REPORT_DIR / "ui_system_suspects.json"
    csv_path = REPORT_DIR / "ui_system_suspects.csv"
    summary_path = REPORT_DIR / "summary.json"

    summary = {
        "scope": ["split_by_prompt/json/ui", "split_by_prompt/json/system_text"],
        "files_scanned": files_scanned,
        "total_rows": total_rows,
        "translated_rows": translated_rows,
        "untranslated_rows_empty": untranslated_rows,
        "suspect_rows": len(suspects),
        "domain_counts": dict(domain_counts),
        "severity_counts": dict(severity_counts),
        "top_issue_counts": dict(issue_counts.most_common(80)),
    }

    suspects_path.write_text(json.dumps(suspects, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    fields = [
        "severity", "domain", "json_file", "json_index", "split_id", "database", "table",
        "primary_key_column", "primary_key", "column", "prompt_domain", "issues",
        "source_en", "new_translation_vi",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in suspects:
            out = dict(row)
            out["issues"] = " | ".join(row["issues"])
            writer.writerow(out)

    print(json.dumps({"summary": summary, "suspects_json": str(suspects_path), "suspects_csv": str(csv_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
