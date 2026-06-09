import os
import json
import re

# Paths
ui_dir = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui"
glossary_path = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\ui_translation_pack\shared_glossary.md"

# 1. Parse Glossary Terms
with open(glossary_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

terms = []
in_section = False
for line in lines:
    if "## THUẬT NGỮ BẮT BUỘC GIỮ NGUYÊN TIẾNG ANH" in line:
        in_section = True
        continue
    if "## Ví dụ về các dịch sai cần tránh" in line:
        in_section = False
        break
    if in_section:
        if "->" in line:
            continue
        found = re.findall(r"`([^`]+)`", line)
        for term in found:
            if "," in term:
                subterms = [t.strip() for t in term.split(",")]
                terms.extend(subterms)
            else:
                terms.append(term.strip())

# Clean proper noun terms
proper_nouns = []
for t in terms:
    if t and t not in proper_nouns:
        if "/" in t or "[" in t or "{" in t or "<" in t:
            continue
        proper_nouns.append(t)

# Sort proper nouns by length descending so we match longer ones first (e.g. "Resonance Skill" before "Resonance")
proper_nouns.sort(key=len, reverse=True)

# 2. Blacklisted Vietnamese Translations
blacklist_translations = [
    # (English Term, Wrong Vietnamese Translation)
    ("Echo", "Tiếng Vang"), ("Echo", "Linh Thú"),
    ("Rover", "Nhà Lữ Hành"), ("Rover", "Vãng Minh Giả"), ("Rover", "Viễn Khách"),
    ("Resonator", "Người Cộng Hưởng"), ("Resonator", "Cộng Hưởng Giả"),
    ("Resonance Skill", "Kỹ Năng Cộng Hưởng"), ("Resonance Skill", "Chiêu Thức Cộng Hưởng"),
    ("Resonance Liberation", "Giải Phóng Cộng Hưởng"), ("Resonance Liberation", "Nộ"),
    ("Forte Circuit", "Mạch Forte"), ("Forte Circuit", "Chuỗi Forte"),
    ("Basic Attack", "Tấn Công Thường"), ("Basic Attack", "Tấn Công Cơ Bản"),
    ("Heavy Attack", "Trọng Kích"), ("Heavy Attack", "Tấn Công Nặng"),
    ("Cooldown", "Hồi Chiêu"), ("Cooldown", "Thời gian hồi"),
    ("Spectro Frazzle", "Nhiễu Loạn Quang Phổ"),
    ("Aero Erosion", "Xói Mòn Gió"),
    ("Glacio Chafe", "Trầy Băng Giá"),
    ("Fusion Burst", "Nổ Nhiệt Hạch"),
    ("Havoc Bane", "Tai Họa Hỗn Loạn"),
    ("Electro Flare", "Điện Tích"), ("Electro Flare", "Bùng Điện"),
    ("Jinzhou", "Kim Châu"),
    ("Mt. Firmament", "Núi Vòm Trời"), ("Mt. Firmament", "Trầm Minh Khánh"),
    ("Emerald of Genesis", "Ngọc Lục Bảo Khởi Nguyên"),
    ("Impermanence Heron", "Vịt Bất Diệt")
]

# Action verbs and weapons patterns
action_verbs_pattern = re.compile(r"\b(Increase|Decrease|Claim|Exchange|Return)\b", re.IGNORECASE)
weapon_pattern = re.compile(r"\bweapons?\b", re.IGNORECASE)

violations = []

for root, dirs, files in os.walk(ui_dir):
    for f in files:
        if f.endswith(".json"):
            path = os.path.join(root, f)
            rel_path = os.path.relpath(path, ui_dir)
            with open(path, "r", encoding="utf-8") as file:
                try:
                    data = json.load(file)
                except Exception as e:
                    print(f"Error reading {rel_path}: {e}")
                    continue
                
                for item in data:
                    split_id = item.get("split_id")
                    source_en = item.get("source_en", "")
                    translation_vi = item.get("new_translation_vi", "")
                    table = item.get("table", "")
                    pk = str(item.get("primary_key", ""))
                    source_file = item.get("source_file", "")
                    
                    if not translation_vi:
                        continue # Skip empty translations
                    
                    # --- CHECK 1: Proper Noun Casing & Preservation ---
                    for noun in proper_nouns:
                        # Use word boundaries or simple presence checks
                        # For short terms like "STA", "HP", "ATK", "DEF", use word boundaries
                        if len(noun) <= 4:
                            noun_pattern = re.compile(rf"\b{re.escape(noun)}\b")
                        else:
                            noun_pattern = re.compile(re.escape(noun))
                        
                        if noun_pattern.search(source_en):
                            # Noun exists in source. Does it exist exactly (case-sensitive) in translation?
                            if noun not in translation_vi:
                                # Check if it exists case-insensitively (casing violation) or not at all (translated violation)
                                if noun.lower() in translation_vi.lower():
                                    violations.append({
                                        "file": rel_path,
                                        "split_id": split_id,
                                        "source": source_en,
                                        "translation": translation_vi,
                                        "type": "Casing Violation",
                                        "detail": f"Proper noun '{noun}' casing is not preserved in translation."
                                    })
                                else:
                                    violations.append({
                                        "file": rel_path,
                                        "split_id": split_id,
                                        "source": source_en,
                                        "translation": translation_vi,
                                        "type": "Glossary Translation Violation",
                                        "detail": f"Proper noun '{noun}' is missing (translated or modified) in translation."
                                    })
                    
                    # --- CHECK 2: Blacklisted Vietnamese Terms ---
                    for eng, wrong_vi in blacklist_translations:
                        if wrong_vi.lower() in translation_vi.lower():
                            # Double check if English word was in source to confirm context
                            if eng.lower() in source_en.lower():
                                violations.append({
                                    "file": rel_path,
                                    "split_id": split_id,
                                    "source": source_en,
                                    "translation": translation_vi,
                                    "type": "Blacklisted Translation",
                                    "detail": f"Incorrect translation '{wrong_vi}' used for '{eng}'."
                                })
                    
                    # --- CHECK 3: Keep English Rules from key patterns ---
                    is_keep_english_key = False
                    if pk.startswith("ResonantChain_") and pk.endswith("_NodeName"):
                        is_keep_english_key = True
                    elif "_SkillName" in pk:
                        is_keep_english_key = True
                    elif pk.startswith("RoleSkillTreeInfo_") and pk.endswith("_Title"):
                        is_keep_english_key = True
                    elif table == "Skill" and source_file == "lang_skill.json":
                        is_keep_english_key = True
                    elif table == "RoleSkillTreeInfo" and source_file == "lang_skillTree.json":
                        is_keep_english_key = True
                    
                    if is_keep_english_key:
                        # For these, translation must equal source exactly
                        if translation_vi != source_en:
                            violations.append({
                                "file": rel_path,
                                "split_id": split_id,
                                "source": source_en,
                                "translation": translation_vi,
                                "type": "Keep English Key Rule Violation",
                                "detail": f"Key rule requires translation to match source exactly, but they differ."
                            })
                    
                    # --- CHECK 4: Placeholders and Rich Text Tags ---
                    # Extract placeholders {...}
                    source_placeholders = re.findall(r"\{[^\}]+\}", source_en)
                    trans_placeholders = re.findall(r"\{[^\}]+\}", translation_vi)
                    
                    # Verify placeholder counts and exact matches
                    source_ph_counts = {}
                    for ph in source_placeholders:
                        source_ph_counts[ph] = source_ph_counts.get(ph, 0) + 1
                        
                    trans_ph_counts = {}
                    for ph in trans_placeholders:
                        trans_ph_counts[ph] = trans_ph_counts.get(ph, 0) + 1
                        
                    if source_ph_counts != trans_ph_counts:
                        violations.append({
                            "file": rel_path,
                            "split_id": split_id,
                            "source": source_en,
                            "translation": translation_vi,
                            "type": "Placeholder Mismatch",
                            "detail": f"Source placeholders {list(source_ph_counts.keys())} vs Translation {list(trans_ph_counts.keys())}."
                        })
                    
                    # Extract Rich Text tags <...>
                    source_tags = re.findall(r"<[^>]+>", source_en)
                    trans_tags = re.findall(r"<[^>]+>", translation_vi)
                    
                    # Verify tags exactly (attribute values, spelling, capitalization)
                    # To check if all tags in source exist in translation
                    for tag in source_tags:
                        if tag not in trans_tags:
                            violations.append({
                                "file": rel_path,
                                "split_id": split_id,
                                "source": source_en,
                                "translation": translation_vi,
                                "type": "Tag Mismatch",
                                "detail": f"Rich text tag '{tag}' from source is missing or modified in translation."
                            })
                    
                    # Verify tag opening/closing balance
                    # Simple check for balanced tags
                    opening_tags = [t for t in trans_tags if not t.startswith("</") and not t.endswith("/>")]
                    closing_tags = [t for t in trans_tags if t.startswith("</")]
                    # Map opening tag name
                    def get_tag_name(t):
                        # E.g. <color=#ffffff> -> color
                        match = re.match(r"<([a-zA-Z]+)", t)
                        return match.group(1) if match else t
                    
                    opening_names = [get_tag_name(t) for t in opening_tags]
                    closing_names = [t[2:-1] for t in closing_tags]
                    
                    for name in set(opening_names):
                        # Filter standard styling tags like color, size, size, te, SapTag
                        if name in ["color", "size", "te", "SapTag"]:
                            op_count = opening_names.count(name)
                            cl_count = closing_names.count(name)
                            if op_count != cl_count:
                                violations.append({
                                    "file": rel_path,
                                    "split_id": split_id,
                                    "source": source_en,
                                    "translation": translation_vi,
                                    "type": "Tag Unbalanced",
                                    "detail": f"Tag '{name}' is unbalanced: {op_count} opening vs {cl_count} closing."
                                })
                                
                    # Newline count verification
                    source_newlines = source_en.count("\\n") + source_en.count("\n")
                    trans_newlines = translation_vi.count("\\n") + translation_vi.count("\n")
                    if source_newlines != trans_newlines:
                        violations.append({
                            "file": rel_path,
                            "split_id": split_id,
                            "source": source_en,
                            "translation": translation_vi,
                            "type": "Newline Mismatch",
                            "detail": f"Source has {source_newlines} newlines, translation has {trans_newlines}."
                        })
                    
                    # --- CHECK 5: Untranslated Action Verbs ---
                    # Check for English action verbs in translation
                    trans_clean = re.sub(r"\{[^\}]+\}", "", translation_vi) # remove placeholders
                    trans_clean = re.sub(r"<[^>]+>", "", trans_clean)       # remove tags
                    
                    verb_matches = action_verbs_pattern.findall(trans_clean)
                    if verb_matches:
                        # Only flag if the verb was also in the source (indicating it was left untranslated)
                        source_clean = re.sub(r"\{[^\}]+\}", "", source_en)
                        source_clean = re.sub(r"<[^>]+>", "", source_clean)
                        source_verbs = action_verbs_pattern.findall(source_clean)
                        
                        violating_verbs = [v for v in verb_matches if any(sv.lower() == v.lower() for sv in source_verbs)]
                        if violating_verbs:
                            violations.append({
                                "file": rel_path,
                                "split_id": split_id,
                                "source": source_en,
                                "translation": translation_vi,
                                "type": "Untranslated Action Verb",
                                "detail": f"Action verbs {list(set(violating_verbs))} were left untranslated."
                            })
                    
                    # --- CHECK 6: Standalone / Isolated Weapon Word ---
                    # Check if 'weapon' or 'weapons' is in translation
                    weapon_matches = weapon_pattern.findall(trans_clean)
                    if weapon_matches:
                        # Verify it was in source as well
                        if weapon_pattern.search(source_en):
                            violations.append({
                                "file": rel_path,
                                "split_id": split_id,
                                "source": source_en,
                                "translation": translation_vi,
                                "type": "Untranslated Weapon Word",
                                "detail": f"Isolated or general word 'Weapon(s)' was left untranslated."
                            })

# Output results
import sys
sys.stdout.reconfigure(encoding='utf-8')
print(f"Total violations found: {len(violations)}")
# Deduplicate violations based on (split_id, type)
unique_violations = {}
for v in violations:
    key = (v["split_id"], v["type"])
    if key not in unique_violations:
        unique_violations[key] = v

print(f"Unique violations count: {len(unique_violations)}")

# Write to a report file inside explorer_m1
with open("violations_report.json", "w", encoding="utf-8") as out:
    json.dump(list(unique_violations.values()), out, ensure_ascii=False, indent=2)

# Print first 15 violations as sample
print("\n--- SAMPLE VIOLATIONS ---")
count = 0
for v in unique_violations.values():
    print(f"File: {v['file']}")
    print(f"Split ID: {v['split_id']}")
    print(f"Source: {v['source']}")
    print(f"Translation: {v['translation']}")
    print(f"Type: {v['type']}")
    print(f"Detail: {v['detail']}")
    print("-" * 50)
    count += 1
    if count >= 15:
        break
