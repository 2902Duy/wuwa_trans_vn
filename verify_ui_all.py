import os
import json
import pandas as pd
from pathlib import Path

# Paths
ui_dir = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui"
excel_path = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\ui_translation_pack\ui_all.xlsx"
log_path = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\verify_log.txt"

def run_verification():
    log_lines = []
    
    def log(msg):
        print(msg)
        log_lines.append(msg)
        
    log("=== UI TRANSLATION VERIFICATION LOG ===")
    
    # 1. Load split JSON files
    log("Loading all split JSON files under UI directory...")
    json_records = {}
    json_split_ids = set()
    total_json_files = 0
    total_json_records = 0
    
    ui_path = Path(ui_dir)
    if not ui_path.exists():
        log(f"Error: UI JSON directory does not exist: {ui_dir}")
        write_log(log_lines)
        return
        
    json_files = list(ui_path.rglob("*.json"))
    total_json_files = len(json_files)
    log(f"Found {total_json_files} JSON files.")
    
    duplicate_split_ids_json = []
    
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
                log(f"Error reading JSON file {f_path}: {e}")
                
    log(f"Loaded {total_json_records} total JSON records. Unique split_ids: {len(json_split_ids)}")
    if duplicate_split_ids_json:
        log(f"WARNING: Found {len(duplicate_split_ids_json)} duplicate split_ids in JSON files:")
        for dup in duplicate_split_ids_json[:10]:
            log(f"  - Split ID: {dup[0]} in {dup[1]} and {dup[2]}")
    else:
        log("No duplicate split_ids found in JSON files.")
        
    # 2. Load Excel file
    log(f"\nLoading consolidated Excel file: {excel_path}...")
    if not os.path.exists(excel_path):
        log(f"Error: Excel file does not exist: {excel_path}")
        write_log(log_lines)
        return
        
    try:
        df = pd.read_excel(excel_path, dtype=str, keep_default_na=False)
        log(f"Excel loaded successfully. Rows: {len(df)}, Columns: {list(df.columns)}")
    except Exception as e:
        log(f"Error loading Excel file: {e}")
        write_log(log_lines)
        return
        
    # 3. Verify columns
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
        # Check column order
        current_cols = list(df.columns)[:len(expected_cols)]
        if current_cols == expected_cols:
            log("Column order is exactly correct.")
        else:
            log(f"WARNING: Column order mismatch. Expected {expected_cols}, got {current_cols}")
            
    # 4. Perform 1:1 key comparison
    excel_split_ids = set(df['split_id'].dropna().tolist())
    log(f"\nUnique split_ids in Excel: {len(excel_split_ids)}")
    
    missing_in_excel = json_split_ids - excel_split_ids
    missing_in_json = excel_split_ids - json_split_ids
    
    if missing_in_excel:
        log(f"ERROR: {len(missing_in_excel)} split_ids in JSON but missing in Excel!")
        for split_id in list(missing_in_excel)[:10]:
            log(f"  - Missing split_id in Excel: {split_id}")
    else:
        log("No split_ids in JSON are missing in Excel.")
        
    if missing_in_json:
        log(f"ERROR: {len(missing_in_json)} split_ids in Excel but missing in JSON!")
        for split_id in list(missing_in_json)[:10]:
            log(f"  - Missing split_id in JSON: {split_id}")
    else:
        log("No split_ids in Excel are missing in JSON.")
        
    # 5. Value comparison
    log("\nPerforming record-by-record value comparison...")
    mismatches = []
    empty_translation_count = 0
    null_value_count = 0
    
    for idx, row in df.iterrows():
        split_id = row['split_id']
        if pd.isna(split_id) or not split_id:
            log(f"Row {idx} has missing split_id in Excel!")
            continue
            
        if split_id not in json_records:
            # Already reported as missing in JSON
            continue
            
        json_rec = json_records[split_id]["data"]
        
        # Check each column value
        for col in expected_cols:
            excel_val = row.get(col, "")
            if pd.isna(excel_val):
                excel_val = ""
            excel_val = str(excel_val).strip()
            
            # original_index in JSON might be int, convert to str
            json_val = json_rec.get(col, "")
            if json_val is None:
                json_val = ""
            json_val = str(json_val).strip()
            
            # Normalize newlines for comparison
            excel_val_norm = excel_val.replace('\r\n', '\n').replace('\r', '\n')
            json_val_norm = json_val.replace('\r\n', '\n').replace('\r', '\n')
            
            if excel_val_norm != json_val_norm:
                mismatches.append({
                    "split_id": split_id,
                    "column": col,
                    "excel_val": excel_val,
                    "json_val": json_val,
                    "file": json_records[split_id]["rel_path"]
                })
                
        # Check edge cases: empty strings or nulls in translations
        new_trans_excel = row.get('new_translation_vi')
        if pd.isna(new_trans_excel) or str(new_trans_excel).strip() == "":
            empty_translation_count += 1
            source_en_excel = row.get('source_en', '')
            if not pd.isna(source_en_excel) and str(source_en_excel).strip() != "":
                log(f"WARNING: Empty translation for non-empty source! Split ID: {split_id}, Source: '{source_en_excel}'")
                
    log(f"Value comparison finished. Found {len(mismatches)} cell mismatches.")
    if mismatches:
        log(f"ERROR: Detailed cell mismatches (first 20):")
        for m in mismatches[:20]:
            log(f"  - Split ID: {m['split_id']}, Column: {m['column']}")
            log(f"    Excel: '{m['excel_val']}'")
            log(f"    JSON:  '{m['json_val']}'")
            log(f"    File:  {m['file']}")
    else:
        log("SUCCESS: All column values match exactly between JSON and Excel files!")
        
    # 6. Verify sorting
    log("\nVerifying row sorting order in Excel...")
    df_temp = df.copy()
    # original_index must be compared as integer for sorting to match correct_ui.py
    df_temp['original_index_int'] = df_temp['original_index'].astype(float).astype(int)
    
    # Let's recreate sorting logic: sorted by ['source_file', 'original_index_int']
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
        
    # Summary of findings
    log("\n=== SUMMARY OF FINDINGS ===")
    log(f"1. Total JSON records: {total_json_records}")
    log(f"2. Total Excel records: {len(df)}")
    log(f"3. Duplicate JSON IDs: {len(duplicate_split_ids_json)}")
    log(f"4. Missing in Excel: {len(missing_in_excel)}")
    log(f"5. Missing in JSON: {len(missing_in_json)}")
    log(f"6. Total Cell Mismatches: {len(mismatches)}")
    log(f"7. Sorting Order Valid: {is_sorted}")
    log(f"8. Empty Translations (Excel): {empty_translation_count}")
    
    write_log(log_lines)

def write_log(log_lines):
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    print(f"Log written to {log_path}")

if __name__ == "__main__":
    run_verification()
