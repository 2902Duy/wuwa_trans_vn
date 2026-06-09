import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path("mistral_translate_work/split_by_prompt/json/name_title")
PROMPTS = Path("mistral_translate_work/prompts")
REPORT_DIR = Path("mistral_translate_work/reports/name_title_english_audit")


VI_RE = re.compile(
    r"[ăâđêôơưĂÂĐÊÔƠƯ]|[\u1EA0-\u1EF9]"
)
TOKEN_RE = re.compile(
    r"(<[^>]+>|\{[^}]+\}|\\[nrt]|%|\d+(?:\.\d+)?|[~_#*/+=<>|^`]+)"
)
WORD_RE = re.compile(r"[A-Za-z][A-Za-z'.-]*")
TAG_ATTR_RE = re.compile(r"<[^>]+>")


COMMON_EN_WORDS_SHOULD_TRANSLATE = {
    "a", "an", "the", "and", "or", "of", "to", "for", "from", "with", "in", "on", "at", "by",
    "about", "after", "before", "during", "through", "into", "until", "while", "when", "where",
    "why", "how", "what", "which", "who", "this", "that", "these", "those", "you", "your", "our",
    "my", "me", "i", "we", "they", "he", "she", "it", "is", "are", "was", "were", "be", "been",
    "being", "do", "does", "did", "can", "could", "should", "would", "will", "shall", "may",
    "might", "must", "have", "has", "had", "not", "no", "yes", "please", "confirm", "cancel",
    "start", "end", "open", "close", "read", "use", "claim", "select", "choose", "equip",
    "unequip", "obtain", "obtained", "gain", "get", "complete", "clear", "defeat", "challenge",
    "reward", "rewards", "score", "rank", "stage", "phase", "chapter", "quest", "task", "mission",
    "level", "difficulty", "shop", "menu", "settings", "title", "description", "info", "battle",
    "combat", "test", "trial", "training", "time", "limited", "limit", "available", "unavailable",
    "locked", "unlock", "go", "return", "back", "next", "previous", "continue", "exit", "enter",
    "search", "find", "talk", "speak", "investigate", "collect", "deliver", "protect", "activate",
    "solve", "mechanism", "device", "material", "item", "weapon", "type", "category", "high",
    "highest", "hard", "normal", "easy", "fast", "travel", "drag", "tap", "move", "switch",
    "skill", "exp", "breakthrough", "game", "stage", "test", "event", "story", "photo",
    "camera", "map", "record",
}

ROLE_WORDS = {
    "guard", "researcher", "merchant", "student", "teacher", "doctor", "engineer", "soldier",
    "captain", "leader", "worker", "staff", "owner", "clerk", "officer", "member", "council",
    "resident", "citizen", "girl", "boy", "man", "woman", "elder", "child", "customer",
    "receptionist", "assistant", "director", "professor", "secretary", "administrator",
    "inspector", "investigator", "crew", "warrior", "knight", "master",
}

GLOSSARY_KEEP = {
    "Echo", "Rover", "Resonator", "Resonance Chain", "RC", "Resonance Skill",
    "Resonance Liberation", "Forte Circuit", "Basic Attack", "Normal Attack", "Heavy Attack",
    "Mid-air Attack", "Dodge Counter", "Intro Skill", "Outro Skill", "Inherent Skill",
    "HP", "ATK", "DEF", "Crit", "Rate", "DMG", "Bonus", "Glacio", "Fusion", "Electro",
    "Aero", "Spectro", "Havoc", "Waveplate", "Astrite", "Lunite", "Tide", "Shell",
    "Credit", "Oscillated", "Coral", "Afterglow", "Hazard", "Record", "Voucher",
    "Supply", "Chest", "Waveband", "STA", "Tacet", "Discord",
}

KNOWN_NON_VI_DIACRITIC_KEYS = {
    "MenuConfig_38_OptionsName_8",  # Português
    "FavorRoleInfo_1205_JP",  # Chiwa Saitô
}


def load_prompt_keep_terms() -> set[str]:
    terms = set()
    for prompt_name in ("keep_english_rules.md", "shared_glossary.md"):
        path = PROMPTS / prompt_name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        terms.update(t.strip() for t in re.findall(r"`([^`]+)`", text) if t.strip())
    return terms


