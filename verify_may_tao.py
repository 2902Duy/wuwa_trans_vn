import json
import os
import re

ROOT = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json"

def main():
    with open('proposed_may_tao.json', 'r', encoding='utf-8') as f:
        corrections = json.load(f)

    compounds = ['lông mày', 'chân mày', 'tao nhã', 'tao ngộ', 'mày râu', 'mày đay', 'tao loạn']
    pattern = re.compile(r'\b(mày|tao)\b', re.IGNORECASE)

    errors = []
    for c in corrections:
        split_id = c['split_id']
        rel_path = c['file']
        full_path = os.path.join(ROOT, rel_path)
        
        with open(full_path, 'r', encoding='utf-8') as f:
            data = json.load(f, strict=False)
            
        item = next((x for x in data if x.get('split_id') == split_id), None)
        if not item:
            errors.append(f"{split_id}: Not found in JSON file")
            continue
            
        actual = item.get('new_translation_vi', '')
        expected = c['new_translation_vi']
        
        if actual != expected:
            errors.append(f"{split_id}: Mismatch!\n  Expected: {repr(expected)}\n  Actual:   {repr(actual)}")
            
        if pattern.search(actual):
            # Check if it is a compound
            vi_lower = actual.lower()
            is_compound = False
            for comp in compounds:
                if comp in vi_lower:
                    is_compound = True
            if not is_compound:
                errors.append(f"{split_id}: Still contains raw pronoun 'mày' or 'tao'! Value: {repr(actual)}")

    print(f"Mày/Tao Verification finished. Total errors: {len(errors)}")
    for e in errors[:50]:
        print(e)

if __name__ == '__main__':
    main()
