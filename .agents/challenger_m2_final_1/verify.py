import os
import json
import pandas as pd
from pathlib import Path

# Absolute paths
ui_dir = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui"
excel_path = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\ui_translation_pack\ui_all.xlsx"
log_path = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\.agents\challenger_m2_final_1\verification_log.txt"

def run_verification():
    log_lines = []
    
    def log(msg):
        print(msg)
        log_lines.append(msg)
        
    log("=== CHALLENGER FINAL UI VERIFICATION START ===")
    
    # 1. Load split JSON files
    log("Scanning and loading split JSON files...")
    json_records = {}
    json_split_ids = set()
    total_json_files = 0
    total_json_records = 0
    duplicate_split_ids_json = []
    
    ui_path = Path(ui_dir)
    if not ui_path.exists():
        log(f"ERROR: UI JSON directory does not exist: {ui_dir}")
        write_log(log_lines)
        return
        
    json_files = list(ui_path.rglob("*.json"))
    total_json_files = len(json_files)
    log(f"Found {total_json_files} JSON files.")
    
    for f_path in json_files:
        with open(f_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if not isinstance(data, list):
                    data = [data]
                for record in data:
                    total_json_records += 1
                    split_id = record.get("split_id")
                    if not split_id:
                        log(f"Warning: Record in {f_path.name} is missing 'split_id'.")
                        continue
                    if split_id in json_records:
                        duplicate_split_ids_json.append((split_id, f_path.name, json_records[split_id]["file_name"]))
                    json_records[split_id] = {
                        "data": record,
                        "file_name": f_path.name,
                        "rel_path": str(f_path.relative_to(ui_path))
                    }
                    json_split_ids.add(split_id)
            except Exception as e:
                log(f"ERROR: Failed to read JSON file {f_path}: {e}")
                
    log(f"Loaded {total_json_records} total JSON records. Unique split_ids: {len(json_split_ids)}")
    if duplicate_split_ids_json:
        log(f"WARNING: Found {len(duplicate_split_ids_json)} duplicate split_ids in JSON files:")
        for dup in duplicate_split_ids_json[:10]:
            log(f"  - Split ID: {dup[0]} in {dup[1]} and {dup[2]}")
    else:
        log("No duplicate split_ids found in JSON files.")
        
    # 2. Load Excel file
    log(f"\nLoading Excel file: {excel_path}...")
    if not os.path.exists(excel_path):
        log(f"ERROR: Excel file does not exist: {excel_path}")
        write_log(log_lines)
        return
        
    try:
        # Load Excel with keep_default_na=False to prevent parsing "None" as NaN
        df = pd.read_excel(excel_path, dtype=str, keep_default_na=False)
        log(f"Excel loaded successfully. Rows: {len(df)}, Columns: {list(df.columns)}")
    except Exception as e:
        log(f"ERROR: Failed to load Excel file: {e}")
        write_log(log_lines)
        return
        
    # 3. Verify columns exist and are sorted correctly
    expected_cols = [
        'split_id', 'prompt_domain', 'prompt_file', 'source_file',
        'original_index', 'database', 'table', 'primary_key_column',
        'primary_key', 'column', 'category', 'source_en',
        'new_translation_vi', 'translator_note'
    ]
    
    cols_exist = True
    for col in expected_cols:
        if col not in df.columns:
            log(f"ERROR: Expected column '{col}' is missing in Excel!")
            cols_exist = False
            
    if cols_exist:
        log("All expected columns exist in Excel.")
        current_cols = list(df.columns)[:len(expected_cols)]
        if current_cols == expected_cols:
            log("Column order in Excel is exactly correct.")
        else:
            log(f"WARNING: Column order mismatch. Expected {expected_cols}, got {current_cols}")
            
    # Check if there are any extra columns
    extra_cols = set(df.columns) - set(expected_cols)
    if extra_cols:
        log(f"WARNING: Found extra columns in Excel: {extra_cols}")
    else:
        log("No extra columns in Excel.")
        
    # 4. Perform 1:1 key comparison
    excel_split_ids = set(df['split_id'].dropna().tolist())
    log(f"\nUnique split_ids in Excel: {len(excel_split_ids)}")
    
    missing_in_excel = json_split_ids - excel_split_ids
    missing_in_json = excel_split_ids - json_split_ids
    
    if missing_in_excel:
        log(f"ERROR: {len(missing_in_excel)} split_ids exist in JSON but missing in Excel!")
        for split_id in list(missing_in_excel)[:10]:
            log(f"  - Missing in Excel: {split_id}")
    else:
        log("SUCCESS: No split_ids in JSON are missing in Excel.")
        
    if missing_in_json:
        log(f"ERROR: {len(missing_in_json)} split_ids exist in Excel but missing in JSON!")
        for split_id in list(missing_in_json)[:10]:
            log(f"  - Missing in JSON: {split_id}")
    else:
        log("SUCCESS: No split_ids in Excel are missing in JSON.")
        
    # 5. Value comparison and edge cases
    log("\nPerforming record-by-record value comparison...")
    mismatches = []
    empty_translation_count = 0
    empty_translation_details = []
    nan_null_count = 0
    nan_null_details = []
    whitespace_mismatches = []
    
    for idx, row in df.iterrows():
        split_id = row['split_id']
        if pd.isna(split_id) or not split_id:
            log(f"Row {idx} has missing split_id in Excel!")
            continue
            
        if split_id not in json_records:
            continue
            
        json_rec = json_records[split_id]["data"]
        
        # Check each expected column value
        for col in expected_cols:
            excel_val = row.get(col, "")
            json_val = json_rec.get(col, "")
            
            # Check for actual pandas NaN/None objects (should be none since keep_default_na=False)
            if pd.isna(excel_val) or excel_val is None:
                nan_null_count += 1
                nan_null_details.append((split_id, col, "Excel", excel_val))
                excel_val = ""
            if pd.isna(json_val) or json_val is None:
                nan_null_count += 1
                nan_null_details.append((split_id, col, "JSON", json_val))
                json_val = ""
                
            excel_val_str = str(excel_val)
            json_val_str = str(json_val)
            
            # Check for leading/trailing whitespace difference only
            if excel_val_str != json_val_str and excel_val_str.strip() == json_val_str.strip():
                whitespace_mismatches.append({
                    "split_id": split_id,
                    "column": col,
                    "excel_val": repr(excel_val_str),
                    "json_val": repr(json_val_str)
                })
            
            # Normalize newlines for strict value comparison
            excel_val_norm = excel_val_str.replace('\r\n', '\n').replace('\r', '\n')
            json_val_norm = json_val_str.replace('\r\n', '\n').replace('\r', '\n')
            
            if excel_val_norm != json_val_norm:
                mismatches.append({
                    "split_id": split_id,
                    "column": col,
                    "excel_val": excel_val_str,
                    "json_val": json_val_str,
                    "file": json_records[split_id]["rel_path"]
                })
                
        # Check edge cases: empty strings or nulls in translations when source is not empty
        new_trans_excel = row.get('new_translation_vi', '')
        source_en_excel = row.get('source_en', '')
        if not str(new_trans_excel).strip():
            if str(source_en_excel).strip():
                empty_translation_count += 1
                empty_translation_details.append((split_id, str(source_en_excel)))
                
    log(f"Value comparison finished. Found {len(mismatches)} cell mismatches.")
    if mismatches:
        log(f"ERROR: Detailed cell mismatches (first 20 shown):")
        for m in mismatches[:20]:
            log(f"  - Split ID: {m['split_id']}, Column: {m['column']}")
            log(f"    Excel: '{m['excel_val']}'")
            log(f"    JSON:  '{m['json_val']}'")
            log(f"    File:  {m['file']}")
    else:
        log("SUCCESS: All column values match exactly between JSON and Excel files (100% 1:1 match)!")
        
    if whitespace_mismatches:
        log(f"WARNING: Found {len(whitespace_mismatches)} whitespace-only mismatches (first 10 shown):")
        for w in whitespace_mismatches[:10]:
            log(f"  - Split ID: {w['split_id']}, Column: {w['column']}, Excel: {w['excel_val']}, JSON: {w['json_val']}")
            
    if nan_null_count > 0:
        log(f"WARNING: Found {nan_null_count} NaN/None values parsed in Excel or JSON:")
        for detail in nan_null_details[:10]:
            log(f"  - Split ID: {detail[0]}, Column: {detail[1]} in {detail[2]} has value {detail[3]}")
    else:
        log("No NaN/None values parsed incorrectly.")
        
    if empty_translation_count > 0:
        log(f"WARNING: Found {empty_translation_count} empty translations for non-empty English sources:")
        for detail in empty_translation_details[:10]:
            log(f"  - Split ID: {detail[0]}, English Source: '{detail[1]}'")
    else:
        log("All non-empty English sources have translations.")
        
    # 6. Verify sorting
    log("\nVerifying row sorting order in Excel...")
    df_temp = df.copy()
    try:
        df_temp['original_index_int'] = df_temp['original_index'].astype(float).astype(int)
        
        # Sort by source_file (alphabetic) and original_index_int (numeric)
        sorted_df = df_temp.sort_values(by=['source_file', 'original_index_int']).reset_index(drop=True)
        df_temp = df_temp.reset_index(drop=True)
        
        is_sorted = True
        for i in range(len(df_temp)):
            if df_temp.loc[i, 'split_id'] != sorted_df.loc[i, 'split_id']:
                is_sorted = False
                log(f"Sorting mismatch at row {i}: Excel row has '{df_temp.loc[i, 'split_id']}', but sorted expects '{sorted_df.loc[i, 'split_id']}'.")
                break
                
        if is_sorted:
            log("SUCCESS: Excel rows are sorted correctly by source_file and original_index.")
        else:
            log("ERROR: Excel sorting order is incorrect!")
    except Exception as e:
        log(f"ERROR: Failed to verify sorting order due to exception: {e}")
        is_sorted = False
        
    # Summary of findings
    log("\n=== SUMMARY OF FINDINGS ===")
    log(f"1. Total JSON records: {total_json_records}")
    log(f"2. Total Excel records: {len(df)}")
    log(f"3. Duplicate JSON IDs: {len(duplicate_split_ids_json)}")
    log(f"4. Missing in Excel: {len(missing_in_excel)}")
    log(f"5. Missing in JSON: {len(missing_in_json)}")
    log(f"6. Total Cell Mismatches: {len(mismatches)}")
    log(f"7. Whitespace-Only Mismatches: {len(whitespace_mismatches)}")
    log(f"8. NaN/None Values: {nan_null_count}")
    log(f"9. Empty Translations for non-empty source: {empty_translation_count}")
    log(f"10. Sorting Order Valid: {is_sorted}")
    
    write_log(log_lines)
    log("=== CHALLENGER FINAL UI VERIFICATION END ===")

def write_log(log_lines):
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    print(f"Log written to {log_path}")

if __name__ == "__main__":
    run_verification()
