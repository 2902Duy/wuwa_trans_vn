import json
import os

ROOT = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json"

def main():
    with open('proposed_may_tao.json', 'r', encoding='utf-8') as f:
        corrections = json.load(f)

    # Group corrections by file path
    by_file = {}
    for c in corrections:
        fpath = c['file']
        if fpath not in by_file:
            by_file[fpath] = []
        by_file[fpath].append(c)

    updated_count = 0
    files_processed = 0
    
    for rel_path, items in by_file.items():
        full_path = os.path.join(ROOT, rel_path)
        if not os.path.exists(full_path):
            print(f"Warning: File {full_path} not found.")
            continue
            
        with open(full_path, 'r', encoding='utf-8') as f:
            data = json.load(f, strict=False)

        # Build lookup dict for the target file list items
        lookup = {item['split_id']: item for item in data if 'split_id' in item}

        file_changed = False
        for c in items:
            split_id = c['split_id']
            if split_id in lookup:
                new_vi = c['new_translation_vi']
                old_vi = lookup[split_id].get('new_translation_vi', '')
                if old_vi != new_vi:
                    lookup[split_id]['new_translation_vi'] = new_vi
                    file_changed = True
                    updated_count += 1

        if file_changed:
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            files_processed += 1

    print(f"Successfully updated {updated_count} items across {files_processed} JSON files.")

if __name__ == '__main__':
    main()