PROMPT_KEEP_TERMS = load_prompt_keep_terms()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"), strict=False)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def strip_markup(text: str) -> str:
    text = TAG_ATTR_RE.sub(" ", text or "")
    return TOKEN_RE.sub(" ", text)


def has_vi(text: str) -> bool:
    return bool(VI_RE.search(text or ""))


def words(text: str) -> list[str]:
    clean = strip_markup(text or "")
    out = []
    for match in WORD_RE.finditer(clean):
        start, end = match.span()
        prev_ch = clean[start - 1] if start > 0 else ""
        next_ch = clean[end] if end < len(clean) else ""
        # Do not count ASCII fragments cut out of Vietnamese words with diacritics,
        # e.g. "th" from "thị" or "kh" from "khí".
        if prev_ch.isalpha() or next_ch.isalpha():
            continue
        out.append(match.group(0))
    return out


def lower_words(text: str) -> set[str]:
    return {w.lower().strip(".-'") for w in words(text)}


def is_exact_same(source: str, target: str) -> bool:
    return (source or "").strip() == (target or "").strip()


def is_placeholder_or_symbol_only(text: str) -> bool:
    clean = strip_markup(text).strip()
    return not WORD_RE.search(clean)


def is_probable_proper_name(text: str, row: dict) -> bool:
    clean = strip_markup(text).strip()
    if not clean or len(clean) > 96 or re.search(r"[.!?。！？]", clean):
        return False
    ws = words(clean)
    if not ws or len(ws) > 6:
        return False
    lowers = {w.lower().strip(".-'") for w in ws}
    if lowers & COMMON_EN_WORDS_SHOULD_TRANSLATE or lowers & ROLE_WORDS:
        return False
    if row.get("source_file") in {
        "lang_speaker.json", "lang_npc_headinfo.json", "lang_area.json", "lang_country.json",
        "lang_weapon.json", "lang_phantom.json", "lang_role.json", "lang_roleDescription.json",
    }:
        return True
    return all(w[:1].isupper() or w.isupper() or any(ch.isdigit() for ch in w) for w in ws)


def is_keep_allowed_exact(source: str, row: dict) -> tuple[bool, str]:
    clean = strip_markup(source).strip()
    if is_placeholder_or_symbol_only(source):
        return True, "placeholder_or_symbol_only"
    if clean in GLOSSARY_KEEP:
        return True, "glossary_exact"
    if clean in PROMPT_KEEP_TERMS:
        return True, "prompt_keep_term_exact"
    if is_probable_proper_name(source, row):
        return True, "probable_proper_name"
    key = str(row.get("primary_key", ""))
    if key.startswith(("Speaker_", "Role_", "Entity_")) and not (lower_words(source) & ROLE_WORDS):
        return True, "speaker_or_entity_name"
    return False, ""


def allowed_english_words(source: str, row: dict) -> set[str]:
    allowed = {w.lower() for w in GLOSSARY_KEEP}
    for term in PROMPT_KEEP_TERMS:
        if term and term in source:
            allowed |= {w.lower().strip(".-'") for w in words(term)}
    source_words = words(source)
    for w in source_words:
        lw = w.lower().strip(".-'")
        if w[:1].isupper() or w.isupper() or any(ch.isdigit() for ch in w):
            allowed.add(lw)
    if is_probable_proper_name(source, row):
        allowed |= {w.lower().strip(".-'") for w in source_words}
    return allowed


def unauthorized_english_tokens(source: str, target: str, row: dict) -> list[str]:
    allowed = allowed_english_words(source, row)
    bad = []
    for w in words(target):
        lw = w.lower().strip(".-'")
        if not lw:
            continue
        if lw in allowed:
            continue
        if len(lw) <= 1:
            continue
        if lw in COMMON_EN_WORDS_SHOULD_TRANSLATE or lw in ROLE_WORDS:
            bad.append(w)
            continue
    return sorted(set(bad), key=str.lower)


