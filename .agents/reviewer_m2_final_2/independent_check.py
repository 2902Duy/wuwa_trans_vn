import os
import json
import re
import pandas as pd
from pathlib import Path

# Paths
ui_dir = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui"
glossary_path = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\ui_translation_pack\shared_glossary.md"
excel_path = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\ui_translation_pack\ui_all.xlsx"
report_path = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\.agents\reviewer_m2_final_2\independent_audit_report.json"

def load_proper_nouns():
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

    proper_nouns = []
    for t in terms:
        if t and t not in proper_nouns:
            if "/" in t or "[" in t or "{" in t or "<" in t:
                continue
            proper_nouns.append(t)

    proper_nouns.sort(key=len, reverse=True)
    return proper_nouns

def run_independent_checks():
    proper_nouns = load_proper_nouns()
    print(f"Loaded {len(proper_nouns)} proper nouns from glossary.")
    
    blacklist_translations = [
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
    
    action_verbs_pattern = re.compile(r"\b(Increase|Decrease|Claim|Exchange|Return)\b", re.IGNORECASE)
    weapon_pattern = re.compile(r"\bweapons?\b", re.IGNORECASE)
    
    violations = []
    total_records = 0
    json_records_by_id = {}
    
    # 1. Check UI JSON files
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
                        total_records += 1
                        split_id = item.get("split_id")
                        source_en = item.get("source_en", "")
                        translation_vi = item.get("new_translation_vi", "")
                        table = item.get("table", "")
                        pk = str(item.get("primary_key", ""))
                        source_file = item.get("source_file", "")
                        
                        if not split_id:
                            continue
                            
                        json_records_by_id[split_id] = item
                        
                        if not translation_vi:
                            continue
                            
                        # Check Keep English Rules
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
                            if translation_vi != source_en:
                                violations.append({
                                    "split_id": split_id,
                                    "file": rel_path,
                                    "type": "Keep English Key Rule Violation",
                                    "source": source_en,
                                    "translation": translation_vi,
                                    "detail": f"Translation differs from source under keep English key rule."
                                })
                                continue
                        
                        # Check proper nouns
                        for noun in proper_nouns:
                            if len(noun) <= 4:
                                noun_pattern = re.compile(rf"\b{re.escape(noun)}\b")
                            else:
                                noun_pattern = re.compile(re.escape(noun))
                                
                            if noun_pattern.search(source_en):
                                if noun not in translation_vi:
                                    if noun.lower() in translation_vi.lower():
                                        violations.append({
                                            "split_id": split_id,
                                            "file": rel_path,
                                            "type": "Casing Violation",
                                            "source": source_en,
                                            "translation": translation_vi,
                                            "detail": f"Proper noun '{noun}' casing is not preserved in translation."
                                        })
                                    else:
                                        violations.append({
                                            "split_id": split_id,
                                            "file": rel_path,
                                            "type": "Glossary Translation Violation",
                                            "source": source_en,
                                            "translation": translation_vi,
                                            "detail": f"Proper noun '{noun}' is missing or translated in translation."
                                        })
                                        
                        # Check blacklisted translations
                        for eng, wrong_vi in blacklist_translations:
                            if wrong_vi.lower() in translation_vi.lower():
                                if eng.lower() in source_en.lower():
                                    violations.append({
                                        "split_id": split_id,
                                        "file": rel_path,
                                        "type": "Blacklisted Translation",
                                        "source": source_en,
                                        "translation": translation_vi,
                                        "detail": f"Incorrect translation '{wrong_vi}' used for '{eng}'."
                                    })
                                    
                        # Placeholders check
                        source_placeholders = re.findall(r"\{[^\}]+\}", source_en)
                        trans_placeholders = re.findall(r"\{[^\}]+\}", translation_vi)
                        
                        source_ph_counts = {}
                        for ph in source_placeholders:
                            source_ph_counts[ph] = source_ph_counts.get(ph, 0) + 1
                            
                        trans_ph_counts = {}
                        for ph in trans_placeholders:
                            trans_ph_counts[ph] = trans_ph_counts.get(ph, 0) + 1
                            
                        if source_ph_counts != trans_ph_counts:
                            violations.append({
                                "split_id": split_id,
                                "file": rel_path,
                                "type": "Placeholder Mismatch",
                                "source": source_en,
                                "translation": translation_vi,
                                "detail": f"Placeholders mismatch: Source {list(source_ph_counts.keys())} vs Translation {list(trans_ph_counts.keys())}."
                            })
                            
                        # Rich text tags check
                        source_tags = re.findall(r"<[^>]+>", source_en)
                        trans_tags = re.findall(r"<[^>]+>", translation_vi)
                        
                        for tag in source_tags:
                            if tag not in trans_tags:
                                violations.append({
                                    "split_id": split_id,
                                    "file": rel_path,
                                    "type": "Tag Mismatch",
                                    "source": source_en,
                                    "translation": translation_vi,
                                    "detail": f"Rich text tag '{tag}' from source is missing or modified."
                                })
                                
                        # Unbalanced tags check
                        opening_tags = [t for t in trans_tags if not t.startswith("</") and not t.endswith("/>")]
                        closing_tags = [t for t in trans_tags if t.startswith("</")]
                        def get_tag_name(t):
                            match = re.match(r"<([a-zA-Z]+)", t)
                            return match.group(1) if match else t
                        opening_names = [get_tag_name(t) for t in opening_tags]
                        closing_names = [t[2:-1] for t in closing_tags]
                        
                        for name in set(opening_names):
                            if name in ["color", "size", "te", "SapTag"]:
                                op_count = opening_names.count(name)
                                cl_count = closing_names.count(name)
                                if op_count != cl_count:
                                    violations.append({
                                        "split_id": split_id,
                                        "file": rel_path,
                                        "type": "Tag Unbalanced",
                                        "source": source_en,
                                        "translation": translation_vi,
                                        "detail": f"Tag '{name}' is unbalanced: {op_count} opening vs {cl_count} closing."
                                    })
                                    
                        # Newlines check
                        source_newlines = source_en.count("\\n") + source_en.count("\n")
                        trans_newlines = translation_vi.count("\\n") + translation_vi.count("\n")
                        if source_newlines != trans_newlines:
                            violations.append({
                                "split_id": split_id,
                                "file": rel_path,
                                "type": "Newline Mismatch",
                                "source": source_en,
                                "translation": translation_vi,
                                "detail": f"Newline count mismatch: Source has {source_newlines}, translation has {trans_newlines}."
                            })
                            
                        # Untranslated action verbs
                        trans_clean = re.sub(r"\{[^\}]+\}", "", translation_vi)
                        trans_clean = re.sub(r"<[^>]+>", "", trans_clean)
                        verb_matches = action_verbs_pattern.findall(trans_clean)
                        if verb_matches:
                            source_clean = re.sub(r"\{[^\}]+\}", "", source_en)
                            source_clean = re.sub(r"<[^>]+>", "", source_clean)
                            source_verbs = action_verbs_pattern.findall(source_clean)
                            violating_verbs = [v for v in verb_matches if any(sv.lower() == v.lower() for sv in source_verbs)]
                            if violating_verbs:
                                violations.append({
                                    "split_id": split_id,
                                    "file": rel_path,
                                    "type": "Untranslated Action Verb",
                                    "source": source_en,
                                    "translation": translation_vi,
                                    "detail": f"Action verbs {list(set(violating_verbs))} were left untranslated."
                                })
                                
                        # Untranslated weapon words
                        weapon_matches = weapon_pattern.findall(trans_clean)
                        if weapon_matches:
                            if weapon_pattern.search(source_en):
                                violations.append({
                                    "split_id": split_id,
                                    "file": rel_path,
                                    "type": "Untranslated Weapon Word",
                                    "source": source_en,
                                    "translation": translation_vi,
                                    "detail": f"Isolated or general word 'Weapon(s)' was left untranslated."
                                })

    # 2. Check Excel consistency
    excel_mismatches = []
    excel_missing_ids = []
    
    if os.path.exists(excel_path):
        try:
            df = pd.read_excel(excel_path, dtype=str, keep_default_na=False)
            excel_ids = set(df['split_id'].tolist())
            json_ids = set(json_records_by_id.keys())
            
            missing_in_excel = json_ids - excel_ids
            missing_in_json = excel_ids - json_ids
            
            for mid in missing_in_excel:
                excel_missing_ids.append({
                    "split_id": mid,
                    "direction": "in JSON but missing in Excel"
                })
            for mid in missing_in_json:
                excel_missing_ids.append({
                    "split_id": mid,
                    "direction": "in Excel but missing in JSON"
                })
                
            expected_cols = [
                'split_id', 'prompt_domain', 'prompt_file', 'source_file',
                'original_index', 'database', 'table', 'primary_key_column',
                'primary_key', 'column', 'category', 'source_en',
                'new_translation_vi', 'translator_note'
            ]
            
            for idx, row in df.iterrows():
                split_id = row['split_id']
                if not split_id or split_id not in json_records_by_id:
                    continue
                json_item = json_records_by_id[split_id]
                for col in expected_cols:
                    excel_val = str(row.get(col, "")).strip()
                    json_val = str(json_item.get(col, "")).strip()
                    
                    # Normalization
                    excel_val_norm = excel_val.replace('\r\n', '\n').replace('\r', '\n')
                    json_val_norm = json_val.replace('\r\n', '\n').replace('\r', '\n')
                    
                    if excel_val_norm != json_val_norm:
                        excel_mismatches.append({
                            "split_id": split_id,
                            "column": col,
                            "excel_val": excel_val,
                            "json_val": json_val
                        })
        except Exception as e:
            print(f"Error checking Excel: {e}")
            excel_mismatches.append({"error": str(e)})
    else:
        excel_mismatches.append({"error": "Excel file not found"})

    report = {
        "total_json_records": total_records,
        "violations": violations,
        "violations_count": len(violations),
        "excel_mismatches": excel_mismatches,
        "excel_mismatches_count": len(excel_mismatches),
        "excel_missing_ids": excel_missing_ids,
        "excel_missing_count": len(excel_missing_ids)
    }
    
    with open(report_path, "w", encoding="utf-8") as rf:
        json.dump(report, rf, ensure_ascii=False, indent=2)
        
    print(f"Independent audit report written to {report_path}")
    print(f"Total violations: {len(violations)}")
    print(f"Total Excel cell mismatches: {len(excel_mismatches)}")
    print(f"Total Excel missing IDs: {len(excel_missing_ids)}")

if __name__ == "__main__":
    run_independent_checks()
