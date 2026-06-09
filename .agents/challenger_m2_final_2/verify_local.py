import os
import json
import pandas as pd
from openpyxl import load_workbook
from pathlib import Path

ui_dir = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui"
excel_path = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\ui_translation_pack\ui_all.xlsx"
violation_report_path = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\reports\translation_surface_audit\targeted_leftovers_post_final_fix.json"

def verify():
    print("--- Challenger Local Verification ---")
    
    # 1. Load Excel with keep_default_na=False to avoid interpreting "None" as NaN
    print(f"Loading Excel: {excel_path}")
    df = pd.read_excel(excel_path, dtype=str, keep_default_na=False)
    print(f"Excel rows: {len(df)}")
    
    # 2. Check columns and ordering
    expected_cols = [
        'split_id', 'prompt_domain', 'prompt_file', 'source_file',
        'original_index', 'database', 'table', 'primary_key_column',
        'primary_key', 'column', 'category', 'source_en',
        'new_translation_vi', 'translator_note'
    ]
    cols = list(df.columns)
    print(f"Excel Columns: {cols}")
    
    # Check if exact order and names match
    if cols[:len(expected_cols)] == expected_cols:
        print("Task 1: Columns are correct and exactly ordered.")
    else:
        print("Task 1 FAILED: Columns or ordering mismatch!")
        print(f"Expected: {expected_cols}")
        print(f"Got: {cols[:len(expected_cols)]}")
        
    # 3. Check sorting
    # Convert original_index to int for correct numeric sorting
    df_temp = df.copy()
    df_temp['original_index_int'] = df_temp['original_index'].astype(int)
    sorted_df = df_temp.sort_values(by=['source_file', 'original_index_int']).reset_index(drop=True)
    df_temp = df_temp.reset_index(drop=True)
    
    is_sorted = True
    for i in range(len(df_temp)):
        if df_temp.loc[i, 'split_id'] != sorted_df.loc[i, 'split_id']:
            is_sorted = False
            print(f"Task 2 FAILED: Row {i} sorting mismatch. Excel has {df_temp.loc[i, 'split_id']}, expected {sorted_df.loc[i, 'split_id']}")
            break
    if is_sorted:
        print("Task 2: Rows are correctly sorted by source_file and original_index.")
        
    # 4. Check for duplicates in Excel split_ids
    split_ids = df['split_id'].tolist()
    unique_split_ids = set(split_ids)
    if len(split_ids) != len(unique_split_ids):
        print(f"Task 3 FAILED: Excel contains duplicate split_ids!")
        dups = [item for item, count in pd.Series(split_ids).value_counts().items() if count > 1]
        print(f"Duplicates: {dups[:10]}")
    else:
        print("Task 3: No duplicate keys/split_ids in Excel.")
        
    # 5. Compare Excel cell values with split JSON files
    print("Loading all JSON files...")
    ui_path = Path(ui_dir)
    json_files = list(ui_path.rglob("*.json"))
    json_records = {}
    for f_path in json_files:
        with open(f_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                data = [data]
            for record in data:
                split_id = record.get("split_id")
                if split_id:
                    json_records[split_id] = record
                    
    print(f"Loaded {len(json_records)} unique records from JSON files.")
    
    # Perform 1:1 check
    excel_split_ids = set(split_ids)
    json_split_ids = set(json_records.keys())
    
    if excel_split_ids != json_split_ids:
        print(f"FAILED: Key mismatch! Excel split_ids: {len(excel_split_ids)}, JSON split_ids: {len(json_split_ids)}")
        print(f"Only in Excel: {list(excel_split_ids - json_split_ids)[:10]}")
        print(f"Only in JSON: {list(json_split_ids - excel_split_ids)[:10]}")
    else:
        print("Excel and JSON contain the exact same split_ids.")
        
    mismatches = []
    for idx, row in df.iterrows():
        split_id = row['split_id']
        if split_id not in json_records:
            continue
        json_rec = json_records[split_id]
        for col in expected_cols:
            excel_val = str(row.get(col, "")).strip()
            json_val = str(json_rec.get(col, "")).strip()
            # Normalize newlines
            excel_val_norm = excel_val.replace('\r\n', '\n').replace('\r', '\n')
            json_val_norm = json_val.replace('\r\n', '\n').replace('\r', '\n')
            
            if excel_val_norm != json_val_norm:
                mismatches.append((split_id, col, excel_val, json_val))
                
    if mismatches:
        print(f"FAILED: Found {len(mismatches)} mismatches between Excel and JSON!")
        for m in mismatches[:20]:
            print(f"  Split ID: {m[0]}, Column: {m[1]} | Excel: '{m[2]}' | JSON: '{m[3]}'")
    else:
        print("SUCCESS: Excel and JSON match exactly on all column values!")
        
    # 6. Verify violation report file
    if os.path.exists(violation_report_path):
        with open(violation_report_path, "r", encoding="utf-8") as f:
            v_data = json.load(f)
        print(f"Task 4: Violation report file content: {v_data}")
        if v_data == []:
            print("Task 4: Violation report file is empty array [].")
        else:
            print("Task 4 FAILED: Violation report file contains violations!")
    else:
        print(f"Task 4: Violation report file not found at {violation_report_path}")

if __name__ == "__main__":
    verify()
