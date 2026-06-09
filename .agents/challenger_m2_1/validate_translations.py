import os
import json
import pandas as pd
import numpy as np
from pathlib import Path

def validate():
    json_dir = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui"
    excel_path = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\ui_translation_pack\ui_all.xlsx"
    output_path = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\.agents\challenger_m2_1\validation_output.txt"
    
    log_lines = []
    def log(msg):
        print(msg)
        log_lines.append(msg)

    log("=== TRANSLATION VALIDATION START ===")
    
    # 1. Load JSON data
    json_records = {}
    json_files_count = 0
    total_json_records = 0
    duplicate_json_ids = []
    
    if not os.path.exists(json_dir):
        log(f"ERROR: JSON directory does not exist: {json_dir}")
        return
        
    json_path = Path(json_dir)
    json_files = list(json_path.rglob("*.json"))
    json_files_count = len(json_files)
    
    for f_path in json_files:
        with open(f_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if not isinstance(data, list):
                    data = [data]
                for item in data:
                    total_json_records += 1
                    split_id = item.get('split_id')
                    if not split_id:
                        log(f"Warning: Item in {f_path.name} has no split_id: {item}")
                        continue
                    if split_id in json_records:
                        duplicate_json_ids.append((split_id, f_path.name, json_records[split_id]['_file']))
                    item['_file'] = str(f_path.relative_to(json_path))
                    json_records[split_id] = item
            except Exception as e:
                log(f"ERROR: Failed to read {f_path}: {e}")

    log(f"Total split JSON files read: {json_files_count}")
    log(f"Total records in JSON: {total_json_records}")
    log(f"Total unique records in JSON: {len(json_records)}")
    if duplicate_json_ids:
        log(f"WARNING: Found {len(duplicate_json_ids)} duplicate split_ids in JSON files:")
        for dup in duplicate_json_ids[:10]:
            log(f"  - Split ID: {dup[0]} in {dup[1]} and {dup[2]}")
    else:
        log("No duplicate split_ids found in JSON files.")

    # 2. Load Excel data
    if not os.path.exists(excel_path):
        log(f"ERROR: Excel file does not exist: {excel_path}")
        return

    try:
        # Load Excel with keep_default_na=False to avoid interpreting "None" or "null" as NaN
        df = pd.read_excel(excel_path, keep_default_na=False, dtype=str)
        log("Excel loaded successfully.")
    except Exception as e:
        log(f"ERROR: Failed to load Excel file: {e}")
        return

    excel_records_count = len(df)
    log(f"Total records in Excel: {excel_records_count}")

    # Check columns
    columns = list(df.columns)
    log(f"Columns in Excel: {columns}")
    
    expected_cols = [
        'split_id', 'prompt_domain', 'prompt_file', 'source_file',
        'original_index', 'database', 'table', 'primary_key_column',
        'primary_key', 'column', 'category', 'source_en',
        'new_translation_vi', 'translator_note'
    ]
    
    missing_cols = [c for c in expected_cols if c not in columns]
    if missing_cols:
        log(f"ERROR: Missing expected columns in Excel: {missing_cols}")
    else:
        log("All expected columns exist in Excel.")
        # Check column order
        current_cols = columns[:len(expected_cols)]
        if current_cols == expected_cols:
            log("Column order in Excel is exactly correct.")
        else:
            log(f"WARNING: Column order mismatch. Expected {expected_cols}, got {current_cols}")

    # 3. 1:1 Key comparison
    excel_records = {}
    excel_duplicates = []
    
    for index, row in df.iterrows():
        split_id = row['split_id'].strip()
        if not split_id:
            log(f"Warning: Excel row {index} has null/empty split_id.")
            continue
        
        if split_id in excel_records:
            excel_duplicates.append(split_id)
        
        excel_records[split_id] = row.to_dict()

    if excel_duplicates:
        log(f"Warning: Duplicate split_ids in Excel ({len(excel_duplicates)}): {excel_duplicates[:10]}")
    else:
        log("No duplicate split_ids found in Excel.")

    # Find missing keys
    json_keys = set(json_records.keys())
    excel_keys = set(excel_records.keys())
    
    missing_in_excel = json_keys - excel_keys
    missing_in_json = excel_keys - json_keys
    
    log(f"Keys in JSON but missing in Excel: {len(missing_in_excel)}")
    if missing_in_excel:
        log(f"Sample missing in Excel: {list(missing_in_excel)[:10]}")
        
    log(f"Keys in Excel but missing in JSON: {len(missing_in_json)}")
    if missing_in_json:
        log(f"Sample missing in JSON: {list(missing_in_json)[:10]}")

    # 4. Compare translation values and all column values
    mismatches = []
    empty_translation_count = 0
    empty_translation_list = []
    
    common_keys = json_keys.intersection(excel_keys)
    log(f"Common keys to compare: {len(common_keys)}")
    
    for key in sorted(common_keys):
        j_rec = json_records[key]
        e_rec = excel_records[key]
        
        # Check all expected columns
        for col in expected_cols:
            j_val = j_rec.get(col, "")
            if j_val is None:
                j_val = ""
            j_val = str(j_val).strip()
            
            e_val = e_rec.get(col, "")
            if e_val is None:
                e_val = ""
            e_val = str(e_val).strip()
            
            # Normalize newlines for comparison
            j_val_norm = j_val.replace('\r\n', '\n').replace('\r', '\n')
            e_val_norm = e_val.replace('\r\n', '\n').replace('\r', '\n')
            
            if j_val_norm != e_val_norm:
                mismatches.append({
                    'split_id': key,
                    'column': col,
                    'json': j_val,
                    'excel': e_val,
                    'json_file': j_rec['_file']
                })
                
        # Check for empty translations in Excel
        new_trans_excel = e_rec.get('new_translation_vi', '').strip()
        if not new_trans_excel:
            empty_translation_count += 1
            empty_translation_list.append(key)

    log(f"Total cell mismatches found: {len(mismatches)}")
    if mismatches:
        log(f"ERROR: Detailed cell mismatches (first 20):")
        for m in mismatches[:20]:
            log(f"  - Split ID: {m['split_id']}, Column: {m['column']}")
            log(f"    Excel: '{m['excel']}'")
            log(f"    JSON:  '{m['json']}'")
            log(f"    File:  {m['json_file']}")
    else:
        log("SUCCESS: All column values match exactly between JSON and Excel files (100% 1:1 match)!")

    log(f"Total empty translations in Excel: {empty_translation_count}")
    if empty_translation_count > 0:
        log(f"Sample keys with empty translations in Excel: {empty_translation_list[:10]}")

    # 5. Verify sorting order in Excel
    log("\nVerifying row sorting order in Excel...")
    df_temp = df.copy()
    # original_index must be compared as integer for sorting to match correct_ui.py
    df_temp['original_index_int'] = df_temp['original_index'].astype(float).astype(int)
    
    # Recreate sorting logic: sorted by ['source_file', 'original_index_int']
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

    # Write output to file
    try:
        with open(output_path, 'w', encoding='utf-8') as out_f:
            out_f.write("\n".join(log_lines))
        print(f"Validation output written to {output_path}")
    except Exception as e:
        print(f"Failed to write output to file: {e}")

    log("=== TRANSLATION VALIDATION END ===")

if __name__ == '__main__':
    validate()
