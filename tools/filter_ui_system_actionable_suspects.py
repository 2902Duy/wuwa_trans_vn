import csv
import json
import re
from collections import Counter
from pathlib import Path


REPORT_DIR = Path("mistral_translate_work/reports/ui_system_full_audit")
FULL_PATH = REPORT_DIR / "ui_system_suspects.json"
ACTIONABLE_JSON = REPORT_DIR / "ui_system_actionable_suspects.json"
ACTIONABLE_CSV = REPORT_DIR / "ui_system_actionable_suspects.csv"
SUMMARY_PATH = REPORT_DIR / "actionable_summary.json"


TRANSLATABLE_EXACT = {
    "Purchase", "High", "Low", "Medium", "General", "Max", "Min", "Details", "Overview",
    "Back", "Close", "Confirm", "Cancel", "Leave", "Start", "Continue", "Retry", "Skip",
    "Next", "Select", "Remove", "Place", "Claim", "Unlocked", "Locked", "Unavailable",
    "Defeated", "Requirement", "Reward", "Rewards", "Description", "Name", "New", "Common",
    "Rare", "Double", "Amount", "Notice", "Time", "Note", "Instructions", "Support", "Reset",
    "Map", "Team", "Friends", "Gallery", "Backpack", "Guidebook", "Tutorials", "Store",
    "Convene", "Trophies", "Utilities", "Feedback", "Database", "Settings", "Controls",
}

ALLOWED_SAME_SOURCE_TERMS = {
    "Crownless", "Bell-Borne Geochelone", "Inferno Rider", "Feilian Beringal",
    "Impermanence Heron", "Fusion Prism", "Glacio Prism", "Rocksteady Guardian",
    "Excarat", "Gulpuff", "Chirpuff", "Cyan-Feathered Heron", "Violet-Feathered Heron",
    "Lil Geohide Saurian", "Cruisewing", "Hoochief", "Spearback Ursa", "Zig Zag",
    "Whiff Whoosh", "Tic Tac", "Fission Junrock", "Chaserazor", "Mourning Aix",
    "Resonance Liberation", "Tacet Field", "Pioneer Association", "Choral Beacon",
    "Resonators", "Normal Attack", "Heavy Attack", "Basic Attack", "Dodge Counter",
    "Sonata", "Echo", "Echoes", "Rover", "Lahai-Roi", "Norfall Barrens",
}

ALWAYS_ACTIONABLE_PREFIXES = (
    "placeholder_mismatch",
    "tag_mismatch",
    "control_character",
    "possible_mojibake",
    "broken_term:",
    "coarse_or_bad_vi:",
    "translated_input_tag",
    "literal_none_or_no",
    "known_machine_translation_artifact",
    "exact_double_percent",
    "unexpected_double_percent",
    "possibly_broken_angle_tag",
)

MIXED_CLEAR_WORDS = {
    "Map", "Play", "Details", "Overview", "Name", "New", "Common", "Rare", "Sticker",
    "Bonus", "Effect", "Tuning", "Trophy", "Insider", "Channel", "Zone", "Purchase",
    "Glider", "Normal", "Hold", "Release", "Jump", "Gather", "Deploy", "Research",
    "Instructions", "Notice", "Malee", "None", "Supplies", "Amount", "Photo",
}

WORD_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9'./&+-]*\b")


def is_numeric_or_token_only(text: str) -> bool:
    text = text.strip()
    return bool(re.fullmatch(r"[\d\s{}:._%#+/-]+", text))


def actionable_reason(row: dict) -> str | None:
    issues = row.get("issues", [])
    source = str(row.get("source_en") or "").strip()
    target = str(row.get("new_translation_vi") or "").strip()

    for issue in issues:
        if issue.startswith(ALWAYS_ACTIONABLE_PREFIXES):
            return issue

    if "empty_translation" in issues:
        return "empty_translation"

    if "same_as_source" in issues:
        if is_numeric_or_token_only(target):
            return None
        if target in ALLOWED_SAME_SOURCE_TERMS:
            return None
        if source in TRANSLATABLE_EXACT:
            return "same_as_source_translatable_ui"
        if len(source.split()) >= 3 and not re.search(r"\b[A-Z][a-z]+(?:[- ][A-Z][a-z]+)+\b", source):
            return "same_as_source_sentence_like"
        return None

    if "english_or_untranslated_short_text" in issues:
        if target == source and target not in ALLOWED_SAME_SOURCE_TERMS:
            return "english_or_untranslated_short_text"
        words = set(WORD_RE.findall(target))
        if words & MIXED_CLEAR_WORDS:
            return "english_ui_word_in_short_translation:" + ",".join(sorted(words & MIXED_CLEAR_WORDS))
        return None

    for issue in issues:
        if issue.startswith("mixed_language_suspicious_words:"):
            words = set(issue.split(":", 1)[1].split(","))
            hit = words & MIXED_CLEAR_WORDS
            if hit:
                return "mixed_language_clear_ui_words:" + ",".join(sorted(hit))

    for issue in issues:
        if issue.startswith("mixed_language_other_words:"):
            words = set(issue.split(":", 1)[1].split(","))
            hit = words & MIXED_CLEAR_WORDS
            if hit:
                return "mixed_language_clear_other_words:" + ",".join(sorted(hit))

    return None


def severity_for(reason: str, original: str) -> str:
    if reason.startswith(("placeholder", "tag_", "control", "possible_mojibake", "broken_term", "translated_input_tag", "literal_none", "known_machine", "coarse")):
        return "high"
    if reason.startswith("same_as_source"):
        return "medium"
    if original == "high":
        return "medium"
    return original


def main() -> None:
    full = json.loads(FULL_PATH.read_text(encoding="utf-8"))
    actionable = []
    reason_counts = Counter()
    severity_counts = Counter()
    domain_counts = Counter()

    for row in full:
        reason = actionable_reason(row)
        if not reason:
            continue
        out = dict(row)
        out["actionable_reason"] = reason
        out["severity"] = severity_for(reason, row.get("severity", "low"))
        actionable.append(out)
        reason_counts[reason] += 1
        severity_counts[out["severity"]] += 1
        domain_counts[out.get("domain", "")] += 1

    actionable.sort(key=lambda r: ({"high": 0, "medium": 1, "low": 2}.get(r["severity"], 9), r["domain"], r["json_file"], str(r["primary_key"])))
    ACTIONABLE_JSON.write_text(json.dumps(actionable, ensure_ascii=False, indent=2), encoding="utf-8")

    fields = [
        "severity", "actionable_reason", "domain", "json_file", "json_index", "split_id",
        "database", "table", "primary_key_column", "primary_key", "column",
        "issues", "source_en", "new_translation_vi",
    ]
    with ACTIONABLE_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in actionable:
            out = {k: row.get(k, "") for k in fields}
            out["issues"] = " | ".join(row.get("issues", []))
            writer.writerow(out)

    summary = {
        "actionable_suspect_rows": len(actionable),
        "severity_counts": dict(severity_counts),
        "domain_counts": dict(domain_counts),
        "reason_counts": dict(reason_counts.most_common(100)),
        "source_full_report": str(FULL_PATH),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
