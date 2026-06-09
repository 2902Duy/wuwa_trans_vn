import json
import os
import re
from pathlib import Path

IN_FILE = "new_strings_classified.json"
JSON_ROOT = Path("mistral_translate_work/split_by_prompt/json")
PART_SIZE = 2000

PROMPT_MAP = {
    "story_dialogue_prompt": "story_dialogue",
    "quest_prompt": "quest",
    "ui_prompt": "ui",
    "lore_prompt": "lore",
    "skill_description_prompt": "skill_description",
    "name_title_prompt": "name_title",
    "item_prompt": "item",
    "weapon_prompt": "weapon",
    "rc_description_prompt": "rc_description",
    "monster_description_prompt": "monster_description",
    "echo_set_prompt": "echo_set",
    "phantom_skill_prompt": "phantom_skill"
}

def load_classified():
    with open(IN_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_split_id_prefix(domain):
    return domain.upper() + "_"

def main():
    data = load_classified()
    classified_list = data.get("classified", [])
    
    total_added = 0
    total_updated = 0
    
    for category_data in classified_list:
        prompt = category_data["prompt"]
        if prompt == "keep_english":
            print("Skipping keep_english prompt strings")
            continue
            
        domain = PROMPT_MAP.get(prompt)
        if not domain:
            print(f"Unknown prompt category: {prompt}, skipping")
            continue
            
        strings = category_data.get("strings", [])
        if not strings:
            continue
            
        print(f"\nProcessing domain: {domain} ({len(strings)} strings)")
        
        # Target directory
        target_dir = JSON_ROOT / domain / "lang_multi_text"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Find all parts
        part_files = sorted(list(target_dir.glob("lang_multi_text__*.json")))
        
        existing_keys = {} # primary_key -> (part_file_path, index_in_file)
        max_num = 0
        all_part_data = {} # part_file_path -> list of rows
        
        for p_file in part_files:
            try:
                rows = json.loads(p_file.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"Error reading {p_file}: {e}")
                rows = []
            all_part_data[p_file] = rows
            
            for idx, row in enumerate(rows):
                pk = row.get("primary_key")
                if pk:
                    existing_keys[pk] = (p_file, idx)
                
                sid = row.get("split_id", "")
                m = re.search(r"_(\d+)$", sid)
                if m:
                    num = int(m.group(1))
                    if num > max_num:
                        max_num = num
        
        prefix = get_split_id_prefix(domain)
        new_rows = []
        changed_parts = set()
        
        for s in strings:
            pk = s["id"]
            if pk in existing_keys:
                if s["type"] == "CHANGED":
                    p_file, idx = existing_keys[pk]
                    row = all_part_data[p_file][idx]
                    
                    # Update fields
                    row["source_en"] = s["new_english"]
                    row["new_translation_vi"] = None
                    row["status"] = "untranslated"
                    row["issues"] = ""
                    row["rule_decision"] = ""
                    row["rule_score"] = ""
                    row["rule_issues"] = ""
                    row["ai_decision"] = ""
                    row["ai_score"] = ""
                    row["ai_reason"] = ""
                    
                    changed_parts.add(p_file)
                    total_updated += 1
            else:
                # Brand new string in split files
                max_num += 1
                sid = f"{prefix}{max_num:07d}"
                
                english_text = s["english"] if s["type"] == "NEW" else s["new_english"]
                
                new_row = {
                    "split_id": sid,
                    "source_file": "lang_multi_text.json",
                    "original_index": -1,
                    "prompt_domain": domain,
                    "prompt_file": f"{domain}_prompt.md",
                    "database": "lang_multi_text.db",
                    "table": "MultiText",
                    "primary_key_column": "Id",
                    "primary_key": pk,
                    "column": "Content",
                    "category": "dialogue",
                    "status": "untranslated",
                    "issues": "",
                    "rule_decision": "",
                    "rule_score": "",
                    "rule_issues": "",
                    "ai_decision": "",
                    "ai_score": "",
                    "ai_reason": "",
                    "source_en": english_text,
                    "review_note": "",
                    "new_translation_vi": None,
                    "translator_note": ""
                }
                new_rows.append(new_row)
                total_added += 1
                
        # Write modified existing parts
        for p_file in changed_parts:
            rows = all_part_data[p_file]
            p_file.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"  Updated changed keys in {p_file.name}")
            
        # Append new rows to parts
        if new_rows:
            # Check the last part file if we can fit some rows in it
            last_part_file = part_files[-1] if part_files else None
            if last_part_file:
                last_rows = all_part_data[last_part_file]
                space_left = PART_SIZE - len(last_rows)
                if space_left > 0:
                    rows_to_add = new_rows[:space_left]
                    last_rows.extend(rows_to_add)
                    last_part_file.write_text(json.dumps(last_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    print(f"  Added {len(rows_to_add)} new rows to last file {last_part_file.name}")
                    new_rows = new_rows[space_left:]
            
            # Write remaining new rows in new part files
            part_index = len(part_files)
            if not last_part_file or PART_SIZE - len(all_part_data[last_part_file]) <= 0:
                part_index += 1
                
            for start in range(0, len(new_rows), PART_SIZE):
                chunk = new_rows[start : start + PART_SIZE]
                new_file_name = f"lang_multi_text__{domain}__part_{part_index:04d}.json"
                new_file_path = target_dir / new_file_name
                new_file_path.write_text(json.dumps(chunk, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(f"  Created new part file {new_file_name} with {len(chunk)} rows")
                part_index += 1

    print(f"\nDone! Added {total_added} new strings, updated {total_updated} changed strings in split JSON files.")

if __name__ == "__main__":
    main()
