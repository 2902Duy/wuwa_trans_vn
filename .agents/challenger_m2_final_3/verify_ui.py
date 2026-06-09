import os
import json
import glob
import pandas as pd

def main():
    json_dir = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui"
    excel_path = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\ui_translation_pack\ui_all.xlsx"

    print("Step 1: Finding and loading all JSON files...")
    json_pattern = os.path.join(json_dir, "**", "*.json")
    json_files = glob.glob(json_pattern, recursive=True)
    print(f"Found {len(json_files)} JSON files.")

    json_records = {}
    for jf in json_files:
        with open(jf, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                split_id = item.get("split_id")
                if not split_id:
                    print(f"Warning: Item without split_id in {jf}")
                    continue
                if split_id in json_records:
                    print(f"Error: Duplicate split_id {split_id} found in JSON files!")
                json_records[split_id] = item

    print(f"Loaded {len(json_records)} unique records from JSON files.")

    print("\nStep 2: Loading consolidated Excel file...")
    # Use keep_default_na=False as requested
    df_excel = pd.read_excel(excel_path, keep_default_na=False)
    excel_records_count = len(df_excel)
    print(f"Loaded {excel_records_count} rows from Excel file.")

    # 1. Row count check
    expected_rows = 13711
    if excel_records_count != expected_rows:
        print(f"FAIL: Excel row count is {excel_records_count}, expected {expected_rows}")
    else:
        print(f"PASS: Excel row count is exactly {expected_rows}")

    if len(json_records) != expected_rows:
        print(f"FAIL: Combined JSON record count is {len(json_records)}, expected {expected_rows}")
    else:
        print(f"PASS: Combined JSON record count is exactly {expected_rows}")

    # 2. Check all expected columns exist in ui_all.xlsx
    excel_cols = list(df_excel.columns)
    print(f"Columns in Excel: {excel_cols}")
    
    # We can inspect the first record of JSON to see its keys
    if json_records:
        sample_key = list(json_records.keys())[0]
        json_cols = list(json_records[sample_key].keys())
        print(f"Columns in JSON (sample): {json_cols}")
        
        # Check if all JSON columns exist in Excel
        missing_in_excel = [c for c in json_cols if c not in excel_cols]
        if missing_in_excel:
            print(f"FAIL: Columns in JSON but missing in Excel: {missing_in_excel}")
        else:
            print("PASS: All JSON columns are present in the Excel file.")

    # 3. Check sorting by source_file and original_index
    # We want to verify that the rows in the Excel file are already sorted by source_file and original_index.
    # To check this, let's compare the Excel DataFrame's order to a copy of itself sorted by source_file and original_index.
    # Note: original_index should be compared numerically.
    print("\nChecking sorting by source_file and original_index...")
    # Let's ensure types are appropriate for sorting
    df_sorted = df_excel.copy()
    # Ensure original_index is numeric for correct sorting check
    df_sorted['original_index_num'] = pd.to_numeric(df_sorted['original_index'])
    # Sort
    df_sorted = df_sorted.sort_values(by=['source_file', 'original_index_num']).drop(columns=['original_index_num'])
    
    # Reset index and compare split_id order
    excel_split_ids = list(df_excel['split_id'])
    sorted_split_ids = list(df_sorted['split_id'])
    
    is_sorted = (excel_split_ids == sorted_split_ids)
    if is_sorted:
        print("PASS: Excel file is correctly sorted by source_file and original_index.")
    else:
        print("FAIL: Excel file is NOT sorted by source_file and original_index.")
        # Find first mismatch
        for idx, (e_id, s_id) in enumerate(zip(excel_split_ids, sorted_split_ids)):
            if e_id != s_id:
                row_e = df_excel.iloc[idx]
                row_s = df_sorted.iloc[idx]
                print(f"Mismatch at Excel index {idx}:")
                print(f"  Excel row: split_id={row_e['split_id']}, source_file={row_e['source_file']}, original_index={row_e['original_index']}")
                print(f"  Sorted row: split_id={row_s['split_id']}, source_file={row_s['source_file']}, original_index={row_s['original_index']}")
                break

    # 4. 1:1 key-based comparison (by split_id) for new_translation_vi
    print("\nPerforming 1:1 key-based comparison of new_translation_vi...")
    mismatches = []
    missing_in_json = []
    missing_in_excel_ids = []

    # Check Excel records against JSON records
    for idx, row in df_excel.iterrows():
        sid = row['split_id']
        excel_val = row['new_translation_vi']
        
        # In Excel, if read with keep_default_na=False, empty strings/cells are empty strings.
        # Let's convert to string to be safe.
        excel_val_str = str(excel_val)
        
        if sid not in json_records:
            missing_in_json.append(sid)
            continue
            
        json_val = json_records[sid].get('new_translation_vi')
        json_val_str = str(json_val) if json_val is not None else ""
        
        if excel_val_str != json_val_str:
            mismatches.append({
                'split_id': sid,
                'source_file': row['source_file'],
                'excel_val': excel_val,
                'json_val': json_val
            })

    # Check JSON records against Excel split_ids
    excel_split_id_set = set(excel_split_ids)
    for sid in json_records:
        if sid not in excel_split_id_set:
            missing_in_excel_ids.append(sid)

    print(f"Mismatches in new_translation_vi: {len(mismatches)}")
    print(f"Excel split_ids missing in JSON: {len(missing_in_json)}")
    print(f"JSON split_ids missing in Excel: {len(missing_in_excel_ids)}")

    if not mismatches and not missing_in_json and not missing_in_excel_ids:
        print("PASS: 1:1 key-based comparison of new_translation_vi shows exact consistency!")
    else:
        if missing_in_json:
            print(f"Missing in JSON: {missing_in_json[:10]}")
        if missing_in_excel_ids:
            print(f"Missing in Excel: {missing_in_excel_ids[:10]}")
        if mismatches:
            print("First 10 mismatches:")
            for m in mismatches[:10]:
                print(f"  split_id={m['split_id']}, source={m['source_file']}: Excel='{m['excel_val']}' vs JSON='{m['json_val']}'")

if __name__ == "__main__":
    main()