def source_is_english_translatable(source: str, row: dict) -> bool:
    if not WORD_RE.search(source or ""):
        return False
    allowed, _ = is_keep_allowed_exact(source, row)
    if allowed:
        return False
    lw = lower_words(source)
    if lw & COMMON_EN_WORDS_SHOULD_TRANSLATE or lw & ROLE_WORDS:
        return True
    if len(words(source)) >= 4:
        return True
    return False


def classify_row(row: dict, path: Path, index: int) -> dict:
    source = row.get("source_en") or ""
    target = row.get("new_translation_vi") or ""
    source_vi = has_vi(source) and str(row.get("primary_key", "")) not in KNOWN_NON_VI_DIACRITIC_KEYS
    target_vi = has_vi(target)
    target_en_words = words(target)
    same = is_exact_same(source, target)
    keep_allowed, keep_reason = is_keep_allowed_exact(source, row)
    translatable = source_is_english_translatable(source, row)
    bad_tokens = unauthorized_english_tokens(source, target, row)

    findings = []
    if not target.strip():
        findings.append("missing_translation")
    if source_vi:
        findings.append("source_en_contains_vietnamese")
    if same and translatable:
        findings.append("english_not_translated_exact")
    elif not target_vi and target_en_words and translatable and not keep_allowed:
        findings.append("english_not_translated_no_vietnamese")
    if target_vi and bad_tokens:
        findings.append("mixed_english_vietnamese_unauthorized")
    if same and keep_allowed:
        findings.append("kept_english_allowed")

    return {
        "findings": findings,
        "json_file": path.relative_to(ROOT).as_posix(),
        "json_index": index,
        "split_id": row.get("split_id", ""),
        "source_file": row.get("source_file", ""),
        "database": row.get("database", ""),
        "table": row.get("table", ""),
        "primary_key": row.get("primary_key", ""),
        "source_en": source,
        "new_translation_vi": target,
        "keep_allowed": keep_allowed,
        "keep_reason": keep_reason,
        "source_translatable": translatable,
        "unauthorized_english_tokens": bad_tokens,
    }


def main() -> None:
    rows = []
    counts = Counter()
    by_file = defaultdict(Counter)

    for path in sorted(ROOT.rglob("*.json")):
        data = load_json(path)
        if not isinstance(data, list):
            continue
        for index, row in enumerate(data):
            if not isinstance(row, dict):
                continue
            audit = classify_row(row, path, index)
            rows.append(audit)
            if not audit["findings"]:
                counts["clean_or_not_actionable"] += 1
                by_file[audit["json_file"]]["clean_or_not_actionable"] += 1
            for finding in audit["findings"]:
                counts[finding] += 1
                by_file[audit["json_file"]][finding] += 1

    groups = defaultdict(list)
    for row in rows:
        for finding in row["findings"]:
            groups[finding].append(row)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(REPORT_DIR / "all_rows_audit.json", {"count": len(rows), "rows": rows})
    for finding, items in sorted(groups.items()):
        write_json(REPORT_DIR / f"{finding}.json", {"count": len(items), "rows": items})

    untranslated = {
        row["split_id"]
        for row in rows
        if "english_not_translated_exact" in row["findings"]
        or "english_not_translated_no_vietnamese" in row["findings"]
    }
    mixed = {
        row["split_id"]
        for row in rows
        if "mixed_english_vietnamese_unauthorized" in row["findings"]
    }
    summary = {
        "total_rows": len(rows),
        "counts": dict(counts.most_common()),
        "english_not_translated_total_unique_rows": len(untranslated),
        "mixed_english_vietnamese_unauthorized_unique_rows": len(mixed),
        "by_file": {k: dict(v.most_common()) for k, v in sorted(by_file.items())},
        "report_dir": str(REPORT_DIR),
        "method_notes": [
            "Exact source==translation is only counted as untranslated when source does not match keep/proper-name rules.",
            "No-Vietnamese translations are counted when the source appears translatable by common UI/role/sentence heuristics.",
            "Mixed English/Vietnamese is counted when Vietnamese text contains English function/UI/role words not allowed by glossary, proper-name, placeholder, or source-name rules.",
            "Português and Chiwa Saitô are excluded from Vietnamese-diacritic contamination because they are non-Vietnamese names.",
        ],
    }
    write_json(REPORT_DIR / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
