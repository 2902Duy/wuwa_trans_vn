"""
fix_targeted_violations.py
============================
Fix chỉ các vi phạm thực sự sai:
1. Tên quái/monster/status effect bị dịch sang tiếng Việt -> khôi phục tiếng Anh
2. {0} placeholder bị mất -> thêm lại từ source
"""
import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path

WORKSPACE = Path(r"C:\Users\tduy2\Documents\antigravity\silly-darwin")
UI_DIR = WORKSPACE / "mistral_translate_work" / "split_by_prompt" / "json" / "ui"
VIOLATIONS_FILE = WORKSPACE / ".agents" / "explorer_m1" / "violations_report.json"

# Load system_text terms (all monster/boss names) as keep-english source
sysdir = WORKSPACE / "mistral_translate_work" / "split_by_prompt" / "json" / "system_text"
MONSTER_NAMES = set()
for f in sysdir.rglob("*.json"):
    for row in json.loads(f.read_text(encoding="utf-8")):
        src = row.get("source_en", "").strip()
        if src:
            MONSTER_NAMES.add(src)

# Additional terms that must stay English (status effects, skill names)
MUST_KEEP_EN = MONSTER_NAMES | {
    "Frozen", "Burning", "Electrocuted", "Drowned", "Confused",
    "Weakened", "Stunned", "Silenced", "Rooted",
    "Outro Skill", "Intro Skill", "Resonance Skill", "Resonance Liberation",
    "Basic Attack", "Heavy Attack", "Normal Attack", "Dodge Counter",
    "Forte Circuit", "Concerto Energy", "Resonance Chain", "Inherent Skill",
    "Echo Skill", "Mid-air Attack",
}

# Load violations
violations = json.loads(VIOLATIONS_FILE.read_text(encoding="utf-8"))
glossary_viols = [v for v in violations if "Glossary" in v.get("type","")]
placeholder_viols = [v for v in violations if "Placeholder" in v.get("type","")]

print(f"Glossary violations: {len(glossary_viols)}")
print(f"Placeholder violations: {len(placeholder_viols)}")

# Load all UI JSON files
all_files = {}
for f in sorted(UI_DIR.rglob("*.json")):
    all_files[f.name] = (f, json.loads(f.read_text(encoding="utf-8")))

# Build split_id lookup across UI files
lookup = {}
for fname, (fpath, rows) in all_files.items():
    for idx, row in enumerate(rows):
        sid = row.get("split_id", "")
        if sid:
            lookup[sid] = (fpath, fname, idx)

fixed_glossary = 0
fixed_placeholder = 0
skip_glossary = 0

# Fix 1: Glossary - restore English for actual monster/boss/status names
for v in glossary_viols:
    sid = v["split_id"]
    source = v.get("source", "")

    # Only restore if the SOURCE is a known monster name or status effect
    # Skip location names, descriptions, etc.
    if source not in MUST_KEEP_EN:
        skip_glossary += 1
        continue

    if sid not in lookup:
        continue

    fpath, fname, idx = lookup[sid]
    rows = all_files[fname][1]
    if rows[idx].get("new_translation_vi", "") != source:
        rows[idx]["new_translation_vi"] = source
        rows[idx]["status"] = "keep_english"
        fixed_glossary += 1
        print(f"  [RESTORE] {sid}: '{v.get('translation','')[:40]}' -> '{source}'")

# Fix 2: Placeholder - restore missing {0} from source
for v in placeholder_viols:
    sid = v["split_id"]
    source = v.get("source", "")
    if sid not in lookup:
        continue
    fpath, fname, idx = lookup[sid]
    rows = all_files[fname][1]
    vi = rows[idx].get("new_translation_vi", "")

    # Find {0} or {number} in source but missing in translation
    src_placeholders = re.findall(r"\{(\d+)\}", source)
    for ph in src_placeholders:
        placeholder = "{" + ph + "}"
        if placeholder not in vi:
            vi = vi.rstrip() + "\n" + placeholder
            rows[idx]["new_translation_vi"] = vi
            fixed_placeholder += 1
            print(f"  [PLACEHOLDER] {sid}: added {placeholder}")

# Write back
for fname, (fpath, rows) in all_files.items():
    fpath.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n✅ Done!")
print(f"  Glossary restored: {fixed_glossary}")
print(f"  Glossary skipped (location/description - OK as translated): {skip_glossary}")
print(f"  Placeholder fixed: {fixed_placeholder}")
