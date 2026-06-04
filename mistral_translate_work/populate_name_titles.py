import json
import glob
from pathlib import Path
import sys

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    workspace = Path(r"C:\Users\tduy2\Documents\antigravity\silly-darwin")
    report_dir = workspace / "mistral_translate_work" / "reports" / "split_name_title_classification"
    name_title_dir = workspace / "mistral_translate_work" / "split_by_prompt" / "json" / "name_title"
    cache_path = workspace / "mistral_translate_work" / "cache_mistral.json"
    
    print("Loading master cache...")
    with open(cache_path, "r", encoding="utf-8") as f:
        master_cache = json.load(f)
    print(f"Loaded master cache with {len(master_cache)} entries.")
    
    # Load classification reports
    print("Loading classifications...")
    split_id_to_class = {}
    report_files = glob.glob(str(report_dir / "*.json"))
    for f in report_files:
        f_path = Path(f)
        if f_path.name in ["all_rows.json", "summary.json"]:
            continue
        classification = f_path.stem
        # Normalize name for ambiguity
        if classification == "translate_ambiguous_name_title":
            classification = "manual_review_name_title"
            
        with open(f_path, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
                rows = data.get("rows", []) if isinstance(data, dict) else data
                for r in rows:
                    sid = r.get("split_id")
                    if sid:
                        split_id_to_class[sid] = classification
            except Exception as e:
                print(f"Error loading {f_path.name}: {e}")
                
    print(f"Mapped {len(split_id_to_class)} split IDs to classifications.")
    
    # 9 Known mismatch corrections
    mismatch_corrections = {
        "NAME_TITLE_0044607": "Người chơi hoàn thành 75%~100% đường đua",
        "NAME_TITLE_0044608": "Người chơi không hoàn thành cuộc đua",
        "NAME_TITLE_0052374": "Nhân vật không thể trao đổi.",
        "NAME_TITLE_0052474": "Nhân vật bị khóa vì lý do khác.",
        "NAME_TITLE_0052508": "Nhân vật đang bị khóa.",
        "NAME_TITLE_0052585": "Nhân vật bị khóa trong đội hình.",
        "NAME_TITLE_0052659": "Nhân vật bị khóa do đang ghép trận.",
        "NAME_TITLE_0053520": "Đã triển khai nhân vật",
        "NAME_TITLE_0053529": "Chưa thêm nhân vật"
    }
    
    # Find split files
    name_title_files = glob.glob(str(name_title_dir / "**" / "*.json"), recursive=True)
    print(f"Found {len(name_title_files)} split JSON files to update.")
    
    total_processed = 0
    kept_count = 0
    translated_count = 0
    fixed_mismatch_count = 0
    
    for f_path in name_title_files:
        modified = False
        with open(f_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"Error reading {f_path}: {e}")
                continue
                
        for row in data:
            total_processed += 1
            sid = row.get("split_id")
            src = row.get("source_en", "")
            
            # Map classification
            mapped_class = split_id_to_class.get(sid)
            if not mapped_class:
                # Default fallback based on existing note or heuristics
                mapped_class = row.get("translator_note") or "keep_proper_name"
                
            row["translator_note"] = mapped_class
            
            # Decide translation
            if mapped_class.startswith("keep_"):
                row["new_translation_vi"] = src
                row["status"] = "translated"
                kept_count += 1
                modified = True
            else:
                # translate_* or manual_review_name_title
                if sid in mismatch_corrections:
                    row["new_translation_vi"] = mismatch_corrections[sid]
                    row["status"] = "translated"
                    fixed_mismatch_count += 1
                    translated_count += 1
                    modified = True
                else:
                    cache_entry = master_cache.get(src)
                    if cache_entry:
                        row["new_translation_vi"] = cache_entry.get("translation_vi", "")
                        row["status"] = "translated"
                        translated_count += 1
                        modified = True
                    else:
                        print(f"Warning: {sid} ({repr(src)}) not found in master cache!")
                        
        if modified:
            with open(f_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
    print("\n=== Integration Completed ===")
    print(f"Total rows processed: {total_processed}")
    print(f"  Rows kept as English: {kept_count}")
    print(f"  Rows translated: {translated_count}")
    print(f"  Token mismatches fixed: {fixed_mismatch_count}")

if __name__ == '__main__':
    main()
