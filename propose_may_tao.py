import json
import re

def clean_may_tao(en, vi):
    is_hostile = False
    hostile_en_keywords = [
        'exile', 'fractsidus', 'bastard', 'scum', 'fool', 'die', 'death', 'kill', 
        'fight', 'weak', 'trash', 'thief', 'rob', 'shut up', 'get out', 'shut your mouth', 
        'damn', 'curse', 'hate', 'enemy', 'target', 'clone', 'phantom', 'thug', 'brute'
    ]
    hostile_vi_keywords = [
        'giết', 'chết', 'lưu đày', 'cút', 'cướp', 'ngu', 'hèn', 'ngươi', 'ta', 
        'chửi', 'đánh', 'mạng', 'kẻ thù', 'hạ đẳng', 'rác rưởi', 'câm mồm', 'nhãi ranh'
    ]
    
    en_lower = en.lower()
    vi_lower = vi.lower()
    
    if any(k in en_lower for k in hostile_en_keywords) or any(k in vi_lower for k in hostile_vi_keywords):
        is_hostile = True

    compounds = [
        ('lông mày', '__LONG_MAY__'),
        ('Lông mày', '__LONG_MAY_CAP__'),
        ('chân mày', '__CHAN_MAY__'),
        ('Chân mày', '__CHAN_MAY_CAP__'),
        ('tao nhã', '__TAO_NHA__'),
        ('Tao nhã', '__TAO_NHA_CAP__'),
        ('tao ngộ', '__TAO_NGO__'),
        ('Tao ngộ', '__TAO_NGO_CAP__'),
        ('tao loạn', '__TAO_LOAN__'),
        ('Tao loạn', '__TAO_LOAN_CAP__'),
        ('mày râu', '__MAY_RAU__'),
        ('Mày râu', '__MAY_RAU_CAP__'),
        ('mày đay', '__MAY_DAY__'),
        ('Mày đay', '__MAY_DAY_CAP__')
    ]
    
    masked_vi = vi
    for comp, mask in compounds:
        masked_vi = masked_vi.replace(comp, mask)
        
    def repl_may(match):
        word = match.group(0)
        is_cap = word[0].isupper()
        if is_hostile:
            return "Ngươi" if is_cap else "ngươi"
        else:
            return "Cậu" if is_cap else "cậu"
            
    def repl_tao(match):
        word = match.group(0)
        is_cap = word[0].isupper()
        if is_hostile:
            return "Ta" if is_cap else "ta"
        else:
            return "Tôi" if is_cap else "tôi"
            
    replaced_vi = re.sub(r'\b(mày)\b', repl_may, masked_vi, flags=re.IGNORECASE)
    replaced_vi = re.sub(r'\b(tao)\b', repl_tao, replaced_vi, flags=re.IGNORECASE)
    
    for comp, mask in compounds:
        replaced_vi = replaced_vi.replace(mask, comp)
        
    return replaced_vi

def main():
    with open('found_may_tao.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    proposed = []
    for item in data:
        en = item['item']['source_en']
        vi = item['item']['new_translation_vi']
        new_vi = clean_may_tao(en, vi)
        proposed.append({
            'split_id': item['item']['split_id'],
            'file': item['file'],
            'index': item['index'],
            'source_en': en,
            'old_translation_vi': vi,
            'new_translation_vi': new_vi
        })

    with open('proposed_may_tao.json', 'w', encoding='utf-8') as out:
        json.dump(proposed, out, ensure_ascii=False, indent=2)
    print(f'Wrote {len(proposed)} proposed changes to proposed_may_tao.json')

if __name__ == '__main__':
    main()
